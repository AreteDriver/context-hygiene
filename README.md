# context-hygiene

**Context window hygiene analyzer for LLM conversations.**

Heuristic detection of staleness, contradictions, deadweight, and compression opportunities in CLAUDE.md files, prompt chains, and agent configs. No LLM required for basic analysis.

---

## Install

```bash
pip install context-hygiene
```

Optional extras:

```bash
pip install "context-hygiene[anthropic]"  # AI-powered deep analysis
pip install "context-hygiene[watch]"      # Live file monitoring
```

## Quick Start

```bash
# Audit a CLAUDE.md file (heuristics, no LLM)
ctx-hygiene audit CLAUDE.md

# Quick staleness score
ctx-hygiene score CLAUDE.md

# Auto-clean deadweight and stale segments
ctx-hygiene clean CLAUDE.md

# View audit history
ctx-hygiene history

# Check license and config
ctx-hygiene status
```

## How It Works

context-hygiene parses structured context files into conversation segments and runs four heuristic analysis passes:

### 1. Staleness Detection

Identifies potentially outdated segments based on:
- **Position decay** — earlier segments in a long conversation are more likely stale
- **Language patterns** — detects corrections ("actually", "instead", "scratch that"), restarts ("let me start over"), and explicit staleness ("old", "deprecated")
- **Error content** — large traceback blocks after a fix is applied
- **Short mid-conversation messages** — often fragmented or superseded context

Scored 0–1 per segment (0 = fresh, 1 = completely stale).

### 2. Contradiction Detection

Finds conflicting instructions between user/system segments using regex pattern matching:
- Positive vs. negative directives ("use X" vs. "don't use X")
- Opposing adverbs ("always" vs. "never")
- Incompatible toggles ("enable" vs. "disable", "include" vs. "exclude")

Flagged with confidence score (currently fixed at 0.7; deep mode uses LLM for refinement).

### 3. Deadweight Detection

Identifies zero-influence messages that consume tokens without shaping output:
- Acknowledgment-only messages ("ok", "thanks", "got it")
- Filler words ("hmm", "um", "well")
- Assistant confirmation preambles ("Sure, I'd be happy to...")
- Exact duplicates of earlier segments
- Empty or whitespace-only messages

### 4. Compression Detection

Finds opportunities to condense without information loss:
- Consecutive same-role runs (3+ messages from user/assistant in a row)
- Large code blocks that could be referenced instead of inlined
- Verbose assistant explanations where prose exceeds code content

---

## Fast vs. Deep Mode

| | **Fast** (default) | **Deep** (Pro) |
|---|---|---|
| **How it works** | Regex + heuristic scoring | LLM semantic analysis |
| **Speed** | Milliseconds | Seconds to minutes |
| **Cost** | $0 | LLM API tokens |
| **Staleness** | Pattern-based | Semantic drift detection |
| **Contradictions** | Regex pairs | LLM cross-references |
| **Deadweight** | Acknowledgment/filler filters | Semantic relevance scoring |
| **Compression** | Token thresholds | Content summarization |

**Fast mode is sufficient for most use cases.** Deep mode is useful when heuristic patterns miss nuanced semantic drift.

---

## Free vs. Pro

| Feature | Free | Pro ($8/mo) |
|---------|------|-------------|
| `audit` (fast mode) | 10/month | Unlimited |
| `score` / `clean` / `history` | Unlimited | Unlimited |
| `audit --deep` (AI analysis) | — | Yes |
| `watch` (live monitoring) | — | Yes |

**[Subscribe Monthly ($8/mo)](https://buy.stripe.com/bJebJ11OHeBl3925kbgrS08)** | **[Subscribe Yearly ($69/yr)](https://buy.stripe.com/3cI6oH0KDal59xq5kbgrS09)**

**All 5 Tools Bundle:** [Monthly ($29/mo)](https://buy.stripe.com/7sY9AT9h90Kv5ha27ZgrS0a) | [Yearly ($199/yr)](https://buy.stripe.com/9B6fZh9h98cX24YfYPgrS0b) — includes claudemd-forge, agent-lint, ai-spend, promptctl, context-hygiene

After purchase, activate via:

```bash
export CONTEXT_HYGIENE_LICENSE="CTHG-XXXX-XXXX-XXXXXXXXXXXXXXXX"
```

Or save to `~/.config/context-hygiene/license`.

---

## Programmatic API

You can also use `context-hygiene` from Python without shelling out to the CLI:

```python
from context_hygiene import audit_file, score_file

# Full audit report
report = audit_file("CLAUDE.md")
print(report.grade)               # 'B'
print(report.tokens_recoverable)  # 1,247

# Quick score
score = score_file("conversation.json")
print(score.grade)      # 'C'
print(score.staleness)  # 0.34
```

## Before / After Demo

**Before:** A messy 14-segment conversation with stale instructions, deadweight, and contradictions.

```
Tokens: 1,847  |  Grade: D
- "ok" (deadweight)
- "Sure, let me know..." (assistant preamble)
- "Actually, scratch that. Use poetry instead." (supersedes prior pip advice)
- "Never mind, let me start over. I'll use uv instead." (supersedes poetry)
- "Use pip for everything" vs "Don't use pip, use poetry" (contradiction)
```

Run the cleaner:

```bash
ctx-hygiene clean conversation.md --apply
# Pruning plan: remove 4/14 segments
# Tokens: 1,847 → 1,124 (save 723)
```

**After:** The same conversation, pruned to 10 segments with no contradictions and no deadweight.

```
Tokens: 1,124  |  Grade: B  |  Recoverable: 723 tokens (39%)
```

## What This Is (and Isn't)

**context-hygiene is a practical heuristic tool, not a novel research metric.** It doesn't measure "semantic entropy" or "information-theoretic density." It applies well-understood pattern-matching techniques to a specific problem: finding waste in LLM context windows.

If you're looking for:
- **Token-level compression** → LLMLingua, Selective Context
- **Novelty scoring** → Build your own embedding-based metric
- **A quick sanity check before sending a long context** → `ctx-hygiene score` does exactly that

---

## Community

[Discord](https://discord.gg/fdzQkrt8) — Join the community

## License

BSL-1.1 (Business Source License 1.1)

The core heuristic analyzer is free to use and modify. AI-powered deep analysis
(`--deep`) and live file monitoring (`watch`) require a Pro license.
