# PA Memory Delegation Skill

A Claude Code skill for Personal Assistants to manage their USER's memory.

## The Key Insight

**This is NOT about the AI's operational memory. It's about managing the USER's life information.**

| Concept | What It Is | Examples |
|---------|-----------|----------|
| User's Memory | Their life, delegated to you | Health events, family, income, decisions |
| AI's Memory | Your operational notes | CLAUDE.md, runbooks, instructions |

## Architecture

Hybrid system combining three technologies:

```
Memvid V2 (fast search) + SQLite (mutable counters) + Markdown (human backup)
```

- **Memvid**: 16x faster than SQLite-vec, but append-only
- **SQLite**: Tracks access_count, reinforcement_count (mutable)
- **Markdown**: Future-proof for larger context windows

## Features

- **Deduplication**: Same fact mentioned twice → reinforces, doesn't duplicate
- **Access tracking**: Know which memories are actually useful
- **Two-tier**: Short-term staging → Long-term permanent
- **Confidence scores**: Frequently reinforced facts = higher confidence

## Quick Start

See `SKILL.md` for full documentation.

```bash
# Add a memory
python tools/memory_indexer.py add "User's income is $100k" --type fact

# Search memories
python tools/memory_indexer.py find "income"

# View stats
python tools/memory_indexer.py stats
```

## Requirements

- Python 3.10+
- `memvid-sdk` package
- `uv` for venv management (recommended)

## License

MIT
