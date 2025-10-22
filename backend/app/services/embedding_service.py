import hashlib
import math
from typing import List

from openai import OpenAI

from app.core.config import get_settings

settings = get_settings()


class EmbeddingService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if self.client:
            response = self.client.embeddings.create(
                input=texts,
                model=settings.embedding_model,
            )
            return [data.embedding for data in response.data]
        return [self._fallback_embedding(text, settings.embedding_dimension) for text in texts]

    @staticmethod
    def _fallback_embedding(text: str, dims: int) -> List[float]:
        # Deterministic hash-based embedding for local development without API keys.
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        repeat_factor = math.ceil(dims / len(digest))
        data = (digest * repeat_factor)[:dims]
        return [byte / 255.0 for byte in data]
