# Architecture (Python Prime Agent)

Phase 1 implements a **provider + agent loop + CLI** slice. Later phases add kernel host, sessions, tools, daemon, and TUI.

## Layers

```text
CLI (Typer + Rich)
  AgentRunner / agent loop
    ModelProvider (Protocol)
      MockProvider | LiteLLMProvider | OpenAICompatibleProvider
    AgentTool registry (minimal)
  Config (YAML + pydantic-settings)
  Observability (structlog, secret masking)
  Stubs: rlm, kernel, tools, context, persistence, skills, mcp, daemon, harness, api
```

There is no new agent framework. The loop is a direct, reduced port of `packages/agent/src/agent-loop.ts`: stream a completion, execute tool calls, append results, repeat until the model stops or hits a turn limit.

## Provider contract

`ModelProvider.complete` always yields `ModelEvent`. Failures that are not `asyncio.CancelledError` become `error` events (and/or a typed `ProviderError` for connection diagnostics). Cancellation is never converted into an error event.

LiteLLM is the default adapter for remote and local OpenAI-shaped servers. Profiles distinguish:

- `provider_name` — user-facing name (`ollama`, `vllm`, `groq`)
- `litellm_model` — LiteLLM model string (`ollama/qwen3:30b`, `openai/served-name`)
- `served_model_name` — name the local server expects, when different from the LiteLLM id

## Config

YAML files under `configs/` are the source of truth for endpoints and model ids. Free-tier model names and quotas are **not** hardcoded in Python. They can change on the vendor side; treat YAML examples as snapshots.

Remote Ollama/vLLM/LM Studio endpoints are unauthenticated HTTP by default. Do not expose them on the public internet without a reverse proxy and auth. See comments in those YAML files.

## Async

Public I/O is asyncio. HTTP goes through LiteLLM/`httpx`. Do not call blocking SDK methods on the event loop. Timeouts use `asyncio.timeout`. Retries are explicit and bounded.

## Stubs

Stub modules raise `NotImplementedError` with a phase note. They exist so import paths and later ports stay stable. They do **not** implement kernel execution, session files, or MCP.

## Relationship to prime-agent-runtime

`prime-agent-runtime` is the **kernel-side** Python package (`import rlm`). The TypeScript coding-agent is the host. A future Python host will speak the same JSONL protocol (`repl.md`). This package must not fork that protocol.
