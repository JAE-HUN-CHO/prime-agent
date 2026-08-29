# Changelog

All notable changes to `python-prime-agent` are documented here.

## Unreleased

- Added Phase 0 mapping docs and a Phase 1 Python port of the provider protocol, LiteLLM/OpenAI-compatible adapters, mock provider, minimal tool-call agent loop, and Typer CLI.
- Documented Phase 1 verification in `docs/phase-1-report.md`.
- Pointed `configs/openrouter-free.yaml` at LiteLLM `openrouter/openrouter/free` instead of `openrouter/openrouter/auto`, which can select paid models.
- Fixed non-streaming multi tool-call assembly when OpenAI-style items omit `index`.
