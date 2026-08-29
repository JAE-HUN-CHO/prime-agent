from __future__ import annotations

import asyncio

import pytest

from prime_agent_py.models.events import ErrorEvent, TextDeltaEvent
from prime_agent_py.models.messages import UserMessage
from prime_agent_py.providers.errors import RateLimitError
from prime_agent_py.providers.litellm_provider import LiteLLMProvider
from prime_agent_py.providers.profiles import ProviderProfile
from tests.fixtures.streams import FakeStream, make_chunk, make_usage, text_stream


def _provider(acompletion: object, **kwargs: object) -> LiteLLMProvider:
    return LiteLLMProvider(
        ProviderProfile(type="litellm", model="openai/x", timeout_seconds=float(kwargs.get("timeout", 0.2)), max_retries=int(kwargs.get("retries", 2))),
        provider_name="openai",
        acompletion=acompletion,
    )


async def test_timeout() -> None:
    async def acompletion(**_kwargs: object) -> None:
        await asyncio.sleep(5)
        raise AssertionError("should have timed out")

    events = [
        event
        async for event in _provider(acompletion, timeout=0.05, retries=0).complete(
            [UserMessage(content="hi")],
            model="openai/x",
        )
    ]
    errors = [e for e in events if isinstance(e, ErrorEvent)]
    assert errors
    assert errors[0].code == "timeout"


async def test_retry_on_rate_limit() -> None:
    calls = {"n": 0}

    async def acompletion(**_kwargs: object) -> FakeStream:
        calls["n"] += 1
        if calls["n"] < 3:
            raise RateLimitError("429 rate limit exceeded", retry_after_seconds=0.01)
        return text_stream("recovered")

    events = [
        event
        async for event in _provider(acompletion, timeout=5, retries=3).complete(
            [UserMessage(content="hi")],
            model="openai/x",
        )
    ]
    assert calls["n"] == 3
    text = "".join(e.delta for e in events if isinstance(e, TextDeltaEvent))
    assert text == "recovered"


async def test_cancellation_is_not_an_error_event() -> None:
    started = asyncio.Event()

    async def acompletion(**_kwargs: object) -> FakeStream:
        async def gen() -> object:
            started.set()
            yield make_chunk(content="partial")
            await asyncio.sleep(30)
            yield make_chunk(content="late", finish_reason="stop", usage=make_usage())

        return gen()  # type: ignore[return-value]

    async def consume() -> list[object]:
        out: list[object] = []
        async for event in _provider(acompletion, timeout=60, retries=0).complete(
            [UserMessage(content="hi")],
            model="openai/x",
        ):
            out.append(event)
        return out

    task = asyncio.create_task(consume())
    await started.wait()
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
