import io
import json
import logging
import re
from datetime import timedelta
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app.core.config import get_settings
from app.core.security import decode_token
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.services import get_rag_service, get_storage_service
from app.models.folder import Folder
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from app.models.video import Video
from app.schemas.video import VideoDetail, VideoRead

logger = logging.getLogger("app.api.videos")
router = APIRouter(prefix="/videos", tags=["videos"])
settings = get_settings()


def _resolve_folder(db: Session, folder_id: Optional[int], owner_id: int) -> Optional[Folder]:
    if folder_id is None:
        return None
    folder = (
        db.query(Folder)
        .filter(Folder.id == folder_id, Folder.owner_id == owner_id)
        .first()
    )
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder


def _sanitize_filename(filename: str) -> str:
    filename = filename.strip()
    filename = re.sub(r"\s+", "", filename)
    return re.sub(r"[^A-Za-z0-9_.-]", "_", filename)


def _compute_path(db: Session, folder: Optional[Folder], filename: str) -> str:
    parts = [filename]
    current = folder
    while current:
        parts.append(current.name)
        if current.parent_id:
            current = db.query(Folder).filter(Folder.id == current.parent_id).first()
        else:
            current = None
    parts.reverse()
    return "/" + "/".join(parts)


def _get_stream_user(request: Request, db: Session) -> User:
    auth_header = request.headers.get("Authorization")
    token: Optional[str] = None
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
    if not token:
        token = request.query_params.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.id == int(payload.sub)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def _compute_path_for_existing(path: str) -> str:
    segments = path.strip("/").split("/")
    if not segments:
        return path
    *dirs, filename = segments
    sanitized_filename = _sanitize_filename(filename)
    sanitized_segments = dirs + [sanitized_filename]
    return "/" + "/".join(sanitized_segments)


def _cleanup_existing_video(
    video: Video,
    user_id: int,
    storage_service,
    rag_service,
    db: Session,
) -> None:
    kb: KnowledgeBase | None = (
        db.query(KnowledgeBase).filter(KnowledgeBase.video_id == video.id).first()
    )
    if kb and kb.vector_ids:
        rag_service.delete_vectors(kb.vector_ids)
    normalized_existing_path = _compute_path_for_existing(video.path)
    if normalized_existing_path != video.path:
        if (
            db.query(Video)
            .filter(Video.path == normalized_existing_path, Video.owner_id == user_id)
            .first()
        ):
            logger.warning(
                "Cannot normalize path %s to %s due to existing record", video.path, normalized_existing_path
            )
        else:
            video.path = normalized_existing_path
            db.commit()


@router.get("", response_model=list[VideoRead])
def list_videos(
    folder_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Video).filter(Video.owner_id == current_user.id)
    if folder_id is None:
        videos = query.all()
    else:
        videos = query.filter(Video.folder_id == folder_id).all()
    return [VideoRead.model_validate(video, from_attributes=True) for video in videos]


