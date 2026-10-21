# Exact-duplicate benchmark protocol (v0.1)

**Status:** prospective protocol; no external-cohort accuracy results yet.

## Scope and claims

Measure whether the **fast** analyzer correctly flags exact repeated parser segments in Markdown instruction files. This is *not* a benchmark of semantic redundancy, safe deletion, useful context compression, agent behavior, or token billing. Synthetic unit controls test known behavior; the external cohort must be analyzed separately.

## Sampling and provenance

1. Before running the detector, select at least **20** publicly accessible, independently maintained repositories with root `AGENTS.md` or `CLAUDE.md` files. Use a reproducible discovery method (query, date, ordering, eligibility criteria) and record **all** screened candidates, including exclusions. Avoid selecting files based on analyzer findings.
2. Cap selection at one file per repository; disclose any common ownership or fork relationships. Record repository URL, commit SHA, path, SHA-256, license, and retrieval timestamp. Never execute upstream code or install upstream dependencies.
3. Freeze the cohort manifest and protocol before inspecting predictions. Do not alter labels to match predictions. Keep a held-out subset for follow-up changes.
4. Do not publish full upstream file contents or private audit logs. Link to pinned upstream sources; retain hashes and aggregate results.

## Ground truth

For each file, two reviewers independently label **section-level exact duplicate pairs** after examining original Markdown boundaries and fenced blocks, without seeing analyzer predictions. Labels must include: duplicate section pair (source line ranges), not duplicate, or ambiguous. Resolve disagreements with recorded reasons; report initial agreement and adjudicated labels separately. If independent human review is unavailable, label the cohort *provisional* and do not claim human-validated precision/recall.

A pair is a positive only when the entire logical section is byte-identical after the explicitly declared newline normalization. Repeated snippets within different sections, Python comments inside code fences, short acknowledgments, and semantically similar text are not positives under this definition. A detector fragment matching only part of a logical section must not count as a true-positive section detection.

## Scoring

Map predictions to original source line ranges. Count a predicted pair as TP only if it matches a labeled complete duplicate section pair; otherwise FP. Each labeled positive not matched is FN. Use unique pairs and a one-to-one matching rule to avoid double-counting fragments. Report TP, FP, FN, precision = TP/(TP+FP), recall = TP/(TP+FN), and F1. When a denominator is zero, report **undefined**, not 100%. Report 95% confidence intervals where sample size permits; show raw per-file counts and aggregate micro-averages. Also report number of files with no labeled duplicates and the number with any false positive.

Track parser segment count, false headings from fenced code, source preservation (including code-fence delimiters), and changes relative to v0.3.2 as **secondary** measurements. Keep token-proxy estimates distinct from tokenizer counts and from realized runtime savings.

## Negative controls and safety

Include clean unique-section files, repeated *similar but nonidentical* sections, nested/long backtick and tilde fences, headings within code blocks, and repeated sections that may be intentionally retained. A detector match does not authorize deletion: authorship intent, references, and downstream effects require separate review. Never automatically modify upstream repositories.

## Reproducibility gate

Record analyzer source commit, installed distribution/version, Python version, dependencies, input hashes, CLI command, telemetry setting, exit codes, and machine-readable output hashes. Publish sanitized per-file outcomes and a discrepancy register. Mark any network failure, parser failure, or unreviewed label as missing evidence rather than a negative result. Review the cohort and methodology before promoting any accuracy claim into marketing or the portfolio.
