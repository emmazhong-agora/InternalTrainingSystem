from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class VideoMaterial(Base):
    """Video material/attachment model for training resources."""

    __tablename__ = "video_materials"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)

    # File information
    file_url = Column(String, nullable=False)  # S3 URL
    original_filename = Column(String, nullable=False)
    file_type = Column(String, nullable=True)  # MIME type or extension
    file_size = Column(BigInteger, nullable=True)  # File size in bytes

    # Metadata
    title = Column(String, nullable=True)  # Optional custom title
    description = Column(String, nullable=True)  # Optional description
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    video = relationship("Video", back_populates="materials")
    uploader = relationship("User", foreign_keys=[uploaded_by])

    def __repr__(self):
        return f"<VideoMaterial(id={self.id}, filename={self.original_filename}, video_id={self.video_id})>"
