from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    folders: Mapped[list["Folder"]] = relationship("Folder", back_populates="owner")
    videos: Mapped[list["Video"]] = relationship("Video", back_populates="owner")
    progress_entries: Mapped[list["LearningProgress"]] = relationship(
        "LearningProgress", back_populates="user"
    )
