"""
Prompt Template Model - Centralized management for AI prompts across services.
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.db.session import Base


class PromptTemplate(Base):
    """
    Centralized storage for AI prompt templates used across the system.

    Supports versioning, A/B testing, and dynamic variable substitution.
    """
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Identification
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # "chat", "quiz", "voice_ai", "analysis"
    description = Column(Text, nullable=True)

    # Prompt Content
    system_message = Column(Text, nullable=False)
    user_message_template = Column(Text, nullable=True)  # Optional template for user message

    # Configuration
    model = Column(String(50), nullable=False, default="gpt-4o")  # "gpt-4o", "gpt-4o-mini", etc.
    temperature = Column(Float, nullable=False, default=0.7)
    max_tokens = Column(Integer, nullable=False, default=1000)
    top_p = Column(Float, nullable=True, default=1.0)

    # Variables & Validation
    variables = Column(JSON, nullable=True)  # List of variable names expected in template
    # Example: ["timestamp", "current_content", "difficulty"]

    response_format = Column(String(20), nullable=True)  # "json", "text", null
    response_schema = Column(JSON, nullable=True)  # JSON schema for validation if response_format="json"

    # Version Management
    version = Column(String(20), nullable=False, default="1.0")
    is_active = Column(Boolean, nullable=False, default=True)
    is_default = Column(Boolean, nullable=False, default=False)  # For A/B testing

    # Metadata
    created_by = Column(Integer, nullable=True)  # User ID who created this prompt
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Usage Statistics (for analytics)
    usage_count = Column(Integer, nullable=False, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<PromptTemplate(name='{self.name}', category='{self.category}', version='{self.version}')>"
