from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MaterialBase(BaseModel):
    """Base schema for video material."""
    title: Optional[str] = None
    description: Optional[str] = None


class MaterialCreate(MaterialBase):
    """Schema for creating a video material."""
    pass


class MaterialUpdate(MaterialBase):
    """Schema for updating a video material."""
    pass


class MaterialResponse(MaterialBase):
    """Schema for video material response."""
    id: int
    video_id: int
    file_url: str
    original_filename: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    uploaded_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MaterialListResponse(BaseModel):
    """Schema for list of materials."""
    total: int
    materials: list[MaterialResponse]
