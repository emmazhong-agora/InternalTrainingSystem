from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Schema for token data."""
    user_id: Optional[int] = None


class UserUpdate(BaseModel):
    """Schema for updating user information (admin only)."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)


class UserDetailResponse(UserResponse):
    """Schema for detailed user response with statistics."""
    total_videos_watched: int = 0
    total_watch_time: int = 0  # in seconds
    videos_completed: int = 0
    chat_sessions_count: int = 0
    total_chat_messages: int = 0
    quizzes_taken: int = 0
    last_activity: Optional[datetime] = None


class UserListResponse(BaseModel):
    """Schema for paginated user list response."""
    total: int
    page: int
    page_size: int
    users: list[UserDetailResponse]
