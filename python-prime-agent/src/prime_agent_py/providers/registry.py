from __future__ import annotations

from typing import Any

from prime_agent_py.providers.litellm_provider import LiteLLMProvider
from prime_agent_py.providers.mock import MockProvider
from prime_agent_py.providers.openai_compat import OpenAICompatibleProvider
from prime_agent_py.providers.profiles import ProviderProfile
from prime_agent_py.providers.protocol import ModelProvider


def build_provider(name: str, profile: ProviderProfile, *, acompletion: Any | None = None) -> ModelProvider:
    if profile.type == "mock":
        return MockProvider(profile, provider_name=name)
    if profile.type == "openai_compatible":
        return OpenAICompatibleProvider(profile, provider_name=name, acompletion=acompletion)
    return LiteLLMProvider(profile, provider_name=name, acompletion=acompletion)
