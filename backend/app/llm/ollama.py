"""
Ollama Remote / Local LLM Provider Implementation
Communicates asynchronously with Ollama's HTTP API (/api/chat).
Supports both batch and true token-by-token streaming via NDJSON.
"""
import json
import time
import httpx
from typing import List, Optional, AsyncGenerator
from backend.app.llm.base import LLMProvider, LLMMessage, LLMResponse
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import LLMProviderError, LLMTimeoutError

class OllamaProvider(LLMProvider):
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[int] = None
    ):
        raw_url = base_url or settings.OLLAMA_BASE_URL
        # Normalize base_url: strip trailing slashes, /api, or /api/chat if present
        clean_url = raw_url.strip().rstrip("/")
        if clean_url.endswith("/api/chat"):
            clean_url = clean_url[:-9].rstrip("/")
        elif clean_url.endswith("/api"):
            clean_url = clean_url[:-4].rstrip("/")

        self.base_url = clean_url
        self.model_name = model or settings.OLLAMA_MODEL
        self.timeout_seconds = timeout_seconds or settings.OLLAMA_TIMEOUT_SECONDS

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def default_model(self) -> str:
        return self.model_name

    def _build_payload(
        self,
        messages: List[LLMMessage],
        temperature: float,
        max_tokens: Optional[int],
        system_instruction: Optional[str],
        model: str,
        stream: bool
    ) -> dict:
        formatted_messages = []
        if system_instruction:
            formatted_messages.append({"role": "system", "content": system_instruction})
        for msg in messages:
            formatted_messages.append({"role": msg.role, "content": msg.content})

        payload: dict = {
            "model": model,
            "messages": formatted_messages,
            "stream": stream,
            "options": {"temperature": temperature}
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        return payload

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None
    ) -> LLMResponse:
        target_model = model or self.model_name
        start_time = time.perf_counter()
        payload = self._build_payload(messages, temperature, max_tokens, system_instruction, target_model, stream=False)
        url = f"{self.base_url}/api/chat"

        try:
            async with httpx.AsyncClient(timeout=float(self.timeout_seconds)) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

            latency_ms = int((time.perf_counter() - start_time) * 1000)
            message_obj = data.get("message", {})
            content = message_obj.get("content", "")

            input_tokens = data.get("prompt_eval_count")
            output_tokens = data.get("eval_count")

            logger.info(
                f"Ollama generation completed in {latency_ms}ms",
                extra={
                    "operation": "llm_generate",
                    "provider": "ollama",
                    "model": target_model,
                    "latency_ms": latency_ms
                }
            )

            return LLMResponse(
                content=content,
                model_provider="ollama",
                model_name=target_model,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                metadata={
                    "total_duration": data.get("total_duration"),
                    "done": data.get("done")
                }
            )
        except httpx.TimeoutException:
            raise LLMTimeoutError(
                message=f"Ollama request to {self.base_url} timed out after {self.timeout_seconds} seconds (model: {target_model}).",
                details={"provider": "ollama", "model": target_model, "base_url": self.base_url}
            )
        except httpx.ConnectError as e:
            raise LLMProviderError(
                message=f"Could not connect to Ollama at {self.base_url}. Please ensure Ollama is running.",
                details={"provider": "ollama", "base_url": self.base_url, "error": str(e)}
            )
        except httpx.HTTPStatusError as e:
            error_details = f"HTTP {e.response.status_code}"
            try:
                err_data = e.response.json()
                if "error" in err_data:
                    error_details = f"{error_details}: {err_data['error']}"
            except Exception:
                if e.response.text:
                    error_details = f"{error_details}: {e.response.text[:200]}"

            logger.error(
                f"Ollama HTTP error ({error_details}) at {url}",
                extra={"operation": "llm_generate", "provider": "ollama", "model": target_model}
            )
            raise LLMProviderError(
                message=f"Ollama generation failed: {error_details}",
                details={"provider": "ollama", "model": target_model, "base_url": self.base_url, "url": url}
            )
        except Exception as e:
            logger.error(f"Ollama generation error: {e}", extra={"operation": "llm_generate", "provider": "ollama"})
            raise LLMProviderError(
                message=f"Ollama generation failed: {str(e)}",
                details={"provider": "ollama", "model": target_model, "original_error": str(e)}
            )

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Real token-by-token streaming from Ollama's /api/chat endpoint.

        Ollama streams NDJSON: each line is a JSON object with a 'message.content'
        field containing the next token, and 'done: true' on the final line.

        Design decisions:
        - Uses httpx async streaming with iter_lines() so we never buffer the
          entire response in memory.
        - Malformed JSON lines are skipped with a warning rather than crashing.
        - Connection failures and timeouts raise LLMProviderError/LLMTimeoutError
          which are handled by the SSE endpoint in the route layer.
        - Empty content tokens (e.g. punctuation-only chunks) are still yielded
          faithfully — filtering is the client's responsibility.
        """
        target_model = model or self.model_name
        payload = self._build_payload(messages, temperature, max_tokens, system_instruction, target_model, stream=True)
        url = f"{self.base_url}/api/chat"

        logger.info(
            f"Ollama streaming started (model: {target_model})",
            extra={"operation": "llm_stream_start", "provider": "ollama", "model": target_model}
        )

        try:
            async with httpx.AsyncClient(timeout=float(self.timeout_seconds)) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            logger.warning(
                                f"Ollama stream: malformed JSON chunk skipped: {line[:80]}",
                                extra={"operation": "llm_stream_chunk_error", "provider": "ollama"}
                            )
                            continue

                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            yield token

                        if chunk.get("done", False):
                            logger.info(
                                f"Ollama stream complete",
                                extra={"operation": "llm_stream_done", "provider": "ollama", "model": target_model}
                            )
                            break

        except httpx.TimeoutException:
            raise LLMTimeoutError(
                message=f"Ollama streaming timed out after {self.timeout_seconds}s (model: {target_model}).",
                details={"provider": "ollama", "model": target_model, "base_url": self.base_url}
            )
        except httpx.ConnectError as e:
            raise LLMProviderError(
                message=f"Could not connect to Ollama at {self.base_url} for streaming.",
                details={"provider": "ollama", "base_url": self.base_url, "error": str(e)}
            )
        except httpx.HTTPStatusError as e:
            error_details = f"HTTP {e.response.status_code}"
            raise LLMProviderError(
                message=f"Ollama streaming failed: {error_details}",
                details={"provider": "ollama", "model": target_model, "url": url}
            )

    async def health(self) -> bool:
        try:
            url = f"{self.base_url}/api/tags"
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                return resp.status_code == 200
        except Exception:
            return False
