from typing import Any, List, Optional

from pydantic import BaseModel


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class KnowledgeMetadata(BaseModel):
    title: str
    author: str | None = None
    tags: List[str] = []


class KnowledgeBasePayload(BaseModel):
    video_id: str
    transcript: List[TranscriptSegment]
    metadata: Optional[KnowledgeMetadata] = None
    raw: Optional[dict[str, Any]] = None


class RAGQuery(BaseModel):
    video_id: int
    question: str
    session_id: str
