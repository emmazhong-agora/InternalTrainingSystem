from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import Optional, List, Tuple
import logging
from datetime import datetime
import json

from app.models.exam import (
    Exam,
    ExamQuestion,
    ExamAttempt,
    ExamAnswer,
    QuestionType
)
from app.models.user import User
from app.schemas.exam import (
    ExamAttemptCreate,
    ExamAttemptSubmit,
    ExamAnswerCreate
)

# Configure logging
logger = logging.getLogger(__name__)


class ExamAttemptService:
    """Service for exam attempt and grading operations."""

    @staticmethod
    def start_attempt(
        db: Session,
        attempt_data: ExamAttemptCreate
    ) -> Optional[ExamAttempt]:
        """
        Start a new exam attempt.

        Args:
            db: Database session
            attempt_data: Attempt creation data (exam_id, user_email)

        Returns:
            Created attempt or None if invalid
        """
        logger.info(f"Starting exam attempt for email: {attempt_data.user_email}")

        # Verify exam exists and is published
        exam = db.query(Exam).filter(Exam.id == attempt_data.exam_id).first()
        if not exam:
            logger.error(f"Exam not found: {attempt_data.exam_id}")
            return None

        # Verify email exists in users table
        user = db.query(User).filter(User.email == attempt_data.user_email).first()
        if not user:
            logger.error(f"User with email {attempt_data.user_email} not found")
            return None

        # Check if max attempts exceeded
        if exam.max_attempts:
            existing_attempts = db.query(ExamAttempt).filter(
                ExamAttempt.exam_id == exam.id,
                ExamAttempt.user_email == attempt_data.user_email,
                ExamAttempt.is_completed == True
            ).count()

            if existing_attempts >= exam.max_attempts:
                logger.warning(f"Max attempts exceeded for {attempt_data.user_email}")
                return None

        # Create attempt
        db_attempt = ExamAttempt(
            exam_id=attempt_data.exam_id,
            user_email=attempt_data.user_email,
            user_id=user.id,
            is_completed=False
        )

        db.add(db_attempt)
        db.commit()
        db.refresh(db_attempt)

        logger.info(f"Exam attempt started: {db_attempt.id}")
        return db_attempt

    @staticmethod
    def submit_attempt(
        db: Session,
        attempt_id: int,
        submission_data: ExamAttemptSubmit
    ) -> Optional[ExamAttempt]:
        """
        Submit an exam attempt and auto-grade it.

        Args:
            db: Database session
            attempt_id: Attempt ID
            submission_data: Submitted answers

        Returns:
            Graded attempt or None
        """
        logger.info(f"Submitting exam attempt: {attempt_id}")

        # Get attempt with exam and questions
        attempt = db.query(ExamAttempt).options(
            joinedload(ExamAttempt.exam).joinedload(Exam.questions)
        ).filter(ExamAttempt.id == attempt_id).first()

        if not attempt:
            logger.error(f"Attempt not found: {attempt_id}")
            return None

        if attempt.is_completed:
            logger.warning(f"Attempt already completed: {attempt_id}")
            return attempt

        # Calculate time spent
        time_spent = (datetime.utcnow() - attempt.started_at).total_seconds()
        attempt.time_spent_seconds = int(time_spent)

        # Save all answers and grade them
        total_points = 0.0
        earned_points = 0.0

        # Create a map of question ID to question object
        questions_map = {q.id: q for q in attempt.exam.questions}

        for answer_data in submission_data.answers:
            question = questions_map.get(answer_data.question_id)
            if not question:
                logger.warning(f"Question not found: {answer_data.question_id}")
                continue

            total_points += question.points

            # Grade the answer
            is_correct, points_earned = ExamAttemptService._grade_answer(
                question=question,
                submitted_answer=answer_data.answer_text
            )

            # Create answer record
            db_answer = ExamAnswer(
                attempt_id=attempt_id,
                question_id=answer_data.question_id,
                answer_text=answer_data.answer_text,
                is_correct=is_correct,
                points_earned=points_earned,
                manually_graded=(question.question_type == QuestionType.SHORT_ANSWER)
            )

            db.add(db_answer)
            earned_points += points_earned

        # Update attempt with scores
        attempt.total_points = total_points
        attempt.earned_points = earned_points
        attempt.score_percentage = (earned_points / total_points * 100) if total_points > 0 else 0
        attempt.passed = attempt.score_percentage >= attempt.exam.pass_threshold_percentage
        attempt.submitted_at = datetime.utcnow()
        attempt.is_completed = True

        db.commit()
        db.refresh(attempt)

        logger.info(f"Exam attempt graded: {attempt_id}, score: {attempt.score_percentage}%")
        return attempt

    @staticmethod
    def _grade_answer(question: ExamQuestion, submitted_answer: str) -> Tuple[bool, float]:
        """
        Grade a single answer.

        Args:
            question: Question object
            submitted_answer: User's submitted answer

        Returns:
            Tuple of (is_correct, points_earned)
        """
        if not submitted_answer:
            return False, 0.0

        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            # Compare answer index
            is_correct = submitted_answer.strip() == question.correct_answer.strip()
            return is_correct, question.points if is_correct else 0.0

        elif question.question_type == QuestionType.TRUE_FALSE:
            # Compare true/false
            is_correct = submitted_answer.lower().strip() == question.correct_answer.lower().strip()
            return is_correct, question.points if is_correct else 0.0

        elif question.question_type == QuestionType.SHORT_ANSWER:
            # For short answer, do a simple case-insensitive comparison
            # In production, this could be more sophisticated or require manual grading
            submitted = submitted_answer.lower().strip()
            correct = question.correct_answer.lower().strip()

            # Check if the correct answer is contained in the submission
            # or if they match exactly
            is_correct = (submitted == correct) or (correct in submitted)

            return is_correct, question.points if is_correct else 0.0

        return False, 0.0

    @staticmethod
    def get_attempt(db: Session, attempt_id: int) -> Optional[ExamAttempt]:
        """
        Get an exam attempt with all details.

        Args:
            db: Database session
            attempt_id: Attempt ID

        Returns:
            Attempt object or None
        """
        return db.query(ExamAttempt).options(
            joinedload(ExamAttempt.exam),
            joinedload(ExamAttempt.answers).joinedload(ExamAnswer.question)
        ).filter(ExamAttempt.id == attempt_id).first()

    @staticmethod
    def list_attempts_by_exam(
        db: Session,
        exam_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[ExamAttempt], int]:
        """
        List all attempts for an exam.

        Args:
            db: Database session
            exam_id: Exam ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            Tuple of (attempts list, total count)
        """
        query = db.query(ExamAttempt).options(
            joinedload(ExamAttempt.answers).joinedload(ExamAnswer.question)
        ).filter(
            ExamAttempt.exam_id == exam_id,
            ExamAttempt.is_completed == True
        )

        total = query.count()
        attempts = query.order_by(desc(ExamAttempt.submitted_at)).offset(skip).limit(limit).all()

        return attempts, total

    @staticmethod
    def list_attempts_by_user(
        db: Session,
        user_email: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[ExamAttempt], int]:
        """
        List all attempts by a user.

        Args:
            db: Database session
            user_email: User email
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            Tuple of (attempts list, total count)
        """
        query = db.query(ExamAttempt).options(
            joinedload(ExamAttempt.exam),
            joinedload(ExamAttempt.answers).joinedload(ExamAnswer.question)
        ).filter(
            ExamAttempt.user_email == user_email,
            ExamAttempt.is_completed == True
        )

        total = query.count()
        attempts = query.order_by(desc(ExamAttempt.submitted_at)).offset(skip).limit(limit).all()

        return attempts, total

    @staticmethod
    def get_user_exam_statistics(db: Session, user_email: str) -> dict:
        """
        Get exam statistics for a user.

        Args:
            db: Database session
            user_email: User email

        Returns:
            Dictionary with user exam statistics
        """
        attempts = db.query(ExamAttempt).filter(
            ExamAttempt.user_email == user_email,
            ExamAttempt.is_completed == True
        ).all()

        if not attempts:
            return {
                "user_email": user_email,
                "total_exams_taken": 0,
                "exams_passed": 0,
                "exams_failed": 0,
                "average_score": None,
                "total_time_spent_minutes": 0
            }

        total_exams = len(attempts)
        exams_passed = sum(1 for a in attempts if a.passed)
        exams_failed = total_exams - exams_passed

        scores = [a.score_percentage for a in attempts if a.score_percentage is not None]
        avg_score = sum(scores) / len(scores) if scores else None

        total_time = sum(a.time_spent_seconds for a in attempts if a.time_spent_seconds)
        total_time_minutes = int(total_time / 60)

        return {
            "user_email": user_email,
            "total_exams_taken": total_exams,
            "exams_passed": exams_passed,
            "exams_failed": exams_failed,
            "average_score": avg_score,
            "total_time_spent_minutes": total_time_minutes
        }

    @staticmethod
    def manually_grade_answer(
        db: Session,
        answer_id: int,
        is_correct: bool,
        points_earned: float,
        feedback: Optional[str] = None
    ) -> Optional[ExamAnswer]:
        """
        Manually grade a short answer question.

        Args:
            db: Database session
            answer_id: Answer ID
            is_correct: Whether the answer is correct
            points_earned: Points to award
            feedback: Optional grader feedback

        Returns:
            Updated answer or None
        """
        answer = db.query(ExamAnswer).filter(ExamAnswer.id == answer_id).first()

        if not answer:
            return None

        # Update grading
        answer.is_correct = is_correct
        answer.points_earned = points_earned
        answer.manually_graded = True
        answer.grader_feedback = feedback

        # Recalculate attempt score
        attempt = db.query(ExamAttempt).options(
            joinedload(ExamAttempt.answers)
        ).filter(ExamAttempt.id == answer.attempt_id).first()

        if attempt:
            # Recalculate total earned points
            earned_points = sum(a.points_earned or 0 for a in attempt.answers)
            attempt.earned_points = earned_points
            attempt.score_percentage = (earned_points / attempt.total_points * 100) if attempt.total_points > 0 else 0
            attempt.passed = attempt.score_percentage >= attempt.exam.pass_threshold_percentage

        db.commit()
        db.refresh(answer)

        logger.info(f"Answer manually graded: {answer_id}")
        return answer


# Create singleton instance
exam_attempt_service = ExamAttemptService()
