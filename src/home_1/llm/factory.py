"""Factory for instantiating configured LLM providers."""

from __future__ import annotations

from home_1.config import Settings
from home_1.llm.base import LLMError, LLMProvider
from home_1.llm.claude import ClaudeProvider
from home_1.llm.gemini import GeminiProvider
from home_1.llm.mock import MockLLMProvider


def create_llm_provider(settings: Settings) -> LLMProvider:
    """Create an LLM provider instance from validated Settings."""
    provider = settings.llm.provider
    model = settings.llm.resolved_model

    if provider == "mock":
        return MockLLMProvider(model=model)
    if provider == "gemini":
        return GeminiProvider(api_key=settings.gemini_api_key or "", model=model)
    if provider == "claude":
        return ClaudeProvider(api_key=settings.anthropic_api_key or "", model=model)

    raise LLMError(f"Unsupported LLM provider: {provider!r}")
