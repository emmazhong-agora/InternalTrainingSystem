import logging
from typing import Any, Dict, List
from uuid import uuid4

from qdrant_client.models import PointStruct
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.knowledge_base import KnowledgeBase
from app.models.video import Video
from app.schemas.knowledge_base import RAGQuery
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStoreService
from app.utils.chunking import chunk_transcript

logger = logging.getLogger("app.services.rag_service")
settings = get_settings()


class RAGService:
    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStoreService()

    def ingest_transcript(self, db: Session, video: Video, payload: Dict[str, Any]) -> KnowledgeBase:
        transcript_segments = self._extract_segments(payload)
        logger.info(
            "RAG ingest: payload keys=%s; transcript count=%d",
            list(payload.keys()),
            len(transcript_segments),
        )

        chunks = chunk_transcript(transcript_segments)
        embeddings = self.embedding_service.embed_texts(chunks)
        point_ids: List[str] = []
        points: List[PointStruct] = []
        for chunk, embedding in zip(chunks, embeddings, strict=False):
            point_id = str(uuid4())
            point_ids.append(point_id)
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "video_id": video.id,
                        "text": chunk,
                        "metadata": payload.get("metadata"),
                    },
                )
            )

        if points:
            self.vector_store.upsert(points)

        kb = db.query(KnowledgeBase).filter(KnowledgeBase.video_id == video.id).first()
        if not kb:
            kb = KnowledgeBase(video_id=video.id, json_content=payload, vector_ids=point_ids)
            db.add(kb)
        else:
            kb.json_content = payload
            kb.vector_ids = point_ids

        db.commit()
        db.refresh(kb)
        return kb

    @staticmethod
    def _extract_segments(payload: Dict[str, Any]) -> List[dict]:
        candidate = payload.get("transcript")
        if candidate is None and isinstance(payload, list):
            candidate = payload
        if candidate is None and isinstance(payload.get("segments"), list):
            candidate = payload["segments"]
        if candidate is None and isinstance(payload.get("results"), list):
            candidate = payload["results"]
        if candidate is None and isinstance(payload.get("glossary"), list):
            candidate = payload["glossary"]
        if candidate is None and isinstance(payload.get("topics"), list):
            candidate = payload["topics"]
        if candidate is None and isinstance(payload.get("items"), list):
            candidate = payload["items"]

        if not isinstance(candidate, list):
            raise ValueError("Transcript must be provided as a list of segments")
        if not candidate:
            raise ValueError("Transcript is empty")
        return candidate

    def query(self, video_id: int, question: str) -> List[Dict[str, Any]]:
        embedding = self.embedding_service.embed_texts([question])[0]
        results = self.vector_store.query(embedding, top_k=3, video_id=video_id)
        return results

    def delete_vectors(self, vector_ids: List[str]) -> None:
        self.vector_store.delete_by_ids(vector_ids)
