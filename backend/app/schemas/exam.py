from pydantic import BaseModel, Field, EmailStr, validator, field_validator
from typing import Optional, List
from datetime import datetime
from app.models.exam import QuestionType, ExamStatus
import json


# ============================================================================
# Exam Question Schemas
# ============================================================================

class ExamQuestionBase(BaseModel):
    """Base exam question schema."""
    question_type: QuestionType
    question_text: str = Field(..., min_length=1)
    points: float = Field(default=1.0, ge=0)
    options: Optional[List[str]] = None  # For multiple choice questions
    correct_answer: str = Field(..., min_length=1)
    explanation: Optional[str] = None
    sort_order: int = Field(default=0)
    source_video_id: Optional[int] = None

    @validator('options')
    def validate_options(cls, v, values):
        """Validate that options are provided for multiple choice questions."""
        if values.get('question_type') == QuestionType.MULTIPLE_CHOICE:
            if not v or len(v) < 2:
                raise ValueError('Multiple choice questions must have at least 2 options')
        return v

    @validator('correct_answer')
    def validate_correct_answer(cls, v, values):
        """Validate correct answer format based on question type."""
        question_type = values.get('question_type')

        if question_type == QuestionType.MULTIPLE_CHOICE:
            # Correct answer should be an index (0, 1, 2, 3)
            try:
                index = int(v)
                options = values.get('options', [])
                if options and (index < 0 or index >= len(options)):
                    raise ValueError(f'Correct answer index {index} out of range for {len(options)} options')
            except ValueError:
                raise ValueError('Correct answer for multiple choice must be a valid option index')

        elif question_type == QuestionType.TRUE_FALSE:
            if v.lower() not in ['true', 'false']:
                raise ValueError('Correct answer for true/false must be "true" or "false"')

        return v


class ExamQuestionCreate(ExamQuestionBase):
    """Schema for creating an exam question."""
    pass


class ExamQuestionUpdate(BaseModel):
    """Schema for updating an exam question."""
    question_type: Optional[QuestionType] = None
    question_text: Optional[str] = Field(None, min_length=1)
    points: Optional[float] = Field(None, ge=0)
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    sort_order: Optional[int] = None


class ExamQuestionResponse(ExamQuestionBase):
    """Schema for exam question response."""
    id: int
    exam_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    @field_validator('options', mode='before')
    @classmethod
    def parse_options(cls, v):
        """Parse options from JSON string if needed."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

    class Config:
        from_attributes = True


class ExamQuestionPublicResponse(BaseModel):
    """Public-facing exam question (without correct answers)."""
    id: int
    question_type: QuestionType
    question_text: str
    points: float
    options: Optional[List[str]] = None
    sort_order: int

    @field_validator('options', mode='before')
    @classmethod
    def parse_options(cls, v):
        """Parse options from JSON string if needed."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

    class Config:
        from_attributes = True


# ============================================================================
# Exam Schemas
# ============================================================================

class ExamBase(BaseModel):
    """Base exam schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = Field(None, ge=1)
    pass_threshold_percentage: float = Field(default=70.0, ge=0, le=100)
    max_attempts: Optional[int] = Field(None, ge=1)
    status: ExamStatus = ExamStatus.DRAFT
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    show_correct_answers: bool = Field(default=False)
    randomize_questions: bool = Field(default=False)
    randomize_options: bool = Field(default=False)


class ExamCreate(ExamBase):
    """Schema for creating an exam."""
    video_ids: Optional[List[int]] = []  # Videos to associate for context


class ExamUpdate(BaseModel):
    """Schema for updating an exam."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = Field(None, ge=1)
    pass_threshold_percentage: Optional[float] = Field(None, ge=0, le=100)
    max_attempts: Optional[int] = Field(None, ge=1)
    status: Optional[ExamStatus] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    show_correct_answers: Optional[bool] = None
    randomize_questions: Optional[bool] = None
    randomize_options: Optional[bool] = None


class ExamResponse(ExamBase):
    """Schema for exam response."""
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    questions: List[ExamQuestionResponse] = []
    video_ids: List[int] = []
    total_points: float = 0.0
    question_count: int = 0

    class Config:
        from_attributes = True


