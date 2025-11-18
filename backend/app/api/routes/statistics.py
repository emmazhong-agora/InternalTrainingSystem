"""
API routes for Statistics and Analytics.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, case, and_
from typing import Optional
from datetime import datetime, timedelta

from app.db.session import get_db
from app.schemas.statistics import (
    SystemOverview,
    UserStatistics,
    VideoStatistics,
    CategoryStatistics,
    ActivityStatistics,
    ActivityTrend,
    PopularContent
)
from app.core.security import get_current_user
from app.models.user import User
from app.models.video import Video, VideoCategory
from app.models.progress import LearningProgress
from app.models.chat import ChatSession, ChatMessage
from app.models.activity import UserActivity

router = APIRouter()


@router.get("/overview", response_model=SystemOverview)
def get_system_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get system-wide statistics overview (admin only).
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view system statistics"
        )

    # Count users
    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()

    # Count videos and categories
    total_videos = db.query(func.count(Video.id)).scalar()
    total_categories = db.query(func.count(VideoCategory.id)).scalar()

    # Calculate total watch hours
    total_watch_seconds = db.query(func.sum(LearningProgress.total_watch_time)).scalar() or 0
    total_watch_hours = total_watch_seconds / 3600.0

    # Count chat sessions and messages
    total_chat_sessions = db.query(func.count(ChatSession.id)).scalar()
    total_chat_messages = db.query(func.count(ChatMessage.id)).scalar()

    # Count activities
    total_activities = db.query(func.count(UserActivity.id)).scalar()

    return SystemOverview(
        total_users=total_users,
        active_users=active_users,
        total_videos=total_videos,
        total_categories=total_categories,
        total_watch_hours=round(total_watch_hours, 2),
        total_chat_sessions=total_chat_sessions,
        total_chat_messages=total_chat_messages,
        total_activities=total_activities
    )


@router.get("/users/{user_id}", response_model=UserStatistics)
def get_user_statistics(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed statistics for a specific user (admin only or own stats).
    """
    # Allow users to view their own stats, or admin to view any user's stats
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own statistics"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Learning progress stats
    progress_stats = db.query(
        func.count(LearningProgress.id).label('total_videos'),
        func.sum(LearningProgress.total_watch_time).label('total_time'),
        func.count(case((LearningProgress.is_completed == True, 1))).label('completed'),
        func.avg(LearningProgress.completion_percentage).label('avg_completion')
    ).filter(LearningProgress.user_id == user_id).first()

    # Chat stats
    chat_stats = db.query(
        func.count(distinct(ChatSession.id)).label('sessions'),
        func.count(ChatMessage.id).label('messages')
    ).outerjoin(ChatMessage, ChatSession.id == ChatMessage.session_id)\
     .filter(ChatSession.user_id == user_id).first()

    # Activity stats
    activity_stats = db.query(
        func.count(case((UserActivity.activity_type == 'quiz', 1))).label('quiz'),
        func.count(case((UserActivity.activity_type == 'voice', 1))).label('voice'),
        func.min(UserActivity.created_at).label('first'),
        func.max(UserActivity.created_at).label('last')
    ).filter(UserActivity.user_id == user_id).first()

    # Calculate days active
    days_active = 0
    if activity_stats.first and activity_stats.last:
        days_active = (activity_stats.last - activity_stats.first).days + 1

    # Get favorite categories
    favorite_categories = db.query(
        VideoCategory.name,
        func.count(LearningProgress.id).label('count')
    ).join(Video, VideoCategory.id == Video.category_id)\
     .join(LearningProgress, Video.id == LearningProgress.video_id)\
     .filter(LearningProgress.user_id == user_id)\
     .group_by(VideoCategory.id, VideoCategory.name)\
     .order_by(func.count(LearningProgress.id).desc())\
     .limit(5).all()

    return UserStatistics(
        user_id=user.id,
        username=user.username,
        email=user.email,
        is_admin=user.is_admin,
        is_active=user.is_active,
        total_videos_watched=progress_stats.total_videos or 0,
        videos_completed=progress_stats.completed or 0,
        total_watch_time=int(progress_stats.total_time or 0),
        average_completion_rate=round(progress_stats.avg_completion or 0, 2),
        chat_sessions_count=chat_stats.sessions or 0,
        total_chat_messages=chat_stats.messages or 0,
        quiz_attempts=activity_stats.quiz or 0,
        voice_sessions=activity_stats.voice or 0,
        first_activity=activity_stats.first,
        last_activity=activity_stats.last,
        days_active=days_active,
        favorite_categories=[
            {"category_name": cat.name, "video_count": cat.count}
            for cat in favorite_categories
        ]
    )


