# Memory

Personal context about the user, stored as human-readable markdown files.

## What Goes Here

This folder stores **the user's** personal information — life events, facts, goals, and profile data. These files are the human-readable complement to the semantic search index (`indexes/memories.mv2`).

**Important:** This is the USER's memory (their life, health, family, events), NOT the agent's operational notes. Agent configuration lives in `brain/`.

## File Naming Conventions

| File | Purpose | When to Update |
|------|---------|----------------|
| `journal-YYYY.md` | Life events, milestones for a given year | When user shares new events or journal entries |
| `goals.md` | Current priorities and objectives | When goals change, are completed, or new ones emerge |
| `{user}-profile.md` | Background, family, personal facts | When learning new personal information |

### Journal Files

- One file per calendar year: `journal-2024.md`, `journal-2025.md`, etc.
- Year boundary: January 1 - December 31
- Older journals become historical (rarely updated)
- Current year journal is actively written to

### Profile File

- Named after the user: e.g., `juan-profile.md`, `sarah-profile.md`
- Contains stable facts: family, background, health, preferences
- Updated when new personal facts are learned

### Goals File

- Always current — not year-scoped
- Contains active goals and priorities
- Archive completed goals with dates

## Memory vs Brain

| Folder | Contains | Owner | Purpose |
|--------|----------|-------|---------|
| `memory/` | User's life context | User | Personal facts, events, goals |
| `brain/` | Agent's operational data | Agent | Tasks, agent registry, runbooks |

## Dual-Save Rule

When the user shares personal information, ALWAYS save to BOTH:
1. **Semantic index** via `memory_indexer.py` (for fast search)
2. **Markdown file** in this folder (for human readability and persistence)

Never save to only one place.
