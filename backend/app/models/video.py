from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class VideoCategory(Base):
    """Video category/folder model for organizing videos."""

    __tablename__ = "video_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("video_categories.id"), nullable=True)

    # Display and organization
    icon = Column(String, nullable=True)  # Icon name or emoji
    sort_order = Column(Integer, default=0, nullable=False)  # For manual sorting
    is_active = Column(Integer, default=1, nullable=False)  # SQLite uses 1/0 for boolean

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    parent = relationship("VideoCategory", remote_side=[id], backref="children")
    videos = relationship("Video", back_populates="category")

    def __repr__(self):
        return f"<VideoCategory(id={self.id}, name={self.name})>"


class Video(Base):
    """Video model for training content."""

    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # File information
    video_url = Column(String, nullable=False)  # S3 URL
    transcript_url = Column(String, nullable=False)  # VTT file S3 URL
    thumbnail_url = Column(String, nullable=True)  # Optional thumbnail
    duration = Column(Float, nullable=True)  # Duration in seconds
    file_size = Column(Integer, nullable=True)  # File size in bytes

    # Organization
    category_id = Column(Integer, ForeignKey("video_categories.id"), nullable=True)
    tags = Column(String, nullable=True)  # Comma-separated tags

    # Metadata
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # AI-generated content (Phase 2)
    ai_summary = Column(Text, nullable=True)
    ai_outline = Column(Text, nullable=True)  # JSON format
    ai_key_terms = Column(Text, nullable=True)  # JSON format
    ai_chunks = Column(Text, nullable=True)  # JSON format

    # VTT Vectorization Status
    vectorization_status = Column(String, default="pending", nullable=False)  # pending, processing, completed, failed
    vectorization_error = Column(Text, nullable=True)  # Error message if failed
    vectorized_at = Column(DateTime(timezone=True), nullable=True)  # When vectorization completed

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    category = relationship("VideoCategory", back_populates="videos")
    learning_progress = relationship("LearningProgress", back_populates="video", cascade="all, delete-orphan")
    materials = relationship("VideoMaterial", back_populates="video", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Video(id={self.id}, title={self.title})>"
