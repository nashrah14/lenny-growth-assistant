"""
Tests for Ollama Streaming (Gap C)
Verifies:
  - generate_stream yields tokens from NDJSON response
  - Empty/whitespace tokens are not yielded
  - Malformed JSON lines are skipped gracefully
  - done=True terminates iteration
  - Connection failure raises LLMProviderError
  - Timeout raises LLMTimeoutError
  - Non-streaming generate() still works (no regression)
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.llm.ollama import OllamaProvider
from backend.app.llm.base import LLMMessage
from backend.app.core.exceptions import LLMProviderError, LLMTimeoutError


def _ndjson_stream(chunks: list) -> list:
    """Create a list of NDJSON lines from chunk dicts."""
    return [json.dumps(c) for c in chunks]


class TestOllamaStreamingChunks:
    @pytest.mark.asyncio
    async def test_stream_yields_tokens(self):
        """generate_stream must yield each non-empty content token."""
        provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2:3b")
        messages = [LLMMessage(role="user", content="Hello")]

        ndjson_lines = _ndjson_stream([
            {"message": {"content": "Hello"}, "done": False},
            {"message": {"content": " world"}, "done": False},
            {"message": {"content": "!"}, "done": True},
        ])

        # Mock httpx streaming context
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        async def _aiter_lines():
            for line in ndjson_lines:
                yield line

        mock_response.aiter_lines = _aiter_lines

        class MockStreamCtx:
            async def __aenter__(self): return mock_response
            async def __aexit__(self, *args): pass

        class MockClient:
            def stream(self, *args, **kwargs): return MockStreamCtx()
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass

        with patch("httpx.AsyncClient", return_value=MockClient()):
            tokens = []
            async for token in provider.generate_stream(messages=messages):
                tokens.append(token)

        assert tokens == ["Hello", " world", "!"]

    @pytest.mark.asyncio
    async def test_stream_skips_empty_tokens(self):
        """Empty content tokens must not be yielded."""
        provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2:3b")
        messages = [LLMMessage(role="user", content="Hi")]

        ndjson_lines = _ndjson_stream([
            {"message": {"content": "A"}, "done": False},
            {"message": {"content": ""}, "done": False},  # empty — skip
            {"message": {"content": "B"}, "done": True},
        ])

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        async def _aiter_lines():
            for line in ndjson_lines:
                yield line

        mock_response.aiter_lines = _aiter_lines

        class MockStreamCtx:
            async def __aenter__(self): return mock_response
            async def __aexit__(self, *args): pass

        class MockClient:
            def stream(self, *args, **kwargs): return MockStreamCtx()
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass

        with patch("httpx.AsyncClient", return_value=MockClient()):
            tokens = []
            async for token in provider.generate_stream(messages=messages):
                tokens.append(token)

        assert "" not in tokens
        assert "A" in tokens
        assert "B" in tokens

    @pytest.mark.asyncio
    async def test_stream_skips_malformed_json(self):
        """Malformed JSON lines must be skipped without crashing."""
        provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2:3b")
        messages = [LLMMessage(role="user", content="Hi")]

        # Mix of valid and invalid NDJSON
        lines = [
            '{"message": {"content": "Good"}, "done": false}',
            'NOT_VALID_JSON{{{',   # malformed
            '{"message": {"content": " token"}, "done": true}',
        ]

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        async def _aiter_lines():
            for line in lines:
                yield line

        mock_response.aiter_lines = _aiter_lines

        class MockStreamCtx:
            async def __aenter__(self): return mock_response
            async def __aexit__(self, *args): pass

        class MockClient:
            def stream(self, *args, **kwargs): return MockStreamCtx()
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass

        with patch("httpx.AsyncClient", return_value=MockClient()):
            tokens = []
            async for token in provider.generate_stream(messages=messages):
                tokens.append(token)

        # Should have yielded the 2 valid tokens, not crashed on invalid JSON
        assert "Good" in tokens
        assert " token" in tokens

    @pytest.mark.asyncio
    async def test_stream_stops_on_done_true(self):
        """done=True must terminate streaming even if more lines follow."""
        provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2:3b")
        messages = [LLMMessage(role="user", content="Hi")]

        ndjson_lines = _ndjson_stream([
            {"message": {"content": "First"}, "done": False},
            {"message": {"content": "Second"}, "done": True},
            {"message": {"content": "Should not appear"}, "done": False},
        ])

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        async def _aiter_lines():
            for line in ndjson_lines:
                yield line

        mock_response.aiter_lines = _aiter_lines

        class MockStreamCtx:
            async def __aenter__(self): return mock_response
            async def __aexit__(self, *args): pass

        class MockClient:
            def stream(self, *args, **kwargs): return MockStreamCtx()
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass

        with patch("httpx.AsyncClient", return_value=MockClient()):
            tokens = []
            async for token in provider.generate_stream(messages=messages):
                tokens.append(token)

        assert "Should not appear" not in tokens
        assert "First" in tokens

    @pytest.mark.asyncio
    async def test_stream_connect_error_raises_provider_error(self):
        """ConnectError during streaming must raise LLMProviderError."""
        import httpx
        provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2:3b")
        messages = [LLMMessage(role="user", content="Hi")]

        class FailingClient:
            def stream(self, *args, **kwargs):
                raise httpx.ConnectError("Connection refused")
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass

        with patch("httpx.AsyncClient", return_value=FailingClient()):
            with pytest.raises(LLMProviderError):
                async for _ in provider.generate_stream(messages=messages):
                    pass

    @pytest.mark.asyncio
    async def test_stream_timeout_raises_timeout_error(self):
        """TimeoutException during streaming must raise LLMTimeoutError."""
        import httpx
        provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2:3b")
        messages = [LLMMessage(role="user", content="Hi")]

        class TimeoutClient:
            def stream(self, *args, **kwargs):
                raise httpx.TimeoutException("Timeout")
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass

        with patch("httpx.AsyncClient", return_value=TimeoutClient()):
            with pytest.raises(LLMTimeoutError):
                async for _ in provider.generate_stream(messages=messages):
                    pass


class TestOllamaBaselineNonStreaming:
    @pytest.mark.asyncio
    async def test_generate_still_works_non_streaming(self):
        """Non-streaming generate() must still work after streaming implementation."""
        provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.2:3b")
        messages = [LLMMessage(role="user", content="Hello")]

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "Hello from Ollama"},
            "prompt_eval_count": 10,
            "eval_count": 5,
            "total_duration": 1000,
            "done": True
        }

        class MockClient:
            async def post(self, *args, **kwargs): return mock_response
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass

        with patch("httpx.AsyncClient", return_value=MockClient()):
            result = await provider.generate(messages=messages)

        assert result.content == "Hello from Ollama"
        assert result.model_provider == "ollama"


class TestLLMBaseStreamingFallback:
    @pytest.mark.asyncio
    async def test_gemini_provider_uses_base_fallback(self):
        """GeminiProvider inherits base generate_stream which yields full content once."""
        from backend.app.llm.gemini import GeminiProvider
        from backend.app.llm.base import LLMResponse

        provider = GeminiProvider(api_key="fake-key")
        messages = [LLMMessage(role="user", content="Hello")]

        mock_response = LLMResponse(
            content="Full Gemini response here.",
            model_provider="gemini",
            model_name="gemini-3.6-flash",
            latency_ms=300
        )

        with patch.object(provider, "generate", new=AsyncMock(return_value=mock_response)):
            tokens = []
            async for token in provider.generate_stream(messages=messages):
                tokens.append(token)

        # Base fallback yields entire content as single chunk
        assert len(tokens) == 1
        assert tokens[0] == "Full Gemini response here."
