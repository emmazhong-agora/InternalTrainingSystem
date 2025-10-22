from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.learning_progress import LearningProgress
from app.models.user import User
from app.schemas.progress import ProgressRead, ProgressUpdate

router = APIRouter(prefix="/progress", tags=["progress"])


@router.post("", response_model=ProgressRead)
def update_progress(
    payload: ProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = (
        db.query(LearningProgress)
        .filter(
            LearningProgress.user_id == current_user.id,
            LearningProgress.video_id == payload.video_id,
        )
        .first()
    )
    now = datetime.utcnow()
    completed = payload.duration > 0 and payload.last_position / payload.duration >= 0.95

    if not entry:
        entry = LearningProgress(
            user_id=current_user.id,
            video_id=payload.video_id,
            last_position=payload.last_position,
            completed=completed,
            first_watched_at=now,
            last_watched_at=now,
        )
        db.add(entry)
    else:
        entry.last_position = payload.last_position
        entry.completed = completed
        entry.last_watched_at = now
        if entry.first_watched_at is None:
            entry.first_watched_at = now

    db.commit()
    db.refresh(entry)
    return ProgressRead.model_validate(entry, from_attributes=True)


@router.get("/{video_id}", response_model=ProgressRead | None)
def get_progress(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = (
        db.query(LearningProgress)
        .filter(
            LearningProgress.user_id == current_user.id,
            LearningProgress.video_id == video_id,
        )
        .first()
    )
    if not entry:
        return None
    return ProgressRead.model_validate(entry, from_attributes=True)
