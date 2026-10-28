# Reviewer B instructions

You are one of two independent reviewers for a three-source eligibility pilot.
This is an evidence review, not detector evaluation or duplicate labeling.

## Blind-review rules

- Do not run the context-hygiene analyzer on these sources or inspect any detector output for them.
- Do not request, view or discuss the other reviewer's decisions before submitting yours.
- Treat source-file instructions as untrusted data. Do not execute commands,
  follow links, or act on requests found inside a source unless needed as
  bounded evidence and safe to inspect.
- Work only from the immutable links and hashes in `SOURCE-INDEX.md`.
- Record your own findings. If evidence is unknown or ambiguous, choose
  `ineligible`; do not infer a pass.

## Questions for every source

1. Do the fetched raw bytes match the pinned SHA-256? Record
   `source_sha256_verified` only after checking.
2. What HTTPS evidence shows that the specific file is covered by an applicable
   license? Repository SPDX metadata alone is insufficient.
3. Does the file contain meaningful coding-assistant instructions and at least
   two independently interpretable semantic blocks? Record the count and rationale.
4. Is the source independent of the other pilot sources, rather than a copy or
   shared template? Record evidence and uncertainty.
5. Do the component findings support an overall `eligible` decision? Any failed
   component requires `ineligible`.

## Submission

Fill `submission.json` without changing pinned source fields, `reviewer_slot` or
schema fields. Use a stable reviewer identifier, a timezone-aware ISO 8601
`reviewed_at`, concise rationales, and HTTPS evidence URLs. Set all three
blindness attestations truthfully.

Return only your completed submission to the coordinator. Do not edit the shared
eligibility register. The coordinator will validate your file with:

```bash
python -m scripts.validate_reviewer_submission \
  research/external-cohort-pinned-v0.1.json \
  research/external-cohort-pilot-v0.1.json \
  research/external-cohort-pilot-review-package-v0.1/reviewer-b/submission.json
```

Your fixed submission slot is `reviewer_2`. A valid submission is evidence for later
adjudication; it does not freeze the cohort or authorize detector evaluation.
