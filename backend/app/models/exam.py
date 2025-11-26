from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class QuestionType(str, enum.Enum):
    """Question type enumeration."""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"


class ExamStatus(str, enum.Enum):
    """Exam status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Exam(Base):
    """Exam model for assessments."""

    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Exam settings
    time_limit_minutes = Column(Integer, nullable=True)  # NULL = no time limit
    pass_threshold_percentage = Column(Float, nullable=False, default=70.0)  # Minimum % to pass
    max_attempts = Column(Integer, nullable=True)  # NULL = unlimited attempts

    # Availability
    status = Column(SQLEnum(ExamStatus), default=ExamStatus.DRAFT, nullable=False)
    available_from = Column(DateTime(timezone=True), nullable=True)
    available_until = Column(DateTime(timezone=True), nullable=True)

    # Display settings
    show_correct_answers = Column(Boolean, default=False)  # Show correct answers after submission
    randomize_questions = Column(Boolean, default=False)  # Randomize question order
    randomize_options = Column(Boolean, default=False)  # Randomize answer options

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    questions = relationship("ExamQuestion", back_populates="exam", cascade="all, delete-orphan")
    video_associations = relationship("ExamVideoAssociation", back_populates="exam", cascade="all, delete-orphan")
    attempts = relationship("ExamAttempt", back_populates="exam", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Exam(id={self.id}, title={self.title}, status={self.status})>"


class ExamQuestion(Base):
    """Question model for exams."""

    __tablename__ = "exam_questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)

    # Question content
    question_type = Column(SQLEnum(QuestionType), nullable=False)
    question_text = Column(Text, nullable=False)
    points = Column(Float, nullable=False, default=1.0)  # Points for this question

    # For multiple choice questions (stored as JSON string)
    # Format: ["Option A", "Option B", "Option C", "Option D"]
    options = Column(Text, nullable=True)

    # Correct answer(s)
    # For MCQ: index of correct option (e.g., "0", "1", "2", "3")
    # For True/False: "true" or "false"
    # For Short Answer: expected answer text (used for auto-grading hints)
    correct_answer = Column(Text, nullable=False)

    # Optional explanation shown after submission
    explanation = Column(Text, nullable=True)

    # Ordering
    sort_order = Column(Integer, default=0, nullable=False)

    # Metadata - track which video this question was generated from (if applicable)
    source_video_id = Column(Integer, ForeignKey("videos.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    exam = relationship("Exam", back_populates="questions")
    answers = relationship("ExamAnswer", back_populates="question", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ExamQuestion(id={self.id}, type={self.question_type}, exam_id={self.exam_id})>"


class ExamVideoAssociation(Base):
    """Association table between exams and videos for question generation context."""

    __tablename__ = "exam_video_associations"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    exam = relationship("Exam", back_populates="video_associations")
    video = relationship("Video")

    def __repr__(self):
        return f"<ExamVideoAssociation(exam_id={self.exam_id}, video_id={self.video_id})>"


class ExamAttempt(Base):
    """Exam attempt model tracking when users take exams."""

    __tablename__ = "exam_attempts"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)

    # User identification
    # Email must match an existing user's email (verified on submission)
    user_email = Column(String, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Set after email verification

    # Attempt timing
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    time_spent_seconds = Column(Integer, nullable=True)  # Calculated on submission

    # Scoring
    total_points = Column(Float, nullable=True)  # Total points available
    earned_points = Column(Float, nullable=True)  # Points earned (auto-calculated)
    score_percentage = Column(Float, nullable=True)  # Percentage score
    passed = Column(Boolean, nullable=True)  # Based on pass_threshold_percentage

    # Status
    is_completed = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    exam = relationship("Exam", back_populates="attempts")
    answers = relationship("ExamAnswer", back_populates="attempt", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ExamAttempt(id={self.id}, exam_id={self.exam_id}, email={self.user_email}, score={self.score_percentage})>"


class ExamAnswer(Base):
    """Individual answers for exam attempts."""

    __tablename__ = "exam_answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("exam_questions.id"), nullable=False)

    # Answer content
    # For MCQ: index of selected option (e.g., "0", "1", "2", "3")
    # For True/False: "true" or "false"
    # For Short Answer: the text answer
    answer_text = Column(Text, nullable=True)

    # Grading
    is_correct = Column(Boolean, nullable=True)  # Auto-graded for MCQ/True-False
    points_earned = Column(Float, nullable=True)

    # Manual grading for short answers
    manually_graded = Column(Boolean, default=False)
    grader_feedback = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    attempt = relationship("ExamAttempt", back_populates="answers")
    question = relationship("ExamQuestion", back_populates="answers")

    def __repr__(self):
        return f"<ExamAnswer(id={self.id}, attempt_id={self.attempt_id}, question_id={self.question_id}, is_correct={self.is_correct})>"
