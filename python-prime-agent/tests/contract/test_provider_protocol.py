from __future__ import annotations

from collections.abc import AsyncIterator
from typing import get_type_hints

from prime_agent_py.providers.mock import MockProvider
from prime_agent_py.providers.protocol import ModelProvider


def test_mock_satisfies_protocol() -> None:
    provider = MockProvider()
    assert isinstance(provider, ModelProvider)


def test_complete_is_async_iterator_annotation() -> None:
    hints = get_type_hints(ModelProvider.complete)
    assert hints["return"].__origin__ is AsyncIterator or "AsyncIterator" in str(hints["return"])
