from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from prime_agent_py.models.messages import AssistantMessage, ToolCall
from prime_agent_py.models.usage import Usage


class TextDeltaEvent(BaseModel):
    type: Literal["text_delta"] = "text_delta"
    delta: str


class ThinkingDeltaEvent(BaseModel):
    type: Literal["thinking_delta"] = "thinking_delta"
    delta: str


class ToolCallStartEvent(BaseModel):
    type: Literal["tool_call_start"] = "tool_call_start"
    id: str
    name: str


class ToolCallDeltaEvent(BaseModel):
    type: Literal["tool_call_delta"] = "tool_call_delta"
    id: str
    delta: str


class ToolCallEndEvent(BaseModel):
    type: Literal["tool_call_end"] = "tool_call_end"
    tool_call: ToolCall


class UsageEvent(BaseModel):
    type: Literal["usage"] = "usage"
    usage: Usage


class FinishEvent(BaseModel):
    type: Literal["finish"] = "finish"
    reason: Literal["stop", "length", "tool_use"]
    message: AssistantMessage


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str
    code: str | None = None
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


ModelEvent = (
    TextDeltaEvent
    | ThinkingDeltaEvent
    | ToolCallStartEvent
    | ToolCallDeltaEvent
    | ToolCallEndEvent
    | UsageEvent
    | FinishEvent
    | ErrorEvent
)
