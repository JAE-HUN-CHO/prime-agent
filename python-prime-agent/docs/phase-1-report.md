# Phase 1 report

## 완료된 기능

- Phase 0 mapping: `docs/migration-map.md`, `docs/architecture.md`, `docs/compatibility.md`
- Pydantic models: messages, `ModelEvent` (`text_delta`, `thinking_delta`, `tool_call_*`, `usage`, `finish`, `error`), usage, tools, in-memory session
- `ModelProvider` protocol; LiteLLM (`acompletion`), OpenAI-compatible, mock; profile registry (`provider_name` / `litellm_model` / `served_model_name`)
- Sequential tool-call agent loop with usage aggregation; loop never parses raw provider payloads
- Typer + Rich CLI `prime-agent-py run`; connection diagnosis (provider, endpoint, model, timeout, cause, check commands, API key need)
- YAML configs for Ollama, vLLM, LM Studio, OpenRouter/Gemini/Groq/Cerebras examples
- Stubs: rlm, kernel, tools, context, persistence, skills, mcp, daemon, harness, api
- Tests without paid APIs (20 passed)

Not implemented (documented as stubs): TUI, daemon, kernel host, RLM spawn, MCP, session JSONL, IPython/bash tools.

## 기존 TypeScript 대응 파일

See `docs/migration-map.md`. Primary sources: `packages/ai/src/types.ts`, `packages/ai/src/stream.ts`, `packages/ai/src/providers/faux.ts`, `packages/agent/src/agent-loop.ts`, `packages/coding-agent/src/core/usage.ts`, `packages/coding-agent/src/core/kernel/*`, `packages/coding-agent/src/modes/daemon/daemon-protocol.ts`, `prime-agent-runtime/src/rlm/*`.

## 테스트 결과

Commands (from `python-prime-agent/`):

```text
uv sync --extra dev
uv run ruff check src tests          # All checks passed
uv run pytest -q                     # 20 passed
uv run prime-agent-py run --provider mock "Return a deterministic test response"
# stdout: deterministic test response  (exit 0)
uv run prime-agent-py run --config configs/ollama.yaml "..."
uv run prime-agent-py run --config configs/vllm.yaml "..."
uv run prime-agent-py run --config configs/lmstudio.yaml "..."
# exit 1 with diagnosis (servers down in this environment; expected)
```

If `uv` is missing: `python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]" && pytest`.

## 호환성

Required Phase 1 behaviors: normalized events, usage fields, tool round-trips, cancel not converted to errors, env API keys, secret redaction, local OpenAI-compatible + Ollama via LiteLLM.

Not compatible: TUI, daemon attach, TS session JSONL resume, per-provider SDK quirks, kernel/RLM host.

## 남은 위험

- LiteLLM wraps some TCP failures as `InternalServerError` (“Connection error”) rather than `APIConnectionError`; CLI still diagnoses via message text.
- Example YAML model slugs (free-tier catalogs) can go stale; they are not hardcoded in Python.
- SSL/repr noise from LiteLLM appears in connection error strings (not secrets).
- Hatch/src layout depends on uv/hatchling auto-discovery of `src/prime_agent_py`.

## 다음 Phase

Python kernel host (`rlm.repl` protocol 3), session JSONL v3, coding tools, RLM `host_request`, daemon capability gates, optional FastAPI.
