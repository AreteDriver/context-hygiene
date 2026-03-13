# context-hygiene

Context window hygiene analyzer for LLM conversations. Detect staleness, contradictions, deadweight, and compression opportunities in CLAUDE.md files, prompt chains, and agent configs.

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
# Audit a CLAUDE.md file
ctx-hygiene audit CLAUDE.md

# Score staleness heuristically (no LLM needed)
ctx-hygiene score CLAUDE.md

# Auto-clean deadweight and stale segments
ctx-hygiene clean CLAUDE.md

# View audit history
ctx-hygiene history

# Check license and config
ctx-hygiene status
```

## Free vs Pro

| Feature | Free | Pro ($8/mo) |
|---------|------|-------------|
| `audit` (fast mode) | 10/month | Unlimited |
| `score` | Unlimited | Unlimited |
| `clean` | Unlimited | Unlimited |
| `history` | Unlimited | Unlimited |
| `status` / `stats` | Unlimited | Unlimited |
| `audit --deep` (AI analysis) | - | Yes |
| `watch` (live monitoring) | - | Yes |

**[Subscribe Monthly ($8/mo)](https://buy.stripe.com/bJebJ11OHeBl3925kbgrS08)** | **[Subscribe Yearly ($69/yr)](https://buy.stripe.com/3cI6oH0KDal59xq5kbgrS09)**

After purchase, you'll receive a license key via email. Activate it:

```bash
export CONTEXT_HYGIENE_LICENSE="CTHG-XXXX-XXXX-XXXX"
```

Or save to `~/.config/context-hygiene/license`.

## How It Works

context-hygiene parses structured context files (CLAUDE.md, YAML configs, prompt chains) into segments and runs four analysis passes:

1. **Staleness** — Detects outdated references, stale version numbers, dead links
2. **Contradictions** — Finds conflicting instructions or redundant rules
3. **Deadweight** — Identifies low-signal boilerplate, excessive examples, noise
4. **Compression** — Suggests where content can be condensed without information loss

Fast mode uses heuristics. Deep mode (`--deep`, Pro) uses an LLM for semantic analysis.

## License

MIT
