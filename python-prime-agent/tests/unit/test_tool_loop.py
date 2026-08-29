from __future__ import annotations

from prime_agent_py.agent.loop import AgentLoopConfig, AgentTool, aggregate_usage, run_agent_loop
from prime_agent_py.models.events import FinishEvent, ModelEvent
from prime_agent_py.models.tools import ToolDefinition
from prime_agent_py.models.usage import Usage
from prime_agent_py.providers.mock import MockProvider, MockTurn, scripted_tool_call


async def _echo(call_id: str, arguments: dict[str, object]) -> str:
    return f"echo:{call_id}:{arguments.get('q')}"


async def test_single_and_consecutive_tool_calls() -> None:
    first = scripted_tool_call("echo", {"q": "one"}, "c1")
    second = scripted_tool_call("echo", {"q": "two"}, "c2")
    provider = MockProvider(
        script=[
            MockTurn(tool_calls=[first], usage=Usage(input=2, output=1, total_tokens=3)),
            MockTurn(tool_calls=[second], usage=Usage(input=3, output=1, total_tokens=4)),
            MockTurn(text="done", usage=Usage(input=4, output=2, total_tokens=6)),
        ]
    )
    tool = AgentTool(
        definition=ToolDefinition(
            name="echo",
            description="echo",
            parameters={"type": "object", "properties": {"q": {"type": "string"}}},
        ),
        execute=_echo,
    )
    events: list[ModelEvent] = [
        event
        async for event in run_agent_loop(
            "go",
            AgentLoopConfig(provider=provider, model="mock-1", tools=[tool], max_turns=5),
        )
    ]
    finishes = [e for e in events if isinstance(e, FinishEvent)]
    assert len(finishes) == 3
    assert finishes[0].reason == "tool_use"
    assert finishes[1].reason == "tool_use"
    assert finishes[2].reason == "stop"
    assert finishes[2].message.content[0].text == "done"  # type: ignore[union-attr]
    usage = aggregate_usage(events)
    assert usage.input == 9
    assert usage.output == 4
    assert usage.total_tokens == 13
    assert provider.calls == 3
