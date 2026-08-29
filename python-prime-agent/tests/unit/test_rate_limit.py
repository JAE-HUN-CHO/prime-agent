from __future__ import annotations

from prime_agent_py.models.events import ErrorEvent
from prime_agent_py.models.messages import UserMessage
from prime_agent_py.providers.errors import RateLimitError
from prime_agent_py.providers.litellm_provider import LiteLLMProvider
from prime_agent_py.providers.profiles import ProviderProfile


async def test_rate_limit_error_handling_mocked() -> None:
    async def acompletion(**_kwargs: object) -> None:
        raise RateLimitError("free tier 429 rate limit", retry_after_seconds=1.0)

    provider = LiteLLMProvider(
        ProviderProfile(
            type="litellm",
            model="openrouter/x",
            api_key_env="OPENROUTER_API_KEY",
            max_retries=0,
            timeout_seconds=5,
        ),
        provider_name="openrouter",
        acompletion=acompletion,
    )
    events = [event async for event in provider.complete([UserMessage(content="hi")], model="openrouter/x")]
    error = next(e for e in events if isinstance(e, ErrorEvent))
    assert error.code == "rate_limit"
    assert error.retryable is True
    assert "429" in error.message or "rate limit" in error.message.lower()
