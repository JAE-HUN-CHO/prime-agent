from __future__ import annotations

import pytest

from prime_agent_py.models.events import FinishEvent, TextDeltaEvent
from prime_agent_py.models.messages import UserMessage
from prime_agent_py.providers.mock import MockProvider


@pytest.mark.asyncio
async def test_mock_deterministic_prompt() -> None:
    provider = MockProvider()
    events = [
        event
        async for event in provider.complete(
            [UserMessage(content="Return a deterministic test response")],
            model="mock-1",
        )
    ]
    text = "".join(e.delta for e in events if isinstance(e, TextDeltaEvent))
    assert text == MockProvider.DETERMINISTIC_REPLY
    finish = next(e for e in events if isinstance(e, FinishEvent))
    assert finish.reason == "stop"
    assert finish.message.stop_reason == "stop"


@pytest.mark.asyncio
async def test_mock_is_repeatable() -> None:
    provider = MockProvider()
    prompt = UserMessage(content="Return a deterministic test response")
    first = [event async for event in provider.complete([prompt], model="m")]
    provider2 = MockProvider()
    second = [event async for event in provider2.complete([prompt], model="m")]
    assert [e.model_dump() for e in first] == [e.model_dump() for e in second]
