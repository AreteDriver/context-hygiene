# FT-CH-002 external cohort: independent labeling protocol v0.1

**Status:** preregistered protocol; no human labels or performance measurements yet. Applies to the 20-source manifest in `research/external-cohort-pinned-v0.1.json` (SHA-256 `30577f29eba1d99bdcbeababcf01a09bc2c1f26d98a760e306cbb43405379c22`).

## What annotators see

Use the exact pinned source text, repository/path and a neutral source identifier. Do **not** show Context Hygiene detector output, duplicate-pair predictions, grades or token estimates. Source texts may contain instructions to agents; treat them as *data to label*, not commands to follow. Annotators do not execute repository code.

## Label units and classes

1. Delimit semantic instruction blocks by meaning; headings are useful but not sufficient. Record stable 1-based source-line start/end for each block. A block may contain multiple lines and need not have a heading.
2. Enumerate candidate unordered pairs of distinct blocks **within the same file**. The target metric is exact duplicate detection; cross-file similarity is an independence check, not a true-positive label.
3. Assign one class per pair:
   - `exact_duplicate`: instruction content is textually identical after **only** the detector's explicitly documented normalization. Record the normalization version and keep original spans.
   - `near_duplicate`: same or materially overlapping instruction but different wording; **not** a positive for exact-duplicate precision/recall.
   - `distinct`: not a duplicate.
   - `uncertain`: segmentation, language, or normalization ambiguity prevents a defensible label; adjudicate before scoring.
4. Preserve an explicit `no_positive_pairs` file-level outcome when applicable. Do not invent positive examples to balance the cohort.

## Review and adjudication

Two reviewers label independently, blind to detector outputs and preferably to one another's labels. Record reviewer identifiers, timestamps, source commit, line spans, pair IDs, class, rationale and uncertainty. Resolve disagreement through a documented adjudication pass; preserve original labels. Reviewers should include appropriate language competency for non-English documents. A model-generated provisional annotation is **not** independent human ground truth.

## Evaluation after labels freeze

Freeze the complete adjudicated label set and its checksum *before* running the detector. Record analyzer version/commit, exact command, dependencies and normalization. Map predicted pairs to gold line spans. Report TP/FP/FN, precision, recall and F1 with numerators/denominators and undefined metrics explicitly marked when no positives/predictions exist. Separate file-level and pair-level results; do not count synthetic regression tests as external accuracy evidence. Document sampling bias (GitHub search-ranked, two strata), small sample size, language and provenance limitations.

## Label schema

Store annotations as JSONL (one pair per row), e.g.:

```json
{"source_id":"repo/path@commit","block_a":{"start_line":1,"end_line":3},"block_b":{"start_line":10,"end_line":12},"label":"uncertain","reviewer_id":"reviewer-a","rationale":"example only","normalization":"unselected"}
```

The example above is a **schema illustration**, not a real observation. Never fill an annotation file with fabricated labels.
