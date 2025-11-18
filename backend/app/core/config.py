from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings."""

    # Application
    PROJECT_NAME: str = "Internal Training System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # AWS S3
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_BUCKET_NAME: str
    AWS_REGION: str = "us-east-1"

    # OpenAI (Phase 2)
    OPENAI_API_KEY: str = ""

    # Agora (Phase 2 - Voice AI)
    AGORA_APP_ID: str = ""
    AGORA_APP_CERTIFICATE: str = ""
    AGORA_CUSTOMER_ID: str = ""
    AGORA_CUSTOMER_SECRET: str = ""
    AGORA_CONVO_AI_BASE_URL: str = "https://api.agora.io/api/conversational-ai-agent/v2/projects"
    AGORA_AGENT_UID: str = "999"

    # Text-to-Speech (Microsoft Azure)
    MICROSOFT_TTS_KEY: str = ""
    MICROSOFT_TTS_REGION: str = ""

    # Text-to-Speech (ElevenLabs)
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = ""  # Default voice ID
    ELEVENLABS_MODEL_ID: str = "eleven_flash_v2_5"  # Default model

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # File Upload
    MAX_VIDEO_SIZE_MB: int = 500
    ALLOWED_VIDEO_EXTENSIONS: List[str] = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
    ALLOWED_TRANSCRIPT_EXTENSIONS: List[str] = [".vtt"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
