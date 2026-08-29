# Python Prime Agent (Phase 1)

Experimental Python port of Prime Agent **core** (providers + agent loop + CLI). The TypeScript packages remain the product. This tree must not modify `packages/*`.

## Status

Phase 0 docs and Phase 1 loop/CLI are in this directory. Kernel, daemon, TUI, sessions on disk, MCP, and RLM host are **not** implemented. Stubs exist only to reserve module paths.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) recommended

## Install

```bash
cd python-prime-agent
uv sync
```

Without uv:

```bash
cd python-prime-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## CLI

```bash
uv run prime-agent-py run --provider mock "Return a deterministic test response"

uv run prime-agent-py run --config configs/ollama.yaml "현재 디렉터리의 Python 파일을 확인하라"
uv run prime-agent-py run --config configs/vllm.yaml "이 프로젝트의 구조를 설명하라"
uv run prime-agent-py run --config configs/lmstudio.yaml "README를 요약하라"
```

Local servers must already be running. If they are not, the CLI prints diagnosis (provider, endpoint, model, timeout, cause, check commands, API key need). That is expected, not a silent failure.

## Tests

```bash
cd python-prime-agent
uv run pytest
```

Tests do not call paid APIs. HTTP is mocked (`respx` or patched `acompletion`).

## Configuration

Copy `.env.example` to `.env` locally. Never commit secrets. Example provider YAML lives in `configs/`. Free-tier model names in examples can become invalid when vendors change catalogs.

## License

MIT (same as the repository root).
