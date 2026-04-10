# context-hygiene — CLAUDE.md

## Project Overview

**Type**: CLI tool / PyPI package
**Language**: Python 3.10+
**Purpose**: Context window hygiene analyzer for LLM conversations — detects staleness, contradictions, deadweight, and compression opportunities
**Owner**: AreteDriver
**PyPI**: `context-hygiene` (v0.2.1)
**License**: BSL-1.1

---

## Architecture

```
context-hygiene/
├── src/context_hygiene/    # Source package
├── tests/                  # pytest suite (398 tests, 92% coverage)
├── scripts/                # Utility scripts
├── dist/                   # Built distributions
├── pyproject.toml          # Package config (setuptools)
├── LICENSE
└── README.md
```

---

## Common Commands

```bash
# Install
pip install -e ".[dev]"

# Test
pytest

# Lint
ruff check . && ruff format .

# Build
python -m build

# Publish (OIDC trusted publish)
twine upload dist/*
```

---

## Coding Standards

- Python 3.10+
- Ruff for linting and formatting
- pytest for testing (398 tests, 92% coverage gate)
- Pydantic for config/models
- setuptools build backend

---

## Dependencies

### Runtime
See `pyproject.toml` [project.dependencies]

### Dev
- pytest
- ruff

---

## CI/CD

PyPI publishing via OIDC trusted publish.

---

## Git Conventions

- Conventional commits: `feat:`, `fix:`, `docs:`, `chore:`
- Branch: main

---

## Security

- BSL-1.1 license with Stripe-gated Pro features
- License validation: local checksum -> 24h cache -> server -> fail-open
- No secrets in source

---

## Domain Context

Part of the AreteDriver AI developer tools suite (anchormd, agent-lint, ai-spend, promptctl, context-hygiene). Stripe billing live. CTHG license key prefix.
