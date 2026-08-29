from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import Any
from uuid import uuid4

from prime_agent_py.models.events import FinishEvent, ModelEvent, TextDeltaEvent, ToolCallEndEvent, ToolCallStartEvent
from prime_agent_py.models.messages import AssistantMessage, Message, TextContent, ToolCall, UserMessage
from prime_agent_py.models.tools import ToolDefinition
from prime_agent_py.models.usage import Usage
from prime_agent_py.providers.profiles import ProviderProfile


class MockTurn:
    def __init__(
        self,
        text: str | None = None,
        tool_calls: Sequence[ToolCall] | None = None,
        usage: Usage | None = None,
    ) -> None:
        self.text = text
        self.tool_calls = list(tool_calls or [])
        self.usage = usage or Usage(input=1, output=1, total_tokens=2)


class MockProvider:
    """Deterministic provider for tests and `--provider mock`."""

    DETERMINISTIC_PROMPT = "Return a deterministic test response"
    DETERMINISTIC_REPLY = "deterministic test response"

    def __init__(
        self,
        profile: ProviderProfile | None = None,
        *,
        script: Sequence[MockTurn] | None = None,
        provider_name: str = "mock",
    ) -> None:
        self.profile = profile or ProviderProfile(type="mock", model="mock-1")
        self.provider_name = provider_name
        self._script = list(script) if script is not None else None
        self.calls = 0

    async def complete(
        self,
        messages: list[Message],
        *,
        model: str,
        tools: list[ToolDefinition] | None = None,
        stream: bool = True,
        **kwargs: Any,
    ) -> AsyncIterator[ModelEvent]:
        _ = tools, stream, kwargs
        self.calls += 1
        if self._script is not None:
            if self.calls - 1 >= len(self._script):
                turn = MockTurn(text="(script exhausted)")
            else:
                turn = self._script[self.calls - 1]
        else:
            turn = self._turn_from_messages(messages)
        if turn.text:
            yield TextDeltaEvent(delta=turn.text)
        tool_calls: list[ToolCall] = []
        for call in turn.tool_calls:
            yield ToolCallStartEvent(id=call.id, name=call.name)
            yield ToolCallEndEvent(tool_call=call)
            tool_calls.append(call)
        from prime_agent_py.models.events import UsageEvent

        yield UsageEvent(usage=turn.usage)
        content: list[TextContent | ToolCall] = []
        if turn.text:
            content.append(TextContent(text=turn.text))
        content.extend(tool_calls)
        reason = "tool_use" if tool_calls else "stop"
        yield FinishEvent(
            reason=reason,
            message=AssistantMessage(
                content=content,
                provider=self.provider_name,
                model=model,
                stop_reason=reason,
                usage=turn.usage.model_dump(),
            ),
        )

    def _turn_from_messages(self, messages: list[Message]) -> MockTurn:
        last_user = ""
        for message in reversed(messages):
            if isinstance(message, UserMessage):
                last_user = message.content
                break
        if self.DETERMINISTIC_PROMPT.lower() in last_user.lower() or last_user.lower().strip() == self.DETERMINISTIC_PROMPT.lower():
            return MockTurn(text=self.DETERMINISTIC_REPLY)
        return MockTurn(text=f"mock reply: {last_user}" if last_user else "mock reply")


def scripted_tool_call(name: str, arguments: dict[str, Any], call_id: str | None = None) -> ToolCall:
    return ToolCall(id=call_id or f"call_{uuid4().hex[:8]}", name=name, arguments=arguments)
