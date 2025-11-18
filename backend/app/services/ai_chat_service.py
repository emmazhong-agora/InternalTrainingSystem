from typing import List, Dict, Optional, Tuple
import logging
from openai import OpenAI
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.vector_store_service import vector_store_service
from app.services.prompt_service import prompt_service
import json

logger = logging.getLogger(__name__)


class AIChatService:
    """Service for AI-powered teaching assistant with RAG (using centralized prompts)."""

    def __init__(self):
        """Initialize OpenAI client."""
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("AIChatService initialized with centralized prompt management")

    def _format_context(self, chunks: List[Dict]) -> str:
        """
        Format retrieved transcript chunks into context string.

        Args:
            chunks: List of transcript chunks from vector store

        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant transcript content found."

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            start_time = chunk['metadata']['start_time']
            end_time = chunk['metadata']['end_time']
            text = chunk['text']

            # Format timestamp for readability
            start_min = int(start_time // 60)
            start_sec = int(start_time % 60)
            end_min = int(end_time // 60)
            end_sec = int(end_time % 60)

            context_parts.append(
                f"[Excerpt {i}] ({start_min}:{start_sec:02d} - {end_min}:{end_sec:02d})\n{text}"
            )

        return "\n\n".join(context_parts)

    def _calculate_confidence(self, chunks: List[Dict], query: str) -> int:
        """
        Calculate confidence score based on retrieval results.

        Args:
            chunks: Retrieved transcript chunks
            query: User's question

        Returns:
            Confidence score (0-100)
        """
        if not chunks:
            return 0

        # Base confidence on number of chunks and distance scores
        avg_distance = sum(chunk.get('distance', 1.0) for chunk in chunks) / len(chunks)

        # Lower distance = higher confidence (distance is typically 0-2)
        # Convert to 0-100 scale
        confidence = max(0, min(100, int((1 - avg_distance / 2) * 100)))

        # Boost confidence if we have multiple relevant chunks
        if len(chunks) >= 3:
            confidence = min(100, confidence + 10)

        return confidence

    def _get_chunks_by_timestamp(
        self,
        video_id: int,
        timestamp: float,
        window_seconds: float = 30.0
    ) -> List[Dict]:
        """
        Get transcript chunks around a specific timestamp.

        Args:
            video_id: ID of the video
            timestamp: Current playback time in seconds
            window_seconds: Time window to search around timestamp

        Returns:
            List of chunks around the timestamp
        """
        try:
            from app.services.vector_store_service import vector_store_service

            collection = vector_store_service._get_or_create_collection(video_id)

            # Get all chunks and filter by timestamp
            results = collection.get(
                include=['metadatas', 'documents']
            )

            if not results or not results['metadatas']:
                return []

            # Filter chunks that overlap with the timestamp window
            relevant_chunks = []
            start_window = max(0, timestamp - window_seconds)
            end_window = timestamp + window_seconds

            for i, metadata in enumerate(results['metadatas']):
                chunk_start = metadata['start_time']
                chunk_end = metadata['end_time']

                # Check if chunk overlaps with the time window
                if chunk_start <= end_window and chunk_end >= start_window:
                    relevant_chunks.append({
                        'text': results['documents'][i],
                        'metadata': metadata,
                        'distance': 0.0  # Direct timestamp match
                    })

            # Sort by proximity to timestamp
            relevant_chunks.sort(key=lambda x: abs(x['metadata']['start_time'] - timestamp))

            logger.info(f"Found {len(relevant_chunks)} chunks around timestamp {timestamp}")
            return relevant_chunks[:5]  # Return top 5 closest chunks

        except Exception as e:
            logger.error(f"Error getting chunks by timestamp: {e}")
            return []

    def ask_question(
        self,
        db: Session,  # Added for centralized prompt management
        video_id: int,
        question: str,
        conversation_history: Optional[List[Dict]] = None,
        n_chunks: int = 5,
        current_timestamp: Optional[float] = None
    ) -> Tuple[str, List[Dict], int, Optional[str]]:
        """
        Answer a user's question using RAG with optional timestamp context (using centralized prompts).

        Args:
            db: Database session for prompt retrieval
            video_id: ID of the video being discussed
            question: User's question
            conversation_history: Previous messages in the conversation
            n_chunks: Number of transcript chunks to retrieve
            current_timestamp: Current playback time in seconds (optional)

        Returns:
            Tuple of (answer, referenced_chunks, confidence_score, context_prompt)
        """
        try:
            logger.info(f"Processing question for video {video_id}: {question}")
            if current_timestamp:
                logger.info(f"Current playback position: {current_timestamp}s")

            # Step 1: Get context chunks
            context_chunks = []
            semantic_chunks = []

            # If timestamp is provided, get nearby chunks for context
            if current_timestamp is not None:
                context_chunks = self._get_chunks_by_timestamp(
                    video_id=video_id,
                    timestamp=current_timestamp,
                    window_seconds=30.0
                )
                logger.info(f"Retrieved {len(context_chunks)} chunks by timestamp")

            # Always do semantic search for question-relevant chunks
            semantic_chunks = vector_store_service.search_similar_chunks(
                video_id=video_id,
                query=question,
                n_results=n_chunks
            )
            logger.info(f"Retrieved {len(semantic_chunks)} semantic chunks")

            # Combine and deduplicate chunks (prioritize context chunks)
            seen_indices = set()
            chunks = []

            # Add context chunks first (these are more relevant to current viewing)
            for chunk in context_chunks:
                idx = chunk['metadata']['index']
                if idx not in seen_indices:
                    seen_indices.add(idx)
                    chunks.append(chunk)

            # Add semantic chunks
            for chunk in semantic_chunks:
                idx = chunk['metadata']['index']
                if idx not in seen_indices and len(chunks) < n_chunks * 2:
                    seen_indices.add(idx)
                    chunks.append(chunk)

            logger.info(f"Using {len(chunks)} total chunks for context")

            # Step 2: Format context from chunks
            context = self._format_context(chunks)

            # Step 2.5: Generate smart context prompt if timestamp provided
            context_prompt = None
            if current_timestamp is not None and context_chunks:
                context_prompt = self._generate_context_prompt(db, context_chunks, current_timestamp)

            # Step 3: Get prompt from centralized service
            logger.info("Retrieving centralized prompt: chat_qa_main")
            prompt_config = prompt_service.render_prompt(
                db=db,
                prompt_name="chat_qa_main",
                variables={}
            )

            # Step 4: Build conversation messages
            messages = [
                {"role": "system", "content": prompt_config["system_message"]}
            ]

            # Add conversation history if provided
            if conversation_history:
                # Limit history to last 10 messages to avoid token limits
                recent_history = conversation_history[-10:]
                for msg in recent_history:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            # Add current question with context
            user_message = f"""Video Transcript Context:
{context}

