# Cohort manifest retention and freeze checklist

The GitHub Actions `external-cohort-pinned` artifact is retained for only seven days. Before a cohort is frozen, copy the **sanitized metadata JSON** from the *latest successful run for the final candidate list* into `research/external-cohort-pinned-v0.1.json` in a separate reviewable commit. Never commit the source files, raw analyzer outputs, or private context.

**Required checks before freezing**

- [ ] Final candidate list has exactly 20 distinct repositories; substitutions are documented.
- [ ] Latest successful workflow artifact matches the final candidate-list commit.
- [ ] Each source commit is immutable, each SHA-256 corresponds to the fetched bytes, and source URLs are pinned.
- [ ] Confirm license and provenance for each file; do not infer content license solely from GitHub's repository-level SPDX field.
- [ ] Check fork/archived status, ownership independence and instruction-file eligibility; log exclusions.
- [ ] Preserve the complete sanitized manifest in Git with a checksum and explicit `pinned_unlabeled` status.
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
