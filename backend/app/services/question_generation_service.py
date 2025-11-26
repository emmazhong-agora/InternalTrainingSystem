from typing import List, Dict
import logging
from openai import OpenAI
from sqlalchemy.orm import Session
import json

from app.core.config import settings
from app.services.vector_store_service import vector_store_service
from app.services.transcript_service import transcript_service
from app.models.video import Video
from app.models.exam import QuestionType
from app.schemas.exam import GeneratedQuestion

logger = logging.getLogger(__name__)


class QuestionGenerationService:
    """Service for AI-powered question generation from video content."""

    def __init__(self):
        """Initialize OpenAI client."""
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("QuestionGenerationService initialized")

    def generate_questions(
        self,
        db: Session,
        video_ids: List[int],
        num_questions: int = 10,
        difficulty: str = "medium",
        question_types: List[QuestionType] = None
    ) -> List[GeneratedQuestion]:
        """
        Generate exam questions from video content using AI.

        Args:
            db: Database session
            video_ids: List of video IDs to generate questions from
            num_questions: Number of questions to generate
            difficulty: Difficulty level (easy, medium, hard)
            question_types: List of question types to include (None = all types)

        Returns:
            List of generated questions
        """
        logger.info(f"Generating {num_questions} questions from {len(video_ids)} videos")

        # Default to all question types if none specified
        if not question_types:
            question_types = [
                QuestionType.MULTIPLE_CHOICE,
                QuestionType.TRUE_FALSE,
                QuestionType.SHORT_ANSWER
            ]

        # Get videos and their transcripts
        videos = db.query(Video).filter(Video.id.in_(video_ids)).all()
        if not videos:
            logger.error("No videos found")
            return []

        all_questions = []

        # Generate questions for each video
        for video in videos:
            # Calculate how many questions to generate from this video
            video_question_count = num_questions // len(videos)
            if video == videos[-1]:  # Last video gets any remainder
                video_question_count += num_questions % len(videos)

            logger.info(f"Generating {video_question_count} questions from video: {video.title}")

            # Get transcript content
            transcript_content = self._get_video_transcript_content(db, video)
            if not transcript_content:
                logger.warning(f"No transcript content found for video {video.id}")
                continue

            # Generate questions using OpenAI
            video_questions = self._generate_questions_from_transcript(
                video_id=video.id,
                video_title=video.title,
                transcript_content=transcript_content,
                num_questions=video_question_count,
                difficulty=difficulty,
                question_types=question_types
            )

            all_questions.extend(video_questions)

        logger.info(f"Generated {len(all_questions)} total questions")
        return all_questions

    def _get_video_transcript_content(self, db: Session, video: Video) -> str:
        """
        Get full transcript content for a video.

        Args:
            db: Database session
            video: Video object

        Returns:
            Transcript text content
        """
        try:
            # Try to get from vector store first (if vectorized)
            if video.vectorization_status == "completed":
                # Get all chunks from vector store
                chunks = vector_store_service.get_all_chunks(video.id)
                if chunks:
                    return "\n".join([chunk['text'] for chunk in chunks])

            # Fallback: parse transcript file directly
            # Download and parse VTT file
            from app.services.s3_service import s3_service
            import tempfile
            import os

            # Generate presigned URL
            transcript_url = s3_service.generate_presigned_url_from_s3_url(video.transcript_url)

            # Download transcript
            import requests
            response = requests.get(transcript_url)
            if response.status_code == 200:
                # Save to temp file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.vtt', delete=False) as f:
                    f.write(response.text)
                    temp_path = f.name

                # Parse VTT
                chunks = transcript_service.parse_vtt(temp_path)

                # Clean up temp file
                os.unlink(temp_path)

                if chunks:
                    return "\n".join([chunk['text'] for chunk in chunks])

            return ""

        except Exception as e:
            logger.error(f"Error getting transcript content: {str(e)}")
            return ""

    def _generate_questions_from_transcript(
        self,
        video_id: int,
        video_title: str,
        transcript_content: str,
        num_questions: int,
        difficulty: str,
        question_types: List[QuestionType]
    ) -> List[GeneratedQuestion]:
        """
        Generate questions from transcript using OpenAI.

        Args:
            video_id: Video ID
            video_title: Video title
            transcript_content: Full transcript text
            num_questions: Number of questions to generate
            difficulty: Difficulty level
            question_types: List of allowed question types

        Returns:
            List of generated questions
        """
        # Build question type instructions
        type_instructions = []
        if QuestionType.MULTIPLE_CHOICE in question_types:
            type_instructions.append("- Multiple choice questions with 4 options")
        if QuestionType.TRUE_FALSE in question_types:
            type_instructions.append("- True/False questions")
        if QuestionType.SHORT_ANSWER in question_types:
            type_instructions.append("- Short answer questions")

        types_str = "\n".join(type_instructions)

        # Create prompt for question generation
        system_prompt = f"""You are an expert educational content creator. Generate high-quality exam questions based on the provided video transcript.

Requirements:
- Generate exactly {num_questions} questions
- Difficulty level: {difficulty}
- Question types to include:
{types_str}
- Distribute questions evenly across the transcript content
- Ensure questions test understanding, not just memorization
- For multiple choice: provide 4 options with only one correct answer
- For true/false: create clear, unambiguous statements
- For short answer: ask questions that have specific, verifiable answers

Output must be valid JSON in this exact format:
{{
  "questions": [
    {{
      "question_type": "multiple_choice" | "true_false" | "short_answer",
      "question_text": "The question text",
      "options": ["Option 1", "Option 2", "Option 3", "Option 4"] (only for multiple_choice),
      "correct_answer": "0" (index for MCQ) | "true"/"false" (for T/F) | "expected answer text" (for short answer),
      "explanation": "Why this is the correct answer",
      "difficulty": "{difficulty}"
    }}
  ]
}}"""

        user_prompt = f"""Video Title: {video_title}

Transcript:
{transcript_content[:8000]}

Generate {num_questions} exam questions based on this content."""

        try:
            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=3000,
                response_format={"type": "json_object"}
            )

            # Parse response
            response_text = response.choices[0].message.content
            data = json.loads(response_text)

            # Convert to GeneratedQuestion objects
            generated_questions = []
            for q_data in data.get("questions", []):
                try:
                    # Validate and create question
                    question = GeneratedQuestion(
                        question_type=QuestionType(q_data["question_type"]),
                        question_text=q_data["question_text"],
                        options=q_data.get("options"),
                        correct_answer=str(q_data["correct_answer"]),
                        explanation=q_data.get("explanation"),
                        difficulty=difficulty,
                        source_video_id=video_id
                    )
                    generated_questions.append(question)
                except Exception as e:
                    logger.error(f"Error parsing question: {str(e)}")
                    continue

            logger.info(f"Successfully generated {len(generated_questions)} questions")
            return generated_questions

        except Exception as e:
            logger.error(f"Error generating questions with OpenAI: {str(e)}")
            return []


# Create singleton instance
question_generation_service = QuestionGenerationService()
