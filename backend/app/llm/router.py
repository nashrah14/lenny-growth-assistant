"""
LLM Router & Dynamic Provider Dispatcher
Resolves active model provider with fallback support.
"""
from typing import Dict, Optional, List
from backend.app.llm.base import LLMProvider, LLMMessage, LLMResponse
from backend.app.llm.gemini import GeminiProvider
from backend.app.llm.ollama import OllamaProvider
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import LLMProviderError

class LLMRouter:
    def __init__(self):
        self._providers: Dict[str, LLMProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        self._providers["gemini"] = GeminiProvider()
        self._providers["ollama"] = OllamaProvider()

    def get_provider(self, provider_name: Optional[str] = None) -> LLMProvider:
        name = (provider_name or settings.LLM_PROVIDER).lower()
        if name not in self._providers:
            raise LLMProviderError(
                message=f"Unsupported LLM provider '{name}'. Available: {list(self._providers.keys())}",
                error_code="UNSUPPORTED_PROVIDER"
            )
        return self._providers[name]

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_instruction: Optional[str] = None,
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        allow_fallback: bool = True
    ) -> LLMResponse:
        primary_name = (provider_name or settings.LLM_PROVIDER).lower()
        provider = self.get_provider(primary_name)

        try:
            return await provider.generate(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                system_instruction=system_instruction,
                model=model
            )
        except Exception as primary_error:
            if not allow_fallback:
                raise primary_error

            # Determine fallback provider
            fallback_name = "ollama" if primary_name == "gemini" else "gemini"
            logger.warning(
                f"Primary provider '{primary_name}' failed: {primary_error}. Attempting fallback to '{fallback_name}'",
                extra={"operation": "llm_fallback", "primary": primary_name, "fallback": fallback_name}
            )

            try:
                fallback_provider = self.get_provider(fallback_name)
                return await fallback_provider.generate(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_instruction=system_instruction
                )
            except Exception as fallback_error:
                logger.error(
                    f"Fallback provider '{fallback_name}' also failed: {fallback_error}",
                    extra={"operation": "llm_fallback_failed"}
                )
                # Raise original error with context
                raise primary_error

    async def get_health_status(self) -> Dict[str, bool]:
        status = {}
        for name, provider in self._providers.items():
            try:
                status[name] = await provider.health()
            except Exception:
                status[name] = False
        return status


# Singleton router instance
llm_router = LLMRouter()
