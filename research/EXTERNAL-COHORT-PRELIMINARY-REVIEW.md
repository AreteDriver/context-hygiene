# Preliminary instruction-file review — 2026-10-21

**Method:** Read the 20 root instruction files at their pinned source commits using GitHub's file API. This is a *single AI-assisted preliminary content review*, **not independent human adjudication**, license clearance, a content-hash audit, or ground-truth duplicate labeling. No duplicate-detector predictions were inspected. Source commit and raw SHA-256 values are in `external-cohort-pinned-v0.1.json`.

| Repository | Root file | Approx. Markdown headings | Initial instruction-content finding | Further review |
| --- | --- | ---: | --- | --- |
| NousResearch/hermes-agent | AGENTS.md | 8 | Instruction hub and routing guidance | License applicability |
| career-ops-hq/career-ops | AGENTS.md | 41 | Extensive repository and process guidance | License applicability |
| thedaviddias/Front-End-Checklist | AGENTS.md | 19 | Contributor and automation rules | License applicability |
| ZhuLinsen/daily_stock_analysis | AGENTS.md | 19 | Chinese-language workflow instructions | Multilingual labeling coverage; license |
| hugohe3/ppt-master | AGENTS.md | 7 | Agent entry point and task-routing instructions | License applicability |
| CherryHQ/cherry-studio | AGENTS.md | 32 | Detailed coding principles and workflow | AGPL file scope |
| HKUDS/nanobot | AGENTS.md | 3 | Task-routing table and development constraints | License applicability |
| siyuan-note/siyuan | AGENTS.md | 16 | Repository operational constraints | AGPL file scope |
| codewhale-hq/Codewhale | AGENTS.md | 8 | Coding-agent guidance | Explicit reference to ponytail method; inspect overlap with DietrichGebert/ponytail |
| CopilotKit/CopilotKit | AGENTS.md | 7 | Nx and repository execution guidance | License applicability |
| can1357/oh-my-pi | AGENTS.md | 25 | Development rules and agent context | License applicability |
| iOfficeAI/AionUi | AGENTS.md | 19 | Contributor and code conventions | Apache file scope |
| morluto/rea | AGENTS.md | 9 | Repository guidelines | License applicability |
| affaan-m/ECC | AGENTS.md | 14 | Agent and development workflow instructions | License applicability |
| DietrichGebert/ponytail | AGENTS.md | 3 | Extended coding-agent instructions | Compare reuse in codewhale-hq/Codewhale |
| Graphify-Labs/graphify | AGENTS.md | 1 | Short but substantive multi-rule instruction file | Borderline size (563 bytes); manual block segmentation |
| OpenHands/OpenHands | AGENTS.md | 12 | Repository notes and developer workflows | License applicability |
| tt-a1i/archify | AGENTS.md | 4 | PR, test and installation instructions | License applicability |
| rtk-ai/rtk | CLAUDE.md | 21 | Claude Code project and development guidance | Apache file scope |
| sickn33/agentic-awesome-skills | AGENTS.md | 13 | Skills and plugin development guidance | License applicability |

**Provisional content screen:** All 20 files visibly contain repository-directed instructions. No file was excluded at this stage. Heading counts are descriptive only and are **not** ground-truth semantic-block counts. Graphify has one heading but multiple distinct directives; assess by meaning, not heading count. The explicit ponytail attribution in Codewhale is a possible *cross-source dependence*, not evidence of duplicated text until independently checked.

**Not yet established:** exact raw-byte re-fetch equality, file-specific license coverage, independence of document authorship, final semantic-block eligibility, and two-reviewer agreement. Do not freeze or report precision/recall until these are resolved and labels are adjudicated.
