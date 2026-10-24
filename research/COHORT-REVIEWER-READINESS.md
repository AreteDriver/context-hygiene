# External-cohort reviewer readiness

This workflow is independent of detector predictions and does not authorize evaluation.

## Readiness check

From the repository root:

```bash
python -m scripts.cohort_readiness research/external-cohort-pinned-v0.1.json research/external-cohort-eligibility-register-v0.1.json
```

The command prints deterministic JSON. Exit code 1 means the cohort is blocked; exit code 0 means the register satisfies the existing complete eligibility validator. The command does not write files, freeze sources, generate labels, or authorize detector evaluation.

Each source includes a list of missing top-level review fields. The `validation_errors` list provides detailed reviewer and adjudication defects, including invalid timestamps, missing HTTPS evidence, inconsistent eligibility dispositions, and conflicting reviewer identities.

## Reviewer checklist

For each pinned source:

1. Independently verify the pinned source bytes against `source_sha256`.
2. Review file-level license evidence, instruction-content eligibility, and source independence.
3. Record two distinct reviewer identities, timezone-aware review timestamps, decisions, rationales, HTTPS evidence URLs, and hash verification.
4. Resolve disagreements using a third independent adjudicator.
5. Record final dispositions and adjudication only when supported by actual evidence.
6. Rerun readiness checks. Do not freeze until every required review is complete.

Do not fabricate identities, reviews, license determinations, or source labels. A repository-level SPDX value alone is not file-level license evidence. The live register currently contains 20 pending sources.

Readiness is a prerequisite for the separate freeze operation; it is not a detector evaluation authorization.
