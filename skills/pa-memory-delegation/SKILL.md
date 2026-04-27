---
name: PA Memory Delegation
description: Personal Assistant skill for managing the USER's memory (life events, facts, learnings) - NOT the AI's operational memory. Uses a hybrid Memvid + SQLite + Markdown architecture for fast semantic search with mutable metadata tracking.
allowed-tools: Bash
---

# PA Memory Delegation

## The Core Concept

**You are a Personal Assistant managing your USER's memory, not your own.**

This is a critical distinction:
- **User's memory** = Their life events, health facts, family info, learnings, decisions
- **AI's memory** = Your operational notes, CLAUDE.md, runbooks, instructions

This skill handles the USER's memory through a delegated system where you:
1. Listen for memorable information during conversations
2. Store it in a searchable, persistent index
3. Retrieve it when relevant to help the user

---

## Architecture: Hybrid Memory System

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Curated Context (Markdown)                            │
│  ├── memory/journal-YYYY.md   # Year summaries                  │
│  ├── memory/goals.md          # Current priorities              │
│  └── memory/profile.md        # User profile                    │
│                                                                 │
│  → Human-readable, version-controlled, future-proof             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: Fast Search (Memvid V2)                               │
│  ├── indexes/memories.mv2     # Long-term (permanent)           │
│  └── indexes/short-term.mv2   # Short-term (staging)            │
│                                                                 │
│  → 16x faster than SQLite-vec, sub-millisecond semantic search  │
│  → Append-only (can't UPDATE records)                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: Mutable Metadata (SQLite)                             │
│  └── indexes/memory_meta.db                                     │
│      ├── access_count        # How often retrieved              │
│      ├── reinforcement_count # How often re-confirmed           │
│      └── confidence          # Quality score                    │
│                                                                 │
│  → Tracks what's actually useful                                │
│  → Enables UPDATE operations Memvid can't do                    │
└─────────────────────────────────────────────────────────────────┘
```

**Why hybrid?**
- Memvid = Fast search (like Redis)
- SQLite = Mutable counters (like PostgreSQL)
- Markdown = Human backup (future-proof for larger context windows)

---

## Setup

```bash
# Create virtual environment (using uv)
cd /path/to/your/assistant
uv venv
source .venv/bin/activate
uv pip install memvid-sdk

# Directory structure
mkdir -p indexes memory tools

# Install wrapper scripts (optional but recommended)
cp tools/memory*.sh ~/.local/bin/
chmod +x ~/.local/bin/memory*.sh
```

**Required files:**
- `tools/memory_indexer.py` - The main indexer tool
- `tools/memory.sh` - Wrapper script (optional)
- `indexes/` - Where .mv2 and .db files live
- `memory/` - Curated markdown journals

---

## Commands

### Quick Commands (with wrapper scripts)

```bash
memory.sh add "User's income is $100k" --type fact
memory.sh find "income"
memory.sh stats
memory.sh review
memory.sh promote
```

### Full Commands (without wrappers)

```bash
source .venv/bin/activate
python tools/memory_indexer.py <command>
```

### Add Memories

```bash
# Add to long-term (permanent)
python tools/memory_indexer.py add "User's income is $215,628/year" --type fact

# Add with metadata
python tools/memory_indexer.py add "Heart attack on 8/13/2024" \
  --type event \
  --date 2024-08-13 \
  --people "User,Dr. White" \
  --tags "health,medical"

# Add to short-term (staging area)
python tools/memory_indexer.py add "User mentioned interest in AI" --type note --short-term

# Force add (skip deduplication)
python tools/memory_indexer.py add "..." --force
```

### Search Memories

```bash
# Basic search (tracks access in SQLite)
python tools/memory_indexer.py find "health issues"

# Filter by type
python tools/memory_indexer.py find "2024" --type event

# Filter by year
python tools/memory_indexer.py find "family" --year 2024

# Filter by person
python tools/memory_indexer.py find "medical" --person "Dr. White"

# Search short-term
python tools/memory_indexer.py find "recent" --short-term
```

### Two-Tier Workflow

```bash
# Review short-term memories (shows promotion eligibility)
python tools/memory_indexer.py review

# Promote mature memories to long-term
python tools/memory_indexer.py promote --dry-run  # Preview
python tools/memory_indexer.py promote            # Execute
```

### Statistics & Maintenance

```bash
# Show full stats (Memvid + SQLite metadata)
python tools/memory_indexer.py stats

# Migrate existing Memvid memories to SQLite (one-time)
python tools/memory_indexer.py migrate
```

---

## Memory Types

| Type | Icon | When to Use |
|------|------|-------------|
| `fact` | 📌 | Permanent truths (income, address, relationships) |
| `event` | 📅 | Things that happened (with dates) |
| `learning` | 💡 | Discoveries, insights gained |
| `decision` | ⚖️ | Choices made and rationale |
| `note` | 📝 | General observations |
| `person` | 👤 | Info about specific people |
| `goal` | 🎯 | Objectives, targets |
| `preference` | ⭐ | User preferences |
| `pattern` | 🔄 | Recurring behaviors, workflows |
| `insight` | 🧠 | Understanding about systems |

---

## When to Add Memories

**PROACTIVELY add when the user shares:**

| User Says | Memory Type | Example |
|-----------|-------------|---------|
| "I make $X per year" | fact | Income, employment |
| "My wife's name is..." | fact, person | Family relationships |
| "I had surgery on..." | event | Health events |
| "We decided to use..." | decision | Technical/life decisions |
| "I learned that..." | learning | New knowledge |
| "I prefer..." | preference | User preferences |
| "My goal is..." | goal | Objectives |

**DON'T add:**
- Trivial conversation filler
- Information already in the index (dedup handles this)
- Sensitive credentials (use secure storage instead)

---

## Deduplication & Reinforcement

When you add a memory that already exists:

1. **Memvid** detects similarity, doesn't create duplicate
2. **SQLite** increments `reinforcement_count`
3. **Confidence** gets boosted (+5% per reinforcement)

This means frequently mentioned facts become higher confidence and easier to find.

```
First mention:  confidence=70%, reinforcement=1
Second mention: confidence=75%, reinforcement=2
Third mention:  confidence=80%, reinforcement=3
```

---

## Access Tracking

Every search automatically:
1. Records which memories were retrieved
2. Increments `access_count` in SQLite
3. Updates `last_accessed` timestamp

This tells you what memories are actually useful vs. just stored.

---

## Short-term → Long-term Promotion

**Short-term** is a staging area for uncertain memories.

**Promotion criteria:**
- Reinforced 2+ times, OR
- Confidence >= 90%

**Workflow:**
1. Add uncertain memories with `--short-term`
2. If mentioned again, reinforcement increases
3. Run `promote` to move mature memories to long-term
4. Or let them age out if never reinforced

---

## Example Session

```bash
# User shares health info
python tools/memory_indexer.py add "User had heart attack on 8/13/2024" \
  --type event --date 2024-08-13 --tags "health"

# Later, user mentions it again (reinforces existing)
python tools/memory_indexer.py add "Heart attack was in August 2024"
# Output: "Similar memory exists (reinforcement #2)"

# When user asks about health
python tools/memory_indexer.py find "health"
# Returns: Heart attack event with [reinforced:2x, accessed:1x]

# Check what's most accessed
python tools/memory_indexer.py stats
# Shows: Most accessed memories, most reinforced memories
```

---

## Integration with Markdown Journals

The indexes complement, not replace, markdown journals:

| Layer | Purpose | Update Frequency |
|-------|---------|------------------|
| Memvid indexes | Searchable details | Every memorable fact |
| Markdown journals | Curated summaries | Periodic (weekly/monthly) |

**Workflow:**
1. Add details to Memvid index (searchable)
2. Periodically summarize important events to journal.md
3. Journal serves as human-readable backup

---

## Why This Design?

1. **Memvid is append-only** - Can't UPDATE records, so SQLite handles mutable data
2. **16x faster search** - Memvid V2 beats SQLite-vec on retrieval
3. **5x smaller storage** - Memvid's compression is excellent
4. **Future-proof** - Markdown journals work when context windows grow
5. **Graceful degradation** - If Memvid fails, markdown still works

---

## Files Reference

```
your-assistant/
├── .venv/                      # Python virtual environment
├── tools/
│   └── memory_indexer.py       # Main indexer tool
├── indexes/
│   ├── memories.mv2            # Long-term Memvid index
│   ├── short-term.mv2          # Short-term Memvid index
│   └── memory_meta.db          # SQLite metadata
└── memory/
    ├── journal-2024.md         # Curated yearly summary
    ├── journal-2025.md
    ├── goals.md                # Current objectives
    └── profile.md              # User profile
```

---

## Troubleshooting

**"memvid-sdk not installed"**
```bash
source .venv/bin/activate
uv pip install memvid-sdk
```

**"Index not found"**
- First `add` command creates the index automatically

**Duplicate detection not working**
- Check similarity: first 50 chars (normalized) must match
- Use `--force` to bypass if needed

**SQLite metadata empty**
- Run `migrate` command to backfill from existing Memvid data
