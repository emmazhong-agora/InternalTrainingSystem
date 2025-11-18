from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
from fastapi import UploadFile
import logging
from datetime import datetime

from app.models.video import Video, VideoCategory
from app.schemas.video import VideoCreate, VideoUpdate
from app.services.s3_service import s3_service
from app.services.vector_store_service import vector_store_service
from app.services.transcript_service import transcript_service

# Configure logging
logger = logging.getLogger(__name__)


class VideoService:
    """Service for video-related operations."""

    @staticmethod
    def _enrich_video_with_presigned_urls(video: Video) -> Video:
        """
        Enrich video object with presigned URLs for secure access.

        Args:
            video: Video object to enrich

        Returns:
            Video object with presigned URLs (24 hour expiration)
        """
        if video:
            # Generate presigned URLs with 24 hour expiration
            video.video_url = s3_service.generate_presigned_url_from_s3_url(video.video_url, expiration=86400)
            video.transcript_url = s3_service.generate_presigned_url_from_s3_url(video.transcript_url, expiration=86400)

            if video.thumbnail_url:
                video.thumbnail_url = s3_service.generate_presigned_url_from_s3_url(video.thumbnail_url, expiration=86400)

            # Enrich materials with presigned URLs
            if video.materials:
                for material in video.materials:
                    material.file_url = s3_service.generate_presigned_url_from_s3_url(material.file_url, expiration=86400)

        return video

    @staticmethod
    def create_video(
        db: Session,
        video_data: VideoCreate,
        video_file: UploadFile,
        transcript_file: UploadFile,
        uploaded_by: int
    ) -> Optional[Video]:
        """Create a new video with file uploads."""

        logger.info(f"Starting video upload: {video_data.title}")
        logger.info(f"Video file: {video_file.filename}, Content-Type: {video_file.content_type}")
        logger.info(f"Transcript file: {transcript_file.filename}, Content-Type: {transcript_file.content_type}")

        # Upload video file to S3
        logger.info("Uploading video file to S3...")
        video_url = s3_service.upload_file(
            video_file.file,
            "videos",
            video_file.filename,
            video_file.content_type
        )

        if not video_url:
            logger.error("Video file upload failed")
            return None

        logger.info(f"Video file uploaded successfully: {video_url}")

        # Upload transcript file to S3
        logger.info("Uploading transcript file to S3...")
        transcript_url = s3_service.upload_file(
            transcript_file.file,
            "transcripts",
            transcript_file.filename,
            transcript_file.content_type
        )

        if not transcript_url:
            logger.error("Transcript file upload failed, cleaning up video file...")
            # Clean up video file if transcript upload fails
            s3_service.delete_file(video_url)
            return None

        logger.info(f"Transcript file uploaded successfully: {transcript_url}")

        # Get file size
        logger.info("Getting file size from S3...")
        file_size = s3_service.get_file_size(video_url)
        logger.info(f"File size: {file_size} bytes")

        # Create video record
        logger.info("Creating video record in database...")
        db_video = Video(
            title=video_data.title,
            description=video_data.description,
            video_url=video_url,
            transcript_url=transcript_url,
            category_id=video_data.category_id,
            tags=video_data.tags,
            uploaded_by=uploaded_by,
            file_size=file_size,
            vectorization_status="pending"  # Initial status
        )

        db.add(db_video)
        db.commit()
        db.refresh(db_video)

        logger.info(f"Video created successfully with ID: {db_video.id}")

        # Trigger VTT vectorization immediately after upload
        logger.info(f"Starting VTT vectorization for video {db_video.id}...")
        VideoService._vectorize_transcript(db, db_video)

        return db_video

    @staticmethod
    def _vectorize_transcript(db: Session, video: Video) -> None:
        """
        Vectorize video transcript and store in ChromaDB.
        Updates video vectorization status in database.

        Args:
            db: Database session
            video: Video object with transcript_url
        """
        try:
            # Update status to processing
            video.vectorization_status = "processing"
            db.commit()

            logger.info(f"Loading transcript from S3: {video.transcript_url}")

            # Load, parse, and chunk transcript from S3
            transcript_chunks = transcript_service.process_video_transcript(
                vtt_url=video.transcript_url,
                chunk_size=5  # 5 VTT entries per chunk
            )

            if not transcript_chunks:
                raise ValueError("No transcript chunks generated from VTT file")

            logger.info(f"Generated {len(transcript_chunks)} transcript chunks")

            # Convert TranscriptChunk objects to dictionaries for vector store
            chunk_dicts = [
                {
                    'text': chunk.text,
                    'start_time': chunk.start_time,
                    'end_time': chunk.end_time,
                    'index': chunk.index
                }
                for chunk in transcript_chunks
            ]

            # Add chunks to vector store
            success = vector_store_service.add_transcript_chunks(
                video_id=video.id,
                chunks=chunk_dicts,
                clear_existing=True  # Clear any existing embeddings
            )

            if success:
                # Update status to completed
                video.vectorization_status = "completed"
                video.vectorized_at = datetime.utcnow()
                video.vectorization_error = None
                db.commit()
                logger.info(f"✅ VTT vectorization completed successfully for video {video.id}")
            else:
                raise Exception("Vector store service returned failure")

        except Exception as e:
            # Update status to failed with error message
            error_msg = str(e)
            logger.error(f"❌ VTT vectorization failed for video {video.id}: {error_msg}")

            video.vectorization_status = "failed"
            video.vectorization_error = error_msg
            db.commit()

            # Don't raise the exception - allow video creation to succeed
            # even if vectorization fails

    @staticmethod
    def get_video_by_id(db: Session, video_id: int) -> Optional[Video]:
        """Get video by ID with presigned URLs."""
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video = VideoService._enrich_video_with_presigned_urls(video)
        return video

    @staticmethod
    def get_all_videos(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        category_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Video], int]:
        """Get all videos with pagination and optional filtering."""
        query = db.query(Video)

        # Filter by category
        if category_id:
            query = query.filter(Video.category_id == category_id)

        # Search by title or description
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Video.title.ilike(search_pattern)) |
                (Video.description.ilike(search_pattern))
            )

        total = query.count()
        videos = query.order_by(Video.created_at.desc()).offset(skip).limit(limit).all()

        # Enrich all videos with presigned URLs
        videos = [VideoService._enrich_video_with_presigned_urls(video) for video in videos]

        return videos, total

    @staticmethod
    def update_video(
        db: Session,
        video_id: int,
        video_data: VideoUpdate
    ) -> Optional[Video]:
        """Update video metadata."""
        video = VideoService.get_video_by_id(db, video_id)
        if not video:
            return None

        update_data = video_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(video, field, value)

        db.commit()
        db.refresh(video)
        return video

    @staticmethod
    def delete_video(db: Session, video_id: int) -> bool:
        """Delete a video and its files from S3."""
        video = VideoService.get_video_by_id(db, video_id)
        if not video:
            return False

        # Delete files from S3
        s3_service.delete_file(video.video_url)
        s3_service.delete_file(video.transcript_url)
        if video.thumbnail_url:
            s3_service.delete_file(video.thumbnail_url)

        # Delete from database
        db.delete(video)
        db.commit()
        return True

    @staticmethod
    def create_category(db: Session, name: str, description: str = None, parent_id: int = None) -> VideoCategory:
        """Create a video category."""
        category = VideoCategory(
            name=name,
            description=description,
            parent_id=parent_id
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def get_all_categories(db: Session) -> List[VideoCategory]:
        """Get all video categories."""
        return db.query(VideoCategory).all()

    @staticmethod
    def get_category_by_id(db: Session, category_id: int) -> Optional[VideoCategory]:
        """Get category by ID."""
        return db.query(VideoCategory).filter(VideoCategory.id == category_id).first()


video_service = VideoService()
