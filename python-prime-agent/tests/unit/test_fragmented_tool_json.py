from __future__ import annotations

from types import SimpleNamespace

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


def test_nonstreaming_parallel_tool_calls_without_index() -> None:
    """Non-streaming message.tool_calls omit index; slots must not all collapse to 0."""
    assembler = ToolCallAssembler()
    first = SimpleNamespace(
        id="call_read",
        function=SimpleNamespace(name="read_file", arguments='{"path":"a.py"}'),
    )
    second = SimpleNamespace(
        id="call_grep",
        function=SimpleNamespace(name="grep", arguments='{"pattern":"foo"}'),
    )
    assembler.ingest(_delta([first, second]))
    ended = assembler.finalize()
    assert [event.tool_call.id for event in ended] == ["call_read", "call_grep"]
    assert [event.tool_call.name for event in ended] == ["read_file", "grep"]
    assert ended[0].tool_call.arguments == {"path": "a.py"}
    assert ended[1].tool_call.arguments == {"pattern": "foo"}


def test_nonstreaming_dict_tool_calls_without_index() -> None:
    assembler = ToolCallAssembler()
    assembler.ingest(
        {
            "tool_calls": [
                {"id": "c1", "function": {"name": "alpha", "arguments": '{"n":1}'}},
                {"id": "c2", "function": {"name": "beta", "arguments": '{"n":2}'}},
            ]
        }
    )
    ended = assembler.finalize()
    assert [event.tool_call.id for event in ended] == ["c1", "c2"]
    assert [event.tool_call.name for event in ended] == ["alpha", "beta"]
    assert ended[0].tool_call.arguments == {"n": 1}
    assert ended[1].tool_call.arguments == {"n": 2}


def test_explicit_index_kept_when_present() -> None:
    assembler = ToolCallAssembler()
    assembler.ingest(
        _delta(
            [
                tool_delta(index=1, call_id="second", name="b", arguments='{"i":1}'),
                tool_delta(index=0, call_id="first", name="a", arguments='{"i":0}'),
            ]
        )
    )
    ended = assembler.finalize()
    assert [event.tool_call.id for event in ended] == ["first", "second"]
    assert [event.tool_call.name for event in ended] == ["a", "b"]


def _delta(tool_calls: list[object]) -> object:
    return SimpleNamespace(tool_calls=tool_calls)
