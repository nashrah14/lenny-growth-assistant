"""
Core Application Configuration
Uses Pydantic Settings v2 for typed, centralized, and validated configuration.
"""
from typing import List, Literal, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path

# Base directory of the backend
BASE_DIR = Path(__file__).resolve().parent.parent.parent
WORKSPACE_ROOT = BASE_DIR.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(WORKSPACE_ROOT / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # Application
    APP_NAME: str = "The Lenny Growth Assistant"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # CORS Configuration
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./lenny_assistant.db"
    DB_ECHO: bool = False

    # Authentication & Session Security (OWASP compliant)
    JWT_SECRET_KEY: str = "lenny-secret-key-change-in-production-2026-secure-jwt"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    COOKIE_NAME: str = "lenny_auth_session"
    COOKIE_SECURE: bool = False  # Set to True in production (HTTPS)
    COOKIE_SAMESITE: str = "lax"
    COOKIE_HTTPONLY: bool = True

    # Qdrant Cloud Vector DB
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION: str = "lenny_transcripts"
    QDRANT_TIMEOUT: float = 30.0

    # LLM Provider Configuration
    LLM_PROVIDER: Literal["gemini", "ollama"] = "gemini"

    # Google Gemini Configuration
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_API_KEY_FALLBACK: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.6-flash"

    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_TIMEOUT_SECONDS: int = 120

    # Embedding Model Configuration
    EMBEDDING_PROVIDER: str = "sentence_transformers"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_BATCH_SIZE: int = 64

    # Retrieval & RRF Configuration
    DENSE_TOP_K: int = 20
    BM25_TOP_K: int = 20
    RRF_K: int = 60
    RRF_TOP_K: int = 20
    RERANK_TOP_K: int = 5

    # Reranker Configuration
    RERANKER_PROVIDER: str = "sentence_transformers"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANKER_ENABLED: bool = True

    # Chunking Configuration
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 120

    # Transcripts Dataset Path
    TRANSCRIPTS_DIR: str = str(
        WORKSPACE_ROOT / "lennys-podcast-transcripts-main" / "lennys-podcast-transcripts-main" / "episodes"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: any) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return [str(i) for i in v]
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def has_gemini_credentials(self) -> bool:
        primary = bool(self.GEMINI_API_KEY and len(self.GEMINI_API_KEY.strip()) > 5)
        fallback = bool(self.GEMINI_API_KEY_FALLBACK and len(self.GEMINI_API_KEY_FALLBACK.strip()) > 5)
        return primary or fallback

    @property
    def has_qdrant_credentials(self) -> bool:
        return bool(self.QDRANT_URL and len(self.QDRANT_URL.strip()) > 5)


# Global settings singleton instance
settings = Settings()
