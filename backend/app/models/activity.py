from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class UserActivity(Base):
    """User activity tracking for all AI interactions."""

    __tablename__ = "user_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=True, index=True)

    # Activity details
    activity_type = Column(String, nullable=False, index=True)  # "chat", "quiz", "voice", "video_watch"
    session_id = Column(Integer, nullable=True)  # Reference to ChatSession or other session IDs

    # Activity metadata (JSON string)
    activity_data = Column(Text, nullable=True)  # Additional data like quiz score, duration, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    video = relationship("Video", foreign_keys=[video_id])

    def __repr__(self):
        return f"<UserActivity(id={self.id}, user_id={self.user_id}, type={self.activity_type})>"
