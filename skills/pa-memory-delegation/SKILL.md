---
name: pa-memory-delegation
description: Use when the user tells you something worth remembering about their life (facts, events, people, preferences), or asks what you know about them. Manages the USER's memory (life events, facts, learnings) - NOT the AI's operational memory. Uses a hybrid Memvid + SQLite + Markdown architecture for fast semantic search with mutable metadata tracking.
allowed-tools: Bash
---

# PA Memory Delegation

This is the user's memory, kept on their behalf: their life, health, family, money, decisions, preferences. It is not your own operational memory (CLAUDE.md, `brain/*.md`), which you manage separately.

It has three layers:

- **Memvid indexes** (`indexes/memories.mv2` long-term, `indexes/short-term.mv2` staging): semantic search. Append-only.
- **SQLite** (`indexes/memory_meta.db`): the mutable part — confidence, how often a memory was reinforced and retrieved, supersessions, soft deletes.
- **Markdown** in `memory/`: the human-readable record (profile, `journal-YYYY.md`, `goals.md`).

## Commands

`memory.sh` (in `$LOLABOT_HOME/tools/`, or `~/.local/bin` if installed there) wraps `tools/memory_indexer.py` and activates the virtualenv.

```bash
memory.sh add "<content>" --type <type> [--date YYYY-MM-DD] [--people "A,B"] [--tags "x,y"] \
    [--source "<where it came from>"] [--files "<paths>"] [--confidence 0.0-1.0] [--context "<why>"] \
    [--topic-key <key>] [--short-term] [--force]
memory.sh find "<query>" [--type <type>] [--year YYYY] [--person "<name>"] [--limit 10] [--short-term]
memory.sh correct "<corrected statement>" [--topics "a,b"] [--source "<who said so>"]
memory.sh remove <frame-id>                  # soft delete
memory.sh review | promote [--dry-run]       # short-term staging
memory.sh stale [--refresh] | stats
```

Types: `fact`, `event`, `person`, `preference`, `goal`, `decision`, `learning`, `note` (default), `pattern`, `insight`.

## Saving

Save what the user would expect you to remember next month: facts about them and their family, dated events, people and how they relate to the user, preferences, goals, decisions and why. Skip conversational filler. Credentials (passwords, PINs, keys) never go into memory.

- **Dated things** get `--date`, and the people involved get `--people`, so `find --year` and `find --person` work.
- **Facts that change** (address, employer, a balance): give them a stable `--topic-key` such as `home-address`. A new value under the same key supersedes the old one instead of sitting beside it.
- **The user corrects you:** use `correct` with the right statement. It is stored at high confidence and outranks the memories it contradicts.
- **Unsure or passing remarks:** add them with `--short-term`. Short-term memories move to long-term with `promote` once reinforced twice or at 0.9 confidence.

Saving the same fact again reinforces it (confidence +0.05, from 0.7) instead of duplicating it. The duplicate check compares the beginning of the text, so a reworded fact is stored as a new memory: when you know a fact is already there, phrase it the same way or use a topic key.

Also write the information to the matching markdown file, as CLAUDE.md requires: personal facts to the user's profile, life events to `memory/journal-YYYY.md`, goals to `memory/goals.md`.

## Recalling

When the user asks what you know, or a task depends on their history, run `find` before answering, and say where a fact came from when it matters. Results show confidence and how often each memory was reinforced; low-confidence or stale memories (`memory.sh stale`) are worth confirming with the user rather than stating as fact.

## Troubleshooting

- `memvid-sdk not installed`: `source .venv/bin/activate && uv pip install memvid-sdk`.
- Index not found: the first `add` creates it.
- SQLite metadata empty for old memories: `memory.sh migrate`.
