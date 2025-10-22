import logging
from typing import List, Sequence

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import (
    Distance,
    Filter,
    FieldCondition,
    PointIdsList,
    PointStruct,
    VectorParams,
)

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger("app.services.vector_store")


class VectorStoreService:
    def __init__(self) -> None:
        self.client = QdrantClient(url=settings.vector_store_url)
        self.collection_name = settings.vector_collection_name
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        try:
            exists = self.client.collection_exists(self.collection_name)
        except UnexpectedResponse as exc:
            if getattr(exc, "status_code", None) == 404:
                exists = False
            else:
                raise
        if exists:
            info = self.client.get_collection(self.collection_name)
            current_size = info.config.params.vectors.size  # type: ignore[union-attr]
            if current_size != settings.embedding_dimension:
                logger.warning(
                    "Recreating Qdrant collection %s due to dimension mismatch (current=%s expected=%s)",
                    self.collection_name,
                    current_size,
                    settings.embedding_dimension,
                )
                self.client.delete_collection(self.collection_name)
            else:
                return
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=settings.embedding_dimension, distance=Distance.COSINE),
        )

    def upsert(
        self,
        points: Sequence[PointStruct],
    ) -> List[str]:
        logger.info(
            "Qdrant request: POST /collections/%s/points (count=%d)",
            self.collection_name,
            len(points),
        )
        result = self.client.upsert(
            collection_name=self.collection_name,
            wait=True,
            points=points,
        )
        return [point.id for point in points]

    def query(self, vector: List[float], top_k: int, video_id: int) -> List[dict]:
        response = self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=top_k,
            with_payload=True,
            query_filter=Filter(
                must=[FieldCondition(key="video_id", match={"value": video_id})]
            ),
        )
        logger.info(
            "Qdrant request: POST /collections/%s/points/search (video_id=%s, top_k=%d)",
            self.collection_name,
            video_id,
            top_k,
        )
        return [{"score": item.score, "payload": item.payload} for item in response]

    def delete_by_ids(self, ids: Sequence[str]) -> None:
        if not ids:
            return
        logger.info(
            "Qdrant request: DELETE /collections/%s/points (count=%d)",
            self.collection_name,
            len(ids),
        )
        selector = PointIdsList(points=list(ids))
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=selector,
            wait=True,
        )
