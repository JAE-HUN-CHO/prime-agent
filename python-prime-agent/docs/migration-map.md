# TypeScript to Python migration map

This document maps the Prime Agent TypeScript implementation (behavioral spec) to `python-prime-agent`. Layout follows the Phase 0/1 target; deviations are listed at the end.

Python does **not** rewrite every TypeScript provider 1:1. Provider I/O goes through LiteLLM (`litellm.acompletion`) plus an OpenAI-compatible profile and a mock provider. The agent loop consumes only `ModelEvent` objects.

## Layout vs target spec

| Target | Status |
|--------|--------|
| `src/prime_agent_py/` package | Implemented |
| `configs/*.yaml` | Implemented |
| `experiments/` placeholders | Implemented |
| `tests/` unit, integration, contract, e2e, fixtures | Implemented |
| `docs/` | Implemented |

No layout deviations were required.

## TS modules → Python modules

| TypeScript | Python (Phase 1) | Notes |
|------------|------------------|--------|
| `packages/ai/src/types.ts` | `prime_agent_py.models` | Messages, usage, tools, events. Event names use Phase 1 names (`tool_call_*`, `finish`) rather than TS `toolcall_*` / `done`. |
| `packages/ai/src/utils/event-stream.ts` | `prime_agent_py.models.events` | Async iterator of `ModelEvent`; no `EventStream` class in Phase 1. |
| `packages/ai/src/stream.ts` | `prime_agent_py.providers.protocol` + registry | `stream` / `complete` become `ModelProvider.complete(..., stream=True)`. |
| `packages/ai/src/providers/*` | `prime_agent_py.providers.litellm_provider`, `openai_compat` | Not ported per-API. LiteLLM covers OpenAI-shaped APIs. |
| `packages/ai/src/providers/faux.ts` | `prime_agent_py.providers.mock` | Deterministic tests. |
| `packages/ai/src/api-registry.ts` | `prime_agent_py.providers.registry` | Profile registry: `provider_name` vs `litellm_model` vs `served_model_name`. |
| `packages/ai/src/env-api-keys.ts` | `prime_agent_py.providers.credentials` | Env lookup + secret masking. No OAuth in Phase 1. |
| `packages/ai/src/models.ts` / `models.generated.ts` | Not generated | Model catalogs stay in YAML profiles. |
| `packages/agent/src/types.ts` | `prime_agent_py.agent.loop` (`AgentLoopConfig`, `AgentTool`) + `prime_agent_py.models.tools` (`ToolDefinition`) | No `agent.types` module. No declaration-merging custom messages. |
| `packages/agent/src/agent-loop.ts` | `prime_agent_py.agent.loop` | Minimal tool-call loop + usage aggregation. No steering/follow-up/continuation queues. |
| `packages/agent/src/agent.ts` | `prime_agent_py.agent.runner` | Thin runner over the loop. |
| `packages/coding-agent/src/core/usage.ts` | `prime_agent_py.models.usage` | `empty_usage` / `add_usage` / `clone_usage`. |
| `packages/coding-agent/src/core/session-manager.ts` | `prime_agent_py.persistence` stub | JSONL session format documented; not implemented. |
| `packages/coding-agent/src/core/kernel/*` | `prime_agent_py.kernel` stub | Host is TypeScript today; Python host is later. |
| `packages/coding-agent/src/core/rlm-runtime.ts` | `prime_agent_py.rlm` stub | Host request types only. |
| `prime-agent-runtime/src/rlm/*` | Reuse later; `prime_agent_py.rlm` notes the import path | Kernel-side Python stays in `prime-agent-runtime`. |
| `packages/coding-agent/src/core/tools/*` | `prime_agent_py.tools` stub | IPython/bash/edit not wired. |
| `packages/coding-agent/src/core/compaction/*` | `prime_agent_py.context` stub | |
| `packages/coding-agent/src/core/skills.ts` | `prime_agent_py.skills` stub | |
| `packages/coding-agent/src/core/mcp/*` | `prime_agent_py.mcp` stub | |
| `packages/coding-agent/src/modes/daemon/*` | `prime_agent_py.daemon` stub | Protocol constants copied for mapping, not a live daemon. |
| `packages/coding-agent/src/core/prompts/rlm.ts` + harness | `prime_agent_py.harness` stub | |
| `packages/coding-agent/src/modes/rpc/*` | `prime_agent_py.api` stub | |
| `packages/tui` | Not ported | CLI uses Typer + Rich. TUI is reference only. |
| `packages/coding-agent/src/modes/interactive/*` | Not ported | |
| `packages/coding-agent/src/core/logging.ts` / telemetry | `prime_agent_py.observability` | structlog + secret masking. |

