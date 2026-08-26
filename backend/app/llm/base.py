"""
LLM Provider Base Protocol & Data Models
Decouples application logic from specific model vendors.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncGenerator
from pydantic import BaseModel, Field


class LLMMessage(BaseModel):
    role: str = Field(..., description="Message role: 'system', 'user', or 'assistant'")
    content: str = Field(..., description="Message content")


class LLMResponse(BaseModel):
    content: str = Field(..., description="Generated text response")
    model_provider: str = Field(..., description="Provider name e.g. 'gemini', 'ollama'")
    model_name: str = Field(..., description="Model identifier e.g. 'gemini-1.5-flash', 'llama3.2'")
    latency_ms: int = Field(..., description="Inference latency in milliseconds")
    input_tokens: Optional[int] = Field(default=None, description="Prompt token count")
    output_tokens: Optional[int] = Field(default=None, description="Completion token count")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional provider metadata")


class LLMProvider(ABC):
    """Abstract Base Class for LLM Providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider."""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model identifier."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None
    ) -> LLMResponse:
        """Generate a complete text response asynchronously."""
        pass

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream generated text token-by-token as an AsyncGenerator[str, None].

        Default implementation falls back to non-streaming generate() for providers
        that do not implement real streaming.  Override this in providers that
        support native streaming (e.g. Ollama).
        """
        response = await self.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            system_instruction=system_instruction,
            model=model
        )
        # Yield the entire content as one chunk (non-streaming fallback)
        yield response.content

    @abstractmethod
    async def health(self) -> bool:
        """Check provider connectivity and health."""
        pass
