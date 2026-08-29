from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from prime_agent_py.models.events import ModelEvent
from prime_agent_py.models.messages import Message
from prime_agent_py.models.tools import ToolDefinition
from prime_agent_py.providers.litellm_provider import LiteLLMProvider
from prime_agent_py.providers.profiles import ProviderProfile


class OpenAICompatibleProvider(LiteLLMProvider):
    """OpenAI-compatible HTTP servers (vLLM, LM Studio, proxies) via LiteLLM `openai/` models."""

    def __init__(
        self,
        profile: ProviderProfile,
        *,
        provider_name: str,
        acompletion: Any | None = None,
    ) -> None:
        if not profile.model.startswith("openai/") and profile.type == "openai_compatible":
            served = profile.served_model_name or profile.model
            profile = profile.model_copy(update={"model": f"openai/{served}"})
        super().__init__(profile, provider_name=provider_name, acompletion=acompletion)

    async def complete(
        self,
        messages: list[Message],
        *,
        model: str,
        tools: list[ToolDefinition] | None = None,
        stream: bool = True,
        **kwargs: Any,
    ) -> AsyncIterator[ModelEvent]:
        request_model = model if model.startswith("openai/") else self.profile.model
        async for event in super().complete(
            messages, model=request_model, tools=tools, stream=stream, **kwargs
        ):
            yield event
