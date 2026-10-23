# FT-CH-002 external cohort: preliminary eligibility review

**Status:** pre-freeze, unlabelled. This review is **not** a detector evaluation.

## Evidence

- The exact replacement manifest has 20 entries, 20 distinct owners, 20 immutable commit IDs, 20 SHA-256 input digests and 20 pinned source URLs. The downloaded manifest is 11,130 bytes, SHA-256 `30577f29eba1d99bdcbeababcf01a09bc2c1f26d98a760e306cbb43405379c22`.
- Repository-level GitHub SPDX metadata: 15 MIT, 3 Apache-2.0, 2 AGPL-3.0. This metadata does not establish the license of each document, or permission to republish its content.
- Smallest pinned file is `Graphify-Labs/graphify/AGENTS.md` (563 bytes); two other short files are `HKUDS/nanobot/AGENTS.md` (1,757 bytes) and `tt-a1i/archify/AGENTS.md` (2,241 bytes).
- The three short root files were inspected as guidance documents, not detector results. Graphify has a heading, a description and multiple instructions; nanobot has a task-specific link table and constraints; archify has task and integration guidance. Shortness alone is **not** grounds for exclusion, but tiny files may have no duplicate pairs and should be reported as such.

## Predeclared inclusion rules

1. A public, non-archived, non-fork repository with a root `AGENTS.md` or `CLAUDE.md` at an immutable commit.
2. The pinned file is human-readable instructions intended to guide coding agents. Links to other files are permitted; linked documents are **out of scope** for this root-file benchmark.
3. No minimum byte or heading count: small and negative-control files remain eligible. Record the distribution of document lengths and positive/negative labels.
4. Repository-level license metadata is descriptive, not sufficient for file-level redistribution. Do not commit copied source text; review exceptions and provenance individually.
5. Exactly one root instruction file per repository; distinct GitHub owners. Record any shared maintainers, templated instructions, or derivative files discovered during review.
6. Selection and exclusions must be determined without viewing duplicate-detector predictions. Human labeling must be performed on frozen source versions, with at least two independent reviewers and documented adjudication.

## Open gates

- [ ] Copy the **exact** sanitized JSON manifest into version control, validating its recorded byte checksum. The workflow artifact expires 2026-10-28.
- [ ] Confirm file-level license applicability and original/derivative provenance across all 20 pinned files.
- [ ] Check for substantive cross-repository shared templates, duplicate ownership or linked project relationships.
- [ ] Review pinned content (not moving default-branch HEAD) for each repository.
- [ ] Freeze candidate list and manifest commit before creating labels.
- [ ] Obtain independent section-pair labels and adjudicate disagreements, blinded to analyzer predictions.

**No accuracy, precision, recall or downstream token-saving claim is supported by this preliminary review.**
