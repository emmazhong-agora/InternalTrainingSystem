from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Video(Base):
    __tablename__ = "videos"
    __table_args__ = (UniqueConstraint("path", name="uq_video_path"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    folder_id: Mapped[int | None] = mapped_column(ForeignKey("folders.id", ondelete="SET NULL"))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    duration: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    owner: Mapped["User"] = relationship("User", back_populates="videos")
    folder: Mapped["Folder | None"] = relationship("Folder", back_populates="videos")
    progress_entries: Mapped[list["LearningProgress"]] = relationship(
        "LearningProgress", back_populates="video", cascade="all, delete-orphan"
    )
    knowledge_base: Mapped["KnowledgeBase | None"] = relationship(
        "KnowledgeBase", back_populates="video", cascade="all, delete-orphan", uselist=False
    )
