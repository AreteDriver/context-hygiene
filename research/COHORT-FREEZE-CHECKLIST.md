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
