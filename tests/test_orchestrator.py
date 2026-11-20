"""Tests for AssistantOrchestrator lifecycle, tool dispatch, and embodiment states."""

from pathlib import Path

from home_1.config import Settings
from home_1.core import AssistantOrchestrator
from home_1.embodiment import AssistantState
from home_1.integrations import TaskStore, ToolRegistry, register_planner_tools
from home_1.llm import MockLLMProvider


class RecordingEmbodiment:
    """Test double that records every state transition."""

    def __init__(self) -> None:
        self.states: list[AssistantState] = []

    def set_state(self, state: AssistantState) -> None:
        self.states.append(state)

    def look_at(self, azimuth_deg: float, elevation_deg: float = 0.0) -> None:
        del azimuth_deg, elevation_deg

    def express(self, cue: str) -> None:
        del cue


def test_orchestrator_plain_reply_and_state_transitions() -> None:
    embodiment = RecordingEmbodiment()
    orchestrator = AssistantOrchestrator(
        llm=MockLLMProvider(),
        settings=Settings(),
        embodiment=embodiment,
    )

    reply = orchestrator.handle_user_input("Hello home_1")
    assert "Hello home_1" in reply
    assert embodiment.states == [
        AssistantState.IDLE,
        AssistantState.THINKING,
        AssistantState.SPEAKING,
        AssistantState.IDLE,
    ]


def test_orchestrator_executes_planner_tool_loop(tmp_path: Path) -> None:
    store = TaskStore(tmp_path / "tasks.json")
    registry = ToolRegistry()
    register_planner_tools(registry, store)

    orchestrator = AssistantOrchestrator(
        llm=MockLLMProvider(),
        settings=Settings(),
        tools=registry,
    )

    add_reply = orchestrator.handle_user_input("add task Wire up Gemini API")
    assert "Added task #1: Wire up Gemini API" in add_reply

    list_reply = orchestrator.handle_user_input("list tasks")
    assert "Wire up Gemini API" in list_reply

    done_reply = orchestrator.handle_user_input("complete task 1")
    assert "Completed task #1" in done_reply
    assert store.list(include_completed=False) == []
