"""
API routes for Admin Category Management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.db.session import get_db
from app.schemas.category import (
    VideoCategoryResponse,
    VideoCategoryCreate,
    VideoCategoryUpdate,
    VideoCategoryTree,
    VideoCategoryListResponse
)
from app.core.security import get_current_user
from app.models.user import User
from app.models.video import VideoCategory, Video
from datetime import datetime

router = APIRouter()


def build_category_tree(categories: List[VideoCategory], db: Session, parent_id: Optional[int] = None) -> List[VideoCategoryTree]:
    """Recursively build category tree."""
    tree = []
    for category in categories:
        if category.parent_id == parent_id:
            # Count videos in this category
            video_count = db.query(func.count(Video.id)).filter(Video.category_id == category.id).scalar()

            category_dict = {
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "parent_id": category.parent_id,
                "icon": category.icon,
                "sort_order": category.sort_order,
                "is_active": bool(category.is_active),
                "created_at": category.created_at,
                "updated_at": category.updated_at,
                "video_count": video_count,
                "children": build_category_tree(categories, db, category.id)
            }
            tree.append(VideoCategoryTree(**category_dict))

    # Sort by sort_order
    tree.sort(key=lambda x: x.sort_order)
    return tree


@router.get("/", response_model=List[VideoCategoryResponse])
def list_categories(
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all categories (flat list).

    Query Parameters:
    - include_inactive: Include inactive categories (default: False)
    """
    query = db.query(VideoCategory)

    if not include_inactive:
        query = query.filter(VideoCategory.is_active == 1)

    categories = query.order_by(VideoCategory.sort_order, VideoCategory.name).all()
    return categories


@router.get("/tree", response_model=List[VideoCategoryTree])
def get_category_tree(
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get categories as a tree structure (public endpoint).

    Query Parameters:
    - include_inactive: Include inactive categories (default: False)
    """
    query = db.query(VideoCategory)

    if not include_inactive:
        query = query.filter(VideoCategory.is_active == 1)

    categories = query.all()
    return build_category_tree(categories, db)


@router.get("/{category_id}", response_model=VideoCategoryResponse)
def get_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get category by ID."""
    category = db.query(VideoCategory).filter(VideoCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


@router.post("/", response_model=VideoCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: VideoCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new category (admin only).
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create categories"
        )

    # Validate parent_id if provided
    if category_data.parent_id is not None:
        parent = db.query(VideoCategory).filter(VideoCategory.id == category_data.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent category not found"
            )

    # Create category
    category = VideoCategory(
        name=category_data.name,
        description=category_data.description,
        parent_id=category_data.parent_id,
        icon=category_data.icon,
        sort_order=category_data.sort_order,
        is_active=1 if category_data.is_active else 0
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


@router.put("/{category_id}", response_model=VideoCategoryResponse)
def update_category(
    category_id: int,
    category_data: VideoCategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a category (admin only).
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update categories"
        )

    category = db.query(VideoCategory).filter(VideoCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Validate parent_id if being updated
    if category_data.parent_id is not None:
        # Prevent category from being its own parent
        if category_data.parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category cannot be its own parent"
            )

        # Validate parent exists
        parent = db.query(VideoCategory).filter(VideoCategory.id == category_data.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent category not found"
            )

    # Update fields
    update_data = category_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == 'is_active':
            setattr(category, field, 1 if value else 0)
        else:
            setattr(category, field, value)

    category.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(category)

    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a category (admin only).

    Note: This is a soft delete (sets is_active=False).
    Cannot delete if category has videos or child categories.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete categories"
        )

    category = db.query(VideoCategory).filter(VideoCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Check if category has videos
    video_count = db.query(func.count(Video.id)).filter(Video.category_id == category_id).scalar()
    if video_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category with {video_count} videos. Please move or delete videos first."
        )

    # Check if category has children
    children_count = db.query(func.count(VideoCategory.id)).filter(VideoCategory.parent_id == category_id).scalar()
    if children_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category with {children_count} subcategories. Please delete subcategories first."
        )

    # Soft delete
    category.is_active = 0
    category.updated_at = datetime.utcnow()
    db.commit()

    return None