class ExamPublicResponse(BaseModel):
    """Public-facing exam response (for exam takers)."""
    id: int
    title: str
    description: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    pass_threshold_percentage: float
    max_attempts: Optional[int] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    questions: List[ExamQuestionPublicResponse] = []
    total_points: float = 0.0
    question_count: int = 0

    class Config:
        from_attributes = True


class ExamListResponse(BaseModel):
    """Schema for paginated exam list."""
    total: int
    page: int
    page_size: int
    exams: List[ExamResponse]


# ============================================================================
# Exam Answer Schemas
# ============================================================================

class ExamAnswerCreate(BaseModel):
    """Schema for creating an exam answer."""
    question_id: int
    answer_text: str


class ExamAnswerResponse(BaseModel):
    """Schema for exam answer response."""
    id: int
    attempt_id: int
    question_id: int
    answer_text: Optional[str] = None
    is_correct: Optional[bool] = None
    points_earned: Optional[float] = None
    manually_graded: bool = False
    grader_feedback: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExamAnswerDetailResponse(ExamAnswerResponse):
    """Detailed exam answer with question information."""
    question: ExamQuestionResponse

    class Config:
        from_attributes = True


# ============================================================================
# Exam Attempt Schemas
# ============================================================================

class ExamAttemptCreate(BaseModel):
    """Schema for starting an exam attempt."""
    exam_id: int
    user_email: EmailStr


class ExamAttemptSubmit(BaseModel):
    """Schema for submitting an exam attempt."""
    answers: List[ExamAnswerCreate]


class ExamAttemptResponse(BaseModel):
    """Schema for exam attempt response."""
    id: int
    exam_id: int
    user_email: str
    user_id: Optional[int] = None
    started_at: datetime
    submitted_at: Optional[datetime] = None
    time_spent_seconds: Optional[int] = None
    total_points: Optional[float] = None
    earned_points: Optional[float] = None
    score_percentage: Optional[float] = None
    passed: Optional[bool] = None
    is_completed: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class ExamAttemptDetailResponse(ExamAttemptResponse):
    """Detailed exam attempt with answers."""
    answers: List[ExamAnswerDetailResponse] = []
    exam_title: Optional[str] = None

    class Config:
        from_attributes = True


class ExamAttemptListResponse(BaseModel):
    """Schema for paginated exam attempt list."""
    total: int
    page: int
    page_size: int
    attempts: List[ExamAttemptDetailResponse]


# ============================================================================
# Question Generation Schemas
# ============================================================================

class QuestionGenerationRequest(BaseModel):
    """Schema for AI-powered question generation."""
    video_ids: List[int] = Field(..., min_items=1)
    num_questions: int = Field(default=10, ge=1, le=50)
    difficulty: Optional[str] = Field(default="medium")  # easy, medium, hard
    question_types: Optional[List[QuestionType]] = None  # If None, use all types

    @validator('difficulty')
    def validate_difficulty(cls, v):
        """Validate difficulty level."""
        if v.lower() not in ['easy', 'medium', 'hard']:
            raise ValueError('Difficulty must be "easy", "medium", or "hard"')
        return v.lower()


class GeneratedQuestion(BaseModel):
    """Schema for a generated question."""
    question_type: QuestionType
    question_text: str
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: Optional[str] = None
    difficulty: str
    source_video_id: int


class QuestionGenerationResponse(BaseModel):
    """Schema for question generation response."""
    questions: List[GeneratedQuestion]
    total_generated: int


# ============================================================================
# Statistics Schemas
# ============================================================================

class ExamStatistics(BaseModel):
    """Schema for exam statistics."""
    exam_id: int
    exam_title: str
    total_attempts: int
    completed_attempts: int
    average_score: Optional[float] = None
    pass_rate: Optional[float] = None  # Percentage of attempts that passed
    highest_score: Optional[float] = None
    lowest_score: Optional[float] = None


class UserExamStatistics(BaseModel):
    """Schema for user exam statistics."""
    user_email: str
    total_exams_taken: int
    exams_passed: int
    exams_failed: int
    average_score: Optional[float] = None
    total_time_spent_minutes: int
