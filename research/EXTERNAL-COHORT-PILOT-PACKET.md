# External-cohort pilot review packet (Issue #32)

**Status: awaiting independent human reviewers.** This packet does not assert any source is eligible or reviewed. It does not authorize a cohort freeze or detector evaluation.

## Pinned source assignments

| Source | Pinned commit | Review A | Review B | Adjudication |
| --- | --- | --- | --- | --- |
| [NousResearch/hermes-agent AGENTS.md](https://github.com/NousResearch/hermes-agent/blob/3a9d585e4f1a60588237587a72d365d187094c74/AGENTS.md) | `3a9d585e4f1a60588237587a72d365d187094c74` | Unassigned | Unassigned | Not started |
| [thedaviddias/Front-End-Checklist AGENTS.md](https://github.com/thedaviddias/Front-End-Checklist/blob/e8d14d049010e2ce25afcd5e8609dfcbbe63e47e/AGENTS.md) | `e8d14d049010e2ce25afcd5e8609dfcbbe63e47e` | Unassigned | Unassigned | Not started |
| [HKUDS/nanobot AGENTS.md](https://github.com/HKUDS/nanobot/blob/130f4edefebdd6e0191fd9f97da930169912dce5/AGENTS.md) | `130f4edefebdd6e0191fd9f97da930169912dce5` | Unassigned | Unassigned | Not started |

## Independent reviewer instructions

1. Work from the exact pinned blob and compare its raw bytes against the corresponding `sha256` in `research/external-cohort-pinned-v0.1.json`. Record verification results; do not assume the GitHub page display is byte-identical.
2. Find and link file-level licensing evidence. The manifest's repository-level SPDX is context only, not proof that the specific file is licensed for this use.
3. Assess whether the file contains instructions relevant to the intended cohort and whether the source is independent of other cohort entries.
4. Independently record actual reviewer ID, timezone-aware timestamp, decision, rationale, HTTPS evidence links, and source hash verification in a proposed change to `research/external-cohort-eligibility-register-v0.1.json`.
5. Do not view or coordinate with the other reviewer's decision before submitting your own. Resolve disagreements through a third independent adjudicator with evidence.
6. Run `python -m scripts.cohort_readiness research/external-cohort-pinned-v0.1.json research/external-cohort-eligibility-register-v0.1.json` and attach the read-only report to the review PR.

## Reviewer handoff questions

- Is the pinned file accessible at its recorded commit, and does its raw SHA-256 match?
- Which exact file-level license evidence URL supports the disposition?
- What specific text supports the instruction-content decision?
- Is the source independent of other entries? What evidence supports this?
- Are there unresolved license, provenance, or adjudication concerns?

## Pilot exit criteria

All three sources have two genuine, independent reviewer records; each has documented source-hash, file-license, content and independence evidence; any disagreement is adjudicated; the pilot's process friction is documented. The other 17 sources remain pending, so the full cohort remains blocked. Never manufacture attestations, final labels, or detector performance claims.
