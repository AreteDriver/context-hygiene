# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Cross-CLI repository guidance** — `AGENTS.md` is now the canonical project
  guide, with a thin Claude Code compatibility file.
- **Current package metadata** — packaging uses SPDX license metadata and the
  README integration examples target the latest published tag, v0.3.2.

### Fixed
- **License documentation** — removed a stale duplicate README section that
  incorrectly labeled the current license as MIT.

## [0.3.3] - 2026-08-17

### Fixed
- **Package version drift** — runtime version reporting now reads installed package metadata instead of duplicating the version in `__init__.py`.
- **Release tag validation** — tagged releases now fail before publishing when the Git tag and package version do not match.

## [0.3.2] - 2026-07-20

### Added
- **CI grade gates** — `audit --fail-under A|B|C|D|F` returns a non-zero exit code when context quality falls below the configured threshold.
- **Watch mode and ecosystem output** — added `--watch`, SARIF output, shell completions, and GitHub Actions integration.

## [0.3.1] - 2026-07-20

### Added
- **Codex JSONL parser** — parses Codex CLI session exports (`response_item` entries with developer/user roles).
- **Section-based markdown parsing** — `GenericParser` now splits AI instruction files (CLAUDE.md, AGENTS.md) by markdown headers when no role markers exist, enabling hygiene analysis on instruction documents.

### Fixed
- **v0.3.0 release workflow failure** — e2e test `test_audit_then_history_shows_entry` was asserting on a table-truncated filename. Fixed assertion to verify by grade/token values instead.

## [0.3.0] - 2026-07-19

### Added
- **Programmatic API** — `audit_file()` and `score_file()` in `context_hygiene.api` for integrating hygiene analysis into Python scripts without shelling out to the CLI.
- **End-to-end CLI tests** (`tests/test_cli_e2e.py`) covering the full audit → history → clean workflow, SQLite persistence verification, and `--apply` output consistency.
- Before/after demo in README showing real token recovery on a messy conversation.

### Fixed
- **License mismatch** — README now correctly states BSL-1.1 (was incorrectly listed as MIT).
- **`clean` double-parse bug** — `clean` no longer re-parses the source file when building the pruning plan. Segments from the initial audit pass are reused, eliminating race conditions and ensuring consistency.
- **`estimate_tokens()` exception handler** narrowed from bare `Exception` to `(ImportError, ModuleNotFoundError, KeyError, OSError)` so unexpected runtime errors surface correctly.

## [0.2.1] - 2026-03-13

### Fixed
- Dependency override for `vite` to resolve security advisory.
- Minor CLI output formatting issues.

## [0.2.0] - 2026-03-08

### Added
- Initial release with four heuristic analyzers: staleness, contradictions, deadweight, and compression.
- TypeScript and Python SDKs for on-chain logging.
- CLI verifier tool.
- Next.js dashboard deployed on Vercel.
- Model version pinning and dead man's switch contracts.