## Major classes / interfaces

| TS | Python |
|----|--------|
| `Message`, `UserMessage`, `AssistantMessage`, `ToolResultMessage` | `UserMessage`, `AssistantMessage`, `ToolResultMessage` (Pydantic) |
| `AssistantMessageEvent` | `ModelEvent` discriminated union |
| `StreamFunction` / `streamSimple` | `ModelProvider.complete` |
| `Tool` / `AgentTool` | `ToolDefinition` + `AgentTool` |
| `AgentLoopConfig` | `AgentLoopConfig` (reduced) |
| `Agent` | `AgentRunner` |
| `ReplKernelManager` | stub `KernelClient` |
| `HostRequestHandler` | stub type alias |
| Daemon protocol v7 / schema 23 | stub constants |

## Event flow (Phase 1)

```text
CLI prompt
  -> AgentRunner.run
    -> ModelProvider.complete (normalized ModelEvent stream)
      text_delta / thinking_delta / tool_call_* / usage / finish | error
    -> if finish with tool calls: execute AgentTool, append tool results, loop
    -> aggregate Usage across turns
  -> Rich prints deltas; errors print diagnostics (never swallowed)
```

The agent loop does **not** parse raw LiteLLM/OpenAI payloads.

TypeScript emits `start` / `text_start` / `*_end` / `done`. Phase 1 collapses streaming to deltas plus `finish`/`error` so LiteLLM chunk mapping stays small. Restoring the full TS event set is a later phase.

## Session lifecycle

TypeScript (`session-manager.ts`): JSONL file, header `{type:"session", version:3, id, timestamp, cwd, ...}`, then entries (`message`, `custom_message`, `model_change`, …). Current version constant: `CURRENT_SESSION_VERSION = 3`.

Python Phase 1: in-memory `Session` model only. Persistence is stubbed (`NotImplementedError` with a pointer to Phase 4). See `docs/sessions.md`.

## Kernel protocol

Kernel is `python -m rlm.repl` (newline-delimited JSON, protocol version 3). Spec: `prime-agent-runtime/src/rlm/repl.md`.

TypeScript host: `packages/coding-agent/src/core/kernel/repl-manager.ts` (`REPL_PROTOCOL_VERSION = 3`). Requests: `execute`, `interrupt`, `host_reply`, `snapshot`, `restore`, `list_names`, `shutdown`. Events: `ready`, `stdout`/`stderr`, `result`, `display`, `host_request`, `error`, `done`.

Phase 1: stub only. The kernel is **not** a sandbox; docs must not call it one.

## RLM host requests

Kernel Python (`prime-agent-runtime/src/rlm/__init__.py`) calls `host_request(type, payload)`. Host replies `{status:"ok","result":...}` or `{status:"error","error":...}`.

Known types from `rlm-runtime.ts` / `__init__.py`:

- `rlm.run` → spawn child agent
- `rlm.find_models`
- `rlm.list_subagents`
- `rlm.delete_subagent`

Plus harness / goal types used by the TS host (not implemented in Python Phase 1).

Reusable runtime files (keep in `prime-agent-runtime`, do not copy into this package unless a later phase needs a vendored subset):

- `src/rlm/repl.py`, `repl.md` — kernel protocol
- `src/rlm/__init__.py` — host bridge + `rlm` callable
- `src/rlm/bash.py`, `harness.py`, `mcp.py`, `mcp_base.py`, `skill.py`

Host-dependent parts require a Python host later. Phase 1 stubs `prime_agent_py.rlm`.

## Daemon protocol

`packages/coding-agent/src/modes/daemon/daemon-protocol.ts`:

- `DAEMON_PROTOCOL_NAME = "prime-agent.daemon"`
- `DAEMON_PROTOCOL_VERSION = 7`
- `DAEMON_SCHEMA_REVISION = 23`

JSONL local transport. Capability-gated commands. Phase 1 stubs constants only. New wire commands stay out of startup (same rule as TS).

## Storage formats

| Artifact | TS location | Python Phase 1 |
|----------|-------------|----------------|
| Session JSONL | `~/.prime/agent/` (via coding-agent config) | stub |
| Auth `auth.json` | coding-agent auth storage | env + `.env.example` only |
| Kernel snapshot dill + manifest | kernel snapshot config | stub |
| Settings YAML/JSON | settings-manager | YAML provider configs under `configs/` |

## Out of scope (Phase 1)

Interactive TUI, daemon attach, OAuth, MCP live servers, IPython tool, compaction, skills loading, extensions, RPC mode, browser, Chrome extension, generated model catalog, per-provider Anthropic/Bedrock/Google SDKs.

## Compatibility summary

See `docs/compatibility.md` for required / best-effort / not compatible.
