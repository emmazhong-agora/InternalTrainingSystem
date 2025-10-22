from functools import lru_cache

from app.services.agora_service import AgoraService
from app.services.rag_service import RAGService
from app.services.storage_service import StorageService


@lru_cache
def get_storage_service() -> StorageService:
    return StorageService()


@lru_cache
def get_rag_service() -> RAGService:
    return RAGService()


@lru_cache
def get_agora_service() -> AgoraService:
    return AgoraService()
