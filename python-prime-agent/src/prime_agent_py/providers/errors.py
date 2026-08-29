from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProviderError(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        retryable: bool = False,
        cause: BaseException | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.cause = cause
        self.details = details or {}


class RateLimitError(ProviderError):
    def __init__(
        self,
        message: str,
        *,
        retry_after_seconds: float | None = None,
        cause: BaseException | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code="rate_limit", retryable=True, cause=cause, details=details)
        self.retry_after_seconds = retry_after_seconds


class ConnectionFailedError(ProviderError):
    def __init__(
        self,
        message: str,
        *,
        cause: BaseException | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code="connection_failed", retryable=True, cause=cause, details=details)


class TimeoutError(ProviderError):
    def __init__(self, message: str, *, cause: BaseException | None = None) -> None:
        super().__init__(message, code="timeout", retryable=True, cause=cause)


class Diagnosis(BaseModel):
    provider_name: str
    endpoint: str
    model: str
    timeout_seconds: float
    cause: str
    check_commands: list[str] = Field(default_factory=list)
    api_key_required: bool = False
    api_key_env: str | None = None

    def format(self) -> str:
        key_line = (
            f"API key: required via ${self.api_key_env}"
            if self.api_key_required and self.api_key_env
            else ("API key: required" if self.api_key_required else "API key: not required for this profile")
        )
        commands = "\n".join(f"  {cmd}" for cmd in self.check_commands) or "  (none)"
        return (
            "Provider connection failed\n"
            f"  provider: {self.provider_name}\n"
            f"  endpoint: {self.endpoint}\n"
            f"  model: {self.model}\n"
            f"  timeout: {self.timeout_seconds}s\n"
            f"  cause: {self.cause}\n"
            f"  {key_line}\n"
            "Check:\n"
            f"{commands}"
        )


def diagnosis_for_profile(
    *,
    provider_name: str,
    endpoint: str,
    model: str,
    timeout_seconds: float,
    cause: str,
    api_key_env: str | None,
    api_key_required: bool,
) -> Diagnosis:
    checks: list[str] = []
    lowered = endpoint.lower()
    if "11434" in endpoint or provider_name == "ollama":
        checks.extend(
            [
                "curl -sS --max-time 2 http://localhost:11434/api/tags",
                "ollama serve",
            ]
        )
    elif ":8000" in endpoint or provider_name == "vllm":
        checks.extend(
            [
                "curl -sS --max-time 2 http://localhost:8000/v1/models",
                "check that vLLM is listening on --port 8000",
            ]
        )
    elif ":1234" in endpoint or provider_name == "lmstudio":
        checks.extend(
            [
                "curl -sS --max-time 2 http://localhost:1234/v1/models",
                "start LM Studio local server on port 1234",
            ]
        )
    elif endpoint.startswith("http"):
        checks.append(f"curl -sS --max-time 2 {endpoint.rstrip('/')}/models")
    if "localhost" not in lowered and "127.0.0.1" not in lowered and endpoint.startswith("http"):
        checks.append("if this is a remote Ollama/vLLM endpoint, confirm TLS and auth; do not expose an open API")
    return Diagnosis(
        provider_name=provider_name,
        endpoint=endpoint or "(default LiteLLM endpoint)",
        model=model,
        timeout_seconds=timeout_seconds,
        cause=cause,
        check_commands=checks,
        api_key_required=api_key_required,
        api_key_env=api_key_env,
    )
