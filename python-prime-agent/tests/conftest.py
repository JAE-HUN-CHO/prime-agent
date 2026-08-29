from __future__ import annotations

from pathlib import Path

import pytest

CONFIGS = Path(__file__).resolve().parents[1] / "configs"


@pytest.fixture
def configs_dir() -> Path:
    return CONFIGS
