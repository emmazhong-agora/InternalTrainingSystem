"""
Prompt Service - Centralized management and rendering of AI prompts.
"""
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import logging
import re
from functools import lru_cache

from app.models.prompt import PromptTemplate
from app.schemas.prompt import PromptTemplateCreate, PromptTemplateUpdate

logger = logging.getLogger(__name__)


class PromptService:
    """Service for managing and rendering AI prompt templates."""

    def __init__(self):
        """Initialize prompt service with caching."""
        self._cache = {}
        self._cache_timestamp = {}

    def create_prompt(
        self,
        db: Session,
        prompt_data: PromptTemplateCreate,
        created_by: Optional[int] = None
    ) -> PromptTemplate:
        """
        Create a new prompt template.

        Args:
            db: Database session
            prompt_data: Prompt template data
            created_by: User ID who created this prompt

        Returns:
            Created PromptTemplate instance
        """
        try:
            # Check if name already exists
            existing = db.query(PromptTemplate).filter(
                PromptTemplate.name == prompt_data.name
            ).first()

            if existing:
                raise ValueError(f"Prompt with name '{prompt_data.name}' already exists")

            # Create prompt
            db_prompt = PromptTemplate(
                **prompt_data.dict(),
                created_by=created_by
            )

            db.add(db_prompt)
            db.commit()
            db.refresh(db_prompt)

            # Clear cache
            self._clear_cache(prompt_data.name)

            logger.info(f"Created prompt template: {prompt_data.name}")
            return db_prompt

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating prompt template: {e}")
            raise

    def get_prompt_by_id(self, db: Session, prompt_id: int) -> Optional[PromptTemplate]:
        """Get prompt template by ID."""
        return db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()

    def get_prompt_by_name(
        self,
        db: Session,
        name: str,
        use_cache: bool = True
    ) -> Optional[PromptTemplate]:
        """
        Get prompt template by name with optional caching.

        Args:
            db: Database session
            name: Prompt template name
            use_cache: Whether to use cache (default: True)

        Returns:
            PromptTemplate instance or None
        """
        # NOTE: Caching disabled to avoid session detachment issues
        # Database objects should not be cached across sessions

        # Query database (always fresh query to avoid session issues)
        prompt = db.query(PromptTemplate).filter(
            PromptTemplate.name == name,
            PromptTemplate.is_active == True
        ).first()

        return prompt

    def get_prompts_by_category(
        self,
        db: Session,
        category: str,
        active_only: bool = True
    ) -> List[PromptTemplate]:
        """Get all prompts in a specific category."""
        query = db.query(PromptTemplate).filter(PromptTemplate.category == category)

        if active_only:
            query = query.filter(PromptTemplate.is_active == True)

        return query.all()

    def list_prompts(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        active_only: bool = False
    ) -> Tuple[List[PromptTemplate], int]:
        """
        List all prompt templates with pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            category: Filter by category (optional)
            active_only: Only return active prompts

        Returns:
            Tuple of (prompts list, total count)
        """
        query = db.query(PromptTemplate)

        if category:
            query = query.filter(PromptTemplate.category == category)

        if active_only:
            query = query.filter(PromptTemplate.is_active == True)

        total = query.count()
        prompts = query.order_by(PromptTemplate.created_at.desc()).offset(skip).limit(limit).all()

        return prompts, total

    def update_prompt(
        self,
        db: Session,
        prompt_id: int,
        prompt_data: PromptTemplateUpdate
    ) -> Optional[PromptTemplate]:
        """
        Update an existing prompt template.

        Args:
            db: Database session
            prompt_id: ID of prompt to update
            prompt_data: Updated prompt data

        Returns:
            Updated PromptTemplate instance or None
        """
        try:
            prompt = self.get_prompt_by_id(db, prompt_id)
            if not prompt:
                return None

            # Update fields
            update_data = prompt_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(prompt, field, value)

            prompt.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(prompt)

            # Clear cache
            self._clear_cache(prompt.name)

            logger.info(f"Updated prompt template: {prompt.name}")
            return prompt

        except Exception as e:
            db.rollback()
            logger.error(f"Error updating prompt template: {e}")
            raise

    def delete_prompt(self, db: Session, prompt_id: int) -> bool:
        """
        Delete a prompt template (soft delete by setting is_active=False).

        Args:
            db: Database session
            prompt_id: ID of prompt to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            prompt = self.get_prompt_by_id(db, prompt_id)
            if not prompt:
                return False

            # Soft delete
            prompt.is_active = False
            prompt.updated_at = datetime.utcnow()

            db.commit()

            # Clear cache
            self._clear_cache(prompt.name)

            logger.info(f"Deleted (soft) prompt template: {prompt.name}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting prompt template: {e}")
            return False

    def render_prompt(
        self,
        db: Session,
        prompt_name: str,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Render a prompt template with provided variables.

        Args:
            db: Database session
            prompt_name: Name of the prompt template
            variables: Dictionary of variables to inject

        Returns:
            Dictionary with rendered prompt and configuration

        Raises:
            ValueError: If prompt not found or required variables missing
        """
        # Get prompt from database (disable cache to avoid session detachment issues)
        prompt = self.get_prompt_by_name(db, prompt_name, use_cache=False)
        if not prompt:
            raise ValueError(f"Prompt template '{prompt_name}' not found or inactive")

        # Validate required variables
        if prompt.variables:
            missing_vars = set(prompt.variables) - set(variables.keys())
            if missing_vars:
                logger.warning(f"Missing variables for prompt '{prompt_name}': {missing_vars}")
                # Don't raise error - use empty string for missing variables
                for var in missing_vars:
                    variables[var] = ""

        # Render system message
        rendered_system = self._substitute_variables(prompt.system_message, variables)

        # Render user message template if exists
        rendered_user = None
        if prompt.user_message_template:
            rendered_user = self._substitute_variables(prompt.user_message_template, variables)

        # Extract all needed values BEFORE commit to avoid session detachment issues
        result = {
            "system_message": rendered_system,
            "user_message": rendered_user,
            "model": prompt.model,
            "temperature": prompt.temperature,
            "max_tokens": prompt.max_tokens,
            "top_p": prompt.top_p,
            "response_format": prompt.response_format,
            "response_schema": prompt.response_schema
        }

        # Update usage statistics
        prompt.usage_count += 1
        prompt.last_used_at = datetime.utcnow()
        db.commit()

        # Return rendered prompt with configuration
        return result

    def _substitute_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Substitute variables in template using {variable_name} syntax.

        Args:
            template: Template string with {variable_name} placeholders
            variables: Dictionary of variable values

        Returns:
            Rendered string with variables substituted
        """
        try:
            # Use string formatting with dict
            return template.format(**variables)
        except KeyError as e:
            logger.error(f"Missing variable in template: {e}")
            # Return template with missing variables as-is
            return template
        except Exception as e:
            logger.error(f"Error substituting variables: {e}")
            return template

    def _clear_cache(self, prompt_name: str):
        """Clear cache for a specific prompt."""
        if prompt_name in self._cache:
            del self._cache[prompt_name]
            del self._cache_timestamp[prompt_name]
            logger.debug(f"Cleared cache for prompt: {prompt_name}")


# Singleton instance
prompt_service = PromptService()
