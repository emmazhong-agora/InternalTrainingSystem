"""
API routes for Admin User Management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from app.db.session import get_db
from app.schemas.user import (
    UserListResponse,
    UserDetailResponse,
    UserUpdate,
    UserCreate
)
from app.schemas.progress import ProgressResponse
from app.schemas.chat import ChatSessionResponse
from app.services.user_service import user_service
from app.core.security import get_current_user
from app.models.user import User
from app.models.progress import LearningProgress
from app.models.chat import ChatSession, ChatMessage
from datetime import datetime

router = APIRouter()


@router.get("/", response_model=UserListResponse)
def list_users(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_admin: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all users with pagination and filters (admin only).

    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20)
    - search: Search by username, email, or full name
    - is_active: Filter by active status
    - is_admin: Filter by admin status
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view user list"
        )

    # Build query
    query = db.query(User)

    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.username.ilike(search_term)) |
            (User.email.ilike(search_term)) |
            (User.full_name.ilike(search_term))
        )

    # Apply status filters
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if is_admin is not None:
        query = query.filter(User.is_admin == is_admin)

    # Order by created_at desc
    query = query.order_by(User.created_at.desc())

    # Get total count
    total = query.count()

    # Apply pagination
    skip = (page - 1) * page_size
    users = query.offset(skip).limit(page_size).all()

    # Enrich users with statistics
    user_details = []
    for user in users:
        # Get learning progress stats
        progress_stats = db.query(
            func.count(LearningProgress.id).label('total_videos'),
            func.sum(LearningProgress.total_watch_time).label('total_time'),
            func.count(LearningProgress.id).filter(LearningProgress.is_completed == True).label('completed')
        ).filter(LearningProgress.user_id == user.id).first()

        # Get chat stats
        chat_stats = db.query(
            func.count(ChatSession.id).label('sessions'),
            func.count(ChatMessage.id).label('messages')
        ).join(ChatMessage, ChatSession.id == ChatMessage.session_id, isouter=True)\
         .filter(ChatSession.user_id == user.id).first()

        # Get last activity
        last_progress = db.query(LearningProgress).filter(
            LearningProgress.user_id == user.id
        ).order_by(LearningProgress.last_accessed.desc()).first()

        user_detail = UserDetailResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at,
            total_videos_watched=progress_stats.total_videos or 0,
            total_watch_time=int(progress_stats.total_time or 0),
            videos_completed=progress_stats.completed or 0,
            chat_sessions_count=chat_stats.sessions or 0,
            total_chat_messages=chat_stats.messages or 0,
            quizzes_taken=0,  # TODO: Implement quiz tracking
            last_activity=last_progress.last_accessed if last_progress else None
        )
        user_details.append(user_detail)

    return UserListResponse(
        total=total,
        page=page,
        page_size=page_size,
        users=user_details
    )


@router.get("/{user_id}", response_model=UserDetailResponse)
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed user information (admin only or own profile).
    """
    # Allow users to view their own profile, or admin to view any profile
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get learning progress stats
    progress_stats = db.query(
        func.count(LearningProgress.id).label('total_videos'),
        func.sum(LearningProgress.total_watch_time).label('total_time'),
        func.count(LearningProgress.id).filter(LearningProgress.is_completed == True).label('completed')
    ).filter(LearningProgress.user_id == user_id).first()

    # Get chat stats
    chat_stats = db.query(
        func.count(ChatSession.id).label('sessions'),
        func.count(ChatMessage.id).label('messages')
    ).join(ChatMessage, ChatSession.id == ChatMessage.session_id, isouter=True)\
     .filter(ChatSession.user_id == user_id).first()

    # Get last activity
    last_progress = db.query(LearningProgress).filter(
        LearningProgress.user_id == user_id
    ).order_by(LearningProgress.last_accessed.desc()).first()

    return UserDetailResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at,
        total_videos_watched=progress_stats.total_videos or 0,
        total_watch_time=int(progress_stats.total_time or 0),
        videos_completed=progress_stats.completed or 0,
        chat_sessions_count=chat_stats.sessions or 0,
        total_chat_messages=chat_stats.messages or 0,
        quizzes_taken=0,  # TODO: Implement quiz tracking
        last_activity=last_progress.last_accessed if last_progress else None
    )


@router.post("/", response_model=UserDetailResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    is_admin: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new user (admin only).
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create users"
        )

    # Check if email already exists
    if user_service.get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username already exists
    if user_service.get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # Create user
    user = user_service.create_user(db, user_data, is_admin=is_admin)

    # Return with empty stats
    return UserDetailResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at,
        total_videos_watched=0,
        total_watch_time=0,
        videos_completed=0,
        chat_sessions_count=0,
        total_chat_messages=0,
        quizzes_taken=0,
        last_activity=None
    )


@router.put("/{user_id}", response_model=UserDetailResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user information (admin only or own profile for limited fields).
    """
    # Get target user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check permissions
    is_self = current_user.id == user_id
    if not current_user.is_admin and not is_self:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )

    # Non-admin users can only update certain fields
    if not current_user.is_admin:
        if user_data.is_admin is not None or user_data.is_active is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot change admin or active status"
            )

    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)

    # Handle password update separately
    if 'password' in update_data:
        from app.core.security import get_password_hash
        user.hashed_password = get_password_hash(update_data.pop('password'))

    # Check for email uniqueness
    if 'email' in update_data and update_data['email'] != user.email:
        existing = user_service.get_user_by_email(db, update_data['email'])
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # Check for username uniqueness
    if 'username' in update_data and update_data['username'] != user.username:
        existing = user_service.get_user_by_username(db, update_data['username'])
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

    # Apply updates
    for field, value in update_data.items():
        setattr(user, field, value)

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    # Get updated stats
    return get_user(user_id, current_user, db)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a user (admin only).

    Note: This is a soft delete (sets is_active=False).
    Hard delete would require cascading deletes of all related data.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete users"
        )

    # Prevent self-deletion
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Soft delete: deactivate user
    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.commit()

    return None


@router.post("/{user_id}/activate", response_model=UserDetailResponse)
def activate_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Activate a deactivated user (admin only).
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can activate users"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_active = True
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return get_user(user_id, current_user, db)


@router.get("/{user_id}/progress", response_model=List[ProgressResponse])
def get_user_progress(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's learning progress (admin only or own progress).
    """
    # Allow users to view their own progress, or admin to view any user's progress
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own progress"
        )

    progress_records = db.query(LearningProgress).filter(
        LearningProgress.user_id == user_id
    ).order_by(LearningProgress.last_accessed.desc()).all()

    return progress_records


@router.get("/{user_id}/chat-sessions", response_model=List[ChatSessionResponse])
def get_user_chat_sessions(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's chat sessions (admin only or own sessions).
    """
    # Allow users to view their own sessions, or admin to view any user's sessions
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own chat sessions"
        )

    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == user_id
    ).order_by(ChatSession.last_message_at.desc()).all()

    return sessions
