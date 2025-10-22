from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_name: str = "Internal Training System"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = 60 * 24
    postgres_dsn: str = Field(
        "postgresql+psycopg://training:training@localhost:5432/training",
        env="POSTGRES_DSN",
    )
    s3_endpoint_url: str = Field("http://localhost:9000", env="S3_ENDPOINT_URL")
    s3_bucket_name: str = Field("training-videos", env="S3_BUCKET_NAME")
    s3_access_key: str = Field("minioadmin", env="S3_ACCESS_KEY")
    s3_secret_key: str = Field("minioadmin", env="S3_SECRET_KEY")
    vector_store_url: str = Field("http://localhost:6333", env="VECTOR_STORE_URL")
    vector_collection_name: str = Field("video_transcripts", env="VECTOR_COLLECTION_NAME")
    embedding_dimension: int = Field(1536, env="EMBEDDING_DIMENSION")
    embedding_model: str = Field("text-embedding-3-small", env="EMBEDDING_MODEL")
    openai_api_key: str | None = Field(None, env="OPENAI_API_KEY")
    agora_app_id: str | None = Field(None, env="AGORA_APP_ID")
    agora_api_key: str | None = Field(None, env="AGORA_API_KEY")
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    model_config = {"env_file": ".env", "case_sensitive": False}


@lru_cache
def get_settings() -> Settings:
    return Settings()
