from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.models.progress import LearningProgress
from app.schemas.progress import ProgressUpdate


class ProgressService:
    """Service for learning progress operations."""

    @staticmethod
    def update_progress(
        db: Session,
        user_id: int,
        progress_data: ProgressUpdate
    ) -> LearningProgress:
        """Update or create learning progress for a user and video."""

        # Check if progress record exists
        progress = db.query(LearningProgress).filter(
            LearningProgress.user_id == user_id,
            LearningProgress.video_id == progress_data.video_id
        ).first()

        if progress:
            # Update existing progress
            progress.current_timestamp = progress_data.current_timestamp
            progress.completion_percentage = progress_data.completion_percentage
            progress.is_completed = progress_data.is_completed
            progress.last_accessed = datetime.utcnow()

            # Calculate total watch time (simplified - could be more sophisticated)
            # This is a basic implementation
            if progress_data.current_timestamp > progress.current_timestamp:
                time_diff = progress_data.current_timestamp - progress.current_timestamp
                progress.total_watch_time += time_diff

        else:
            # Create new progress record
            progress = LearningProgress(
                user_id=user_id,
                video_id=progress_data.video_id,
                current_timestamp=progress_data.current_timestamp,
                total_watch_time=0,
                completion_percentage=progress_data.completion_percentage,
                is_completed=progress_data.is_completed
            )
            db.add(progress)

        db.commit()
        db.refresh(progress)
        return progress

    @staticmethod
    def get_user_progress(
        db: Session,
        user_id: int,
        video_id: Optional[int] = None
    ) -> Optional[LearningProgress] | List[LearningProgress]:
        """Get learning progress for a user, optionally for a specific video."""

        if video_id:
            return db.query(LearningProgress).filter(
                LearningProgress.user_id == user_id,
                LearningProgress.video_id == video_id
            ).first()
        else:
            return db.query(LearningProgress).filter(
                LearningProgress.user_id == user_id
            ).all()

    @staticmethod
    def get_video_progress_stats(db: Session, video_id: int) -> dict:
        """Get progress statistics for a video (for admin/manager view)."""

        total_users = db.query(LearningProgress).filter(
            LearningProgress.video_id == video_id
        ).count()

        completed_users = db.query(LearningProgress).filter(
            LearningProgress.video_id == video_id,
            LearningProgress.is_completed == True
        ).count()

        avg_completion = db.query(LearningProgress).filter(
            LearningProgress.video_id == video_id
        ).with_entities(
            LearningProgress.completion_percentage
        ).all()

        avg_percentage = sum([p[0] for p in avg_completion]) / len(avg_completion) if avg_completion else 0

        return {
            "total_users": total_users,
            "completed_users": completed_users,
            "completion_rate": (completed_users / total_users * 100) if total_users > 0 else 0,
            "average_completion_percentage": avg_percentage
        }


progress_service = ProgressService()
