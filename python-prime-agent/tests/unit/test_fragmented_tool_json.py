from __future__ import annotations

from tests.fixtures.streams import tool_delta

from prime_agent_py.providers.openai_messages import ToolCallAssembler


def test_fragmented_tool_call_json() -> None:
    assembler = ToolCallAssembler()
    events = []
    events.extend(assembler.ingest(_delta([tool_delta(call_id="c1", name="echo", arguments='{"q')])))
    events.extend(assembler.ingest(_delta([tool_delta(arguments='ue":"he')])))
    events.extend(assembler.ingest(_delta([tool_delta(arguments='llo"}')])))
    ended = assembler.finalize()
    assert any(e.type == "tool_call_start" for e in events)
    assert any(e.type == "tool_call_delta" for e in events)
    assert ended[0].type == "tool_call_end"
    assert ended[0].tool_call.name == "echo"
    assert ended[0].tool_call.arguments == {"que": "hello"}


def _delta(tool_calls: list[object]) -> object:
    from types import SimpleNamespace

    return SimpleNamespace(tool_calls=tool_calls)
