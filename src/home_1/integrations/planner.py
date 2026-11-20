"""Local personal planning store and assistant tools (add, list, complete tasks)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from home_1.integrations.base import FunctionTool, ToolRegistry
from home_1.llm.base import ToolDefinition


class Task(BaseModel):
    """A personal planning item."""

    id: int
    title: str
    due: str | None = None
    notes: str | None = None
    completed: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: str | None = None


class TaskStore:
    """JSON-backed local task store (kept in gitignored data/ by default)."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def _load(self) -> list[Task]:
        if not self._path.exists():
            return []
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return [Task.model_validate(item) for item in raw]

    def _save(self, tasks: list[Task]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = [task.model_dump() for task in tasks]
        self._path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def add(self, title: str, *, due: str | None = None, notes: str | None = None) -> Task:
        clean_title = title.strip()
        if not clean_title:
            raise ValueError("Task title cannot be empty.")
        tasks = self._load()
        next_id = max((task.id for task in tasks), default=0) + 1
        task = Task(
            id=next_id,
            title=clean_title,
            due=due.strip() if due else None,
            notes=notes.strip() if notes else None,
        )
        tasks.append(task)
        self._save(tasks)
        return task

    def list(self, *, include_completed: bool = False) -> list[Task]:
        tasks = self._load()
        if include_completed:
            return tasks
        return [task for task in tasks if not task.completed]

    def complete(self, task_id: int) -> Task | None:
        tasks = self._load()
        for idx, task in enumerate(tasks):
            if task.id == task_id:
                updated = task.model_copy(
                    update={
                        "completed": True,
                        "completed_at": datetime.now(UTC).isoformat(),
                    }
                )
                tasks[idx] = updated
                self._save(tasks)
                return updated
        return None


def format_tasks(tasks: list[Task]) -> str:
    """Render a readable summary of tasks."""
    if not tasks:
        return "No tasks found."
    lines: list[str] = []
    for task in tasks:
        box = "x" if task.completed else " "
        due_part = f" (due: {task.due})" if task.due else ""
        notes_part = f" — {task.notes}" if task.notes else ""
        lines.append(f"[{box}] #{task.id}: {task.title}{due_part}{notes_part}")
    return "\n".join(lines)


def register_planner_tools(registry: ToolRegistry, store: TaskStore) -> None:
    """Register personal planning tools on the given ToolRegistry."""

    def _add_task(args: dict[str, Any]) -> str:
        task = store.add(
            title=str(args.get("title", "")),
            due=args.get("due"),
            notes=args.get("notes"),
        )
        return f"Added task #{task.id}: {task.title}"

    def _list_tasks(args: dict[str, Any]) -> str:
        include_completed = bool(args.get("include_completed", False))
        return format_tasks(store.list(include_completed=include_completed))

    def _complete_task(args: dict[str, Any]) -> str:
        task_id = int(args["task_id"])
        updated = store.complete(task_id)
        if updated is None:
            return f"Task #{task_id} not found."
        return f"Completed task #{updated.id}: {updated.title}"

    registry.register(
        FunctionTool(
            definition=ToolDefinition(
                name="add_task",
                description="Add a new personal planning task or to-do item.",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Short description of the task.",
                        },
                        "due": {
                            "type": "string",
                            "description": (
                                "Optional due date or time (e.g. '2026-11-21' or 'tomorrow')."
                            ),
                        },
                        "notes": {
                            "type": "string",
                            "description": "Optional extra details or context.",
                        },
                    },
                    "required": ["title"],
                },
            ),
            handler=_add_task,
        )
    )

    registry.register(
        FunctionTool(
            definition=ToolDefinition(
                name="list_tasks",
                description="List current personal planning tasks.",
                parameters={
                    "type": "object",
                    "properties": {
                        "include_completed": {
                            "type": "boolean",
                            "description": "Include already completed tasks.",
                        }
                    },
                },
            ),
            handler=_list_tasks,
        )
    )

    registry.register(
        FunctionTool(
            definition=ToolDefinition(
                name="complete_task",
                description=(
                    "Mark an existing personal planning task as completed by its numeric ID."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "integer",
                            "description": "Numeric ID of the task to mark complete.",
                        }
                    },
                    "required": ["task_id"],
                },
            ),
            handler=_complete_task,
        )
    )
