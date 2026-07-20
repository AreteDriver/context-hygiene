# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
