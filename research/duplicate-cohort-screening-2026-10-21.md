# External duplicate-detection cohort — screening log (in progress)

**Status:** 12 screened, 8 provisional candidates, 4 excluded. **Not frozen or labeled. No accuracy claim.**

## Discovery rule

GitHub repository search `topic:ai-agent stars:>100`, ordered by GitHub's default search relevance, page 1, first 12 results, screened 2026-10-21. For each result, check root `AGENTS.md` first, then root `CLAUDE.md` if absent. Exclude when neither exists. Do not select based on analyzer findings. This discovery stratum is AI-agent-focused and not representative of all software repositories. Expand to other strata before freezing the 20-repository cohort.

The file blob SHA below verifies which Git blob was observed, but is **not** a pinned commit SHA or a SHA-256 of the file contents. These must be recorded independently before evaluation. License, fork status, owner independence and content eligibility also remain unverified. Do not label or run the detector until the manifest is frozen.

| Search rank | Repository | Root file | Git blob SHA | Screen |
|---:|---|---|---|---|
| 1 | NousResearch/hermes-agent | AGENTS.md | `4c4ce5c04528945b372af20f4e86970d40a6db6e` | provisional |
| 2 | Panniantong/Agent-Reach | — | — | exclude: neither root file |
| 3 | shareAI-lab/learn-claude-code | — | — | exclude: neither root file |
| 4 | career-ops-hq/career-ops | AGENTS.md | `3a5ae0774827cb98ebd9343549362e03e828d5e8` | provisional |
| 5 | thedaviddias/Front-End-Checklist | AGENTS.md | `bd02f81294195aeaa11c59c85f0d91a80f28a364` | provisional |
| 6 | ZhuLinsen/daily_stock_analysis | AGENTS.md | `6c90718d4aec85e4763f009ce46dc4f654cd16e2` | provisional |
| 7 | hugohe3/ppt-master | AGENTS.md | `488086a725d9a9edcc702681a82cdcbdd9ae1d1c` | provisional |
| 8 | bojieli/ai-agent-book | — | — | exclude: neither root file |
| 9 | CherryHQ/cherry-studio | AGENTS.md | `681311eb9cf453d0faddf3aacaec7357e97ba8e9` | provisional |
| 10 | HKUDS/nanobot | AGENTS.md | `d85d4aafb102e77875447a90e427ddb7811374de` | provisional |
| 11 | zhayujie/CowAgent | — | — | exclude: neither root file |
| 12 | siyuan-note/siyuan | AGENTS.md | `b647b154119417b0e2ea1a52b0593bb626a3e1c6` | provisional |

## Before evaluation

1. Screen the remaining results and at least one non-agent discovery stratum; record exclusions.
2. Check distinct ownership, forks, license, and accessibility; select at least 20 independent repositories without consulting analyzer predictions.
3. Resolve immutable source commit and path; retrieve file SHA-256, line count, size, license and timestamp.
4. Freeze cohort manifest and preregister label rules per `docs/benchmark-exact-duplicates-v0.1.md`.
5. Independently label full logical duplicate section pairs, then run the analyzer blind to labels; report discrepancies, TP/FP/FN and undefined metrics where applicable.

No source content or raw audit report is stored here.
