"""Interactive CLI entry point for Phase 1 software-only execution."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from home_1 import __version__
from home_1.config import Settings, load_settings
from home_1.core import AssistantOrchestrator
from home_1.embodiment import create_embodiment
from home_1.integrations import TaskStore, ToolRegistry, format_tasks, register_planner_tools
from home_1.llm import LLMError, create_llm_provider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="home_1",
        description="home_1 personal assistant (Phase 1 CLI)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to YAML config file (default: config/default.yaml).",
    )
    parser.add_argument(
        "--provider",
        choices=("mock", "gemini", "claude"),
        default=None,
        help="LLM backend to use (overrides config/env).",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model identifier override.",
    )
    parser.add_argument(
        "--embodiment",
        choices=("null", "console"),
        default=None,
        help="Embodiment output mode (overrides config/env).",
    )
    parser.add_argument(
        "--once",
        default=None,
        help="Send a single prompt non-interactively and exit.",
    )
    return parser


def build_runtime(settings: Settings) -> tuple[AssistantOrchestrator, TaskStore]:
    llm = create_llm_provider(settings)
    embodiment = create_embodiment(settings.embodiment.mode)
    store = TaskStore(settings.storage.tasks_path)
    registry = ToolRegistry()
    register_planner_tools(registry, store)
    orchestrator = AssistantOrchestrator(
        llm=llm,
        settings=settings,
        tools=registry,
        embodiment=embodiment,
    )
    return orchestrator, store


def _handle_slash_command(
    raw: str,
    orchestrator: AssistantOrchestrator,
    store: TaskStore,
    settings: Settings,
) -> bool:
    """Handle built-in CLI slash commands. Returns True if the REPL should exit."""
    cmd = raw.strip().lower()
    if cmd in {"/quit", "/exit"}:
        print("Goodbye!")
        return True
    if cmd == "/clear":
        orchestrator.clear_history()
        print("Conversation history cleared.")
        return False
    if cmd == "/tasks":
        print(format_tasks(store.list(include_completed=False)))
        return False
    if cmd == "/tasks-all":
        print(format_tasks(store.list(include_completed=True)))
        return False
    if cmd == "/info":
        print(
            f"provider={settings.llm.provider} "
            f"model={settings.llm.resolved_model} "
            f"embodiment={settings.embodiment.mode} "
            f"tasks={store.path}"
        )
        return False
    if cmd == "/help":
        print("Commands: /tasks, /tasks-all, /clear, /info, /help, /quit")
        return False

    print(f"Unknown command: {raw!r}. Type /help for available commands.")
    return False


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    overrides = {
        "provider": args.provider,
        "model": args.model,
        "embodiment": args.embodiment,
    }

    try:
        settings = load_settings(config_path=args.config, overrides=overrides)
        orchestrator, store = build_runtime(settings)
    except (LLMError, ValueError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    if args.once is not None:
        try:
            reply = orchestrator.handle_user_input(args.once)
        except LLMError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(reply)
        return 0

    print(
        f"home_1 v{__version__} | provider={settings.llm.provider} "
        f"({settings.llm.resolved_model}) | type /help or /quit"
    )

    while True:
        try:
            user_text = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return 0

        if not user_text:
            continue

        if user_text.startswith("/"):
            if _handle_slash_command(user_text, orchestrator, store, settings):
                return 0
            continue

        try:
            reply = orchestrator.handle_user_input(user_text)
        except LLMError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            continue

        print(f"\n{settings.assistant.name}> {reply}")
