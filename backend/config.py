"""
Application configuration.

Loads environment variables from .env using Pydantic Settings.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # ==========================
    # Google Gemini
    # ==========================

    GOOGLE_API_KEY: str = Field(...)

    LLM_MODEL: str = Field(
        default="gemini-2.5-flash"
    )

    EMBEDDING_MODEL: str = Field(
        default="gemini-embedding-001"
    )

    # ==========================
    # RAG
    # ==========================

    CHUNK_SIZE: int = 500

    CHUNK_OVERLAP: int = 30

    RETRIEVAL_K: int = 3

    EMBEDDING_DIMENSION: int = 768

    # ==========================
    # Storage
    # ==========================

    VECTOR_DB: str = "backend/storage/faiss_index"

    UPLOAD_FOLDER: str = "backend/storage/uploads"

    # ==========================
    # API
    # ==========================

    API_TITLE: str = "RAG PDF Chatbot"

    API_VERSION: str = "1.0.0"

    DEBUG: bool = True


@lru_cache
def get_settings() -> Settings:
    """
    Returns a singleton Settings object.
    """

    return Settings()