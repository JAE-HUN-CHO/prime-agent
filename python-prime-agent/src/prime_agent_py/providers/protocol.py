from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Protocol, runtime_checkable

from prime_agent_py.models.events import ModelEvent
from prime_agent_py.models.messages import Message
from prime_agent_py.models.tools import ToolDefinition


@runtime_checkable
class ModelProvider(Protocol):
    async def complete(
        self,
        messages: list[Message],
        *,
        model: str,
        tools: list[ToolDefinition] | None = None,
        stream: bool = True,
        **kwargs: Any,
    ) -> AsyncIterator[ModelEvent]: ...
