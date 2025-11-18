from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class LearningProgress(Base):
    """Learning progress tracking model."""

    __tablename__ = "learning_progress"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)

    # Progress tracking
    current_timestamp = Column(Float, default=0.0)  # Current playback position in seconds
    total_watch_time = Column(Float, default=0.0)  # Total time spent watching in seconds
    completion_percentage = Column(Float, default=0.0)  # 0-100
    is_completed = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_accessed = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="learning_progress")
    video = relationship("Video", back_populates="learning_progress")

    # Ensure one progress record per user-video combination
    __table_args__ = (
        UniqueConstraint('user_id', 'video_id', name='unique_user_video_progress'),
    )

    def __repr__(self):
        return f"<LearningProgress(user_id={self.user_id}, video_id={self.video_id}, completion={self.completion_percentage}%)>"
