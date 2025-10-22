from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class VideoBase(BaseModel):
    filename: str
    path: str
    folder_id: Optional[int] = None
    duration: Optional[float] = None


class VideoCreate(BaseModel):
    folder_id: Optional[int] = None


class VideoRead(VideoBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class VideoDetail(VideoRead):
    playback_url: str
    transcript_url: str | None = None
