from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
import logging
import json

from app.db.session import get_db
from app.schemas.exam import (
    ExamCreate,
    ExamUpdate,
    ExamResponse,
    ExamPublicResponse,
    ExamListResponse,
    ExamQuestionCreate,
    ExamQuestionUpdate,
    ExamQuestionResponse,
    ExamQuestionPublicResponse,
    ExamAttemptCreate,
    ExamAttemptSubmit,
    ExamAttemptResponse,
    ExamAttemptDetailResponse,
    ExamAttemptListResponse,
    QuestionGenerationRequest,
    QuestionGenerationResponse,
    ExamStatistics,
    UserExamStatistics
)
from app.services.exam_service import exam_service
from app.services.question_generation_service import question_generation_service
from app.services.exam_attempt_service import exam_attempt_service
from app.core.security import get_current_active_user, get_current_admin_user
from app.models.user import User
from app.models.exam import ExamStatus

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Exam Management Endpoints (Admin)
# ============================================================================

@router.post("/", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
def create_exam(
    exam_data: ExamCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new exam (Admin only)."""
    logger.info(f"Creating exam: {exam_data.title} by user {current_user.id}")

    exam = exam_service.create_exam(
        db=db,
        exam_data=exam_data,
        created_by=current_user.id
    )

    # Prepare response with video_ids and calculated fields
    response_data = ExamResponse.model_validate(exam)
    response_data.video_ids = [assoc.video_id for assoc in exam.video_associations]
    response_data.total_points = sum(q.points for q in exam.questions)
    response_data.question_count = len(exam.questions)

    return response_data


@router.get("/", response_model=ExamListResponse)
def list_exams(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all exams with pagination (Admin only)."""
    skip = (page - 1) * page_size

    exams, total = exam_service.list_exams(
        db=db,
        skip=skip,
        limit=page_size,
        search=search,
        status=status_filter
    )

    # Enrich response data
    exam_responses = []
    for exam in exams:
        response = ExamResponse.model_validate(exam)
        response.video_ids = [assoc.video_id for assoc in exam.video_associations]
        response.total_points = sum(q.points for q in exam.questions)
        response.question_count = len(exam.questions)
        exam_responses.append(response)

    return ExamListResponse(
        total=total,
        page=page,
        page_size=page_size,
        exams=exam_responses
    )


@router.get("/{exam_id}", response_model=ExamResponse)
def get_exam(
    exam_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get exam details (Admin only)."""
    exam = exam_service.get_exam(db=db, exam_id=exam_id)

    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )

    # Enrich response
    response = ExamResponse.model_validate(exam)
    response.video_ids = [assoc.video_id for assoc in exam.video_associations]
    response.total_points = sum(q.points for q in exam.questions)
    response.question_count = len(exam.questions)

    # Parse JSON options for questions
    for question in response.questions:
        if question.options:
            try:
                question.options = json.loads(question.options)
            except:
                question.options = None

    return response


@router.put("/{exam_id}", response_model=ExamResponse)
def update_exam(
    exam_id: int,
    exam_data: ExamUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update exam details (Admin only)."""
    exam = exam_service.update_exam(db=db, exam_id=exam_id, exam_data=exam_data)

    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )

    # Refresh to get related data
    exam = exam_service.get_exam(db=db, exam_id=exam_id)

    response = ExamResponse.model_validate(exam)
    response.video_ids = [assoc.video_id for assoc in exam.video_associations]
    response.total_points = sum(q.points for q in exam.questions)
    response.question_count = len(exam.questions)

    return response


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam(
    exam_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete an exam (Admin only)."""
    success = exam_service.delete_exam(db=db, exam_id=exam_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )

    return None


# ============================================================================
# Question Management Endpoints (Admin)
# ============================================================================

@router.post("/{exam_id}/questions", response_model=ExamQuestionResponse, status_code=status.HTTP_201_CREATED)
def add_question(
    exam_id: int,
    question_data: ExamQuestionCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Add a question to an exam (Admin only)."""
    question = exam_service.add_question(
        db=db,
        exam_id=exam_id,
        question_data=question_data
    )

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )

    # Parse options if present
    response = ExamQuestionResponse.model_validate(question)
    if response.options:
        try:
            response.options = json.loads(response.options)
        except:
            response.options = None

    return response


@router.put("/questions/{question_id}", response_model=ExamQuestionResponse)
def update_question(
    question_id: int,
    question_data: ExamQuestionUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update a question (Admin only)."""
    question = exam_service.update_question(
        db=db,
        question_id=question_id,
        question_data=question_data
    )

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    # Parse options if present
    response = ExamQuestionResponse.model_validate(question)
    if response.options:
        try:
            response.options = json.loads(response.options)
        except:
            response.options = None

    return response


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a question (Admin only)."""
    success = exam_service.delete_question(db=db, question_id=question_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    return None


# ============================================================================
# AI Question Generation Endpoint (Admin)
# ============================================================================

@router.post("/generate-questions", response_model=QuestionGenerationResponse)
def generate_questions(
    request: QuestionGenerationRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Generate exam questions from video content using AI (Admin only)."""
    logger.info(f"Generating questions from {len(request.video_ids)} videos")

    questions = question_generation_service.generate_questions(
        db=db,
        video_ids=request.video_ids,
        num_questions=request.num_questions,
        difficulty=request.difficulty,
        question_types=request.question_types
    )

    return QuestionGenerationResponse(
        questions=questions,
        total_generated=len(questions)
    )


@router.post("/{exam_id}/add-generated-questions", response_model=ExamResponse)
def add_generated_questions(
    exam_id: int,
    questions: List[ExamQuestionCreate],
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Add multiple generated questions to an exam (Admin only)."""
    added_questions = exam_service.add_questions_bulk(
        db=db,
        exam_id=exam_id,
        questions_data=questions
    )

    if not added_questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found or no questions added"
        )

    # Get updated exam
    exam = exam_service.get_exam(db=db, exam_id=exam_id)

    response = ExamResponse.model_validate(exam)
    response.video_ids = [assoc.video_id for assoc in exam.video_associations]
    response.total_points = sum(q.points for q in exam.questions)
    response.question_count = len(exam.questions)

    return response


# ============================================================================
# Public Exam Taking Endpoints (No Auth Required)
# ============================================================================

@router.get("/public/{exam_id}", response_model=ExamPublicResponse)
def get_public_exam(
    exam_id: int,
    db: Session = Depends(get_db)
):
    """Get exam for taking (public access, no authentication required)."""
    exam = exam_service.get_public_exam(db=db, exam_id=exam_id)

    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found or not available"
        )

    # Build public response (without correct answers)
    public_questions = []
    for question in exam.questions:
        # Parse options if present
        options = None
        if question.options:
            try:
                options = json.loads(question.options)
            except:
                options = None

        public_q = ExamQuestionPublicResponse(
            id=question.id,
            question_type=question.question_type,
            question_text=question.question_text,
            points=question.points,
            options=options,
            sort_order=question.sort_order
        )
        public_questions.append(public_q)

    return ExamPublicResponse(
        id=exam.id,
        title=exam.title,
        description=exam.description,
        time_limit_minutes=exam.time_limit_minutes,
        pass_threshold_percentage=exam.pass_threshold_percentage,
        max_attempts=exam.max_attempts,
        available_from=exam.available_from,
        available_until=exam.available_until,
        questions=public_questions,
        total_points=sum(q.points for q in exam.questions),
        question_count=len(exam.questions)
    )


@router.post("/public/start", response_model=ExamAttemptResponse)
def start_exam_attempt(
    attempt_data: ExamAttemptCreate,
    db: Session = Depends(get_db)
):
    """Start an exam attempt (public access, email verification required)."""
    attempt = exam_attempt_service.start_attempt(db=db, attempt_data=attempt_data)

    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start exam. Possible reasons: email not registered, max attempts exceeded, or exam not found."
        )

    return ExamAttemptResponse.model_validate(attempt)


@router.post("/public/submit/{attempt_id}", response_model=ExamAttemptDetailResponse)
def submit_exam_attempt(
    attempt_id: int,
    submission_data: ExamAttemptSubmit,
    db: Session = Depends(get_db)
):
    """Submit an exam attempt (public access)."""
    attempt = exam_attempt_service.submit_attempt(
        db=db,
        attempt_id=attempt_id,
        submission_data=submission_data
    )

    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found"
        )

    # Build detailed response
    response = ExamAttemptDetailResponse.model_validate(attempt)
    response.exam_title = attempt.exam.title

    # Parse options for questions in answers
    for answer in response.answers:
        if answer.question.options:
            try:
                answer.question.options = json.loads(answer.question.options)
            except:
                answer.question.options = None

    return response


# ============================================================================
# Exam Attempt & Results Endpoints (Admin)
# ============================================================================

@router.get("/{exam_id}/attempts", response_model=ExamAttemptListResponse)
def list_exam_attempts(
    exam_id: int,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all attempts for an exam (Admin only)."""
    skip = (page - 1) * page_size

    attempts, total = exam_attempt_service.list_attempts_by_exam(
        db=db,
        exam_id=exam_id,
        skip=skip,
        limit=page_size
    )

    # Build detailed responses
    attempt_responses = []
    for attempt in attempts:
        response = ExamAttemptDetailResponse.model_validate(attempt)
        response.exam_title = attempt.exam.title

        # Parse options for questions
        for answer in response.answers:
            if answer.question.options:
                try:
                    answer.question.options = json.loads(answer.question.options)
                except:
                    answer.question.options = None

        attempt_responses.append(response)

    return ExamAttemptListResponse(
        total=total,
        page=page,
        page_size=page_size,
        attempts=attempt_responses
    )


@router.get("/attempts/{attempt_id}", response_model=ExamAttemptDetailResponse)
def get_attempt_details(
    attempt_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get detailed attempt information (Admin only)."""
    attempt = exam_attempt_service.get_attempt(db=db, attempt_id=attempt_id)

    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found"
        )

    response = ExamAttemptDetailResponse.model_validate(attempt)
    response.exam_title = attempt.exam.title

    # Parse options for questions
    for answer in response.answers:
        if answer.question.options:
            try:
                answer.question.options = json.loads(answer.question.options)
            except:
                answer.question.options = None

    return response


# ============================================================================
# Statistics Endpoints (Admin)
# ============================================================================

@router.get("/{exam_id}/statistics", response_model=ExamStatistics)
def get_exam_statistics(
    exam_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get statistics for an exam (Admin only)."""
    stats = exam_service.get_exam_statistics(db=db, exam_id=exam_id)

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )

    return ExamStatistics(**stats)


@router.get("/users/{user_email}/statistics", response_model=UserExamStatistics)
def get_user_statistics(
    user_email: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get exam statistics for a user (Admin only)."""
    stats = exam_attempt_service.get_user_exam_statistics(db=db, user_email=user_email)

    return UserExamStatistics(**stats)
