from sqlalchemy.orm import Session
from typing import Optional, List
from fastapi import UploadFile
import logging

from app.models.material import VideoMaterial
from app.schemas.material import MaterialCreate, MaterialUpdate
from app.services.s3_service import s3_service

# Configure logging
logger = logging.getLogger(__name__)


class MaterialService:
    """Service for video material-related operations."""

    @staticmethod
    def create_material(
        db: Session,
        video_id: int,
        material_data: MaterialCreate,
        material_file: UploadFile,
        uploaded_by: int
    ) -> Optional[VideoMaterial]:
        """Create a new video material with file upload."""

        logger.info(f"Starting material upload for video ID: {video_id}")
        logger.info(f"File: {material_file.filename}, Content-Type: {material_file.content_type}")

        # Upload material file to S3
        file_url = s3_service.upload_file(
            material_file.file,
            "materials",
            material_file.filename,
            material_file.content_type or "application/octet-stream"
        )

        if not file_url:
            logger.error("Material file upload failed")
            return None

        logger.info(f"Material file uploaded successfully: {file_url}")

        # Get file size
        file_size = s3_service.get_file_size(file_url)

        # Create material record
        db_material = VideoMaterial(
            video_id=video_id,
            file_url=file_url,
            original_filename=material_file.filename,
            file_type=material_file.content_type,
            file_size=file_size,
            title=material_data.title,
            description=material_data.description,
            uploaded_by=uploaded_by
        )

        db.add(db_material)
        db.commit()
        db.refresh(db_material)

        logger.info(f"Material created successfully with ID: {db_material.id}")
        return db_material

    @staticmethod
    def get_material_by_id(db: Session, material_id: int) -> Optional[VideoMaterial]:
        """Get material by ID."""
        return db.query(VideoMaterial).filter(VideoMaterial.id == material_id).first()

    @staticmethod
    def get_materials_by_video(db: Session, video_id: int) -> List[VideoMaterial]:
        """Get all materials for a specific video."""
        return db.query(VideoMaterial).filter(VideoMaterial.video_id == video_id).order_by(VideoMaterial.created_at.desc()).all()

    @staticmethod
    def update_material(
        db: Session,
        material_id: int,
        material_data: MaterialUpdate
    ) -> Optional[VideoMaterial]:
        """Update material metadata (title, description)."""
        material = MaterialService.get_material_by_id(db, material_id)
        if not material:
            return None

        update_data = material_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(material, field, value)

        db.commit()
        db.refresh(material)
        return material

    @staticmethod
    def delete_material(db: Session, material_id: int) -> bool:
        """Delete a material and its file from S3."""
        material = MaterialService.get_material_by_id(db, material_id)
        if not material:
            return False

        logger.info(f"Deleting material ID: {material_id}, file: {material.original_filename}")

        # Delete file from S3
        s3_service.delete_file(material.file_url)

        # Delete from database
        db.delete(material)
        db.commit()

        logger.info(f"Material deleted successfully")
        return True


material_service = MaterialService()
