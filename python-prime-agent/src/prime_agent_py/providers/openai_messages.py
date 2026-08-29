from __future__ import annotations

import asyncio
import json
from typing import Any

from prime_agent_py.models.events import (
    ErrorEvent,
    FinishEvent,
    ModelEvent,
    TextDeltaEvent,
    ThinkingDeltaEvent,
    ToolCallDeltaEvent,
    ToolCallEndEvent,
    ToolCallStartEvent,
    UsageEvent,
)
from prime_agent_py.models.messages import (
    AssistantMessage,
    Message,
    TextContent,
    ThinkingContent,
    ToolCall,
    ToolResultMessage,
    UserMessage,
)
from prime_agent_py.models.tools import ToolDefinition
from prime_agent_py.models.usage import Usage
from prime_agent_py.providers.credentials import redact_text, safe_exc_text
from prime_agent_py.providers.errors import ConnectionFailedError, ProviderError, RateLimitError, TimeoutError


def messages_to_openai(messages: list[Message], system: str | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if system:
        out.append({"role": "system", "content": system})
    pending_assistant_tools: list[dict[str, Any]] = []
    for message in messages:
        if isinstance(message, UserMessage):
            out.append({"role": "user", "content": message.content})
        elif isinstance(message, AssistantMessage):
            text_parts = [p.text for p in message.content if isinstance(p, TextContent)]
            thinking_parts = [p.thinking for p in message.content if isinstance(p, ThinkingContent)]
            tool_calls = [p for p in message.content if isinstance(p, ToolCall)]
            payload: dict[str, Any] = {"role": "assistant", "content": "".join(text_parts) or None}
            if thinking_parts:
                payload["reasoning_content"] = "".join(thinking_parts)
            if tool_calls:
                payload["tool_calls"] = [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {"name": call.name, "arguments": json.dumps(call.arguments)},
                    }
                    for call in tool_calls
                ]
            out.append(payload)
            pending_assistant_tools = tool_calls
        elif isinstance(message, ToolResultMessage):
            out.append(
                {
                    "role": "tool",
                    "tool_call_id": message.tool_call_id,
                    "content": message.content,
                }
            )
            _ = pending_assistant_tools
    return out


def tools_to_openai(tools: list[ToolDefinition] | None) -> list[dict[str, Any]] | None:
    if not tools:
        return None
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            },
        }
        for tool in tools
    ]


