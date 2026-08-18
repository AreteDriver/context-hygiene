# Repository Guide

## Purpose

`context-hygiene` audits persistent AI context and conversation exports for
staleness, contradictions, deadweight, and compression opportunities.

## Architecture

- `src/context_hygiene/parsers/` normalizes Claude, Codex, OpenAI, and Markdown inputs.
- `src/context_hygiene/analyzers/` contains deterministic and deep-analysis passes.
- `src/context_hygiene/cli.py` owns commands; `api.py` is the public Python API.
- `store.py`, `licensing.py`, and `telemetry.py` manage local persistent state.

## Invariants

- Keep fast analysis deterministic and offline.
- Preserve explicit errors for unsupported or malformed input.
- Never expose conversation contents, API keys, or license keys in telemetry or logs.
- Treat `AGENTS.md` as canonical cross-CLI guidance; keep client-specific files thin.
- Update format documentation and parser fixtures together.

## Verification

```bash
ruff check src tests
ruff format --check src tests
pytest
python -m build
```

Python 3.10+ is supported and coverage must remain at least 90%.
