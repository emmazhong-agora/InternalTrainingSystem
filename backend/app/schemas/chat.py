from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.chat import MessageRole


class ChatMessageBase(BaseModel):
    """Base schema for chat message."""
    role: MessageRole
    content: str


class ChatMessageCreate(BaseModel):
    """Schema for creating a chat message."""
    content: str  # User message content


class ChatMessageResponse(ChatMessageBase):
    """Schema for chat message response."""
    id: int
    session_id: int
    transcript_references: Optional[str] = None
    confidence_score: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionBase(BaseModel):
    """Base schema for chat session."""
    video_id: int
    title: Optional[str] = None


class ChatSessionCreate(ChatSessionBase):
    """Schema for creating a chat session."""
    pass


class ChatSessionResponse(ChatSessionBase):
    """Schema for chat session response."""
    id: int
    user_id: int
    s3_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_message_at: datetime
    messages: List[ChatMessageResponse] = []

    class Config:
        from_attributes = True


class ChatSessionListResponse(BaseModel):
    """Schema for list of chat sessions."""
    total: int
    sessions: List[ChatSessionResponse]


class AskQuestionRequest(BaseModel):
    """Schema for asking a question to the AI assistant."""
    session_id: Optional[int] = None  # If None, create new session
    video_id: int
    question: str
    current_timestamp: Optional[float] = None  # Current playback time in seconds


class AskQuestionResponse(BaseModel):
    """Schema for AI assistant response."""
    session_id: int
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    referenced_chunks: Optional[List[dict]] = None  # Transcript chunks used
    context_prompt: Optional[str] = None  # Smart suggestion based on current context


class QuizQuestion(BaseModel):
    """Schema for a quiz question."""
    question: str
    options: List[str]
    correct_answer: int  # Index of correct option (0-based)
    explanation: str


class GenerateQuizRequest(BaseModel):
    """Schema for generating a quiz."""
    video_id: int
    current_timestamp: Optional[float] = None
    difficulty: Optional[str] = "medium"  # easy, medium, hard


class GenerateQuizResponse(BaseModel):
    """Schema for quiz generation response."""
    quiz: QuizQuestion
    context_timestamp: Optional[float] = None
