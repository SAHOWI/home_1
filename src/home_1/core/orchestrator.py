"""Central assistant orchestrator connecting LLM, tools, memory, and embodiment."""

from __future__ import annotations

from home_1.config import Settings
from home_1.embodiment.base import AssistantState, Embodiment, NullEmbodiment
from home_1.integrations.base import ToolRegistry
from home_1.llm.base import LLMProvider, Message, Role


class AssistantOrchestrator:
    """Manages conversation turns, tool dispatch loops, and embodiment state transitions."""

    def __init__(
        self,
        *,
        llm: LLMProvider,
        settings: Settings,
        tools: ToolRegistry | None = None,
        embodiment: Embodiment | None = None,
    ) -> None:
        self._llm = llm
        self._settings = settings
        self._tools = tools or ToolRegistry()
        self._embodiment: Embodiment = embodiment or NullEmbodiment()
        self._history: list[Message] = []
        self._embodiment.set_state(AssistantState.IDLE)

    @property
    def history(self) -> tuple[Message, ...]:
        """Immutable view of the current conversation history."""
        return tuple(self._history)

    def clear_history(self) -> None:
        """Reset conversation history while keeping persisted data intact."""
        self._history.clear()

    def handle_user_input(self, text: str) -> str:
        """Process one user message through the LLM and any requested tool calls."""
        clean_input = text.strip()
        if not clean_input:
            return ""

        self._history.append(Message(role=Role.USER, content=clean_input))
        self._embodiment.set_state(AssistantState.THINKING)

        try:
            tool_defs = self._tools.definitions()
            for _ in range(self._settings.assistant.max_tool_rounds):
                response = self._llm.generate(
                    self._history,
                    system_prompt=self._settings.assistant.system_prompt,
                    tools=tool_defs,
                    temperature=self._settings.llm.temperature,
                    max_tokens=self._settings.llm.max_tokens,
                )

                self._history.append(
                    Message(
                        role=Role.ASSISTANT,
                        content=response.content,
                        tool_calls=response.tool_calls,
                    )
                )

                if not response.tool_calls:
                    self._embodiment.set_state(AssistantState.SPEAKING)
                    reply = response.content or "(no response)"
                    self._embodiment.set_state(AssistantState.IDLE)
                    return reply

                for tool_call in response.tool_calls:
                    result = self._tools.execute(tool_call.name, tool_call.arguments)
                    self._history.append(
                        Message(
                            role=Role.TOOL,
                            content=result,
                            tool_call_id=tool_call.id,
                            tool_name=tool_call.name,
                        )
                    )

            fallback = "Reached maximum tool-calling rounds before producing a final reply."
            self._embodiment.set_state(AssistantState.ERROR)
            self._embodiment.set_state(AssistantState.IDLE)
            return fallback
        except Exception:
            self._embodiment.set_state(AssistantState.ERROR)
            self._embodiment.set_state(AssistantState.IDLE)
            raise
