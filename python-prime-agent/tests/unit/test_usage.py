from __future__ import annotations

from prime_agent_py.models.usage import Usage, add_usage, empty_usage


def test_add_usage() -> None:
    total = empty_usage()
    add_usage(total, Usage(input=1, output=2, cache_read=3, reasoning_tokens=4, total_tokens=7))
    add_usage(total, Usage(input=10, output=20, cache_read=1, reasoning_tokens=1, total_tokens=31))
    assert total.input == 11
    assert total.output == 22
    assert total.cache_read == 4
    assert total.reasoning_tokens == 5
    assert total.total_tokens == 38
