from typing import Any, Dict

import httpx
from fastapi import HTTPException

from app.core.config import get_settings

settings = get_settings()

logger = __import__("logging").getLogger("app.services.agora")


class AgoraService:
    """
    Thin wrapper around Agora Conversational AI REST API.
    Replace the placeholder endpoints with actual Agora endpoints before production.
    """

    def __init__(self) -> None:
        self.base_url = "https://api.agora.io/conversationalai"  # Placeholder
        if settings.agora_api_key:
            self.session: httpx.AsyncClient | None = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {settings.agora_api_key}"}
            )
        else:
            self.session = None

    async def create_session(self, user_id: int, video_path: str) -> Dict[str, Any]:
        if not self.session:
            return {"session_id": f"dev-{user_id}-{video_path}"}
        try:
            response = await self.session.post(
                f"{self.base_url}/sessions",
                json={"user_id": user_id, "video_path": video_path},
                timeout=10.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Agora session creation failed, using local fallback: %s", exc)
            return {"session_id": f"dev-{user_id}-{video_path}"}
        return response.json()

    async def send_message(self, session_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        if not self.session:
            return {
                "session_id": session_id,
                "response": {
                    "text": "根据当前视频内容，我无法回答该问题（本地开发环境未连接 Agora）。",
                    "confidence": 0.0,
                },
            }
        try:
            response = await self.session.post(
                f"{self.base_url}/sessions/{session_id}/messages", json=message, timeout=10.0
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Agora message failed, returning fallback response: %s", exc)
            return {
                "session_id": session_id,
                "response": {
                    "text": "根据当前视频内容，我无法回答该问题（本地开发环境未连接 Agora）。",
                    "confidence": 0.0,
                },
            }
        return response.json()

    async def close_session(self, session_id: str) -> None:
        if not self.session:
            return
        try:
            response = await self.session.delete(
                f"{self.base_url}/sessions/{session_id}", timeout=5.0
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Agora close session failed, ignoring: %s", exc)

    async def aclose(self) -> None:
        if self.session:
            await self.session.aclose()
