from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import json
from datetime import datetime

from app.db.session import get_db
from app.schemas.chat import (
    AskQuestionRequest,
    AskQuestionResponse,
    ChatSessionResponse,
    ChatSessionListResponse,
    ChatMessageResponse,
    GenerateQuizRequest,
    GenerateQuizResponse
)
from app.models.chat import ChatSession, ChatMessage, MessageRole
from app.models.video import Video
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.ai_chat_service import ai_chat_service
from app.services.transcript_service import transcript_service
from app.services.vector_store_service import vector_store_service
from app.services.s3_service import s3_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ask", response_model=AskQuestionResponse)
async def ask_question(
    request: AskQuestionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Ask a question to the AI teaching assistant.
    Creates a new session if session_id is not provided.
    """
    logger.info(f"User {current_user.id} asking question about video {request.video_id}")

    # Verify video exists
    video = db.query(Video).filter(Video.id == request.video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    # Get or create chat session
    if request.session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == request.session_id,
            ChatSession.user_id == current_user.id
        ).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
    else:
        # Create new session
        session = ChatSession(
            user_id=current_user.id,
            video_id=request.video_id
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        logger.info(f"Created new chat session {session.id}")

    # Get conversation history
    conversation_history = []
    if request.session_id:
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at).all()

        conversation_history = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages[-10:]  # Last 10 messages
        ]

    try:
        # Ask the AI assistant with optional timestamp context
        answer, referenced_chunks, confidence, context_prompt = ai_chat_service.ask_question(
            db=db,  # Added for centralized prompt management
            video_id=request.video_id,
            question=request.question,
            conversation_history=conversation_history,
            n_chunks=5,
            current_timestamp=request.current_timestamp
        )

        # Save user message
        user_message = ChatMessage(
            session_id=session.id,
            role=MessageRole.USER,
            content=request.question
        )
        db.add(user_message)

        # Save assistant message
        assistant_message = ChatMessage(
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            content=answer,
            transcript_references=json.dumps(referenced_chunks) if referenced_chunks else None,
            confidence_score=confidence
        )
        db.add(assistant_message)

        # Update session last_message_at
        session.last_message_at = datetime.utcnow()

        # Generate title for first message
        if not session.title:
            title = ai_chat_service.generate_session_title(db, request.question, answer)
            session.title = title
            logger.info(f"Generated session title: {title}")

        db.commit()
        db.refresh(user_message)
        db.refresh(assistant_message)
        db.refresh(session)

        logger.info(f"Saved messages to session {session.id}, confidence: {confidence}")

        return AskQuestionResponse(
            session_id=session.id,
            user_message=ChatMessageResponse.model_validate(user_message),
            assistant_message=ChatMessageResponse.model_validate(assistant_message),
            referenced_chunks=referenced_chunks,
            context_prompt=context_prompt
        )

    except Exception as e:
        logger.error(f"Error processing question: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process question: {str(e)}"
        )


@router.get("/sessions", response_model=ChatSessionListResponse)
def list_sessions(
    video_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's chat sessions."""
    query = db.query(ChatSession).filter(ChatSession.user_id == current_user.id)

    if video_id:
        query = query.filter(ChatSession.video_id == video_id)

    query = query.order_by(ChatSession.last_message_at.desc())

    total = query.count()
    sessions = query.offset((page - 1) * page_size).limit(page_size).all()

    logger.info(f"Retrieved {len(sessions)} chat sessions for user {current_user.id}")

    return ChatSessionListResponse(
        total=total,
        sessions=[ChatSessionResponse.model_validate(s) for s in sessions]
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def get_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific chat session with all messages."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    return ChatSessionResponse.model_validate(session)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    db.delete(session)
    db.commit()
    logger.info(f"Deleted chat session {session_id}")

    return None


@router.post("/sessions/{session_id}/export")
def export_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export chat session to S3."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    try:
        # Get all messages
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all()

        # Format conversation
        session_data = {
            'title': session.title,
            'video_id': session.video_id,
            'user_id': session.user_id,
            'created_at': str(session.created_at),
            'updated_at': str(session.updated_at) if session.updated_at else None
        }

        messages_data = [
            {
                'role': msg.role.value,
                'content': msg.content,
                'created_at': str(msg.created_at),
                'transcript_references': msg.transcript_references
            }
            for msg in messages
        ]

        formatted_content = ai_chat_service.format_conversation_export(
            session_data,
            messages_data
        )

        # Upload to S3
        filename = f"chat_export_{session_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
        s3_url = s3_service.upload_content(
            content=formatted_content.encode('utf-8'),
            filename=filename,
            folder="chats",
            content_type="text/markdown"
        )

        # Update session with S3 URL
        session.s3_url = s3_url
        db.commit()

        logger.info(f"Exported chat session {session_id} to {s3_url}")

        return {
            "message": "Chat session exported successfully",
            "s3_url": s3_url
        }

    except Exception as e:
        logger.error(f"Error exporting session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export session: {str(e)}"
        )


@router.post("/process-transcript/{video_id}")
async def process_transcript(
    video_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Process a video's transcript and store embeddings in vector database.
    This should be called after video upload or when transcript needs reprocessing.
    """
    logger.info(f"Processing transcript for video {video_id}")

    # Verify video exists
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    if not video.transcript_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Video has no transcript"
        )

    try:
        # Process transcript (load, parse, chunk)
        chunks = transcript_service.process_video_transcript(
            vtt_url=video.transcript_url,
            chunk_size=5
        )

        logger.info(f"Processed {len(chunks)} transcript chunks")

        # Prepare chunks for vector store
        chunk_dicts = [
            {
                'text': chunk.text,
                'start_time': chunk.start_time,
                'end_time': chunk.end_time,
                'index': chunk.index
            }
            for chunk in chunks
        ]

        # Store in vector database
        vector_store_service.add_transcript_chunks(
            video_id=video_id,
            chunks=chunk_dicts,
            clear_existing=True  # Clear old embeddings if re-processing
        )

        logger.info(f"Successfully stored embeddings for video {video_id}")

        # Perform AI content analysis
        try:
            logger.info(f"Starting AI content analysis for video {video_id}")
            analysis_result = ai_chat_service.analyze_video_content(db, video_id)

            # Update video with AI-generated content
            video.ai_summary = analysis_result['ai_summary']
            video.ai_outline = analysis_result['ai_outline']
            video.ai_key_terms = analysis_result['ai_key_terms']
            db.commit()

            logger.info(f"AI analysis complete and saved for video {video_id}")
        except Exception as e:
            logger.error(f"AI analysis failed for video {video_id}: {e}")
            # Don't fail the whole request if AI analysis fails
            pass

        # Get collection info
        collection_info = vector_store_service.get_collection_info(video_id)

        return {
            "message": "Transcript processed successfully",
            "video_id": video_id,
            "chunks_processed": len(chunks),
            "collection_info": collection_info,
            "ai_analysis_complete": video.ai_summary is not None
        }

    except Exception as e:
        logger.error(f"Error processing transcript for video {video_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process transcript: {str(e)}"
        )


@router.get("/collection-info/{video_id}")
def get_collection_info(
    video_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get information about a video's vector database collection."""
    # Verify video exists
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    collection_info = vector_store_service.get_collection_info(video_id)
    return collection_info


@router.post("/generate-quiz", response_model=GenerateQuizResponse)
async def generate_quiz(
    request: GenerateQuizRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate a quiz question based on video content.
    If current_timestamp is provided, generates quiz based on content around that time.
    """
    logger.info(f"Generating quiz for video {request.video_id}, timestamp: {request.current_timestamp}")

    # Verify video exists
    video = db.query(Video).filter(Video.id == request.video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    try:
        quiz_data = ai_chat_service.generate_quiz(
            db=db,  # Added for centralized prompt management
            video_id=request.video_id,
            current_timestamp=request.current_timestamp,
            difficulty=request.difficulty or "medium"
        )

        logger.info(f"Generated quiz successfully for video {request.video_id}")

        return GenerateQuizResponse(**quiz_data)

    except Exception as e:
        logger.error(f"Error generating quiz for video {request.video_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quiz: {str(e)}"
        )
