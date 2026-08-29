"""Phase 1 stub. Kernel host lives in TypeScript; protocol is prime-agent-runtime/src/rlm/repl.md."""

from __future__ import annotations

from typing import Any

KERNEL_IS_NOT_A_SANDBOX = True
REPL_PROTOCOL_VERSION = 3


class KernelClient:
    async def execute(self, code: str) -> dict[str, Any]:
        raise NotImplementedError("Kernel client is not implemented in Phase 1. See docs/migration-map.md.")
