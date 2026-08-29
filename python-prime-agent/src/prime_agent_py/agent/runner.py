from __future__ import annotations

from dataclasses import dataclass, field

from prime_agent_py.agent.loop import AgentLoopConfig, aggregate_usage, run_agent_loop
from prime_agent_py.models.events import ErrorEvent, FinishEvent, ModelEvent
from prime_agent_py.models.session import Session
from prime_agent_py.models.usage import empty_usage


@dataclass
class AgentRunResult:
    session: Session
    events: list[ModelEvent] = field(default_factory=list)
    error: ErrorEvent | None = None
    last_finish: FinishEvent | None = None


class AgentRunner:
    def __init__(self, config: AgentLoopConfig) -> None:
        self.config = config

    async def run(self, prompt: str, *, session_id: str = "ephemeral") -> AgentRunResult:
        session = Session(
            id=session_id,
            provider_name=getattr(self.config.provider, "provider_name", ""),
            model=self.config.model,
            usage=empty_usage(),
        )
        events: list[ModelEvent] = []
        error: ErrorEvent | None = None
        last_finish: FinishEvent | None = None
        async for event in run_agent_loop(prompt, self.config):
            events.append(event)
            if isinstance(event, ErrorEvent):
                error = event
            if isinstance(event, FinishEvent):
                last_finish = event
                session.messages.append(event.message)
        session.usage = aggregate_usage(events)
        return AgentRunResult(session=session, events=events, error=error, last_finish=last_finish)
