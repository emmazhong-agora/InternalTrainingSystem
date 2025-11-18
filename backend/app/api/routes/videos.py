from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import logging

from app.db.session import get_db
from app.schemas.video import VideoResponse, VideoListResponse, VideoCategoryCreate, VideoCategoryResponse, VideoUpdate
from app.services.video_service import video_service
from app.core.security import get_current_active_user, get_current_admin_user
from app.models.user import User
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    tags: Optional[str] = Form(None),
    video_file: UploadFile = File(...),
    transcript_file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Upload a new video with transcript (Admin only)."""

    logger.info(f"=== Video Upload Request ===")
    logger.info(f"User: {current_user.username} (ID: {current_user.id})")
    logger.info(f"Title: {title}")
    logger.info(f"Video file: {video_file.filename}")
    logger.info(f"Transcript file: {transcript_file.filename}")

    # Validate video file extension
    video_ext = os.path.splitext(video_file.filename)[1].lower()
    logger.info(f"Validating video file extension: {video_ext}")
    if video_ext not in settings.ALLOWED_VIDEO_EXTENSIONS:
        logger.warning(f"Invalid video file extension: {video_ext}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid video file type. Allowed types: {', '.join(settings.ALLOWED_VIDEO_EXTENSIONS)}"
        )

    # Validate transcript file extension
    transcript_ext = os.path.splitext(transcript_file.filename)[1].lower()
    logger.info(f"Validating transcript file extension: {transcript_ext}")
    if transcript_ext not in settings.ALLOWED_TRANSCRIPT_EXTENSIONS:
        logger.warning(f"Invalid transcript file extension: {transcript_ext}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transcript file type. Must be .vtt format"
        )

    logger.info("File validation passed")

    # Create video data object
    from app.schemas.video import VideoCreate
    video_data = VideoCreate(
        title=title,
        description=description,
        category_id=category_id,
        tags=tags
    )

    # Upload video
    logger.info("Calling video_service.create_video...")
    video = video_service.create_video(
        db=db,
        video_data=video_data,
        video_file=video_file,
        transcript_file=transcript_file,
        uploaded_by=current_user.id
    )

    if not video:
        logger.error("Video upload failed - video_service.create_video returned None")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload video"
        )

    logger.info(f"Video upload completed successfully - Video ID: {video.id}")
    logger.info(f"=== End Video Upload Request ===")
    return video


@router.get("/", response_model=VideoListResponse)
def list_videos(
    page: int = 1,
    page_size: int = 20,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get list of all videos with pagination."""

    if page < 1:
        page = 1
    if page_size > settings.MAX_PAGE_SIZE:
        page_size = settings.MAX_PAGE_SIZE

    skip = (page - 1) * page_size

    videos, total = video_service.get_all_videos(
        db=db,
        skip=skip,
        limit=page_size,
        category_id=category_id,
        search=search
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "videos": videos
    }


@router.get("/{video_id}", response_model=VideoResponse)
def get_video(
    video_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific video by ID."""

    video = video_service.get_video_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    return video


@router.put("/{video_id}", response_model=VideoResponse)
def update_video(
    video_id: int,
    video_data: VideoUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update video metadata (Admin only)."""

    video = video_service.update_video(db, video_id, video_data)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    return video


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a video (Admin only)."""

    success = video_service.delete_video(db, video_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    return None


@router.post("/categories", response_model=VideoCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: VideoCategoryCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a video category (Admin only)."""

    category = video_service.create_category(
        db=db,
        name=category_data.name,
        description=category_data.description,
        parent_id=category_data.parent_id
    )

    return category


@router.get("/categories/", response_model=List[VideoCategoryResponse])
def list_categories(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all video categories."""

    categories = video_service.get_all_categories(db)
    return categories
