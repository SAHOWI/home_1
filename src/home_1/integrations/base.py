"""Pluggable tool registry abstraction (ready for planning tools, Home Assistant, and MCP)."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from home_1.llm.base import ToolDefinition


class Tool(Protocol):
    """A callable integration tool exposed to the LLM."""

    @property
    def definition(self) -> ToolDefinition:
        """Schema describing this tool to LLM providers."""

    def execute(self, arguments: dict[str, Any]) -> str:
        """Execute the tool with JSON-decoded arguments and return a string result."""


@dataclass(frozen=True)
class FunctionTool:
    """Wrap a plain Python callable as a registered assistant tool."""

    definition: ToolDefinition
    handler: Callable[[dict[str, Any]], Any]

    def execute(self, arguments: dict[str, Any]) -> str:
        result = self.handler(arguments)
        if isinstance(result, str):
            return result
        return json.dumps(result, ensure_ascii=False, indent=2)


class ToolRegistry:
    """Central registry for assistant tools and future MCP/home-automation adapters."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        name = tool.definition.name
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name!r}")
        self._tools[name] = tool

    def definitions(self) -> tuple[ToolDefinition, ...]:
        return tuple(tool.definition for tool in self._tools.values())

    def names(self) -> tuple[str, ...]:
        return tuple(self._tools.keys())

    def execute(self, name: str, arguments: dict[str, Any]) -> str:
        tool = self._tools.get(name)
        if tool is None:
            return f"Error: unknown tool '{name}'."
        try:
            return tool.execute(arguments)
        except Exception as exc:
            return f"Error executing tool '{name}': {exc}"
