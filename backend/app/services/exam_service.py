from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import Optional, List, Tuple
import logging
from datetime import datetime
import json

from app.models.exam import Exam, ExamQuestion, ExamVideoAssociation, QuestionType
from app.models.user import User
from app.schemas.exam import ExamCreate, ExamUpdate, ExamQuestionCreate, ExamQuestionUpdate

# Configure logging
logger = logging.getLogger(__name__)


class ExamService:
    """Service for exam-related operations."""

    @staticmethod
    def create_exam(db: Session, exam_data: ExamCreate, created_by: int) -> Exam:
        """
        Create a new exam.

        Args:
            db: Database session
            exam_data: Exam creation data
            created_by: User ID of creator

        Returns:
            Created exam object
        """
        logger.info(f"Creating exam: {exam_data.title}")

        # Create exam record
        db_exam = Exam(
            title=exam_data.title,
            description=exam_data.description,
            time_limit_minutes=exam_data.time_limit_minutes,
            pass_threshold_percentage=exam_data.pass_threshold_percentage,
            max_attempts=exam_data.max_attempts,
            status=exam_data.status,
            available_from=exam_data.available_from,
            available_until=exam_data.available_until,
            show_correct_answers=exam_data.show_correct_answers,
            randomize_questions=exam_data.randomize_questions,
            randomize_options=exam_data.randomize_options,
            created_by=created_by
        )

        db.add(db_exam)
        db.flush()

        # Create video associations if provided
        if exam_data.video_ids:
            for video_id in exam_data.video_ids:
                association = ExamVideoAssociation(
                    exam_id=db_exam.id,
                    video_id=video_id
                )
                db.add(association)

        db.commit()
        db.refresh(db_exam)

        logger.info(f"Exam created successfully: {db_exam.id}")
        return db_exam

    @staticmethod
    def get_exam(db: Session, exam_id: int) -> Optional[Exam]:
        """
        Get exam by ID with all related data.

        Args:
            db: Database session
            exam_id: Exam ID

        Returns:
            Exam object or None
        """
        return db.query(Exam).options(
            joinedload(Exam.questions),
            joinedload(Exam.video_associations)
        ).filter(Exam.id == exam_id).first()

    @staticmethod
    def get_public_exam(db: Session, exam_id: int) -> Optional[Exam]:
        """
        Get exam for public access (exam takers).
        Only returns published exams within availability window.

        Args:
            db: Database session
            exam_id: Exam ID

        Returns:
            Exam object or None
        """
        from app.models.exam import ExamStatus

        now = datetime.utcnow()
        query = db.query(Exam).options(
            joinedload(Exam.questions)
        ).filter(
            Exam.id == exam_id,
            Exam.status == ExamStatus.PUBLISHED
        )

        # Check availability window
        exam = query.first()
        if not exam:
            return None

        # Check if exam is currently available
        if exam.available_from and exam.available_from > now:
            return None
        if exam.available_until and exam.available_until < now:
            return None

        return exam

    @staticmethod
    def list_exams(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[Exam], int]:
        """
        List exams with pagination and filtering.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Optional search query for title
            status: Optional status filter

        Returns:
            Tuple of (exams list, total count)
        """
        query = db.query(Exam).options(
            joinedload(Exam.questions)
        )

        # Apply filters
        if search:
            query = query.filter(Exam.title.ilike(f"%{search}%"))

        if status:
            from app.models.exam import ExamStatus
            query = query.filter(Exam.status == status)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        exams = query.order_by(desc(Exam.created_at)).offset(skip).limit(limit).all()

        return exams, total

    @staticmethod
    def update_exam(
        db: Session,
        exam_id: int,
        exam_data: ExamUpdate
    ) -> Optional[Exam]:
        """
        Update exam details.

        Args:
            db: Database session
            exam_id: Exam ID
            exam_data: Update data

        Returns:
            Updated exam or None
        """
        db_exam = db.query(Exam).filter(Exam.id == exam_id).first()

        if not db_exam:
            return None

        # Update fields
        update_data = exam_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_exam, key, value)

        db.commit()
        db.refresh(db_exam)

        logger.info(f"Exam updated: {exam_id}")
        return db_exam

    @staticmethod
    def delete_exam(db: Session, exam_id: int) -> bool:
        """
        Delete an exam (cascades to questions, attempts, etc.).

        Args:
            db: Database session
            exam_id: Exam ID

        Returns:
            True if deleted, False if not found
        """
        db_exam = db.query(Exam).filter(Exam.id == exam_id).first()

        if not db_exam:
            return False

        db.delete(db_exam)
        db.commit()

        logger.info(f"Exam deleted: {exam_id}")
        return True

    @staticmethod
    def add_question(
        db: Session,
        exam_id: int,
        question_data: ExamQuestionCreate
    ) -> Optional[ExamQuestion]:
        """
        Add a question to an exam.

        Args:
            db: Database session
            exam_id: Exam ID
            question_data: Question creation data

        Returns:
            Created question or None
        """
        # Verify exam exists
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            return None

        # Convert options list to JSON string if present
        options_json = None
        if question_data.options:
            options_json = json.dumps(question_data.options)

        # Create question
        db_question = ExamQuestion(
            exam_id=exam_id,
            question_type=question_data.question_type,
            question_text=question_data.question_text,
            points=question_data.points,
            options=options_json,
            correct_answer=question_data.correct_answer,
            explanation=question_data.explanation,
            sort_order=question_data.sort_order,
            source_video_id=question_data.source_video_id
        )

        db.add(db_question)
        db.commit()
        db.refresh(db_question)

        logger.info(f"Question added to exam {exam_id}: {db_question.id}")
        return db_question

    @staticmethod
    def add_questions_bulk(
        db: Session,
        exam_id: int,
        questions_data: List[ExamQuestionCreate]
    ) -> List[ExamQuestion]:
        """
        Add multiple questions to an exam in bulk.

        Args:
            db: Database session
            exam_id: Exam ID
            questions_data: List of question creation data

        Returns:
            List of created questions
        """
        # Verify exam exists
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            return []

        created_questions = []
        for question_data in questions_data:
            # Convert options list to JSON string if present
            options_json = None
            if question_data.options:
                options_json = json.dumps(question_data.options)

            db_question = ExamQuestion(
                exam_id=exam_id,
                question_type=question_data.question_type,
                question_text=question_data.question_text,
                points=question_data.points,
                options=options_json,
                correct_answer=question_data.correct_answer,
                explanation=question_data.explanation,
                sort_order=question_data.sort_order,
                source_video_id=question_data.source_video_id
            )
            db.add(db_question)
            created_questions.append(db_question)

        db.commit()

        # Refresh all questions
        for question in created_questions:
            db.refresh(question)

        logger.info(f"Added {len(created_questions)} questions to exam {exam_id}")
        return created_questions

    @staticmethod
    def update_question(
        db: Session,
        question_id: int,
        question_data: ExamQuestionUpdate
    ) -> Optional[ExamQuestion]:
        """
        Update a question.

        Args:
            db: Database session
            question_id: Question ID
            question_data: Update data

        Returns:
            Updated question or None
        """
        db_question = db.query(ExamQuestion).filter(ExamQuestion.id == question_id).first()

        if not db_question:
            return None

        # Update fields
        update_data = question_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == 'options' and value is not None:
                # Convert options list to JSON string
                setattr(db_question, key, json.dumps(value))
            else:
                setattr(db_question, key, value)

        db.commit()
        db.refresh(db_question)

        logger.info(f"Question updated: {question_id}")
        return db_question

    @staticmethod
    def delete_question(db: Session, question_id: int) -> bool:
        """
        Delete a question.

        Args:
            db: Database session
            question_id: Question ID

        Returns:
            True if deleted, False if not found
        """
        db_question = db.query(ExamQuestion).filter(ExamQuestion.id == question_id).first()

        if not db_question:
            return False

        db.delete(db_question)
        db.commit()

        logger.info(f"Question deleted: {question_id}")
        return True

    @staticmethod
    def get_exam_statistics(db: Session, exam_id: int) -> dict:
        """
        Get statistics for an exam.

        Args:
            db: Database session
            exam_id: Exam ID

        Returns:
            Dictionary with exam statistics
        """
        from app.models.exam import ExamAttempt

        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            return None

        # Get all completed attempts
        attempts = db.query(ExamAttempt).filter(
            ExamAttempt.exam_id == exam_id,
            ExamAttempt.is_completed == True
        ).all()

        total_attempts = len(attempts)
        if total_attempts == 0:
            return {
                "exam_id": exam_id,
                "exam_title": exam.title,
                "total_attempts": 0,
                "completed_attempts": 0,
                "average_score": None,
                "pass_rate": None,
                "highest_score": None,
                "lowest_score": None
            }

        scores = [attempt.score_percentage for attempt in attempts if attempt.score_percentage is not None]
        passed_count = sum(1 for attempt in attempts if attempt.passed)

        return {
            "exam_id": exam_id,
            "exam_title": exam.title,
            "total_attempts": total_attempts,
            "completed_attempts": total_attempts,
            "average_score": sum(scores) / len(scores) if scores else None,
            "pass_rate": (passed_count / total_attempts * 100) if total_attempts > 0 else None,
            "highest_score": max(scores) if scores else None,
            "lowest_score": min(scores) if scores else None
        }


# Create singleton instance
exam_service = ExamService()
