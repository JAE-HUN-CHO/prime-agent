from __future__ import annotations

from prime_agent_py.models.events import ErrorEvent
from prime_agent_py.models.messages import UserMessage
from prime_agent_py.providers.openai_compat import OpenAICompatibleProvider
from prime_agent_py.providers.profiles import ProviderProfile


async def test_openai_compatible_connection_failure() -> None:
    async def acompletion(**_kwargs: object) -> None:
        raise ConnectionError("Failed to establish a new connection: Connection refused")

    provider = OpenAICompatibleProvider(
        ProviderProfile(
            type="openai_compatible",
            model="local-model",
            api_base="http://127.0.0.1:1/v1",
            timeout_seconds=2,
            max_retries=0,
        ),
        provider_name="vllm",
        acompletion=acompletion,
    )
    events = [event async for event in provider.complete([UserMessage(content="hi")], model="openai/local-model")]
    error = next(e for e in events if isinstance(e, ErrorEvent))
    assert error.code == "connection_failed"
    diag = provider.diagnosis(error.message)
    assert "vllm" in diag
    assert "127.0.0.1:1" in diag or "http://127.0.0.1:1/v1" in diag
    assert "timeout" in diag.lower()
