"""Hardware-agnostic physical expression interface.

Software-only runs use NullEmbodiment or ConsoleEmbodiment.
Future hardware adapters (LED rings, Reachy Mini servos) implement the same Embodiment protocol.
"""

from __future__ import annotations

import sys
from enum import StrEnum
from typing import Protocol, TextIO


class AssistantState(StrEnum):
    """Canonical lifecycle states synchronized across audio, core, and embodiment."""

    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    ERROR = "error"


class Embodiment(Protocol):
    """Behavioral interface decoupled from physical hardware."""

    def set_state(self, state: AssistantState) -> None:
        """Transition visual/physical state indicators."""

    def look_at(self, azimuth_deg: float, elevation_deg: float = 0.0) -> None:
        """Orient toward a target direction (e.g., microphone array DoA angle)."""

    def express(self, cue: str) -> None:
        """Trigger a short expressive cue (e.g., 'nod', 'curious', 'happy')."""


class NullEmbodiment:
    """No-op embodiment used for headless execution and unit tests."""

    def __init__(self) -> None:
        self.state: AssistantState = AssistantState.IDLE

    def set_state(self, state: AssistantState) -> None:
        self.state = state

    def look_at(self, azimuth_deg: float, elevation_deg: float = 0.0) -> None:
        del azimuth_deg, elevation_deg

    def express(self, cue: str) -> None:
        del cue


class ConsoleEmbodiment:
    """Prints subtle state and expression updates to a text stream during software-only runs."""

    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = stream or sys.stderr
        self.state: AssistantState = AssistantState.IDLE

    def set_state(self, state: AssistantState) -> None:
        if state != self.state:
            self.state = state
            self._stream.write(f"[embodiment] state -> {state.value}\n")
            self._stream.flush()

    def look_at(self, azimuth_deg: float, elevation_deg: float = 0.0) -> None:
        self._stream.write(
            f"[embodiment] look_at(azimuth={azimuth_deg:.1f} deg, "
            f"elevation={elevation_deg:.1f} deg)\n"
        )
        self._stream.flush()

    def express(self, cue: str) -> None:
        self._stream.write(f"[embodiment] express -> {cue}\n")
        self._stream.flush()


def create_embodiment(mode: str, stream: TextIO | None = None) -> Embodiment:
    """Instantiate an embodiment adapter by configured mode name."""
    if mode == "null":
        return NullEmbodiment()
    if mode == "console":
        return ConsoleEmbodiment(stream=stream)
    raise ValueError(f"Unsupported embodiment mode: {mode!r}")
