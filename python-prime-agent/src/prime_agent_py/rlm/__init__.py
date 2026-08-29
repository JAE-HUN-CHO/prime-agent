"""Phase 1 stub. Kernel-side RLM API remains `prime-agent-runtime` (`import rlm`)."""

from __future__ import annotations

from typing import Any

HOST_REQUEST_TYPES = ("rlm.run", "rlm.find_models", "rlm.list_subagents", "rlm.delete_subagent")


async def host_request(request_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    raise NotImplementedError(
        f"Python RLM host is not implemented in Phase 1 (request {request_type!r}). "
        "Use prime-agent-runtime inside the kernel once a Python host exists."
    )
