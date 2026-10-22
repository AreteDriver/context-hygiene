# Cohort manifest retention and freeze checklist

The GitHub Actions `external-cohort-pinned` artifact is retained for only seven days. Before a cohort is frozen, copy the **sanitized metadata JSON** from the *latest successful run for the final candidate list* into `research/external-cohort-pinned-v0.1.json` in a separate reviewable commit. Never commit the source files, raw analyzer outputs, or private context.

**Required checks before freezing**

- [ ] Final candidate list has exactly 20 distinct repositories; substitutions are documented.
- [ ] Latest successful workflow artifact matches the final candidate-list commit.
- [ ] Each source commit is immutable, each SHA-256 corresponds to the fetched bytes, and source URLs are pinned.
- [ ] Confirm license and provenance for each file; do not infer content license solely from GitHub's repository-level SPDX field.
- [ ] Check fork/archived status, ownership independence and instruction-file eligibility; log exclusions.
- [ ] Preserve the complete sanitized manifest in Git with a checksum and explicit `pinned_unlabeled` status.
- [ ] Run the eligibility validator with `--require-complete`; pending decisions, malformed reviewer provenance, duplicate reviewer identities and unadjudicated conflicts must fail closed.
- [ ] Generate the deterministic metadata-only eligibility freeze with `scripts/freeze_eligible_cohort.py`; retain its printed SHA-256 in the review record.
- [ ] Ground-truth section-pair labels are created independently of detector predictions and disagreements documented.
- [ ] Freeze a manifest commit before any detector evaluation. Record analyzer source commit, dependency versions and exact commands.

The prior artifact `12389243818` belongs to the **superseded** candidate list containing `Twigpine/openclaude`. It must not be used as the final manifest after that repository's substitution.

## Exact artifact validation

The replacement manifest from workflow run `39696739615`, artifact `12391211998`, is the only currently accepted candidate for durable storage. Its **uncompressed JSON** is 11,130 bytes, SHA-256 `30577f29eba1d99bdcbeababcf01a09bc2c1f26d98a760e306cbb43405379c22`. After extracting the artifact and **before committing** the JSON, run:

```bash
python scripts/validate_benchmark_manifest.py \
  --expected-sha256 30577f29eba1d99bdcbeababcf01a09bc2c1f26d98a760e306cbb43405379c22 \
  research/external-cohort-pinned-v0.1.json
```

Do not replace this file with a generated approximation, blank placeholder, or a newer run's manifest without explicitly recording the new checksum and reviewing the change. Passing structural validation does not substitute for content licensing and human ground-truth labels.

## Review queue for file-level eligibility

Use the exact manifest's `source_url` for each item; inspect **the pinned commit**, not the moving default branch. Record reviewer, date, evidence, verdict and exclusion reason before unblinding detector output.

- **Priority license review:** `CherryHQ/cherry-studio` and `siyuan-note/siyuan` have AGPL-3.0 repository metadata; confirm the proposed use of their instruction text is compatible with the evaluation and any redistribution. The remaining SPDX values are repository metadata, not file-level grants.
- **Short-file eligibility:** `Graphify-Labs/graphify` (563 bytes), `HKUDS/nanobot` (1,757 bytes), `tt-a1i/archify` (2,241 bytes), and `DietrichGebert/ponytail` (2,721 bytes). Do not discard short files post hoc based on detector output; declare a minimum structure criterion first, and preserve exclusions transparently.
- **Independence:** distinct GitHub owner logins do not establish independently authored instructions. Check for generated templates, copied boilerplate, common contributors and organizational relationships before treating the 20 documents as independent samples.
- **Ground truth:** label exact-duplicate section pairs against a written annotation protocol. Use independent reviewers and adjudicate disagreement without seeing detector predictions. Only then compute pair-level precision and recall, with confidence intervals and a clearly scoped sampling frame.

This queue is **not** a completed file-level review.
