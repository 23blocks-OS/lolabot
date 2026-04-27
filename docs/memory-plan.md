# Lola Two-Tier Memory System Plan

**Date:** 2026-01-25
**Status:** Draft - Needs Review

---

## The Biology Analogy

Human memory works in layers:

```
SENSORY INPUT → WORKING MEMORY → SHORT-TERM → LONG-TERM
                (seconds)        (minutes)    (permanent)

Sleep consolidates short-term → long-term
Repetition strengthens memories
Unused memories fade
Important/emotional memories get priority
```

**For Lola:**

```
CONVERSATIONS → SHORT-TERM → LONG-TERM
(JSONL files)   (recent,     (permanent,
                 detailed)    distilled)

Consolidation extracts insights
Repetition = reinforcement
Access patterns show importance
Confidence scores = memory strength
```

---

## Current State

### What We Have

| Component | Location | Purpose |
|-----------|----------|---------|
| Conversation JSONL | `~/.claude/projects/*/conversations/` | Raw conversation history |
| memories.mv2 | `lola/indexes/memories.mv2` | Manually curated memories |
| files.mv2 | `lola/indexes/files.mv2` | File location index |
| Markdown journals | `lola/memory/journal-*.md` | High-level summaries |

### What's Missing

1. **No automatic extraction** - I manually add memories
2. **No short-term buffer** - Everything is either raw JSONL or manually curated
3. **No deduplication** - Same fact can be added multiple times
4. **No reinforcement** - Can't see what's mentioned repeatedly
5. **No confidence** - All memories treated equally
6. **No access tracking** - Don't know what's actually useful

