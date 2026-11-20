"""Tests for configuration loading and environment overrides."""

from pathlib import Path

from home_1.config import load_settings


def test_load_default_yaml(monkeypatch) -> None:
    monkeypatch.delenv("HOME_1_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("HOME_1_MODEL", raising=False)
    monkeypatch.delenv("HOME_1_EMBODIMENT", raising=False)
    monkeypatch.delenv("HOME_1_TASKS_PATH", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    settings = load_settings(Path("config/default.yaml"), load_env_file=False)
    assert settings.assistant.name == "home_1"
    assert settings.llm.provider == "mock"
    assert settings.llm.resolved_model == "mock-echo-v1"
    assert settings.embodiment.mode == "console"


def test_env_and_cli_overrides(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME_1_LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("HOME_1_EMBODIMENT", "null")

    settings = load_settings(
        tmp_path / "missing.yaml",
        load_env_file=False,
        overrides={"provider": "claude", "model": "claude-custom"},
    )
    assert settings.llm.provider == "claude"
    assert settings.llm.resolved_model == "claude-custom"
    assert settings.embodiment.mode == "null"
    assert settings.gemini_api_key == "test-key"
