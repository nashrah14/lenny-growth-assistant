"""
Unit Tests for LLM Providers & Router Fallback
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.llm.base import LLMMessage, LLMResponse
from backend.app.llm.router import LLMRouter
from backend.app.llm.ollama import OllamaProvider
from backend.app.core.exceptions import LLMProviderError

@pytest.mark.asyncio
async def test_llm_router_provider_selection():
    router = LLMRouter()
    gemini = router.get_provider("gemini")
    assert gemini.provider_name == "gemini"

    ollama = router.get_provider("ollama")
    assert ollama.provider_name == "ollama"

    with pytest.raises(LLMProviderError):
        router.get_provider("unsupported_vendor")

@pytest.mark.asyncio
async def test_llm_router_fallback_on_primary_failure():
    router = LLMRouter()

    mock_gemini = router.get_provider("gemini")
    mock_ollama = router.get_provider("ollama")

    fallback_response = LLMResponse(
        content="Response from Ollama fallback",
        model_provider="ollama",
        model_name="llama3.2",
        latency_ms=450
    )

    # Primary (Gemini) fails, Fallback (Ollama) succeeds
    with patch.object(mock_gemini, "generate", side_effect=LLMProviderError("Gemini Key Quota Exceeded")):
        with patch.object(mock_ollama, "generate", new_callable=AsyncMock) as mock_ollama_gen:
            mock_ollama_gen.return_value = fallback_response

            resp = await router.generate(
                messages=[LLMMessage(role="user", content="Hello")],
                provider_name="gemini",
                allow_fallback=True
            )

            assert resp.model_provider == "ollama"
            assert resp.content == "Response from Ollama fallback"
            mock_ollama_gen.assert_called_once()

def test_ollama_provider_url_normalization():
    # Test handling of trailing slash
    p1 = OllamaProvider(base_url="http://localhost:11434/")
    assert p1.base_url == "http://localhost:11434"

    # Test handling of /api suffix
    p2 = OllamaProvider(base_url="http://localhost:11434/api")
    assert p2.base_url == "http://localhost:11434"

    # Test handling of /api/chat suffix
    p3 = OllamaProvider(base_url="http://localhost:11434/api/chat/")
    assert p3.base_url == "http://localhost:11434"

    # Test default model
    p4 = OllamaProvider()
    assert p4.model_name == "llama3.2:3b"

