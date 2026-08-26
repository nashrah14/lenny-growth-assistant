"""
SQLAlchemy Declarative Base & Common Model Utilities
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, JSON
from sqlalchemy.types import TypeDecorator, CHAR
import json

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses CHAR(36) to store 128 bit UUID values across PostgreSQL, SQLite, etc.
    """
    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif isinstance(value, uuid.UUID):
            return str(value)
        else:
            return str(uuid.UUID(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value


class Base(DeclarativeBase):
    """Base declarative class for all database models."""
    pass
