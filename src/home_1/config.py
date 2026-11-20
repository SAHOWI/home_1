"""Configuration loading for home_1.

Combines YAML defaults (config/default.yaml) with environment variables and an optional .env file.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

ProviderName = Literal["mock", "gemini", "claude"]
EmbodimentMode = Literal["null", "console"]

DEFAULT_CONFIG_PATH = Path("config/default.yaml")


class AssistantConfig(BaseModel):
    """Core assistant persona and execution settings."""

    name: str = "home_1"
    system_prompt: str = (
        "You are home_1, a helpful, concise personal assistant. "
        "You help the user plan tasks, organize daily activities, and answer questions clearly."
    )
    max_tool_rounds: int = Field(default=5, ge=1, le=20)


class LLMConfig(BaseModel):
    """LLM backend configuration."""

    provider: ProviderName = "mock"
    model: str | None = None
    temperature: float = Field(default=0.4, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1)
    models: dict[str, str] = Field(
        default_factory=lambda: {
            "gemini": "gemini-2.5-flash",
            "claude": "claude-sonnet-4-6",
            "mock": "mock-echo-v1",
        }
    )

    @property
    def resolved_model(self) -> str:
        """Return the explicit model override or the configured default for the active provider."""
        if self.model:
            return self.model
        return self.models.get(self.provider, "mock-echo-v1")


class EmbodimentConfig(BaseModel):
    """Embodiment adapter settings."""

    mode: EmbodimentMode = "console"


class StorageConfig(BaseModel):
    """Local persistence paths."""

    tasks_path: Path = Path("data/tasks.json")


class Settings(BaseModel):
    """Top-level validated settings for home_1."""

    assistant: AssistantConfig = Field(default_factory=AssistantConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embodiment: EmbodimentConfig = Field(default_factory=EmbodimentConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    gemini_api_key: str | None = Field(default=None, repr=False)
    anthropic_api_key: str | None = Field(default=None, repr=False)


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(f"Expected YAML mapping in {path}, got {type(raw).__name__}")
    return raw


def load_settings(
    config_path: Path | None = None,
    *,
    load_env_file: bool = True,
    overrides: dict[str, Any] | None = None,
) -> Settings:
    """Load settings from YAML, environment variables, and optional CLI overrides."""
    if load_env_file:
        load_dotenv(override=False)

    env_config = os.getenv("HOME_1_CONFIG_FILE")
    resolved_path = config_path or (Path(env_config) if env_config else DEFAULT_CONFIG_PATH)
    data = _read_yaml(resolved_path)

    llm_section = dict(data.get("llm") or {})
    if env_provider := os.getenv("HOME_1_LLM_PROVIDER"):
        llm_section["provider"] = env_provider.strip().lower()
    if env_model := os.getenv("HOME_1_MODEL"):
        llm_section["model"] = env_model.strip()
    data["llm"] = llm_section

    emb_section = dict(data.get("embodiment") or {})
    if env_emb := os.getenv("HOME_1_EMBODIMENT"):
        emb_section["mode"] = env_emb.strip().lower()
    data["embodiment"] = emb_section

    storage_section = dict(data.get("storage") or {})
    if env_tasks := os.getenv("HOME_1_TASKS_PATH"):
        storage_section["tasks_path"] = env_tasks.strip()
    data["storage"] = storage_section

    if overrides:
        if overrides.get("provider"):
            data["llm"]["provider"] = overrides["provider"]
        if overrides.get("model"):
            data["llm"]["model"] = overrides["model"]
        if overrides.get("embodiment"):
            data["embodiment"]["mode"] = overrides["embodiment"]
        if overrides.get("tasks_path"):
            data["storage"]["tasks_path"] = overrides["tasks_path"]

    data["gemini_api_key"] = os.getenv("GEMINI_API_KEY") or None
    data["anthropic_api_key"] = os.getenv("ANTHROPIC_API_KEY") or None

    return Settings.model_validate(data)
