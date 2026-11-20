"""Embodiment adapters bridging software-only runs to future Reachy Mini-style hardware."""

from home_1.embodiment.base import (
    AssistantState,
    ConsoleEmbodiment,
    Embodiment,
    NullEmbodiment,
    create_embodiment,
)

__all__ = [
    "AssistantState",
    "ConsoleEmbodiment",
    "Embodiment",
    "NullEmbodiment",
    "create_embodiment",
]
