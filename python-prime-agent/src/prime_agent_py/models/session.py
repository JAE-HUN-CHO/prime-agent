from __future__ import annotations

from pydantic import BaseModel, Field

from prime_agent_py.models.messages import Message
from prime_agent_py.models.usage import Usage, empty_usage


class Session(BaseModel):
    """In-memory session. Disk JSONL persistence is Phase 4 (see docs/sessions.md)."""

    id: str
    cwd: str = ""
    messages: list[Message] = Field(default_factory=list)
    usage: Usage = Field(default_factory=empty_usage)
    provider_name: str = ""
    model: str = ""
