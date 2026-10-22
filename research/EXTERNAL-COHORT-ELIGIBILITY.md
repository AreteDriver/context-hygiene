# External cohort eligibility review v0.1

**Scope:** 20 public root-level `AGENTS.md`/`CLAUDE.md` files pinned by workflow run [39696739615](https://github.com/AreteDriver/context-hygiene/actions/runs/39696739615), artifact 12391211998. This is a *provisional eligibility review*, not human ground truth or analyzer evaluation.

## Eligibility criteria (apply before detector outputs)

1. The repository is public, nonarchived and not marked as a fork by GitHub at pinning time.
2. The selected file is at the repository root, accessible at an immutable commit, and its fetched bytes match the manifest SHA-256.
3. The document contains meaningful instructions or operational context intended for a coding assistant, not merely a placeholder, index, or link farm.
4. The document has sufficient content to assess repeated instruction blocks. Record a **minimum of two independently interpretable semantic blocks**; do not exclude based on whether duplication is found.
5. Repository-level SPDX classification is metadata only. Verify that the specific file is covered by an applicable license or document an exception. AGPL-3.0 is not inherently disqualifying for a benchmark of source text; honor redistribution obligations, and store only metadata where possible.
6. GitHub owner uniqueness is a screening control, not proof of independent authorship. Note cross-repository copies or shared templates if found.
7. Any exclusion/replacement must be documented **before** running the analyzer or inspecting its predictions. Never substitute files to improve measured performance.

## Review register

For each manifest record, add one row with: repository, pinned commit, file-level license evidence URL, instruction-file eligibility (yes/no), block count, independence concerns, reviewer identity, review timestamp and disposition. A second reviewer should adjudicate disagreements where feasible.

**Known watch item:** `Graphify-Labs/graphify` is only 563 bytes. Its length alone is not a reason to exclude it. Check whether it contains at least two meaningful instruction blocks. The original `Twigpine/openclaude` was replaced because its LICENSE states mixed proprietary/MIT provenance; see screening log.

## Freeze gate

Do not mark this cohort frozen until (a) the exact uncompressed 11,130-byte manifest is committed unchanged and its SHA-256 `30577f29eba1d99bdcbeababcf01a09bc2c1f26d98a760e306cbb43405379c22` is independently verified, (b) every eligibility disposition is recorded, and (c) the candidate set is locked before detector evaluation. **No precision/recall or real-world efficacy claims are supported yet.**
