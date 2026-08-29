from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from prime_agent_py.agent.loop import AgentLoopConfig
from prime_agent_py.agent.runner import AgentRunner
from prime_agent_py.models.events import ErrorEvent, TextDeltaEvent, ThinkingDeltaEvent
from prime_agent_py.observability import configure_logging
from prime_agent_py.providers.config_load import load_config, mock_profile
from prime_agent_py.providers.registry import build_provider

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console(stderr=False)


def main() -> None:
    app()


@app.command("run")
def run_command(
    prompt: str = typer.Argument(..., help="User prompt"),
    provider: Optional[str] = typer.Option(None, "--provider", help="Profile name, or 'mock'"),
    config: Optional[Path] = typer.Option(None, "--config", exists=False, help="YAML provider config"),
) -> None:
    """Run one agent turn loop (Phase 1)."""
    configure_logging()
    exit_code = asyncio.run(_run(prompt, provider_name=provider, config_path=config))
    raise typer.Exit(exit_code)


async def _run(prompt: str, *, provider_name: str | None, config_path: Path | None) -> int:
    try:
        name, profile, provider = _resolve_provider(provider_name, config_path)
    except (OSError, KeyError, ValueError) as exc:
        console.print(f"[red]config error:[/red] {exc}")
        return 1

    runner = AgentRunner(AgentLoopConfig(provider=provider, model=profile.model, max_turns=8))
    result = await runner.run(prompt)
    printed = False
    for event in result.events:
        if isinstance(event, TextDeltaEvent):
            console.print(event.delta, end="")
            printed = True
        elif isinstance(event, ThinkingDeltaEvent):
            console.print(f"[dim]{event.delta}[/dim]", end="")
            printed = True
        elif isinstance(event, ErrorEvent):
            if printed:
                console.print()
            console.print(f"[red]error:[/red] {event.message}")
            diag = getattr(provider, "diagnosis", None)
            if callable(diag) and event.code in {"connection_failed", "timeout", "rate_limit"}:
                console.print(diag(event.message))
            elif event.code == "connection_failed" or "connect" in event.message.lower():
                from prime_agent_py.providers.errors import diagnosis_for_profile

                console.print(
                    diagnosis_for_profile(
                        provider_name=name,
                        endpoint=profile.api_base or "",
                        model=profile.served_model_name or profile.model,
                        timeout_seconds=profile.timeout_seconds,
                        cause=event.message,
                        api_key_env=profile.api_key_env,
                        api_key_required=profile.api_key_required(),
                    ).format()
                )
            return 1
    if printed:
        console.print()
    return 0


def _resolve_provider(provider_name: str | None, config_path: Path | None) -> tuple[str, object, object]:
    if provider_name == "mock" and config_path is None:
        profile = mock_profile()
        return "mock", profile, build_provider("mock", profile)
    if config_path is None:
        raise ValueError("pass --config PATH or --provider mock")
    app_config = load_config(config_path)
    name, profile = app_config.selected(None if provider_name == "mock" else provider_name)
    if provider_name == "mock":
        profile = mock_profile()
        name = "mock"
    return name, profile, build_provider(name, profile)
