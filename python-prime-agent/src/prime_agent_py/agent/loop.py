from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from prime_agent_py.models.events import ErrorEvent, FinishEvent, ModelEvent, UsageEvent
from prime_agent_py.models.messages import Message, ToolCall, ToolResultMessage, UserMessage
from prime_agent_py.models.tools import ToolDefinition
from prime_agent_py.models.usage import Usage, add_usage, empty_usage
from prime_agent_py.providers.protocol import ModelProvider


@dataclass
class AgentTool:
    definition: ToolDefinition
    execute: Callable[[str, dict[str, Any]], Awaitable[str]]


@dataclass
class AgentLoopConfig:
    provider: ModelProvider
    model: str
    tools: list[AgentTool] | None = None
    max_turns: int = 8
    system: str | None = None


async def run_agent_loop(
    prompt: str,
    config: AgentLoopConfig,
    *,
    history: list[Message] | None = None,
    complete_kwargs: dict[str, Any] | None = None,
) -> AsyncIterator[ModelEvent]:
    """Minimal tool-call loop. Reduced from packages/agent/src/agent-loop.ts."""

    messages: list[Message] = list(history or [])
    messages.append(UserMessage(content=prompt))
    tool_map = {tool.definition.name: tool for tool in (config.tools or [])}
    kwargs = dict(complete_kwargs or {})
    if config.system:
        kwargs.setdefault("system", config.system)
    tool_defs = [tool.definition for tool in tool_map.values()] or None

    for _turn in range(config.max_turns):
        finish: FinishEvent | None = None
        errored = False
        stream = config.provider.complete(
            messages,
            model=config.model,
            tools=tool_defs,
            stream=True,
            **kwargs,
        )
        async for event in stream:
            if isinstance(event, ErrorEvent):
                errored = True
            if isinstance(event, FinishEvent):
                finish = event
            yield event
        if errored:
            return
        if finish is None:
            yield ErrorEvent(message="provider stream ended without finish or error", code="incomplete_stream")
            return
        messages.append(finish.message)
        tool_calls = [part for part in finish.message.content if isinstance(part, ToolCall)]
        if not tool_calls:
            return
        for call in tool_calls:
            tool = tool_map.get(call.name)
            if tool is None:
                result_text = f"unknown tool: {call.name}"
                is_error = True
            else:
                try:
                    result_text = await tool.execute(call.id, call.arguments)
                    is_error = False
                except Exception as exc:
                    result_text = f"tool error: {exc}"
                    is_error = True
            messages.append(
                ToolResultMessage(
                    tool_call_id=call.id,
                    tool_name=call.name,
                    content=result_text,
                    is_error=is_error,
                )
            )
    yield ErrorEvent(message=f"agent stopped after {config.max_turns} turns", code="max_turns")


def aggregate_usage(events: list[ModelEvent]) -> Usage:
    total = empty_usage()
    for event in events:
        if isinstance(event, UsageEvent):
            add_usage(total, event.usage)
    return total
