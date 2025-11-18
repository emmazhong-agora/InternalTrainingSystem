from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProgressUpdate(BaseModel):
    """Schema for updating learning progress."""
    video_id: int
    current_timestamp: float = Field(..., ge=0)
    completion_percentage: float = Field(..., ge=0, le=100)
    is_completed: bool = False


class ProgressResponse(BaseModel):
    """Schema for progress response."""
    id: int
    user_id: int
    video_id: int
    current_timestamp: float
    total_watch_time: float
    completion_percentage: float
    is_completed: bool
    last_accessed: datetime
    created_at: datetime

    class Config:
        from_attributes = True
