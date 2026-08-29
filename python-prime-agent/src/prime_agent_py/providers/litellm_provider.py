from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from prime_agent_py.models.events import ErrorEvent, FinishEvent, ModelEvent, UsageEvent
from prime_agent_py.models.messages import AssistantMessage, Message, ToolCall
from prime_agent_py.models.tools import ToolDefinition
from prime_agent_py.models.usage import Usage
from prime_agent_py.providers.credentials import resolve_api_key
from prime_agent_py.providers.errors import RateLimitError, diagnosis_for_profile
from prime_agent_py.providers.errors import TimeoutError as ProviderTimeoutError
from prime_agent_py.providers.openai_messages import (
    ToolCallAssembler,
    assistant_from_parts,
    classify_exception,
    error_event_from_exc,
    iter_stream_chunk_events,
    map_finish_reason,
    messages_to_openai,
    tools_to_openai,
    usage_from_chunk,
)
from prime_agent_py.providers.profiles import ProviderProfile


class LiteLLMProvider:
    """Adapter over `litellm.acompletion`. The agent loop never sees raw chunks."""

    def __init__(
        self,
        profile: ProviderProfile,
        *,
        provider_name: str,
        acompletion: Any | None = None,
    ) -> None:
        self.profile = profile
        self.provider_name = provider_name
        self._acompletion = acompletion

    async def _call_acompletion(self, **kwargs: Any) -> Any:
        fn = self._acompletion
        if fn is None:
            import litellm

            litellm.suppress_debug_info = True
            fn = litellm.acompletion
        return await fn(**kwargs)

    def _request_kwargs(
        self,
        messages: list[Message],
        *,
        model: str,
        tools: list[ToolDefinition] | None,
        stream: bool,
        extra: dict[str, Any],
    ) -> dict[str, Any]:
        served = self.profile.served_model_name or model
        api_key = resolve_api_key(self.profile.api_key_env, extra.pop("api_key", None))
        params: dict[str, Any] = {
            "model": self.profile.litellm_model if model == self.profile.model else model,
            "messages": messages_to_openai(messages, system=extra.pop("system", None)),
            "stream": stream,
            "timeout": extra.pop("timeout", self.profile.timeout_seconds),
        }
        # served_model_name is the id the HTTP server expects
        if self.profile.served_model_name:
            params["model"] = (
                model
                if "/" in model and model.endswith(self.profile.served_model_name)
                else self._with_served_id(params["model"], served)
            )
        if self.profile.api_base:
            params["api_base"] = extra.pop("api_base", self.profile.api_base)
        elif "api_base" in extra:
            params["api_base"] = extra.pop("api_base")
        if api_key:
            params["api_key"] = api_key
        elif self.profile.api_base and (
            "localhost" in self.profile.api_base or "127.0.0.1" in self.profile.api_base
        ):
            # OpenAI-compatible local servers often require a placeholder key.
            params["api_key"] = resolve_api_key("OPENAI_API_KEY") or "not-needed"
        openai_tools = tools_to_openai(tools)
        if openai_tools:
            params["tools"] = openai_tools
        if self.profile.json_mode or extra.pop("json_mode", False):
            params["response_format"] = {"type": "json_object"}
        if self.profile.temperature is not None:
            params["temperature"] = self.profile.temperature
        if self.profile.max_tokens is not None:
            params["max_tokens"] = self.profile.max_tokens
        params.update(self.profile.extra_params)
        params.update(extra)
        if stream:
            params.setdefault("stream_options", {"include_usage": True})
        return params

    def _with_served_id(self, litellm_model: str, served: str) -> str:
        if "/" in litellm_model:
            prefix, _, _rest = litellm_model.partition("/")
            return f"{prefix}/{served}"
        return served

    async def complete(
        self,
        messages: list[Message],
        *,
        model: str,
        tools: list[ToolDefinition] | None = None,
        stream: bool = True,
        **kwargs: Any,
    ) -> AsyncIterator[ModelEvent]:
        timeout = float(kwargs.get("timeout", self.profile.timeout_seconds))
        retries = int(kwargs.pop("max_retries", self.profile.max_retries))
        last_error: BaseException | None = None
        for attempt in range(retries + 1):
            yielded = False
            try:
                async with asyncio.timeout(timeout):
                    async for event in self._complete_once(
                        messages, model=model, tools=tools, stream=stream, extra=dict(kwargs)
                    ):
                        yielded = True
                        yield event
                return
            except asyncio.CancelledError:
                raise
            except ProviderTimeoutError as exc:
                last_error = exc
                event = error_event_from_exc(exc)
                if yielded or attempt >= retries:
                    yield event
                    yield self._finish_error_as_diag(exc)
                    return
            except TimeoutError as exc:
                mapped = ProviderTimeoutError(f"provider timed out after {timeout}s", cause=exc)
                last_error = mapped
                if yielded or attempt >= retries:
                    yield error_event_from_exc(mapped)
                    return
            except RateLimitError as exc:
                last_error = exc
                delay = exc.retry_after_seconds if exc.retry_after_seconds is not None else min(2**attempt, 8)
                if yielded or attempt >= retries:
                    yield error_event_from_exc(exc)
                    return
                await asyncio.sleep(delay)
            except BaseException as exc:
                if isinstance(exc, asyncio.CancelledError):
                    raise
                mapped = classify_exception(exc)
                last_error = mapped
                if isinstance(mapped, RateLimitError) and not yielded and attempt < retries:
                    delay = mapped.retry_after_seconds or min(2**attempt, 8)
                    await asyncio.sleep(delay)
                    continue
                yield error_event_from_exc(mapped)
                return
        if last_error is not None:
            yield error_event_from_exc(last_error)

    def _finish_error_as_diag(self, exc: BaseException) -> ErrorEvent:
        return error_event_from_exc(exc)

    def diagnosis(self, cause: str) -> str:
        return diagnosis_for_profile(
            provider_name=self.provider_name,
            endpoint=self.profile.api_base or "",
            model=self.profile.served_model_name or self.profile.model,
            timeout_seconds=self.profile.timeout_seconds,
            cause=cause,
            api_key_env=self.profile.api_key_env,
            api_key_required=self.profile.api_key_required(),
        ).format()

    async def _complete_once(
        self,
        messages: list[Message],
        *,
        model: str,
        tools: list[ToolDefinition] | None,
        stream: bool,
        extra: dict[str, Any],
    ) -> AsyncIterator[ModelEvent]:
        params = self._request_kwargs(messages, model=model, tools=tools, stream=stream, extra=extra)
        response = await self._call_acompletion(**params)
        assembler = ToolCallAssembler()
        text_acc: list[str] = []
        thinking_acc: list[str] = []
        last_usage: Usage | None = None
        finish_reason = "stop"
        if stream:
            async for chunk in response:
                for event in iter_stream_chunk_events(chunk, assembler, text_acc=text_acc, thinking_acc=thinking_acc):
                    if isinstance(event, UsageEvent):
                        last_usage = event.usage
                    yield event
                choices = getattr(chunk, "choices", None) or (chunk.get("choices") if isinstance(chunk, dict) else None)
                if choices:
                    raw_reason = getattr(choices[0], "finish_reason", None)
                    if raw_reason is None and isinstance(choices[0], dict):
                        raw_reason = choices[0].get("finish_reason")
                    if raw_reason:
                        finish_reason = map_finish_reason(str(raw_reason))
        else:
            last_usage = usage_from_chunk(response)
            if last_usage:
                yield UsageEvent(usage=last_usage)
            choices = getattr(response, "choices", None) or []
            if choices:
                message = getattr(choices[0], "message", None) or {}
                content = getattr(message, "content", None) if not isinstance(message, dict) else message.get("content")
                if content:
                    text_acc.append(str(content))
                    from prime_agent_py.models.events import TextDeltaEvent

                    yield TextDeltaEvent(delta=str(content))
                assembler.ingest(message)
                raw_reason = getattr(choices[0], "finish_reason", None)
                if raw_reason:
                    finish_reason = map_finish_reason(str(raw_reason))
        end_events = assembler.finalize()
        tool_calls: list[ToolCall] = []
        for event in end_events:
            yield event
            if event.type == "tool_call_end":
                tool_calls.append(event.tool_call)
        if tool_calls:
            finish_reason = "tool_use"
        assistant: AssistantMessage = assistant_from_parts(
            text="".join(text_acc),
            thinking="".join(thinking_acc),
            tool_calls=tool_calls,
            provider=self.provider_name,
            model=model,
            stop_reason=finish_reason,
            usage=last_usage,
        )
        if finish_reason not in {"stop", "length", "tool_use"}:
            finish_reason = "stop"
        yield FinishEvent(reason=finish_reason, message=assistant)  # type: ignore[arg-type]
