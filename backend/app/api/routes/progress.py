from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.schemas.progress import ProgressUpdate, ProgressResponse
from app.services.progress_service import progress_service
from app.core.security import get_current_active_user, get_current_admin_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=ProgressResponse)
def update_progress(
    progress_data: ProgressUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update learning progress for the current user."""

    progress = progress_service.update_progress(
        db=db,
        user_id=current_user.id,
        progress_data=progress_data
    )

    return progress


@router.get("/my-progress", response_model=List[ProgressResponse])
def get_my_progress(
    video_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get learning progress for the current user."""

    if video_id:
        progress = progress_service.get_user_progress(db, current_user.id, video_id)
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No progress found for this video"
            )
        return [progress]
    else:
        progress_list = progress_service.get_user_progress(db, current_user.id)
        return progress_list


@router.get("/video/{video_id}/stats")
def get_video_stats(
    video_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get progress statistics for a specific video (Admin only)."""

    stats = progress_service.get_video_progress_stats(db, video_id)
    return stats
