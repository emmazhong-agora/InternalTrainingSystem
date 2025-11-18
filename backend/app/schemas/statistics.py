from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class SystemOverview(BaseModel):
    """System-wide statistics overview."""
    total_users: int
    active_users: int
    total_videos: int
    total_categories: int
    total_watch_hours: float
    total_chat_sessions: int
    total_chat_messages: int
    total_activities: int


class UserStatistics(BaseModel):
    """Detailed statistics for a specific user."""
    user_id: int
    username: str
    email: str
    is_admin: bool
    is_active: bool

    # Learning progress
    total_videos_watched: int
    videos_completed: int
    total_watch_time: int  # seconds
    average_completion_rate: float

    # AI interactions
    chat_sessions_count: int
    total_chat_messages: int
    quiz_attempts: int
    voice_sessions: int

    # Activity
    first_activity: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    days_active: int

    # Engagement
    favorite_categories: List[Dict[str, Any]] = []  # [{category_name, video_count}, ...]


class VideoStatistics(BaseModel):
    """Detailed statistics for a specific video."""
    video_id: int
    title: str
    category_name: Optional[str] = None

    # View metrics
    total_views: int
    unique_viewers: int
    total_watch_time: int  # seconds
    average_watch_time: float

    # Completion metrics
    completion_rate: float  # percentage
    completed_count: int

    # Engagement metrics
    chat_sessions: int
    quiz_attempts: int

    # Timestamps
    first_viewed: Optional[datetime] = None
    last_viewed: Optional[datetime] = None


class CategoryStatistics(BaseModel):
    """Statistics for a specific category."""
    category_id: int
    category_name: str
    parent_name: Optional[str] = None

    # Content
    total_videos: int
    total_subcategories: int

    # Engagement
    total_views: int
    unique_viewers: int
    total_watch_time: int
    average_completion_rate: float

    # Top videos
    top_videos: List[Dict[str, Any]] = []


class ActivityTrend(BaseModel):
    """Activity trends over time."""
    date: str  # YYYY-MM-DD
    video_views: int
    chat_sessions: int
    quiz_attempts: int
    voice_sessions: int
    unique_users: int
    total_watch_time: int


class ActivityStatistics(BaseModel):
    """Activity statistics with trends."""
    date_range: str
    total_activities: int

    # Breakdown by type
    video_views: int
    chat_sessions: int
    quiz_attempts: int
    voice_sessions: int

    # Trends
    daily_trends: List[ActivityTrend] = []

    # Top users
    most_active_users: List[Dict[str, Any]] = []


class PopularContent(BaseModel):
    """Popular videos and categories."""
    most_viewed_videos: List[Dict[str, Any]] = []
    most_completed_videos: List[Dict[str, Any]] = []
    most_discussed_videos: List[Dict[str, Any]] = []  # Most chat sessions
    popular_categories: List[Dict[str, Any]] = []
