from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.db.session import get_db
from app.schemas.material import MaterialResponse, MaterialListResponse, MaterialUpdate
from app.services.material_service import material_service
from app.services.video_service import video_service
from app.core.security import get_current_active_user, get_current_admin_user
from app.models.user import User

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/videos/{video_id}/materials", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def upload_material(
    video_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    material_file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Upload a material file for a video (Admin only)."""

    logger.info(f"=== Material Upload Request ===")
    logger.info(f"User: {current_user.username} (ID: {current_user.id})")
    logger.info(f"Video ID: {video_id}")
    logger.info(f"Material file: {material_file.filename}")

    # Check if video exists
    video = video_service.get_video_by_id(db, video_id)
    if not video:
        logger.warning(f"Video not found: {video_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    logger.info("Video found, uploading material...")

    # Create material data object
    from app.schemas.material import MaterialCreate
    material_data = MaterialCreate(
        title=title,
        description=description
    )

    # Upload material
    material = material_service.create_material(
        db=db,
        video_id=video_id,
        material_data=material_data,
        material_file=material_file,
        uploaded_by=current_user.id
    )

    if not material:
        logger.error("Material upload failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload material"
        )

    logger.info(f"Material upload completed successfully - Material ID: {material.id}")
    logger.info(f"=== End Material Upload Request ===")
    return material


@router.get("/videos/{video_id}/materials", response_model=MaterialListResponse)
def list_materials(
    video_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all materials for a specific video."""

    # Check if video exists
    video = video_service.get_video_by_id(db, video_id)
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    materials = material_service.get_materials_by_video(db, video_id)

    return {
        "total": len(materials),
        "materials": materials
    }


@router.get("/materials/{material_id}", response_model=MaterialResponse)
def get_material(
    material_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific material by ID."""

    material = material_service.get_material_by_id(db, material_id)
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    return material


@router.put("/materials/{material_id}", response_model=MaterialResponse)
def update_material(
    material_id: int,
    material_data: MaterialUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update material metadata (Admin only)."""

    material = material_service.update_material(db, material_id, material_data)
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    return material


@router.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(
    material_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a material (Admin only)."""

    success = material_service.delete_material(db, material_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    return None
