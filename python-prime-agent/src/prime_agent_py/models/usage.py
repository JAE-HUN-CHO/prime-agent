from __future__ import annotations

from pydantic import BaseModel


class Usage(BaseModel):
    """Token usage. Field names follow the TypeScript `Usage` object in packages/ai."""

    input: int = 0
    output: int = 0
    cache_read: int = 0
    cache_write: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0
    cost_input: float = 0.0
    cost_output: float = 0.0
    cost_cache_read: float = 0.0
    cost_cache_write: float = 0.0
    cost_total: float = 0.0

    def recompute_total(self) -> None:
        if self.total_tokens == 0:
            self.total_tokens = self.input + self.output


def empty_usage() -> Usage:
    return Usage()


def clone_usage(usage: Usage) -> Usage:
    return usage.model_copy(deep=True)


def add_usage(total: Usage, usage: Usage) -> Usage:
    total.input += usage.input
    total.output += usage.output
    total.cache_read += usage.cache_read
    total.cache_write += usage.cache_write
    total.reasoning_tokens += usage.reasoning_tokens
    total.total_tokens += usage.total_tokens
    total.cost_input += usage.cost_input
    total.cost_output += usage.cost_output
    total.cost_cache_read += usage.cost_cache_read
    total.cost_cache_write += usage.cost_cache_write
    total.cost_total += usage.cost_total
    return total
