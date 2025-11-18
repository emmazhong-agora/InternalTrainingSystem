"""
API routes for Prompt Template management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.schemas.prompt import (
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    PromptTemplateListResponse,
    PromptRenderRequest,
    PromptRenderResponse
)
from app.services.prompt_service import prompt_service
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=PromptTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_prompt(
    prompt_data: PromptTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new prompt template.

    Requires authentication. Admin users can create prompts.
    """
    # Only admin users can create prompts
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create prompt templates"
        )

    try:
        prompt = prompt_service.create_prompt(db, prompt_data, created_by=current_user.id)
        return prompt
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=PromptTemplateListResponse)
def list_prompts(
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all prompt templates with pagination.

    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20)
    - category: Filter by category (optional)
    - active_only: Only show active prompts (default: False)
    """
    skip = (page - 1) * page_size
    prompts, total = prompt_service.list_prompts(
        db,
        skip=skip,
        limit=page_size,
        category=category,
        active_only=active_only
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "prompts": prompts
    }


@router.get("/{prompt_id}", response_model=PromptTemplateResponse)
def get_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific prompt template by ID."""
    prompt = prompt_service.get_prompt_by_id(db, prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt template with ID {prompt_id} not found"
        )
    return prompt


@router.get("/name/{prompt_name}", response_model=PromptTemplateResponse)
def get_prompt_by_name(
    prompt_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific prompt template by name."""
    prompt = prompt_service.get_prompt_by_name(db, prompt_name)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt template '{prompt_name}' not found or inactive"
        )
    return prompt


@router.put("/{prompt_id}", response_model=PromptTemplateResponse)
def update_prompt(
    prompt_id: int,
    prompt_data: PromptTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a prompt template.

    Requires admin privileges.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update prompt templates"
        )

    try:
        prompt = prompt_service.update_prompt(db, prompt_id, prompt_data)
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt template with ID {prompt_id} not found"
            )
        return prompt
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a prompt template (soft delete).

    Requires admin privileges.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete prompt templates"
        )

    success = prompt_service.delete_prompt(db, prompt_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt template with ID {prompt_id} not found"
        )

    return None


@router.post("/render", response_model=PromptRenderResponse)
def render_prompt(
    request: PromptRenderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Render a prompt template with provided variables.

    This is a utility endpoint for testing prompts before using them.
    """
    try:
        rendered = prompt_service.render_prompt(
            db,
            prompt_name=request.prompt_name,
            variables=request.variables
        )

        return {
            "prompt_name": request.prompt_name,
            **rendered
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/category/{category}", response_model=List[PromptTemplateResponse])
def get_prompts_by_category(
    category: str,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all prompts in a specific category.

    Categories: chat, quiz, voice_ai, analysis
    """
    prompts = prompt_service.get_prompts_by_category(db, category, active_only)
    return prompts