---

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RAW CONVERSATIONS                             │
│  ~/.claude/projects/*/conversations/*.jsonl                          │
│  - Every message between Juan and Lola                              │
│  - Huge, verbose, temporary context                                  │
│  - Read-only (Claude manages these)                                  │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
                    CONSOLIDATION PROCESS
                    (On-demand or scheduled)
                    "What did I learn today?"
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      SHORT-TERM MEMORY                               │
│  lola/indexes/short-term.mv2                                         │
│                                                                      │
│  - Recent extractions (last 30 days)                                │
│  - Higher detail than long-term                                     │
│  - Includes: context, source conversation, timestamp                │
│  - Subject to pruning after consolidation                           │
│                                                                      │
│  Fields: content, type, date, source_file, context, confidence      │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
                    CONSOLIDATION TO LONG-TERM
                    (Weekly or on threshold)
                    "What's worth keeping forever?"
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      LONG-TERM MEMORY                                │
│  lola/indexes/memories.mv2 (existing, enhanced)                      │
│                                                                      │
│  - Permanent, distilled knowledge                                   │
│  - Deduplicated with reinforcement                                  │
│  - Categories: fact, event, decision, preference, pattern,          │
│                learning, person, goal, insight                      │
│                                                                      │
│  Fields: content, type, date, confidence, reinforcement_count,      │
│          last_reinforced, access_count, last_accessed,              │
│          tags, people, files                                        │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      CURATED CONTEXT                                 │
│  lola/memory/*.md, CLAUDE.md, brain/*.md                            │
│                                                                      │
│  - Hand-written summaries loaded into context                       │
│  - Most important, most refined                                     │
│  - Updated manually from long-term insights                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## What's Worth Implementing

### High Value ✅

| Feature | Why Worth It | Effort |
|---------|--------------|--------|
| **Deduplication** | Prevents memory bloat, cleaner data | Low |
| **Reinforcement tracking** | Shows what matters (mentioned repeatedly) | Low |
| **Confidence scores** | Better search ranking, quality indicator | Low |
| **Access tracking** | Shows what's actually useful | Low |
| **JSONL → Short-term extraction** | Automatic learning from conversations | Medium |
| **Short-term → Long-term consolidation** | Two-tier like biology | Medium |

### Medium Value ⚠️

| Feature | Why Maybe | Consideration |
|---------|-----------|---------------|
| **Scheduled consolidation** | Nice automation | But we're often in conversation anyway |
| **Pruning old short-term** | Saves space | But storage is cheap |
| **Pattern detection** | Find workflows | But might be noise |

### Not Worth It ❌

| Feature | Why Skip | Alternative |
|---------|----------|-------------|
| **Ollama/Claude provider abstraction** | We're already in Claude | Just use current session |
| **Complex UI** | We're CLI-based | Keep it terminal |
| **Real-time consolidation** | Overkill | On-demand is fine |
| **Decay/forgetting** | Biology has this but... | We have unlimited storage |

---

## Detailed Design

### 1. Enhanced Memory Schema

```python
# Current fields
content: str        # The memory itself
type: str           # fact, event, learning, etc.
date: str           # When it happened
tags: list[str]     # Categories
people: list[str]   # Related people
files: list[str]    # Related file URIs

# New fields to add
confidence: float       # 0.0-1.0, how sure are we
reinforcement_count: int  # Times this was re-confirmed
last_reinforced: str    # Date of last reinforcement
access_count: int       # Times this was searched/used
last_accessed: str      # Date of last access
source_conversation: str  # Which JSONL file this came from
context: str            # Additional context/reasoning
```

### 2. Deduplication Logic

When adding a memory:

```python
def add_memory(new_memory):
    # 1. Search existing memories for similar content
    similar = find_similar(new_memory.content, threshold=0.85)

    if similar:
        # 2. Reinforce existing instead of duplicate
        existing = similar[0]
        existing.reinforcement_count += 1
        existing.last_reinforced = today()

        # 3. Maybe merge context if new info
        if new_memory.context and new_memory.context not in existing.context:
            existing.context += f"\n{new_memory.context}"

        # 4. Boost confidence if reinforced
        existing.confidence = min(1.0, existing.confidence + 0.05)
        return existing
    else:
        # 5. Create new memory
        return create_new(new_memory)
```

### 3. Access Tracking

When searching memories:

```python
def search_memories(query):
    results = memvid.find(query)

    for memory in results:
        # Track that this memory was useful
        memory.access_count += 1
        memory.last_accessed = today()

    return results
```

### 4. Consolidation from JSONL

```python
def consolidate_conversations(days=7):
    """Extract memories from recent conversations."""

    # 1. Find JSONL files modified in last N days
    jsonl_files = find_recent_conversations(days)

    # 2. For each conversation
    for jsonl in jsonl_files:
        # 3. Read and summarize
        messages = read_jsonl(jsonl)

        # 4. Extract memories (this is where LLM helps)
        # In our case, I (Lola) am the LLM - I can do this interactively
        # Or we can use a prompt template

        # 5. Add to short-term with source tracking
        for memory in extracted:
            memory.source_conversation = jsonl
            add_to_short_term(memory)
```

### 5. Short-term → Long-term Promotion

```python
def promote_to_long_term(threshold_days=30, min_reinforcement=2):
    """Move mature short-term memories to long-term."""

    short_term = load_short_term()

    for memory in short_term:
        # Promote if:
        # - Old enough (survived short-term)
        # - Reinforced (mentioned multiple times)
        # - High confidence

        if (memory.age > threshold_days and
            memory.reinforcement_count >= min_reinforcement):

            # Check for duplicate in long-term
            if not exists_in_long_term(memory):
                add_to_long_term(memory)

            # Remove from short-term
            remove_from_short_term(memory)
```

---

## Implementation Plan

### Phase 1: Enhance Current System ✅ COMPLETE (2026-01-25)

**Goal:** Add new fields without breaking existing memories.

**Implemented:**

1. ✅ New fields in memory records:
   - `Confidence` (0.0-1.0, default 0.7)
   - `Reinforcement_count` (times this memory was re-added)
   - `Access_count` (times this memory was searched)
   - `Context` (additional reasoning)
   - `Created` date

2. ✅ Deduplication:
   - `find_similar()` checks first 50 chars (normalized)
   - If match found → reinforce existing, don't duplicate
   - `--force` flag to skip dedup if needed

3. ✅ New memory types:
   - `pattern` (🔄) - recurring workflows
   - `insight` (🧠) - understanding about systems

4. ✅ Enhanced output:
   - Shows confidence, reinforcement count, access count
   - Icons for all memory types

**Files:**
- `tools/memory_indexer.py` - Enhanced

### Phase 2: Short-term Layer ✅ COMPLETE (2026-01-25)

**Goal:** Create separate short-term index.

**Implemented:**

1. ✅ Two separate indexes:
   - `indexes/memories.mv2` - Long-term (permanent)
   - `indexes/short-term.mv2` - Short-term (staging)

2. ✅ New CLI commands:
   - `--short-term` / `-S` flag on add/find
   - `review` - Show short-term memories with promotion status
   - `promote` - Move mature memories to long-term
   - `promote --dry-run` - Preview what would be promoted

3. ✅ Promotion logic:
   - Auto-promote if reinforced 2+ times OR confidence >= 90%
   - Configurable thresholds

**Limitation noted:**
- Memvid is append-only, so reinforcement_count in stored text doesn't update
- Deduplication works (detects and prevents duplicates)
- But stored reinforcement count stays at 1
- Workaround: Use high confidence (0.9+) for promotion eligibility

**Files:**
- `tools/memory_indexer.py` - Enhanced
- `indexes/short-term.mv2` - Created

### Phase 2.5: SQLite Metadata Layer ✅ COMPLETE (2026-01-26)

**Goal:** Add mutable counters that Memvid can't provide.

**Implemented:**

1. ✅ SQLite database for mutable metadata:
   - `indexes/memory_meta.db` - Stores mutable counters
   - Schema: memory_id, content_hash, memory_type, index_type, confidence, access_count, reinforcement_count, created_at, last_accessed, last_reinforced, content_preview

2. ✅ Integration with MemoryIndex:
   - `add_memory()` → Creates SQLite record for new memories
   - `add_memory()` → Updates reinforcement_count for duplicates (actually updates!)
   - `find()` → Updates access_count when memories are retrieved
   - `stats` → Shows most accessed and most reinforced memories

3. ✅ Hybrid architecture realized:
   - Memvid V2 = Fast semantic search (like Redis)
   - SQLite = Mutable counters (like PostgreSQL)
   - Markdown = Human-readable backup (future-proof)

**Files:**
- `tools/memory_indexer.py` - MemoryMetadataDB class added
- `indexes/memory_meta.db` - SQLite database created

**Python Environment:**
- Virtual env: `.venv/` (created with `uv venv`)
- Activate: `source .venv/bin/activate`
- Run: `python tools/memory_indexer.py <command>`

### Phase 3: Automation (Future)

**Goal:** Make consolidation smoother.

1. End-of-session prompt: "What did we learn today?"
2. Weekly summary generation
3. Automatic promotion based on thresholds

---

## Directory Structure (After Implementation)

```
lola/
├── indexes/
│   ├── memories.mv2      # Long-term (permanent, distilled)
│   ├── short-term.mv2    # Short-term (recent, detailed)
│   └── files.mv2         # File locations
├── memory/
│   ├── journal-2024.md   # Curated high-level
│   ├── journal-2025.md
│   └── journal-2026.md
├── brain/
│   ├── memory-plan.md    # This document
│   ├── memory-architecture.md
│   └── ...
└── tools/
    ├── memory_indexer.py # Enhanced with new features
    └── file_indexer.py
```

---

## Open Questions

1. **How often to consolidate?**
   - Option A: End of each conversation (too frequent?)
   - Option B: Daily (scheduled job)
   - Option C: On-demand ("Lola, consolidate today's memories")
   - **Recommendation:** C - On-demand feels more natural

2. **Who extracts memories from JSONL?**
   - Option A: I (Lola) do it interactively in conversation
   - Option B: Automated with prompt template
   - **Recommendation:** A - I'm already the LLM, let me do it thoughtfully

3. **What threshold for similarity?**
   - 0.85 seems standard (AI Maestro uses this)
   - Could tune based on experience

4. **Keep short-term forever or prune?**
   - Storage is cheap, could keep
   - But noise accumulates
   - **Recommendation:** Prune after promotion to long-term

---

## Success Criteria

- [ ] No duplicate memories (deduplication works)
- [ ] Can see which memories are reinforced frequently
- [ ] Can see which memories are actually accessed
- [ ] Short-term captures recent conversation insights
- [ ] Long-term contains only mature, valuable memories
- [ ] Consolidation feels natural, not bureaucratic

---

## Next Steps

1. **Review this plan with Juan**
2. Decide on open questions
3. Start Phase 1 implementation
