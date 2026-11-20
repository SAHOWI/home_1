"""Offline mock LLM provider for local testing and zero-API-key runs."""

from __future__ import annotations

import re
from collections.abc import Sequence

from home_1.llm.base import LLMResponse, Message, Role, ToolCall, ToolDefinition


class MockLLMProvider:
    """Deterministic offline LLM adapter.

    Supports basic natural-language triggers for planning tools so the full
    orchestrator + tool loop can be exercised without network access or API keys.
    """

    def __init__(self, model: str = "mock-echo-v1") -> None:
        self._model = model
        self._call_counter = 0

    @property
    def name(self) -> str:
        return "mock"

    @property
    def model(self) -> str:
        return self._model

    def _next_call_id(self) -> str:
        self._call_counter += 1
        return f"mock_call_{self._call_counter}"

    def generate(
        self,
        messages: Sequence[Message],
        *,
        system_prompt: str = "",
        tools: Sequence[ToolDefinition] = (),
        temperature: float = 0.4,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        del system_prompt, temperature, max_tokens
        if not messages:
            return LLMResponse(
                content="Hello! I am home_1 running in offline mock mode.",
                provider=self.name,
                model=self.model,
            )

        last = messages[-1]
        if last.role == Role.TOOL:
            return LLMResponse(
                content=f"[mock] Tool '{last.tool_name}' result:\n{last.content}",
                provider=self.name,
                model=self.model,
            )

        text = last.content.strip()
        tool_names = {tool.name for tool in tools}

        if "add_task" in tool_names:
            match = re.match(r"^(?:add|create)\s+task[:\s]+(.+)$", text, flags=re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                return LLMResponse(
                    tool_calls=(
                        ToolCall(
                            id=self._next_call_id(),
                            name="add_task",
                            arguments={"title": title},
                        ),
                    ),
                    provider=self.name,
                    model=self.model,
                )

        if "list_tasks" in tool_names and re.match(
            r"^(?:list|show)\s+tasks\b", text, flags=re.IGNORECASE
        ):
            return LLMResponse(
                tool_calls=(
                    ToolCall(
                        id=self._next_call_id(),
                        name="list_tasks",
                        arguments={"include_completed": False},
                    ),
                ),
                provider=self.name,
                model=self.model,
            )

        if "complete_task" in tool_names:
            match = re.match(
                r"^(?:complete|finish|done)\s+task\s+(\d+)$", text, flags=re.IGNORECASE
            )
            if match:
                return LLMResponse(
                    tool_calls=(
                        ToolCall(
                            id=self._next_call_id(),
                            name="complete_task",
                            arguments={"task_id": int(match.group(1))},
                        ),
                    ),
                    provider=self.name,
                    model=self.model,
                )

        return LLMResponse(
            content=(
                f"[mock] You said: {text!r}. "
                "Try 'add task Buy Pi CM4 heatsink', 'list tasks', or switch to "
                "--provider gemini / --provider claude."
            ),
            provider=self.name,
            model=self.model,
        )
