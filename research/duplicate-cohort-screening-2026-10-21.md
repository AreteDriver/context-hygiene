# External duplicate-detection cohort — screening log (in progress)

**Status:** 45 screened, 29 initial file-present candidates, 16 without root files. One file-present candidate (localstack/localstack) was subsequently rejected by the pinning eligibility gate. Twenty selected candidates are listed in `research/external-cohort-candidates-v0.1.json`; `sickn33/agentic-awesome-skills` replaces LocalStack. Not frozen or labeled. **Not frozen or labeled. No accuracy claim.**

## Discovery rule

GitHub repository search `topic:ai-agent stars:>100`, ordered by GitHub's default search relevance, page 1, first 30 results, screened 2026-10-21. For each result, check root `AGENTS.md` first, then root `CLAUDE.md` if absent. Exclude when neither exists. Do not select based on analyzer findings. This discovery stratum is AI-agent-focused and not representative of all software repositories. Expand to other strata before freezing the 20-repository cohort.

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

| 13 | codewhale-hq/Codewhale | AGENTS.md | `0180f8340d69ce5e7244f6794e14ec3591ba037d` | provisional |
| 14 | CopilotKit/CopilotKit | AGENTS.md | `26db928b366eddbc1f85c6f9c532029ca5a28219` | provisional |
| 15 | HKUDS/Vibe-Trading | — | — | exclude: neither root file |
| 16 | can1357/oh-my-pi | AGENTS.md | `705cc3f4ed361aeaaa31923f4bf0d54e86dbd3d1` | provisional |
| 17 | agentscope-ai/QwenPaw | — | — | exclude: neither root file |
| 18 | esengine/DeepSeek-Reasonix | AGENTS.md | `f16da0860282d51291e11ad230f6c7ecb2303880` | provisional; only 158 characters, check eligibility |
| 19 | Twigpine/openclaude | AGENTS.md | `bcdd5aaded7c460777281a1cc6b7a01a8762a1b4` | provisional |
| 20 | iOfficeAI/AionUi | AGENTS.md | `32f4aa9389e39e08c3932589893d23dd3f86416e` | provisional |
| 21 | feder-cr/invisible_dots | — | — | exclude: neither root file |
| 22 | googleworkspace/cli | AGENTS.md | `722112264ba71816a4e7c5561b56aa19011e0dea` | provisional |
| 23 | trycua/cua | AGENTS.md | `694b448c6d8269934f28e392777ec0fc690ec693` | provisional |
| 24 | jackwener/OpenCLI | — | — | exclude: neither root file |
| 25 | TencentCloud/TencentDB-Agent-Memory | — | — | exclude: neither root file |
| 26 | QwenLM/qwen-code | AGENTS.md | `597db3baad469df278458f8df0ef313dd719c1b2` | provisional |
| 27 | op7418/guizang-ppt-skill | — | — | exclude: neither root file |
| 28 | titanwings/distilly | — | — | exclude: neither root file |
| 29 | activepieces/activepieces | AGENTS.md | `e7f8168ecc8909c0a2bb01af1cae18407a5470e8` | provisional |
| 30 | nocobase/nocobase | AGENTS.md | `030a2aae85d670ac1cdade03e19100ca581a1dbe` | provisional |


## Second discovery stratum: developer tools

GitHub repository search `topic:developer-tools stars:>100`, default relevance, page 1, first 15 results, screened 2026-10-21. The same root-file screening rule applies. This stratum broadens beyond AI-agent-focused repositories but is still search-ranked, not random.

| Search rank | Repository | Root file | Git blob SHA | Screen |
|---:|---|---|---|---|
| 1 | morluto/rea | AGENTS.md | `1f26ffbe24f3e438da5ec6d7f3f11626d33bde1b` | provisional |
| 2 | affaan-m/ECC | AGENTS.md | `f2f049297454806522722b3bbe2b7ebb10811a0b` | provisional |
| 3 | DietrichGebert/ponytail | AGENTS.md | `ee5d6f1d6c1e4ff197a41d3ff43fa6597dbc81d4` | provisional |
| 4 | Graphify-Labs/graphify | AGENTS.md | `38857bdc2d175525367110a814289f9b9bb90f7d` | provisional; short (563 chars) |
| 5 | puppeteer/puppeteer | — | — | exclude: neither root file |
| 6 | OpenHands/OpenHands | AGENTS.md | `119dce3b9b9ad95c07624d4858eb5b58c59dd367` | provisional |
| 7 | tt-a1i/archify | AGENTS.md | `562788125a8bd393392eff656a31109e94485833` | provisional |
| 8 | rtk-ai/rtk | CLAUDE.md | `b62fce49594e043a3b41028b44315ce50409e11d` | provisional |
| 9 | hoppscotch/hoppscotch | — | — | exclude: neither root file |
| 10 | ComposioHQ/awesome-claude-skills | — | — | exclude: neither root file |
| 11 | daytonaio/daytona | — | — | exclude: neither root file |
| 12 | localstack/localstack | AGENTS.md | `e5f81c35c2119f521ba9d570491094290e773714` | excluded from selected cohort: GitHub API reports archived/fork/private; pinning rejected |
| 13 | ayghri/i-have-adhd | AGENTS.md | `49a84d2088b0943517b199347065f8c45487dac8` | provisional |
| 14 | GitHubDaily/GitHubDaily | — | — | exclude: neither root file |
| 15 | sickn33/agentic-awesome-skills | AGENTS.md | `443dfed383a76b42aea747634eb729086bdadc11` | provisional |

## Before evaluation

1. Verify eligibility and independence of at least 20 of the 29 provisional candidates across both discovery strata; record exclusions.
2. Check distinct ownership, forks, license, and accessibility; select at least 20 independent repositories without consulting analyzer predictions.
3. Resolve immutable source commit and path; retrieve file SHA-256, line count, size, license and timestamp.
4. Freeze cohort manifest and preregister label rules per `docs/benchmark-exact-duplicates-v0.1.md`.
5. Independently label full logical duplicate section pairs, then run the analyzer blind to labels; report discrepancies, TP/FP/FN and undefined metrics where applicable.

No source content or raw audit report is stored here.
