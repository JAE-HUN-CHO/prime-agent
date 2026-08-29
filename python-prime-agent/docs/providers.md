# Providers (Phase 1)

Python uses **LiteLLM** instead of the TypeScript per-API clients (`openai-completions`, `anthropic-messages`, `bedrock-converse-stream`, …).

## Profiles

Each YAML profile has:

- `type`: `litellm`, `openai_compatible`, or `mock`
- `model`: LiteLLM model id (`litellm_model`)
- optional `served_model_name` when the HTTP `model` field differs
- optional `api_base`, `api_key_env`, `timeout_seconds`, `max_retries`, `extra_params`

Free-tier model slugs and rate limits are **not** encoded in Python. Example YAML can go stale when vendors change free catalogs.

## Mock

`--provider mock` does not call the network. It is for CLI smoke tests and unit tests.

## Local servers

| Config | Default endpoint | Notes |
|--------|------------------|--------|
| `configs/ollama.yaml` | `http://localhost:11434` | Ollama HTTP API via LiteLLM `ollama/` |
| `configs/vllm.yaml` | `http://localhost:8000/v1` | OpenAI-compatible |
| `configs/lmstudio.yaml` | `http://localhost:1234/v1` | OpenAI-compatible |

If the process is down, the CLI prints provider name, endpoint, model, timeout, cause, check commands, and whether an API key is required. Failures are not hidden.

**Security:** binding Ollama/vLLM/LM Studio on a non-localhost interface without authentication exposes the model API. Prefer localhost. Treat remote URLs as untrusted networks.

## Cloud examples

`openrouter-free.yaml`, `gemini.yaml`, `groq.yaml`, `cerebras.yaml` document env var names only. Never commit keys. Quotas change; see vendor docs.

`configs/openrouter-free.yaml` uses LiteLLM model `openrouter/openrouter/free` (OpenRouter native id `openrouter/free`). That is OpenRouter's free-model router, not a frozen list of slugs. Which models are free, and the quota, can change on the vendor side. `openrouter/auto` (`openrouter/openrouter/auto` in LiteLLM) can route to paid models and does not belong in this profile.
