from pydantic import BaseModel, Field
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.schemas.material import MaterialResponse


class VideoCategoryBase(BaseModel):
    """Base video category schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None


class VideoCategoryCreate(VideoCategoryBase):
    """Schema for creating a video category."""
    pass


class VideoCategoryResponse(VideoCategoryBase):
    """Schema for video category response."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class VideoBase(BaseModel):
    """Base video schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[str] = None


class VideoCreate(VideoBase):
    """Schema for creating a video (metadata only, files uploaded separately)."""
    pass


class VideoUpdate(BaseModel):
    """Schema for updating video metadata."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[str] = None


class VideoResponse(VideoBase):
    """Schema for video response."""
    id: int
    video_url: str
    transcript_url: str
    thumbnail_url: Optional[str] = None
    duration: Optional[float] = None
    file_size: Optional[int] = None
    uploaded_by: Optional[int] = None
    ai_summary: Optional[str] = None
    ai_outline: Optional[str] = None
    ai_key_terms: Optional[str] = None
    vectorization_status: str = "pending"  # pending, processing, completed, failed
    vectorization_error: Optional[str] = None
    vectorized_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    materials: List["MaterialResponse"] = []

    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    """Schema for paginated video list."""
    total: int
    page: int
    page_size: int
    videos: List[VideoResponse]


# Import MaterialResponse to resolve forward reference
from app.schemas.material import MaterialResponse
VideoResponse.model_rebuild()
