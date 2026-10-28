# Pilot review coordinator guide

**State:** ready to distribute; no reviewers are assigned and no review is complete. This package does not authorize a cohort freeze or detector evaluation.

## Before distribution

1. Recruit two humans who can assess software-document licensing, coding-assistant instruction content and cross-source provenance. Verify their identities and conflicts outside this repository.
2. Give one person only the `reviewer-a` directory and the other only the `reviewer-b` directory. Do not give either reviewer the other person's submission or any detector output for these sources.
3. Keep the files separate until both reviewers have returned complete submissions. Reviewer identifiers are provenance records, not identity authentication.
4. Do not prefill decisions, rationales, attestations or identities. Do not ask a reviewer to agree with an expected result.

The invitation in `INVITATION.md` is a draft for individual outreach. Sending it is a separate external action.

## Verify the distributed files

From the repository root, confirm that both packets still match the pinned manifest and pilot selection:

```bash
python -m scripts.build_reviewer_package \
  research/external-cohort-pinned-v0.1.json \
  research/external-cohort-pilot-v0.1.json \
  research/external-cohort-pilot-review-package-v0.1 \
  --check
```

## Validate returned submissions

Validate each file when it arrives. This is expected to fail on the unfilled templates:

```bash
python -m scripts.validate_reviewer_submission \
  research/external-cohort-pinned-v0.1.json \
  research/external-cohort-pilot-v0.1.json \
  path/to/returned-submission.json
```

After both arrive, validate the pair together to require distinct slots and reviewer identifiers:

```bash
python -m scripts.validate_reviewer_submission \
  research/external-cohort-pinned-v0.1.json \
  research/external-cohort-pilot-v0.1.json \
  path/to/reviewer-a-submission.json \
  path/to/reviewer-b-submission.json
```

Passing validation confirms structure, exact source bindings and internally consistent attestations. It does not authenticate identities, establish that evidence is true, adjudicate disagreements, update the live register, freeze the cohort or authorize detector evaluation. Review the cited evidence manually before importing anything. A third independent adjudicator is required for disagreements.
