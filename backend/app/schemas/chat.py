from typing import List, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    video_id: int
    question: str
    session_id: Optional[str] = None


class ChatSource(BaseModel):
    score: float
    text: str
    metadata: dict | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[ChatSource]
    session_id: Optional[str] = None
