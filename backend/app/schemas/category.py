from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class VideoCategoryBase(BaseModel):
    """Base schema for video category."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class VideoCategoryCreate(VideoCategoryBase):
    """Schema for creating a video category."""
    pass


class VideoCategoryUpdate(BaseModel):
    """Schema for updating a video category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class VideoCategoryResponse(VideoCategoryBase):
    """Schema for video category response."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VideoCategoryTree(VideoCategoryResponse):
    """Schema for video category with children (tree structure)."""
    children: List['VideoCategoryTree'] = []
    video_count: int = 0  # Number of videos in this category

    class Config:
        from_attributes = True


# Update forward references for recursive model
VideoCategoryTree.model_rebuild()


class VideoCategoryListResponse(BaseModel):
    """Schema for paginated category list response."""
    total: int
    categories: List[VideoCategoryResponse]
