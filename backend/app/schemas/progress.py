from datetime import datetime

from pydantic import BaseModel


class ProgressUpdate(BaseModel):
    video_id: int
    last_position: float
    duration: float


class ProgressRead(BaseModel):
    user_id: int
    video_id: int
    last_position: float
    completed: bool
    first_watched_at: datetime | None
    last_watched_at: datetime | None

    class Config:
        from_attributes = True
