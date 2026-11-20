"""Tests for LLM provider factory, SDK compatibility, and validation."""

from types import SimpleNamespace

import pytest

from home_1.config import LLMConfig, Settings
from home_1.llm import (
    ClaudeProvider,
    LLMError,
    Message,
    MockLLMProvider,
    Role,
    create_llm_provider,
)


def test_factory_creates_mock_provider() -> None:
    provider = create_llm_provider(Settings(llm=LLMConfig(provider="mock")))
    assert isinstance(provider, MockLLMProvider)
    assert provider.name == "mock"


def test_factory_requires_gemini_api_key() -> None:
    with pytest.raises(LLMError, match="GEMINI_API_KEY"):
        create_llm_provider(Settings(llm=LLMConfig(provider="gemini"), gemini_api_key=None))


def test_factory_requires_anthropic_api_key() -> None:
    with pytest.raises(LLMError, match="ANTHROPIC_API_KEY"):
        create_llm_provider(Settings(llm=LLMConfig(provider="claude"), anthropic_api_key=None))


def test_claude_provider_respects_installed_sdk_signature(monkeypatch) -> None:
    provider = ClaudeProvider(api_key="test-key", model="claude-sonnet-4-6")
    captured: dict[str, object] = {}

    def fake_create(**kwargs: object) -> SimpleNamespace:
        captured.update(kwargs)
        return SimpleNamespace(content=[SimpleNamespace(type="text", text="Hello from Claude!")])

    monkeypatch.setattr(provider._client.messages, "create", fake_create)
    response = provider.generate(
        [Message(role=Role.USER, content="hello!")],
        system_prompt="Be concise.",
        temperature=0.4,
        max_tokens=256,
    )

    assert response.content == "Hello from Claude!"
    assert captured["model"] == "claude-sonnet-4-6"
    assert captured["max_tokens"] == 256
    assert "temperature" not in captured
