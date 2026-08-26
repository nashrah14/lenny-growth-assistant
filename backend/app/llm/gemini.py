"""
Google Gemini LLM Provider Implementation
Uses the official Google GenAI Python SDK (google-genai).
"""
import time
import asyncio
from typing import List, Optional
from backend.app.llm.base import LLMProvider, LLMMessage, LLMResponse
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import LLMProviderError, LLMTimeoutError

class GeminiProvider(LLMProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        fallback_api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.fallback_api_key = fallback_api_key or settings.GEMINI_API_KEY_FALLBACK
        self.model_name = model or settings.GEMINI_MODEL
        self._clients = {}

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return self.model_name

    def _get_client_for_key(self, key: Optional[str]):
        if not key:
            raise LLMProviderError(
                message="Google Gemini API key is not configured. Please set GEMINI_API_KEY in .env.",
                error_code="GEMINI_KEY_MISSING"
            )
        if key not in self._clients:
            try:
                from google import genai
                self._clients[key] = genai.Client(api_key=key)
            except Exception as e:
                raise LLMProviderError(
                    message=f"Failed to initialize Google GenAI Client: {e}",
                    error_code="GEMINI_INIT_FAILED"
                )
        return self._clients[key]

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

        # Build contents from messages
        contents = []
        sys_prompt = system_instruction or ""

        for msg in messages:
            if msg.role == "system":
                if sys_prompt:
                    sys_prompt += "\n\n" + msg.content
                else:
                    sys_prompt = msg.content
            elif msg.role in ("user", "assistant"):
                # Role in genai: 'user' or 'model'
                genai_role = "user" if msg.role == "user" else "model"
                contents.append({"role": genai_role, "parts": [{"text": msg.content}]})

        if not contents:
            contents = [{"role": "user", "parts": [{"text": "Hello"}]}]

        def _sync_call(client_instance):
            from google.genai import types
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                system_instruction=sys_prompt if sys_prompt else None
            )
            return client_instance.models.generate_content(
                model=target_model,
                contents=contents,
                config=config
            )

        keys_to_try = []
        if self.api_key:
            keys_to_try.append(("primary", self.api_key))
        if self.fallback_api_key and self.fallback_api_key != self.api_key:
            keys_to_try.append(("fallback", self.fallback_api_key))

        if not keys_to_try:
            raise LLMProviderError(
                message="No Gemini API keys configured.",
                error_code="GEMINI_KEY_MISSING"
            )

        last_error = None
        for key_type, key_val in keys_to_try:
            try:
                client = self._get_client_for_key(key_val)
                response = await asyncio.wait_for(
                    asyncio.to_thread(_sync_call, client),
                    timeout=60.0
                )
                latency_ms = int((time.perf_counter() - start_time) * 1000)

                content_text = ""
                if response and response.text:
                    content_text = response.text

                input_tokens = None
                output_tokens = None
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    input_tokens = getattr(response.usage_metadata, "prompt_token_count", None)
                    output_tokens = getattr(response.usage_metadata, "candidates_token_count", None)

                logger.info(
                    f"Gemini generation completed using {key_type} key in {latency_ms}ms",
                    extra={
                        "operation": "llm_generate",
                        "provider": "gemini",
                        "model": target_model,
                        "key_type": key_type,
                        "latency_ms": latency_ms
                    }
                )

                return LLMResponse(
                    content=content_text,
                    model_provider="gemini",
                    model_name=target_model,
                    latency_ms=latency_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    metadata={"finish_reason": "completed", "key_type": key_type}
                )
            except asyncio.TimeoutError:
                last_error = LLMTimeoutError(
                    message=f"Gemini API request timed out after 60 seconds (model: {target_model}).",
                    details={"provider": "gemini", "model": target_model, "key_type": key_type}
                )
                logger.warning(f"Gemini {key_type} key timed out. Trying next key if available.")
            except Exception as e:
                last_error = e
                logger.warning(f"Gemini {key_type} key encountered error: {e}. Trying fallback key if available.")

        logger.error(f"All configured Gemini API keys failed: {last_error}", extra={"operation": "llm_generate", "provider": "gemini"})
        raise LLMProviderError(
            message=f"Gemini generation failed on all available keys: {str(last_error)}",
            details={"provider": "gemini", "model": target_model, "original_error": str(last_error)}
        )

    async def health(self) -> bool:
        keys_to_test = []
        if self.api_key:
            keys_to_test.append(self.api_key)
        if self.fallback_api_key and self.fallback_api_key != self.api_key:
            keys_to_test.append(self.fallback_api_key)

        if not keys_to_test:
            return False

        for k in keys_to_test:
            try:
                client = self._get_client_for_key(k)
                def _test(cl):
                    return cl.models.get(model=self.model_name)
                await asyncio.wait_for(asyncio.to_thread(_test, client), timeout=10.0)
                return True
            except Exception:
                continue
        return False
