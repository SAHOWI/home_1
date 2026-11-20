"""Tests for local TaskStore and planner tool registration."""

from pathlib import Path

from home_1.integrations import TaskStore, ToolRegistry, register_planner_tools


def test_task_store_crud(tmp_path: Path) -> None:
    store = TaskStore(tmp_path / "tasks.json")
    assert store.list() == []

    t1 = store.add("Order ReSpeaker Lite USB", due="2026-11-22", notes="For Pi CM4")
    t2 = store.add("Set up Pi CM4 OS")
    assert t1.id == 1
    assert t2.id == 2
    assert len(store.list()) == 2

    completed = store.complete(1)
    assert completed is not None
    assert completed.completed is True
    assert [t.id for t in store.list(include_completed=False)] == [2]
    assert [t.id for t in store.list(include_completed=True)] == [1, 2]


def test_planner_tools_via_registry(tmp_path: Path) -> None:
    store = TaskStore(tmp_path / "tasks.json")
    registry = ToolRegistry()
    register_planner_tools(registry, store)

    assert set(registry.names()) == {"add_task", "list_tasks", "complete_task"}

    add_msg = registry.execute("add_task", {"title": "Plan sprint", "due": "Monday"})
    assert "#1" in add_msg

    list_msg = registry.execute("list_tasks", {})
    assert "Plan sprint" in list_msg

    done_msg = registry.execute("complete_task", {"task_id": 1})
    assert "Completed task #1" in done_msg
    assert registry.execute("list_tasks", {}) == "No tasks found."
