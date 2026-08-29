from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class TextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ThinkingContent(BaseModel):
    type: Literal["thinking"] = "thinking"
    thinking: str
    redacted: bool = False


class ToolCall(BaseModel):
    type: Literal["toolCall"] = "toolCall"
    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class UserMessage(BaseModel):
    role: Literal["user"] = "user"
    content: str
    timestamp_ms: int = 0


class AssistantMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: list[TextContent | ThinkingContent | ToolCall] = Field(default_factory=list)
    provider: str = ""
    model: str = ""
    usage: dict[str, Any] | None = None
    stop_reason: Literal["stop", "length", "tool_use", "error", "aborted"] | None = None
    error_message: str | None = None
    timestamp_ms: int = 0


class ToolResultMessage(BaseModel):
    role: Literal["toolResult"] = "toolResult"
    tool_call_id: str
    tool_name: str
    content: str
    is_error: bool = False
    timestamp_ms: int = 0


Message = UserMessage | AssistantMessage | ToolResultMessage
