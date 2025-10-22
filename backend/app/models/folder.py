from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Folder(Base):
    __tablename__ = "folders"
    __table_args__ = (UniqueConstraint("name", "parent_id", "owner_id", name="uq_folder_path_owner"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("folders.id", ondelete="CASCADE"))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    parent: Mapped["Folder | None"] = relationship("Folder", remote_side="Folder.id", backref="children")
    owner: Mapped["User"] = relationship("User", back_populates="folders")
    videos: Mapped[list["Video"]] = relationship("Video", back_populates="folder")