@router.get("/videos/{video_id}", response_model=VideoStatistics)
def get_video_statistics(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed statistics for a specific video.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    # Get category name
    category_name = None
    if video.category_id:
        category = db.query(VideoCategory).filter(VideoCategory.id == video.category_id).first()
        if category:
            category_name = category.name

    # View metrics
    view_stats = db.query(
        func.count(LearningProgress.id).label('total_views'),
        func.count(distinct(LearningProgress.user_id)).label('unique_viewers'),
        func.sum(LearningProgress.total_watch_time).label('total_time'),
        func.avg(LearningProgress.total_watch_time).label('avg_time'),
        func.min(LearningProgress.created_at).label('first_view'),
        func.max(LearningProgress.last_accessed).label('last_view')
    ).filter(LearningProgress.video_id == video_id).first()

    # Completion metrics
    completion_stats = db.query(
        func.count(case((LearningProgress.is_completed == True, 1))).label('completed'),
        func.avg(LearningProgress.completion_percentage).label('completion_rate')
    ).filter(LearningProgress.video_id == video_id).first()

    # Engagement metrics
    chat_count = db.query(func.count(ChatSession.id))\
        .filter(ChatSession.video_id == video_id).scalar()

    quiz_count = db.query(func.count(UserActivity.id))\
        .filter(
            and_(
                UserActivity.video_id == video_id,
                UserActivity.activity_type == 'quiz'
            )
        ).scalar()

    return VideoStatistics(
        video_id=video.id,
        title=video.title,
        category_name=category_name,
        total_views=view_stats.total_views or 0,
        unique_viewers=view_stats.unique_viewers or 0,
        total_watch_time=int(view_stats.total_time or 0),
        average_watch_time=round(view_stats.avg_time or 0, 2),
        completion_rate=round(completion_stats.completion_rate or 0, 2),
        completed_count=completion_stats.completed or 0,
        chat_sessions=chat_count or 0,
        quiz_attempts=quiz_count or 0,
        first_viewed=view_stats.first_view,
        last_viewed=view_stats.last_view
    )


@router.get("/categories/{category_id}", response_model=CategoryStatistics)
def get_category_statistics(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics for a specific category.
    """
    category = db.query(VideoCategory).filter(VideoCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Get parent name
    parent_name = None
    if category.parent_id:
        parent = db.query(VideoCategory).filter(VideoCategory.id == category.parent_id).first()
        if parent:
            parent_name = parent.name

    # Count videos and subcategories
    total_videos = db.query(func.count(Video.id))\
        .filter(Video.category_id == category_id).scalar()

    total_subcategories = db.query(func.count(VideoCategory.id))\
        .filter(VideoCategory.parent_id == category_id).scalar()

    # Engagement stats
    engagement_stats = db.query(
        func.count(LearningProgress.id).label('total_views'),
        func.count(distinct(LearningProgress.user_id)).label('unique_viewers'),
        func.sum(LearningProgress.total_watch_time).label('total_time'),
        func.avg(LearningProgress.completion_percentage).label('avg_completion')
    ).join(Video, LearningProgress.video_id == Video.id)\
     .filter(Video.category_id == category_id).first()

    # Top videos in this category
    top_videos = db.query(
        Video.id,
        Video.title,
        func.count(LearningProgress.id).label('views')
    ).join(LearningProgress, Video.id == LearningProgress.video_id)\
     .filter(Video.category_id == category_id)\
     .group_by(Video.id, Video.title)\
     .order_by(func.count(LearningProgress.id).desc())\
     .limit(5).all()

    return CategoryStatistics(
        category_id=category.id,
        category_name=category.name,
        parent_name=parent_name,
        total_videos=total_videos or 0,
        total_subcategories=total_subcategories or 0,
        total_views=engagement_stats.total_views or 0,
        unique_viewers=engagement_stats.unique_viewers or 0,
        total_watch_time=int(engagement_stats.total_time or 0),
        average_completion_rate=round(engagement_stats.avg_completion or 0, 2),
        top_videos=[
            {"video_id": v.id, "title": v.title, "views": v.views}
            for v in top_videos
        ]
    )


@router.get("/activities", response_model=ActivityStatistics)
def get_activity_statistics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get activity statistics with trends (admin only).

    Query Parameters:
    - days: Number of days to analyze (default: 30, max: 365)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view activity statistics"
        )

    start_date = datetime.utcnow() - timedelta(days=days)

    # Overall stats
    total_activities = db.query(func.count(UserActivity.id))\
        .filter(UserActivity.created_at >= start_date).scalar()

    video_views = db.query(func.count(UserActivity.id))\
        .filter(
            and_(
                UserActivity.created_at >= start_date,
                UserActivity.activity_type == 'video_watch'
            )
        ).scalar()

    chat_sessions = db.query(func.count(ChatSession.id))\
        .filter(ChatSession.created_at >= start_date).scalar()

    quiz_attempts = db.query(func.count(UserActivity.id))\
        .filter(
            and_(
                UserActivity.created_at >= start_date,
                UserActivity.activity_type == 'quiz'
            )
        ).scalar()

    voice_sessions = db.query(func.count(UserActivity.id))\
        .filter(
            and_(
                UserActivity.created_at >= start_date,
                UserActivity.activity_type == 'voice'
            )
        ).scalar()

    # Most active users
    most_active = db.query(
        User.id,
        User.username,
        func.count(UserActivity.id).label('activity_count')
    ).join(UserActivity, User.id == UserActivity.user_id)\
     .filter(UserActivity.created_at >= start_date)\
     .group_by(User.id, User.username)\
     .order_by(func.count(UserActivity.id).desc())\
     .limit(10).all()

    return ActivityStatistics(
        date_range=f"Last {days} days",
        total_activities=total_activities or 0,
        video_views=video_views or 0,
        chat_sessions=chat_sessions or 0,
        quiz_attempts=quiz_attempts or 0,
        voice_sessions=voice_sessions or 0,
        daily_trends=[],  # TODO: Implement daily breakdown
        most_active_users=[
            {"user_id": u.id, "username": u.username, "activity_count": u.activity_count}
            for u in most_active
        ]
    )


@router.get("/popular", response_model=PopularContent)
def get_popular_content(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get popular videos and categories.

    Query Parameters:
    - days: Time period for popularity calculation (default: 30, max: 365)
    """
    start_date = datetime.utcnow() - timedelta(days=days)

    # Most viewed videos
    most_viewed = db.query(
        Video.id,
        Video.title,
        func.count(LearningProgress.id).label('views')
    ).join(LearningProgress, Video.id == LearningProgress.video_id)\
     .filter(LearningProgress.created_at >= start_date)\
     .group_by(Video.id, Video.title)\
     .order_by(func.count(LearningProgress.id).desc())\
     .limit(10).all()

    # Most completed videos
    most_completed = db.query(
        Video.id,
        Video.title,
        func.count(case((LearningProgress.is_completed == True, 1))).label('completions')
    ).join(LearningProgress, Video.id == LearningProgress.video_id)\
     .filter(LearningProgress.created_at >= start_date)\
     .group_by(Video.id, Video.title)\
     .order_by(func.count(case((LearningProgress.is_completed == True, 1))).desc())\
     .limit(10).all()

    # Most discussed videos (most chat sessions)
    most_discussed = db.query(
        Video.id,
        Video.title,
        func.count(ChatSession.id).label('chat_count')
    ).join(ChatSession, Video.id == ChatSession.video_id)\
     .filter(ChatSession.created_at >= start_date)\
     .group_by(Video.id, Video.title)\
     .order_by(func.count(ChatSession.id).desc())\
     .limit(10).all()

    # Popular categories
    popular_cats = db.query(
        VideoCategory.id,
        VideoCategory.name,
        func.count(LearningProgress.id).label('views')
    ).join(Video, VideoCategory.id == Video.category_id)\
     .join(LearningProgress, Video.id == LearningProgress.video_id)\
     .filter(LearningProgress.created_at >= start_date)\
     .group_by(VideoCategory.id, VideoCategory.name)\
     .order_by(func.count(LearningProgress.id).desc())\
     .limit(10).all()

    return PopularContent(
        most_viewed_videos=[
            {"video_id": v.id, "title": v.title, "views": v.views}
            for v in most_viewed
        ],
        most_completed_videos=[
            {"video_id": v.id, "title": v.title, "completions": v.completions}
            for v in most_completed
        ],
        most_discussed_videos=[
            {"video_id": v.id, "title": v.title, "chat_sessions": v.chat_count}
            for v in most_discussed
        ],
        popular_categories=[
            {"category_id": c.id, "name": c.name, "views": c.views}
            for c in popular_cats
        ]
    )
