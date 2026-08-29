from __future__ import annotations

import os
import re
from typing import Any

_SECRET_ENV_HINTS = (
    "API_KEY",
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "AUTHORIZATION",
)

_BEARER_RE = re.compile(r"(Bearer\s+)(\S+)", re.IGNORECASE)
_KEY_ASSIGN_RE = re.compile(r"(?i)((?:api[_-]?key|token|secret|password)\s*[:=]\s*)([^\s,;]+)")


def looks_like_secret_env(name: str) -> bool:
    upper = name.upper()
    return any(hint in upper for hint in _SECRET_ENV_HINTS)


def mask_secret(value: str | None) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "***"
    return f"{value[:2]}…{value[-2:]}"


def redact_text(text: str, extra_secrets: list[str] | None = None) -> str:
    redacted = _BEARER_RE.sub(r"\1***", text)
    redacted = _KEY_ASSIGN_RE.sub(r"\1***", redacted)
    for secret in extra_secrets or []:
        if secret and secret in redacted:
            redacted = redacted.replace(secret, "***")
    return redacted


def env_secrets() -> list[str]:
    secrets: list[str] = []
    for name, value in os.environ.items():
        if looks_like_secret_env(name) and value:
            secrets.append(value)
    return secrets


def safe_exc_text(exc: BaseException) -> str:
    return redact_text(str(exc), env_secrets())


def resolve_api_key(api_key_env: str | None, explicit: str | None = None) -> str | None:
    if explicit:
        return explicit
    if api_key_env:
        value = os.environ.get(api_key_env)
        return value if value else None
    return None


def pick_default_api_key_env(provider_name: str) -> str | None:
    mapping = {
        "openrouter": "OPENROUTER_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "google": "GEMINI_API_KEY",
        "groq": "GROQ_API_KEY",
        "cerebras": "CEREBRAS_API_KEY",
        "openai": "OPENAI_API_KEY",
        "openai_compatible": "OPENAI_API_KEY",
    }
    return mapping.get(provider_name)
