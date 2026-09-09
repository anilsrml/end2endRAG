from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "end2endRAG"
    database_url: str = "postgresql+psycopg://rag:rag@db:5432/rag"
    uploads_dir: Path = Path("var/uploads")
    max_upload_mb: int = 25

    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536
    openrouter_api_key: str = ""
    openrouter_model: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    cohere_api_key: str = ""
    cohere_rerank_model: str = "rerank-v4.0-fast"

    vector_candidates: int = Field(default=30, ge=1, le=100)
    keyword_candidates: int = Field(default=30, ge=1, le=100)
    rerank_candidates: int = Field(default=20, ge=1, le=100)
    final_chunks: int = Field(default=6, ge=1, le=20)

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
