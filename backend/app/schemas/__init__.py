# Schemas module
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.schemas.video import VideoCreate, VideoUpdate, VideoResponse, VideoCategoryCreate, VideoCategoryResponse
from app.schemas.progress import ProgressUpdate, ProgressResponse

__all__ = [
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
    "VideoCreate",
    "VideoUpdate",
    "VideoResponse",
    "VideoCategoryCreate",
    "VideoCategoryResponse",
    "ProgressUpdate",
    "ProgressResponse",
]
