"""
Unit Tests for Configuration & Settings
"""
import os
import pytest
from backend.app.core.config import Settings

def test_settings_defaults():
    settings = Settings()
    assert settings.APP_NAME == "The Lenny Growth Assistant"
    assert settings.EMBEDDING_DIMENSION == 384
    assert settings.CHUNK_SIZE == 800
    assert settings.CHUNK_OVERLAP == 120
    assert settings.RRF_K == 60
    assert "http://localhost:5173" in settings.CORS_ORIGINS

def test_settings_cors_parsing():
    s = Settings(CORS_ORIGINS='["http://localhost:3000", "http://test.local"]')
    assert "http://localhost:3000" in s.CORS_ORIGINS
    assert "http://test.local" in s.CORS_ORIGINS
