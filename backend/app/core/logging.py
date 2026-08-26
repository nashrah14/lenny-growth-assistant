"""
Structured JSON and Console Logging for The Lenny Growth Assistant
Provides request tracing, latency tracking, RAG diagnostics, and secret redaction.
"""
import logging
import json
import sys
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Regex patterns for masking sensitive information
SECRET_PATTERNS = [
    (re.compile(r'(api[-_]?key|apikey|secret|password|token|auth)["\']?\s*[:=]\s*["\']?([^"\'\s&]+)', re.IGNORECASE), r'\1=***REDACTED***'),
    (re.compile(r'(Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'(postgres(ql)?:\/\/[^:]+:)[^@]+(@)', re.IGNORECASE), r'\1***REDACTED***\3'),
]

def mask_secrets(text: str) -> str:
    """Mask credentials and sensitive strings in log messages."""
    if not isinstance(text, str):
        return str(text)
    for pattern, repl in SECRET_PATTERNS:
        text = pattern.sub(repl, text)
    return text


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as structured JSON with security redactions."""
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": mask_secrets(record.getMessage()),
        }

        # Include custom extra fields if provided
        for attr in ["request_id", "session_id", "operation", "latency_ms", "route", "status_code", "provider", "model"]:
            if hasattr(record, attr):
                log_data[attr] = getattr(record, attr)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure root logger with structured formatter."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter())
    root_logger.addHandler(handler)

    # Silence overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

    logger = logging.getLogger("lenny_assistant")
    logger.info("Structured logging initialized", extra={"operation": "startup"})
    return logger

# Module logger instance
logger = logging.getLogger("lenny_assistant")
