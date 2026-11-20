"""Provider-agnostic LLM data types and protocol."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol


class Role(StrEnum):
    """Conversation turn role."""

    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(frozen=True)
class ToolDefinition:
    """JSON-Schema tool definition exposed to any LLM provider."""

    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    """A structured tool invocation requested by the LLM."""

    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Message:
    """A single turn in a conversation history."""

    role: Role
    content: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    tool_call_id: str | None = None
    tool_name: str | None = None


@dataclass(frozen=True)
class LLMResponse:
    """Normalized output returned by an LLM provider."""

    content: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    provider: str = ""
    model: str = ""


class LLMError(RuntimeError):
    """Raised when an LLM backend cannot be initialized or fails to respond."""


class LLMProvider(Protocol):
    """Common interface implemented by Gemini, Claude, local, and mock backends."""

    @property
    def name(self) -> str:
        """Short identifier for this provider (e.g., 'gemini', 'claude', 'mock')."""

    @property
    def model(self) -> str:
        """Active model identifier."""

    def generate(
        self,
        messages: Sequence[Message],
        *,
        system_prompt: str = "",
        tools: Sequence[ToolDefinition] = (),
        temperature: float = 0.4,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Produce the next assistant response (text and/or tool calls)."""
