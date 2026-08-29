# Compatibility with TypeScript Prime Agent

Levels: **required** (Phase 1 must match intent), **best-effort** (same idea, different shape), **not compatible** (explicitly deferred).

## Required (Phase 1)

| Behavior | TS source | Python |
|----------|-----------|--------|
| Normalized model events, not raw HTTP bodies in the agent loop | `packages/ai` stream events | `ModelEvent` only |
| Usage fields: input, output, cache read/write, total | `Usage` in `types.ts` | `Usage` + `reasoning_tokens` optional |
| Tool round-trips until stop | `agent-loop.ts` | `agent.loop` |
| Abort/cancel is not an application error | abort → `stopReason: aborted` | `CancelledError` propagated; optional `error` only if the provider already failed |
| API keys from environment | `env-api-keys.ts` | env + optional `api_key_env` on profile |
| Secret masking in logs | diagnostics utilities | `observability.secrets` |
| Local OpenAI-compatible servers (vLLM, LM Studio) | openai-completions + baseUrl | LiteLLM `openai/` + `api_base` |
| Ollama via LiteLLM | not first-class TS API | `ollama/` model prefix |

## Best-effort

| Behavior | Gap |
|----------|-----|
| Event granularity (`text_start`/`text_end`, `start`/`done`) | Phase 1 uses deltas + `finish` |
| Per-provider quirks (Anthropic cache_control, Bedrock SDK, Google thought signatures) | LiteLLM mapping only |
| Cost accounting | Usage tokens only; cost stays 0 unless a later phase ports pricing |
| Tool execution parallel vs sequential | Phase 1 sequential |
| Steering / follow-up / continuation queues | Not in Phase 1 loop |
| `convertToLlm` / `transformContext` | Identity conversion |
| Model catalog / featured models | YAML profiles only |
| Session header v3 JSONL | Documented, not written |

## Not compatible (this phase)

- Interactive TUI (`packages/tui`, interactive mode)
- Daemon protocol live server (v7 / schema 23)
- Kernel client + `python -m rlm.repl` host
- RLM spawn (`rlm.run`) from Python host
- MCP client manager
- Skills / extensions / compaction / context tree
- OAuth (Anthropic, Copilot, Codex)
- Generated `models.generated.ts` catalog
- Print/RPC/ACP modes
- Chrome extension / browser smoke
- Claiming kernel isolation is a sandbox

## Wire / file compatibility

Python Phase 1 **cannot** attach to a running TypeScript daemon or resume a TS session JSONL file. Those are later phases. Event JSON produced by the Python CLI is a Python-native `ModelEvent` dump, not the TS `AssistantMessageEvent` schema.
