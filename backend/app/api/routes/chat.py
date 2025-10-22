from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.services import get_agora_service, get_rag_service
from app.models.user import User
from app.models.video import Video
from app.schemas.chat import ChatRequest, ChatResponse, ChatSource

router = APIRouter(prefix="/chat", tags=["chat"])
settings = get_settings()

openai_client: Optional[OpenAI] = (
    OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
)

PROMPT_TEMPLATE = """你是一位技术支持培训助手。请根据以下从当前培训视频中检索到的内容回答问题。
如果内容不相关或无法回答，请说“根据当前视频内容，我无法回答该问题”。

检索内容：
{retrieved_chunks}

用户问题：{user_query}
"""


@router.post("/query", response_model=ChatResponse)
def query_chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rag_service=Depends(get_rag_service),
):
    video = (
        db.query(Video)
        .filter(Video.id == payload.video_id, Video.owner_id == current_user.id)
        .first()
    )
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    results = rag_service.query(video_id=video.id, question=payload.question)
    sources: list[ChatSource] = []
    retrieved_chunks: list[str] = []
    for index, item in enumerate(results, start=1):
        payload_item = item.get("payload", {}) if item else {}
        text = payload_item.get("text", "")
        metadata = payload_item.get("metadata")
        sources.append(
            ChatSource(
                score=float(item.get("score", 0.0)),
                text=text,
                metadata=metadata,
            )
        )
        retrieved_chunks.append(f"[{index}] {text}")

    context = "\n".join(retrieved_chunks) if retrieved_chunks else "无相关内容。"
    prompt = PROMPT_TEMPLATE.format(retrieved_chunks=context, user_query=payload.question)

    answer = "根据当前视频内容，我无法回答该问题"
    if openai_client and retrieved_chunks:
        try:
            completion = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "你是内部培训系统的智能助手。"},
                    {"role": "user", "content": prompt},
                ],
            )
            answer = completion.choices[0].message.content.strip()
        except Exception:
            # Fall back to deterministic summary if LLM call fails.
            answer = retrieved_chunks[0]
    elif retrieved_chunks:
        answer = retrieved_chunks[0]

    return ChatResponse(answer=answer, sources=sources, session_id=payload.session_id)


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_agora_session(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    agora_service=Depends(get_agora_service),
):
    video = (
        db.query(Video)
        .filter(Video.id == video_id, Video.owner_id == current_user.id)
        .first()
    )
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    session = await agora_service.create_session(current_user.id, video.path)
    return session


@router.post("/sessions/{session_id}/messages")
async def send_agora_message(
    session_id: str,
    message: dict,
    agora_service=Depends(get_agora_service),
):
    response = await agora_service.send_message(session_id, message)
    return response


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def close_agora_session(
    session_id: str,
    agora_service=Depends(get_agora_service),
):
    await agora_service.close_session(session_id)
