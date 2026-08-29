"""Phase 1 stub. TypeScript session JSONL v3 is documented in docs/sessions.md."""

from __future__ import annotations

from pathlib import Path

from prime_agent_py.models.session import Session


def save_session(_session: Session, _path: Path) -> None:
    raise NotImplementedError("Session persistence is Phase 4. See docs/sessions.md.")


def load_session(_path: Path) -> Session:
    raise NotImplementedError("Session persistence is Phase 4. See docs/sessions.md.")
