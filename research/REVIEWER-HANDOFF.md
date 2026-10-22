# External cohort labeling handoff

**Reviewer instructions:** Start with `research/EXTERNAL-COHORT-ELIGIBILITY.md` and `research/EXTERNAL-COHORT-LABELING-PROTOCOL.md`. The pinned source list is `research/external-cohort-pinned-v0.1.json`. Use only the source commit URLs in that manifest, not moving default branches.

Before assigning any duplicate labels, confirm file eligibility, license applicability and the independent-review process. The preliminary content screen in `research/EXTERNAL-COHORT-PRELIMINARY-REVIEW.md` is not an adjudicated eligibility decision. In particular, investigate possible reuse of Ponytail guidance in Codewhale and the short Graphify instructions. Chinese-language instructions require competent language review.

**Required deliverables:** (1) eligibility register with per-file evidence and dispositions; (2) two blind independent label files containing real reviewer IDs and source-line spans; (3) disagreement/adjudication register; (4) frozen label manifest with checksums. Do not record made-up reviewers, labels, or agreement statistics. Do not run the analyzer until labels are frozen.

**Stop condition:** If no independent reviewers are available, keep this research PR in draft. Synthetic tests may continue separately but cannot substitute for external ground truth.
