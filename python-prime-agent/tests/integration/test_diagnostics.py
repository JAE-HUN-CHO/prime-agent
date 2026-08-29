from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from prime_agent_py.cli.app import app
from prime_agent_py.providers.config_load import load_config
from prime_agent_py.providers.errors import diagnosis_for_profile
from prime_agent_py.providers.registry import build_provider


def test_diagnostics_when_server_missing(configs_dir: Path) -> None:
    config = load_config(configs_dir / "ollama.yaml")
    name, profile = config.selected()
    provider = build_provider(name, profile)
    diag = provider.diagnosis("Connection refused")  # type: ignore[union-attr]
    assert "ollama" in diag
    assert "http://localhost:11434" in diag
    assert "ollama/qwen3:30b" in diag
    assert "curl" in diag
    assert "API key: not required" in diag

    vllm = load_config(configs_dir / "vllm.yaml")
    vname, vprofile = vllm.selected()
    formatted = diagnosis_for_profile(
        provider_name=vname,
        endpoint=vprofile.api_base or "",
        model=vprofile.served_model_name or vprofile.model,
        timeout_seconds=vprofile.timeout_seconds,
        cause="Connection refused",
        api_key_env=vprofile.api_key_env,
        api_key_required=vprofile.api_key_required(),
    ).format()
    assert "localhost:8000" in formatted
    assert "curl" in formatted

    lm = load_config(configs_dir / "lmstudio.yaml")
    lname, lprofile = lm.selected()
    lm_fmt = diagnosis_for_profile(
        provider_name=lname,
        endpoint=lprofile.api_base or "",
        model=lprofile.served_model_name or lprofile.model,
        timeout_seconds=lprofile.timeout_seconds,
        cause="Connection refused",
        api_key_env=lprofile.api_key_env,
        api_key_required=lprofile.api_key_required(),
    ).format()
    assert "1234" in lm_fmt


def test_cli_prints_diagnosis_on_connection_error(monkeypatch: object, configs_dir: Path) -> None:
    from collections.abc import AsyncIterator

    from prime_agent_py.models.events import ErrorEvent, ModelEvent
    from prime_agent_py.models.messages import Message
    from prime_agent_py.models.tools import ToolDefinition

    async def fake_complete(
        self: object,
        messages: list[Message],
        *,
        model: str,
        tools: list[ToolDefinition] | None = None,
        stream: bool = True,
        **kwargs: object,
    ) -> AsyncIterator[ModelEvent]:
        _ = messages, model, tools, stream, kwargs
        yield ErrorEvent(message="Connection refused", code="connection_failed", retryable=True)

    monkeypatch.setattr(  # type: ignore[attr-defined]
        "prime_agent_py.providers.litellm_provider.LiteLLMProvider.complete",
        fake_complete,
    )
    runner = CliRunner()
    result = runner.invoke(app, ["run", "--config", str(configs_dir / "ollama.yaml"), "hello"])
    assert result.exit_code == 1
    assert "provider: ollama" in result.output
    assert "localhost:11434" in result.output
    assert "Connection refused" in result.output
