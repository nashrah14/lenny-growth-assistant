"""
Custom Domain Exceptions & Structured Error Codes
Ensures clear, safe error responses without leaking internal stack traces.
"""
from typing import Any, Dict, Optional

class AppException(Exception):
    """Base application exception."""
    status_code: int = 500
    error_code: str = "INTERNAL_SERVER_ERROR"
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details
            }
        }


class EntityNotFoundError(AppException):
    """Raised when a requested resource is not found."""
    status_code = 404
    error_code = "NOT_FOUND"


class SessionNotFoundError(EntityNotFoundError):
    """Raised when a session does not exist."""
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session with ID '{session_id}' was not found.",
            details={"session_id": str(session_id)},
            error_code="SESSION_NOT_FOUND"
        )


class ArtifactNotFoundError(EntityNotFoundError):
    """Raised when an artifact does not exist."""
    def __init__(self, artifact_id: str):
        super().__init__(
            message=f"Artifact with ID '{artifact_id}' was not found.",
            details={"artifact_id": str(artifact_id)},
            error_code="ARTIFACT_NOT_FOUND"
        )


class LLMProviderError(AppException):
    """Raised when LLM API call fails."""
    status_code = 502
    error_code = "LLM_PROVIDER_ERROR"


class LLMTimeoutError(AppException):
    """Raised when LLM call exceeds configured timeout."""
    status_code = 504
    error_code = "LLM_TIMEOUT"


class VectorDBError(AppException):
    """Raised when Qdrant vector database operations fail."""
    status_code = 503
    error_code = "VECTOR_DB_UNAVAILABLE"


class EmbeddingError(AppException):
    """Raised when text embedding computation fails."""
    status_code = 500
    error_code = "EMBEDDING_ERROR"


class SanitizationError(AppException):
    """Raised when artifact sanitization fails or encounters prohibited content."""
    status_code = 400
    error_code = "SANITIZATION_FAILED"


class IngestionError(AppException):
    """Raised during transcript dataset parsing or indexing failures."""
    status_code = 500
    error_code = "INGESTION_ERROR"
