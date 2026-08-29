from __future__ import annotations

from typer.testing import CliRunner

from prime_agent_py.cli.app import app
from prime_agent_py.providers.mock import MockProvider


def test_cli_mock_deterministic() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["run", "--provider", "mock", MockProvider.DETERMINISTIC_PROMPT])
    assert result.exit_code == 0, result.output
    assert MockProvider.DETERMINISTIC_REPLY in result.output
