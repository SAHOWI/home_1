"""Anthropic Claude LLM provider adapter using the official anthropic SDK."""

from __future__ import annotations

import inspect
from collections.abc import Sequence
from typing import Any

from home_1.llm.base import LLMError, LLMResponse, Message, Role, ToolCall, ToolDefinition


class ClaudeProvider:
    """Adapter for Anthropic Claude models via `anthropic`."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        if not api_key:
            raise LLMError(
                "ANTHROPIC_API_KEY is not set. Add it to your .env file or environment variables."
            )
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise LLMError("anthropic is not installed. Run `uv sync` first.") from exc

        self._client = Anthropic(api_key=api_key)
        self._model = model
        self._supports_temperature = (
            "temperature" in inspect.signature(self._client.messages.create).parameters
        )

    @property
    def name(self) -> str:
        return "claude"

    @property
    def model(self) -> str:
        return self._model

    def generate(
        self,
        messages: Sequence[Message],
        *,
        system_prompt: str = "",
        tools: Sequence[ToolDefinition] = (),
        temperature: float = 0.4,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": _to_claude_messages(messages),
        }
        if self._supports_temperature:
            kwargs["temperature"] = temperature
        if system_prompt:
            kwargs["system"] = system_prompt
        if tools:
            kwargs["tools"] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.parameters,
                }
                for tool in tools
            ]

        try:
            response = self._client.messages.create(**kwargs)
        except Exception as exc:
            raise LLMError(f"Claude request failed: {exc}") from exc

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []

        for block in response.content:
            block_type = getattr(block, "type", None)
            if block_type == "text" and getattr(block, "text", None):
                text_parts.append(block.text)
            elif block_type == "tool_use":
                raw_input = getattr(block, "input", None) or {}
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=dict(raw_input),
                    )
                )

        return LLMResponse(
            content="\n".join(text_parts).strip(),
            tool_calls=tuple(tool_calls),
            provider=self.name,
            model=self.model,
        )


def _to_claude_messages(messages: Sequence[Message]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    pending_tool_results: list[dict[str, Any]] = []

    def flush_tool_results() -> None:
        if pending_tool_results:
            payload.append({"role": "user", "content": list(pending_tool_results)})
            pending_tool_results.clear()

    for msg in messages:
        if msg.role == Role.TOOL:
            pending_tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": msg.tool_call_id or "unknown_call_id",
                    "content": msg.content,
                }
            )
            continue

        flush_tool_results()

        if msg.role == Role.USER:
            payload.append({"role": "user", "content": msg.content})
        elif msg.role == Role.ASSISTANT:
            blocks: list[dict[str, Any]] = []
            if msg.content:
                blocks.append({"type": "text", "text": msg.content})
            for tc in msg.tool_calls:
                blocks.append(
                    {
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments,
                    }
                )
            if blocks:
                payload.append({"role": "assistant", "content": blocks})

    flush_tool_results()
    return payload