User Question: {question}

Please answer the question using the transcript context provided above. Reference specific timestamps when relevant."""

            messages.append({"role": "user", "content": user_message})

            # Step 5: Call OpenAI API with prompt configuration
            logger.info(f"Calling OpenAI API with model: {prompt_config['model']}")
            response = self.openai_client.chat.completions.create(
                model=prompt_config["model"],
                messages=messages,
                temperature=prompt_config["temperature"],
                max_tokens=prompt_config["max_tokens"]
            )

            answer = response.choices[0].message.content
            logger.info(f"Received answer from OpenAI (length: {len(answer)})")

            # Step 6: Calculate confidence score
            confidence = self._calculate_confidence(chunks, question)

            # Step 7: Format chunks for response
            referenced_chunks = [
                {
                    'text': chunk['text'],
                    'start_time': chunk['metadata']['start_time'],
                    'end_time': chunk['metadata']['end_time'],
                    'index': chunk['metadata']['index']
                }
                for chunk in chunks
            ]

            return answer, referenced_chunks, confidence, context_prompt

        except Exception as e:
            logger.error(f"Error in ask_question: {e}")
            raise

    def _generate_context_prompt(
        self,
        db: Session,  # Added for centralized prompt management
        context_chunks: List[Dict],
        timestamp: float
    ) -> str:
        """
        Generate a smart context-aware prompt based on what user is watching (using centralized prompts).

        Args:
            db: Database session for prompt retrieval
            context_chunks: Chunks around current timestamp
            timestamp: Current playback time

        Returns:
            Smart prompt string
        """
        try:
            if not context_chunks:
                return None

            # Get the most relevant chunk text
            current_content = context_chunks[0]['text'][:200]  # First 200 chars

            # Get prompt from centralized service
            logger.info("Retrieving centralized prompt: chat_context_engagement")
            prompt_config = prompt_service.render_prompt(
                db=db,
                prompt_name="chat_context_engagement",
                variables={
                    "timestamp": int(timestamp),
                    "current_content": current_content
                }
            )

            messages = [
                {"role": "system", "content": prompt_config["system_message"]},
                {"role": "user", "content": prompt_config["user_message"]}
            ]

            response = self.openai_client.chat.completions.create(
                model=prompt_config["model"],
                messages=messages,
                temperature=prompt_config["temperature"],
                max_tokens=prompt_config["max_tokens"]
            )

            prompt = response.choices[0].message.content.strip()
            logger.info(f"Generated context prompt: {prompt}")
            return prompt

        except Exception as e:
            logger.error(f"Error generating context prompt: {e}")
            return None

    def generate_quiz(
        self,
        db: Session,  # Added for centralized prompt management
        video_id: int,
        current_timestamp: Optional[float] = None,
        difficulty: str = "medium"
    ) -> Dict:
        """
        Generate a quiz question based on video content (using centralized prompts).

        Args:
            db: Database session for prompt retrieval
            video_id: ID of the video
            current_timestamp: Current playback time (if None, use random content)
            difficulty: Difficulty level (easy, medium, hard)

        Returns:
            Dictionary with quiz question, options, answer, and explanation
        """
        try:
            # Get relevant content
            if current_timestamp is not None:
                chunks = self._get_chunks_by_timestamp(
                    video_id=video_id,
                    timestamp=current_timestamp,
                    window_seconds=60.0
                )
            else:
                # Get random chunks
                chunks = vector_store_service.search_similar_chunks(
                    video_id=video_id,
                    query="important concepts",
                    n_results=3
                )

            if not chunks:
                raise ValueError("No content available to generate quiz")

            # Combine chunk texts for context
            context_text = "\n\n".join([chunk['text'] for chunk in chunks[:3]])

            # Get prompt from centralized service
            logger.info("Retrieving centralized prompt: quiz_generation")
            prompt_config = prompt_service.render_prompt(
                db=db,
                prompt_name="quiz_generation",
                variables={
                    "difficulty": difficulty,
                    "context_text": context_text
                }
            )

            messages = [
                {"role": "system", "content": prompt_config["system_message"]},
                {"role": "user", "content": prompt_config["user_message"]}
            ]

            response = self.openai_client.chat.completions.create(
                model=prompt_config["model"],
                messages=messages,
                temperature=prompt_config["temperature"],
                max_tokens=prompt_config["max_tokens"],
                response_format={"type": "json_object"} if prompt_config["response_format"] == "json" else None
            )

            quiz_data = json.loads(response.choices[0].message.content)
            logger.info(f"Generated quiz question: {quiz_data['question']}")

            return {
                'quiz': quiz_data,
                'context_timestamp': current_timestamp
            }

        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            raise

    def generate_session_title(
        self,
        db: Session,  # Added for centralized prompt management
        first_question: str,
        first_answer: str
    ) -> str:
        """
        Generate a concise title for a chat session based on the first question (using centralized prompts).

        Args:
            db: Database session for prompt retrieval
            first_question: The user's first question
            first_answer: The assistant's first answer

        Returns:
            Generated title string
        """
        try:
            # Get prompt from centralized service
            logger.info("Retrieving centralized prompt: chat_session_title")
            prompt_config = prompt_service.render_prompt(
                db=db,
                prompt_name="chat_session_title",
                variables={"first_question": first_question}
            )

            messages = [
                {"role": "system", "content": prompt_config["system_message"]},
                {"role": "user", "content": prompt_config["user_message"]}
            ]

            response = self.openai_client.chat.completions.create(
                model=prompt_config["model"],
                messages=messages,
                temperature=prompt_config["temperature"],
                max_tokens=prompt_config["max_tokens"]
            )

            title = response.choices[0].message.content.strip().strip('"\'')
            logger.info(f"Generated session title: {title}")

            return title[:50]  # Ensure max 50 chars

        except Exception as e:
            logger.error(f"Error generating session title: {e}")
            # Fallback to truncated question
            return first_question[:50]

    def analyze_video_content(
        self,
        db: Session,  # Added for centralized prompt management
        video_id: int,
        transcript_text: str = None
    ) -> Dict:
        """
        Analyze video content and generate summary, outline, and key terms (using centralized prompts).

        Args:
            db: Database session for prompt retrieval
            video_id: ID of the video
            transcript_text: Optional full transcript text (if None, will retrieve from vector store)

        Returns:
            Dictionary with ai_summary, ai_outline, and ai_key_terms
        """
        try:
            # Get transcript content if not provided
            if not transcript_text:
                from app.services.vector_store_service import vector_store_service
                collection = vector_store_service._get_or_create_collection(video_id)

                results = collection.get(include=['documents'])
                if not results or not results['documents']:
                    raise ValueError("No transcript content available for analysis")

                # Combine all chunks
                transcript_text = "\n\n".join(results['documents'])

            logger.info(f"Analyzing video content for video {video_id}, transcript length: {len(transcript_text)}")

            # Limit transcript length for API (keep first ~15000 chars for context)
            max_chars = 15000
            if len(transcript_text) > max_chars:
                transcript_text = transcript_text[:max_chars] + "\n\n[Content truncated for analysis]"

            # Get prompt from centralized service
            logger.info("Retrieving centralized prompt: video_content_analysis")
            prompt_config = prompt_service.render_prompt(
                db=db,
                prompt_name="video_content_analysis",
                variables={"transcript_text": transcript_text}
            )

            # Generate comprehensive analysis
            messages = [
                {"role": "system", "content": prompt_config["system_message"]},
                {"role": "user", "content": prompt_config["user_message"]}
            ]

            response = self.openai_client.chat.completions.create(
                model=prompt_config["model"],
                messages=messages,
                temperature=prompt_config["temperature"],
                max_tokens=prompt_config["max_tokens"],
                response_format={"type": "json_object"} if prompt_config["response_format"] == "json" else None
            )

            analysis = json.loads(response.choices[0].message.content)

            logger.info(f"Video analysis complete for video {video_id}")
            logger.info(f"Summary: {analysis.get('summary', 'N/A')[:100]}...")

            return {
                'ai_summary': analysis.get('summary', ''),
                'ai_outline': json.dumps(analysis.get('outline', []), ensure_ascii=False),
                'ai_key_terms': json.dumps(analysis.get('key_terms', []), ensure_ascii=False)
            }

        except Exception as e:
            logger.error(f"Error analyzing video content for video {video_id}: {e}")
            raise

    def format_conversation_export(
        self,
        session_data: Dict,
        messages: List[Dict]
    ) -> str:
        """
        Format a chat session for export to S3.

        Args:
            session_data: Session metadata
            messages: List of messages in the session

        Returns:
            Formatted string (markdown format)
        """
        lines = [
            f"# Chat Session: {session_data.get('title', 'Untitled')}",
            f"",
            f"**Video ID:** {session_data['video_id']}",
            f"**User ID:** {session_data['user_id']}",
            f"**Created:** {session_data.get('created_at', 'Unknown')}",
            f"**Last Updated:** {session_data.get('updated_at', 'Unknown')}",
            f"",
            f"---",
            f""
        ]

        for msg in messages:
            role = msg['role'].upper()
            content = msg['content']
            timestamp = msg.get('created_at', 'Unknown')

            lines.append(f"## {role} ({timestamp})")
            lines.append(f"")
            lines.append(content)
            lines.append(f"")

            # Add transcript references if available
            if msg.get('transcript_references'):
                try:
                    refs = json.loads(msg['transcript_references'])
                    if refs:
                        lines.append(f"**Transcript References:**")
                        for ref in refs:
                            start = ref['start_time']
                            end = ref['end_time']
                            lines.append(f"- {int(start//60)}:{int(start%60):02d} - {int(end//60)}:{int(end%60):02d}")
                        lines.append(f"")
                except:
                    pass

            lines.append(f"---")
            lines.append(f"")

        return "\n".join(lines)


# Singleton instance
ai_chat_service = AIChatService()
