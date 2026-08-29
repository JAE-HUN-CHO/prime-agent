"""Phase 1 stub. Constants copied for mapping; this is not a live daemon."""

from __future__ import annotations

DAEMON_PROTOCOL_NAME = "prime-agent.daemon"
DAEMON_PROTOCOL_VERSION = 7
DAEMON_SCHEMA_REVISION = 23


def serve() -> None:
    raise NotImplementedError("Daemon is not implemented in Phase 1.")
