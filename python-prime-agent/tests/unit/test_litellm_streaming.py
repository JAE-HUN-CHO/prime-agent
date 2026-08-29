from __future__ import annotations

from tests.fixtures.streams import FakeStream, make_chunk, make_usage, text_stream

from prime_agent_py.models.events import FinishEvent, TextDeltaEvent, UsageEvent
from prime_agent_py.models.messages import UserMessage
from prime_agent_py.providers.litellm_provider import LiteLLMProvider
from prime_agent_py.providers.profiles import ProviderProfile


def _provider(acompletion: object) -> LiteLLMProvider:
    return LiteLLMProvider(
        ProviderProfile(type="litellm", model="openai/gpt-test", timeout_seconds=5, max_retries=0),
        provider_name="openai",
        acompletion=acompletion,
    )


async def test_litellm_streaming_text() -> None:
    async def acompletion(**_kwargs: object) -> FakeStream:
        return text_stream("hello world", usage=make_usage(prompt=2, completion=4, cached=1, reasoning=3))

    events = [
        event
        async for event in _provider(acompletion).complete(
            [UserMessage(content="hi")],
            model="openai/gpt-test",
        )
    ]
    text = "".join(e.delta for e in events if isinstance(e, TextDeltaEvent))
    assert text == "hello world"
    usage_events = [e for e in events if isinstance(e, UsageEvent)]
    assert usage_events
    assert usage_events[-1].usage.cache_read == 1
    assert usage_events[-1].usage.reasoning_tokens == 3
    finish = next(e for e in events if isinstance(e, FinishEvent))
    assert finish.reason == "stop"


async def test_litellm_passes_timeout_retry_json_and_api_base() -> None:
    captured: dict[str, object] = {}

    async def acompletion(**kwargs: object) -> FakeStream:
        captured.update(kwargs)
        return FakeStream([make_chunk(content="ok", finish_reason="stop", usage=make_usage())])

    profile = ProviderProfile(
        type="litellm",
        model="openai/foo",
        api_base="http://localhost:9/v1",
        timeout_seconds=12,
        json_mode=True,
        extra_params={"temperature": 0.1},
        max_retries=0,
    )
    provider = LiteLLMProvider(profile, provider_name="local", acompletion=acompletion)
    async for _event in provider.complete([UserMessage(content="x")], model="openai/foo"):
        pass
    assert captured["api_base"] == "http://localhost:9/v1"
    assert captured["timeout"] == 12
    assert captured["response_format"] == {"type": "json_object"}
    assert captured["temperature"] == 0.1
    assert captured["stream"] is True
