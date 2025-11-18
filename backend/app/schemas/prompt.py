"""
Pydantic schemas for Prompt Template management.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class PromptTemplateBase(BaseModel):
    """Base schema for prompt templates."""
    name: str = Field(..., min_length=1, max_length=100, description="Unique prompt name")
    category: str = Field(..., description="Prompt category: chat, quiz, voice_ai, analysis")
    description: Optional[str] = Field(None, description="Human-readable description")

    system_message: str = Field(..., description="System prompt text")
    user_message_template: Optional[str] = Field(None, description="Optional user message template")

    model: str = Field(default="gpt-4o", description="OpenAI model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature parameter")
    max_tokens: int = Field(default=1000, gt=0, description="Max tokens in response")
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0, description="Top-p parameter")

    variables: Optional[List[str]] = Field(None, description="List of variable names used in template")
    response_format: Optional[str] = Field(None, description="Expected response format: json, text")
    response_schema: Optional[Dict[str, Any]] = Field(None, description="JSON schema for validation")

    version: str = Field(default="1.0", description="Version string")
    is_active: bool = Field(default=True, description="Whether this prompt is active")
    is_default: bool = Field(default=False, description="Whether this is the default version")


class PromptTemplateCreate(PromptTemplateBase):
    """Schema for creating a new prompt template."""
    pass


class PromptTemplateUpdate(BaseModel):
    """Schema for updating an existing prompt template."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = None
    description: Optional[str] = None

    system_message: Optional[str] = None
    user_message_template: Optional[str] = None

    model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)

    variables: Optional[List[str]] = None
    response_format: Optional[str] = None
    response_schema: Optional[Dict[str, Any]] = None

    version: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class PromptTemplateResponse(PromptTemplateBase):
    """Schema for prompt template response."""
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    usage_count: int = 0
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PromptTemplateListResponse(BaseModel):
    """Schema for paginated prompt template list."""
    total: int
    page: int
    page_size: int
    prompts: List[PromptTemplateResponse]


class PromptRenderRequest(BaseModel):
    """Schema for rendering a prompt with variables."""
    prompt_name: str = Field(..., description="Name of the prompt template to use")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Variables to inject into template")


class PromptRenderResponse(BaseModel):
    """Schema for rendered prompt response."""
    prompt_name: str
    system_message: str
    user_message: Optional[str] = None
    model: str
    temperature: float
    max_tokens: int
    top_p: Optional[float] = None
    response_format: Optional[str] = None