@router.get("/{video_id}", response_model=VideoDetail)
def get_video_detail(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage_service=Depends(get_storage_service),
):
    video = (
        db.query(Video)
        .filter(Video.id == video_id, Video.owner_id == current_user.id)
        .first()
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    storage_key = storage_service.build_object_key(current_user.id, video.path)
    transcript_key = storage_key.rsplit(".", 1)[0] + ".json"
    transcript_url = storage_service.generate_presigned_url(transcript_key, timedelta(minutes=30))
    base_read = VideoRead.model_validate(video, from_attributes=True)
    detail = VideoDetail(
        **base_read.model_dump(),
        playback_url=f"{settings.api_v1_prefix}/videos/{video.id}/stream",
        transcript_url=transcript_url,
    )
    return detail


@router.get("/{video_id}/stream")
def stream_video(
    video_id: int,
    request: Request,
    db: Session = Depends(get_db),
    storage_service=Depends(get_storage_service),
):
    user = _get_stream_user(request, db)
    video = (
        db.query(Video)
        .filter(Video.id == video_id, Video.owner_id == user.id)
        .first()
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    storage_key = storage_service.build_object_key(user.id, video.path)
    range_header = request.headers.get("Range")
    try:
        body, content_type, content_length, content_range, status_code = storage_service.get_object_stream(
            storage_key, range_header
        )
    except FileNotFoundError:
        alt_path = _compute_path_for_existing(video.path)
        alt_key = storage_service.build_object_key(user.id, alt_path)
        if alt_key != storage_key:
            try:
                body, content_type, content_length, content_range, status_code = storage_service.get_object_stream(
                    alt_key, range_header
                )
                video.path = alt_path
                db.commit()
            except FileNotFoundError:
                logger.warning("Video stream missing object key=%s for user_id=%s", storage_key, user.id)
                raise HTTPException(status_code=404, detail="Video file not found")
        else:
            logger.warning("Video stream missing object key=%s for user_id=%s", storage_key, user.id)
            raise HTTPException(status_code=404, detail="Video file not found")

    headers = {"Accept-Ranges": "bytes"}
    if content_length is not None:
        headers["Content-Length"] = str(content_length)
    if content_range:
        headers["Content-Range"] = content_range

    response = StreamingResponse(body.iter_chunks(chunk_size=1024 * 512), media_type=content_type)
    response.headers.update(headers)
    response.status_code = status_code
    return response


@router.post("/upload", response_model=VideoDetail, status_code=status.HTTP_201_CREATED)
async def upload_video(
    folder_id: Optional[int] = Form(default=None),
    duration: Optional[float] = Form(default=None),
    video_file: UploadFile = File(...),
    transcript_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage_service=Depends(get_storage_service),
    rag_service=Depends(get_rag_service),
):
    if not video_file.filename or not video_file.filename.lower().endswith(".mp4"):
        logger.warning("Upload rejected: invalid video file %s (user_id=%s)", video_file.filename, current_user.id)
        raise HTTPException(status_code=400, detail="Video file must be .mp4")
    if (
        not transcript_file.filename
        or not transcript_file.filename.lower().endswith(".json")
    ):
        logger.warning(
            "Upload rejected: invalid transcript file %s (user_id=%s)",
            transcript_file.filename,
            current_user.id,
        )
        raise HTTPException(status_code=400, detail="Transcript file must be .json")

    video_base = video_file.filename.rsplit(".", 1)[0]
    transcript_base = transcript_file.filename.rsplit(".", 1)[0]
    if video_base != transcript_base:
        logger.warning(
            "Upload rejected: base name mismatch video=%s transcript=%s (user_id=%s)",
            video_file.filename,
            transcript_file.filename,
            current_user.id,
        )
        raise HTTPException(status_code=400, detail="Video and transcript file names must match")

    sanitized_video_name = _sanitize_filename(video_file.filename)
    sanitized_transcript_name = _sanitize_filename(transcript_file.filename)
    if sanitized_video_name.rsplit(".", 1)[0] != sanitized_transcript_name.rsplit(".", 1)[0]:
        logger.warning(
            "Upload rejected: sanitized name mismatch video=%s transcript=%s (user_id=%s)",
            sanitized_video_name,
            sanitized_transcript_name,
            current_user.id,
        )
        raise HTTPException(status_code=400, detail="Video and transcript file names must match")

    folder = _resolve_folder(db, folder_id, current_user.id)
    path = _compute_path(db, folder, sanitized_video_name)

    existing = db.query(Video).filter(Video.path == path, Video.owner_id == current_user.id).first()
    if existing:
        logger.info(
            "Upload replacing existing video path=%s for user_id=%s", path, current_user.id
        )
        _cleanup_existing_video(existing, current_user.id, storage_service, rag_service, db)
        existing_prefix = storage_service.build_object_key(current_user.id, existing.path).rsplit(".", 1)[0]
        storage_service.delete_prefix(existing_prefix)
        db.delete(existing)
        db.commit()

    storage_key = storage_service.build_object_key(current_user.id, path)
    transcript_key = storage_service.build_object_key(
        current_user.id, _compute_path(db, folder, sanitized_transcript_name)
    )

    storage_service.upload_file(
        storage_key,
        video_file.file,
        content_type=video_file.content_type or "video/mp4",
    )

    transcript_bytes = await transcript_file.read()
    try:
        transcript_payload = json.loads(transcript_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        logger.exception("Failed to decode transcript JSON for file=%s", transcript_file.filename)
        raise HTTPException(status_code=400, detail="Transcript JSON is invalid") from exc

    storage_service.upload_file(
        transcript_key,
        io.BytesIO(transcript_bytes),
        content_type="application/json",
    )

    video = Video(
        filename=video_file.filename,
        path=path,
        folder_id=folder.id if folder else None,
        owner_id=current_user.id,
        duration=duration,
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    transcript_payload["video_id"] = transcript_payload.get("video_id") or video.path
    try:
        rag_service.ingest_transcript(db=db, video=video, payload=transcript_payload)
    except ValueError as exc:
        logger.exception(
            "Transcript ingestion failed for video_id=%s; payload_keys=%s",
            video.id,
            list(transcript_payload.keys()),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error during transcript ingestion for video_id=%s", video.id)
        raise HTTPException(status_code=500, detail="Failed to process transcript") from exc

    base_read = VideoRead.model_validate(video, from_attributes=True)
    detail = VideoDetail(
        **base_read.model_dump(),
        playback_url=f"{settings.api_v1_prefix}/videos/{video.id}/stream",
        transcript_url=storage_service.generate_presigned_url(
            transcript_key, timedelta(minutes=30)
        ),
    )
    return detail


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage_service=Depends(get_storage_service),
    rag_service=Depends(get_rag_service),
):
    video = (
        db.query(Video)
        .filter(Video.id == video_id, Video.owner_id == current_user.id)
        .first()
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    kb: KnowledgeBase | None = (
        db.query(KnowledgeBase).filter(KnowledgeBase.video_id == video.id).first()
    )
    if kb and kb.vector_ids:
        rag_service.delete_vectors(kb.vector_ids)

    storage_key_prefix = storage_service.build_object_key(current_user.id, video.path).rsplit(
        ".", 1
    )[0]
    storage_service.delete_prefix(storage_key_prefix)

    db.delete(video)
    db.commit()
