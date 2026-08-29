from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ProviderProfile(BaseModel):
    """YAML provider profile. Free-tier model names are data, not code constants."""

    type: Literal["litellm", "openai_compatible", "mock"]
    model: str
    served_model_name: str | None = None
    api_base: str | None = None
    api_key_env: str | None = None
    timeout_seconds: float = 60.0
    max_retries: int = 2
    extra_params: dict[str, Any] = Field(default_factory=dict)
    json_mode: bool = False
    temperature: float | None = None
    max_tokens: int | None = None

    @field_validator("timeout_seconds")
    @classmethod
    def timeout_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("timeout_seconds must be positive")
        return value

    @field_validator("max_retries")
    @classmethod
    def retries_non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("max_retries must be >= 0")
        return value

    @property
    def litellm_model(self) -> str:
        return self.model

    def api_key_required(self) -> bool:
        if self.type == "mock":
            return False
        if self.api_key_env:
            return True
        if self.api_base and ("localhost" in self.api_base or "127.0.0.1" in self.api_base):
            return False
        return self.type == "openai_compatible" and not self.api_base


class AppConfig(BaseModel):
    default_provider: str | None = None
    providers: dict[str, ProviderProfile]

    def selected(self, name: str | None = None) -> tuple[str, ProviderProfile]:
        if name:
            if name not in self.providers:
                raise KeyError(f"unknown provider profile: {name}")
            return name, self.providers[name]
        if self.default_provider:
            return self.selected(self.default_provider)
        if len(self.providers) == 1:
            key = next(iter(self.providers))
            return key, self.providers[key]
        raise KeyError("config has multiple providers; pass --provider or set default_provider")
