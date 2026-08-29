from __future__ import annotations

from types import SimpleNamespace
from typing import Any


class FakeUsage(SimpleNamespace):
    pass


def make_usage(*, prompt: int = 3, completion: int = 5, cached: int = 0, reasoning: int = 0, total: int | None = None) -> Any:
    return SimpleNamespace(
        prompt_tokens=prompt,
        completion_tokens=completion,
        total_tokens=total if total is not None else prompt + completion,
        prompt_tokens_details=SimpleNamespace(cached_tokens=cached),
        completion_tokens_details=SimpleNamespace(reasoning_tokens=reasoning),
        cache_creation_input_tokens=0,
    )


def make_chunk(
    *,
    content: str | None = None,
    reasoning: str | None = None,
    tool_calls: list[Any] | None = None,
    finish_reason: str | None = None,
    usage: Any | None = None,
) -> Any:
    delta = SimpleNamespace(content=content, reasoning_content=reasoning, reasoning=reasoning, tool_calls=tool_calls)
    choice = SimpleNamespace(delta=delta, finish_reason=finish_reason)
    return SimpleNamespace(choices=[choice], usage=usage)


def tool_delta(*, index: int = 0, call_id: str | None = None, name: str | None = None, arguments: str | None = None) -> Any:
    return SimpleNamespace(
        index=index,
        id=call_id,
        function=SimpleNamespace(name=name, arguments=arguments),
    )


class FakeStream:
    def __init__(self, chunks: list[Any]) -> None:
        self._chunks = chunks

    def __aiter__(self) -> FakeStream:
        self._iter = iter(self._chunks)
        return self

    async def __anext__(self) -> Any:
        try:
            return next(self._iter)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


def text_stream(text: str, usage: Any | None = None) -> FakeStream:
    chunks = [make_chunk(content=part) for part in _split(text)]
    chunks.append(make_chunk(finish_reason="stop", usage=usage or make_usage()))
    return FakeStream(chunks)


def _split(text: str) -> list[str]:
    if not text:
        return []
    return [text[i : i + 4] for i in range(0, len(text), 4)]