def _attr(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def usage_from_chunk(chunk: Any) -> Usage | None:
    raw = _attr(chunk, "usage")
    if raw is None:
        return None
    prompt = int(_attr(raw, "prompt_tokens", 0) or 0)
    completion = int(_attr(raw, "completion_tokens", 0) or 0)
    total = int(_attr(raw, "total_tokens", 0) or 0)
    prompt_details = _attr(raw, "prompt_tokens_details") or {}
    completion_details = _attr(raw, "completion_tokens_details") or {}
    cached = int(_attr(prompt_details, "cached_tokens", 0) or _attr(raw, "cache_read_input_tokens", 0) or 0)
    cache_write = int(_attr(raw, "cache_creation_input_tokens", 0) or 0)
    reasoning = int(_attr(completion_details, "reasoning_tokens", 0) or _attr(raw, "reasoning_tokens", 0) or 0)
    usage = Usage(
        input=prompt,
        output=completion,
        cache_read=cached,
        cache_write=cache_write,
        reasoning_tokens=reasoning,
        total_tokens=total or (prompt + completion),
    )
    return usage


def map_finish_reason(reason: str | None) -> str:
    if reason in {"tool_calls", "tool_use", "function_call"}:
        return "tool_use"
    if reason in {"length", "max_tokens"}:
        return "length"
    return "stop"


class ToolCallAssembler:
    """Reassemble fragmented streamed tool-call JSON (OpenAI-style argument deltas)."""

    def __init__(self) -> None:
        self._by_index: dict[int, dict[str, str]] = {}
        self._started: set[str] = set()
        self._ended: set[str] = set()

    def ingest(self, delta: Any) -> list[ModelEvent]:
        events: list[ModelEvent] = []
        tool_calls = _attr(delta, "tool_calls")
        if not tool_calls:
            return events
        for item in tool_calls:
            index = int(_attr(item, "index", 0) or 0)
            slot = self._by_index.setdefault(index, {"id": "", "name": "", "arguments": ""})
            item_id = _attr(item, "id")
            if item_id:
                slot["id"] = str(item_id)
            function = _attr(item, "function") or {}
            name = _attr(function, "name")
            if name:
                slot["name"] = str(name)
            arguments = _attr(function, "arguments")
            if arguments:
                slot["arguments"] += str(arguments)
            call_id = slot["id"] or f"call_{index}"
            slot["id"] = call_id
            if call_id not in self._started and slot["name"]:
                self._started.add(call_id)
                events.append(ToolCallStartEvent(id=call_id, name=slot["name"]))
            if arguments:
                events.append(ToolCallDeltaEvent(id=call_id, delta=str(arguments)))
        return events

    def finalize(self) -> list[ModelEvent]:
        events: list[ModelEvent] = []
        tool_calls: list[ToolCall] = []
        for index in sorted(self._by_index):
            slot = self._by_index[index]
            call_id = slot["id"] or f"call_{index}"
            if call_id in self._ended:
                continue
            args_raw = slot["arguments"] or "{}"
            try:
                parsed: dict[str, Any] = json.loads(args_raw) if args_raw else {}
                if not isinstance(parsed, dict):
                    parsed = {"_raw": parsed}
            except json.JSONDecodeError:
                parsed = {"_raw": args_raw}
            call = ToolCall(id=call_id, name=slot["name"] or "unknown", arguments=parsed)
            tool_calls.append(call)
            self._ended.add(call_id)
            events.append(ToolCallEndEvent(tool_call=call))
        return events

    def tool_calls(self) -> list[ToolCall]:
        calls: list[ToolCall] = []
        for event in self.finalize():
            if isinstance(event, ToolCallEndEvent):
                calls.append(event.tool_call)
        return calls


def classify_exception(exc: BaseException) -> ProviderError:
    if isinstance(exc, asyncio.CancelledError):
        raise exc
    if isinstance(exc, ProviderError):
        return exc
    text = safe_exc_text(exc)
    lowered = text.lower()
    name = type(exc).__name__.lower()
    if ("rate" in lowered and "limit" in lowered) or "429" in lowered:
        return RateLimitError(text, cause=exc)
    if "timeout" in lowered or "timed out" in lowered:
        return TimeoutError(text, cause=exc)
    if any(
        token in lowered
        for token in (
            "connect",
            "connection refused",
            "connection error",
            "name or service not known",
            "nodename nor servname",
            "temporarily unavailable",
            "failed to establish",
        )
    ):
        return ConnectionFailedError(text, cause=exc)
    status = getattr(exc, "status_code", None)
    if status == 429:
        return RateLimitError(text, cause=exc)
    return ProviderError(text, code=name or "provider_error", cause=exc)


def error_event_from_exc(exc: BaseException) -> ErrorEvent:
    mapped = classify_exception(exc)
    return ErrorEvent(
        message=redact_text(str(mapped)),
        code=mapped.code,
        retryable=mapped.retryable,
        details=mapped.details,
    )


def assistant_from_parts(
    *,
    text: str,
    thinking: str,
    tool_calls: list[ToolCall],
    provider: str,
    model: str,
    stop_reason: str,
    usage: Usage | None,
) -> AssistantMessage:
    content: list[TextContent | ThinkingContent | ToolCall] = []
    if thinking:
        content.append(ThinkingContent(thinking=thinking))
    if text:
        content.append(TextContent(text=text))
    content.extend(tool_calls)
    return AssistantMessage(
        content=content,
        provider=provider,
        model=model,
        stop_reason=stop_reason,  # type: ignore[arg-type]
        usage=usage.model_dump() if usage else None,
    )


def iter_stream_chunk_events(
    chunk: Any,
    assembler: ToolCallAssembler,
    *,
    text_acc: list[str],
    thinking_acc: list[str],
) -> list[ModelEvent]:
    events: list[ModelEvent] = []
    usage = usage_from_chunk(chunk)
    if usage is not None:
        events.append(UsageEvent(usage=usage))
    choices = _attr(chunk, "choices") or []
    if not choices:
        return events
    choice = choices[0]
    delta = _attr(choice, "delta") or _attr(choice, "message") or {}
    content = _attr(delta, "content")
    if isinstance(content, str) and content:
        text_acc.append(content)
        events.append(TextDeltaEvent(delta=content))
    reasoning = _attr(delta, "reasoning_content") or _attr(delta, "reasoning")
    if isinstance(reasoning, str) and reasoning:
        thinking_acc.append(reasoning)
        events.append(ThinkingDeltaEvent(delta=reasoning))
    events.extend(assembler.ingest(delta))
    return events
