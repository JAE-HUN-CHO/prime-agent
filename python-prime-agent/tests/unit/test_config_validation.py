from __future__ import annotations

from pathlib import Path

from prime_agent_py.providers.config_load import load_config


def test_ollama_vllm_lmstudio_configs(configs_dir: Path) -> None:
    ollama = load_config(configs_dir / "ollama.yaml")
    name, profile = ollama.selected()
    assert name == "ollama"
    assert profile.type == "litellm"
    assert profile.model.startswith("ollama/")
    assert profile.api_base == "http://localhost:11434"

    vllm = load_config(configs_dir / "vllm.yaml")
    _, vprofile = vllm.selected()
    assert vprofile.type == "openai_compatible"
    assert vprofile.api_base == "http://localhost:8000/v1"
    assert vprofile.served_model_name == "local-model"

    lm = load_config(configs_dir / "lmstudio.yaml")
    _, lprofile = lm.selected()
    assert lprofile.type == "openai_compatible"
    assert lprofile.api_base == "http://localhost:1234/v1"


def test_openrouter_free_profile_uses_free_router(configs_dir: Path) -> None:
    loaded = load_config(configs_dir / "openrouter-free.yaml")
    name, profile = loaded.selected()
    assert name == "openrouter"
    assert profile.model == "openrouter/openrouter/free"
    assert profile.model != "openrouter/openrouter/auto"


def test_timeout_must_be_positive(configs_dir: Path, tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("providers:\n  x:\n    type: mock\n    model: m\n    timeout_seconds: 0\n", encoding="utf-8")
    try:
        load_config(path)
        raise AssertionError("expected validation error")
    except ValueError as exc:
        assert "timeout_seconds" in str(exc)
