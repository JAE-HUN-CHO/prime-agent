# Sessions

**Not implemented in Phase 1.** TypeScript persists JSONL sessions (`CURRENT_SESSION_VERSION = 3`) via `packages/coding-agent/src/core/session-manager.ts`.

Python holds an in-memory `Session` for a single `run` invocation. Resume, listing, and file format compatibility are Phase 4 work. See `prime_agent_py.persistence`.
