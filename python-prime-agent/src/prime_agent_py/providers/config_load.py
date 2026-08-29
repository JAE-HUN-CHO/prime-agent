from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from prime_agent_py.providers.profiles import AppConfig, ProviderProfile


def load_config(path: str | Path) -> AppConfig:
    raw_path = Path(path)
    data = yaml.safe_load(raw_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{raw_path} must contain a YAML mapping")
    try:
        return AppConfig.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"invalid provider config {raw_path}: {exc}") from exc


def mock_profile() -> ProviderProfile:
    return ProviderProfile(type="mock", model="mock-1", timeout_seconds=5.0, max_retries=0)
