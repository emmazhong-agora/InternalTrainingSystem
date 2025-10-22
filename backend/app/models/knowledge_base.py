from sqlalchemy import ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), unique=True)
    json_content: Mapped[dict] = mapped_column(JSON, nullable=False)
    vector_ids: Mapped[list[str] | None] = mapped_column(JSON)

    video: Mapped["Video"] = relationship("Video", back_populates="knowledge_base")
