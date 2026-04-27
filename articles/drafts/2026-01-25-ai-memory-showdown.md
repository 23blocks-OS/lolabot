# AI Memory Showdown: SQLite vs Memvid V2 for Persistent Agent Memory

**Status:** Draft
**Target:** Medium, 3Metas Blog, LinkedIn
**Author:** Juan Pelaez (with Lola)
**Date:** 2026-01-25

---

## TL;DR

We benchmarked SQLite+sqlite-vec against Memvid V2 for AI agent memory. Memvid V2 won on search speed (16x faster) and storage (5x smaller). SQLite won on insert speed. For persistent AI assistants that search more than they write, Memvid V2 is the better choice.

---

## The Problem

Building a persistent AI assistant means solving memory. The LLM's context window is temporary - everything disappears between sessions. You need external storage that:

1. Persists across sessions
2. Retrieves relevant information quickly
3. Scales without becoming unwieldy
4. Stays portable (no server dependencies)

The common approaches:
- **Markdown files** - Simple, but no semantic search
- **Vector databases** - Semantic search, but infrastructure overhead
- **SQLite + vectors** - Best of both worlds?
- **Memvid** - New contender using video-codec-inspired storage

We tested the last two head-to-head.

---

## The Contenders

### SQLite + sqlite-vec

The established approach. SQLite is battle-tested (literally everywhere), and sqlite-vec adds vector similarity search via an extension.

**Setup:**
- SQLite database with memories table
- sqlite-vec extension for vector search
- sentence-transformers for embeddings (all-MiniLM-L6-v2)

**Architecture:**
```
memories.db
├── memories table (id, type, content, tags, created_at)
└── memory_vectors virtual table (id, embedding[384])
```

### Memvid V2

The newcomer. Originally encoded text as QR codes in MP4 files (seriously). V2 is a complete Rust rewrite with a custom `.mv2` binary format.

**Setup:**
- Single Python package: `pip install memvid-sdk`
- No external embedding model needed
- Uses Tantivy (Rust search engine) internally

**Architecture:**
```
memories.mv2
└── Single binary file with everything
```

---

## The Test

29 memories covering:
- Personal facts
- Events and milestones
- Journal entries
- File references
- Technical learnings

10 natural language queries like:
- "What health issues has Juan had?"
- "What happened in Ecuador?"
- "Show me photos from important events"

---

## Results

| Metric | SQLite+vec | Memvid V2 | Winner |
|--------|------------|-----------|--------|
| Init time | 1.66s | 0.03s | Memvid (59x) |
| Insert 29 memories | 0.68s | 5.89s | SQLite (9x) |
| Avg search time | 18.85ms | 1.17ms | **Memvid (16x)** |
| Storage size | 1,592 KB | 332 KB | Memvid (4.8x) |

### The Surprise

Memvid's internal search time was **0.8ms**. Sub-millisecond retrieval from a single file, no server, no infrastructure.

SQLite's 19ms includes embedding the query with sentence-transformers in Python. Memvid has embeddings built into its Rust core.

---

## Why This Matters

For an AI assistant:
- **Searches happen constantly** (every conversation turn)
- **Inserts happen rarely** (when learning something new)

A 16x improvement on the frequent operation beats a 9x improvement on the rare operation.

### The Portability Win

```bash
# Memvid: One file, take it anywhere
cp memories.mv2 /backup/
git add memories.mv2  # Yes, you can version control it

# SQLite: Also one file, but larger
cp memories.db /backup/  # 5x larger
```

### Time Travel

Memvid V2 supports querying historical states:

```python
# What did I know as of frame 100?
result = mem.find("query", as_of_frame=100)
```

This is built into the format. SQLite would need WAL configuration and additional tooling.

---

## The Gotcha: Append-Only

Here's what the benchmarks don't tell you: **Memvid V2 is append-only**. You cannot update records.

We discovered this when building a two-tier memory system (short-term → long-term). We wanted to track:
- `reinforcement_count` - how many times a memory was re-confirmed
- `access_count` - how many times a memory was retrieved
- `last_accessed` - when it was last used

With SQLite, this is trivial:

```sql
UPDATE memories SET access_count = access_count + 1 WHERE id = ?
```

With Memvid V2, you can't. The `.mv2` format is immutable once written.

### The Solution: Hybrid Architecture

Don't choose - use both. Think of it like Redis + PostgreSQL:

```
Memvid V2 (Redis-like)     SQLite (PostgreSQL-like)
├── Fast search            ├── access_count
├── Immutable content      ├── reinforcement_count
├── 16x faster queries     ├── last_accessed
└── Append-only            └── UPDATE-able
```

**Search flow:**
1. Query Memvid for relevant memories (fast)
2. Look up metadata in SQLite (counters, relationships)
3. Update access_count in SQLite
4. Return enriched results

**Write flow:**
1. Add memory to Memvid (content + embeddings)
2. Create metadata row in SQLite (id, created_at, counters=0)

This gives you the best of both worlds: sub-millisecond semantic search AND mutable metadata.

### Why It's Still Worth It

For most AI agent memory use cases, even without the hybrid approach:

- **Memories are written once** - Facts don't change often
- **Search is the hot path** - 16x faster search outweighs update limitations
- **Deduplication works** - You can detect duplicates, just can't update counters
- **Time-travel is read-only anyway** - Historical queries don't need updates

---

## When to Use What

### Choose Memvid V2 when:
- Search speed matters (interactive AI)
- You want minimal dependencies
- Portability is important
- You're building append-mostly systems
- You want time-travel debugging

### Choose SQLite+vec when:
- You need to **update records** (counters, timestamps, status flags)
- You need complex SQL queries (JOINs, aggregations)
- Insert performance is critical
- You want maximum ecosystem compatibility
- Your team already knows SQL

---

## The Markdown Question

Before diving into databases, we researched whether simple markdown files work.

**Surprising finding:** Letta's benchmark showed filesystem-based agents scored 74% on LoCoMo, beating Mem0's specialized graph memory (68.5%).

Why? LLMs are heavily trained on file operations. They use filesystem tools more reliably than specialized memory APIs.

**But there's a limit.** Claude's documentation calls it "fading memory" - as markdown files grow, the signal gets lost in noise. The context window isn't infinite, and finding the right information becomes harder.

**Our conclusion:** Markdown for curated high-level context (project instructions, key facts). Database/Memvid for queryable details (file indexes, searchable events).

---

## What We're Building

A three-layer hybrid system for our AI assistant Lola:

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Curated Context (Markdown)                            │
│  ├── CLAUDE.md           # Project instructions                 │
│  ├── memory/goals.md     # Current priorities                   │
│  └── memory/journal.md   # Key events                           │
│                                                                 │
│  → Loaded into LLM context every session                        │
│  → Future-proof: when context windows grow, more fits           │
│  → Human-readable backup                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: Fast Search (Memvid V2) — like Redis                  │
│  ├── memories.mv2        # Long-term facts, events              │
│  ├── short-term.mv2      # Recent, staging area                 │
│  └── files.mv2           # File location index                  │
│                                                                 │
│  → Sub-millisecond semantic search                              │
│  → Immutable, append-only                                       │
│  → Queried on demand during conversations                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: Mutable Metadata (SQLite) — like PostgreSQL           │
│  └── memory_meta.db                                             │
│      ├── access_counts    # How often each memory is used       │
│      ├── reinforcements   # How many times re-confirmed         │
│      └── relationships    # Links between memories              │
│                                                                 │
│  → UPDATE-able counters and timestamps                          │
│  → Relational queries (JOINs, aggregations)                     │
│  → Tracks what's actually useful                                │
└─────────────────────────────────────────────────────────────────┘
```

### The Redis/PostgreSQL Analogy

| Component | Analogy | Strength |
|-----------|---------|----------|
| Memvid V2 | Redis | Fast reads, simple, cache-like |
| SQLite | PostgreSQL | Mutable, relational, ACID |
| Markdown | Source files | Human-readable, version-controlled |

### Why Keep Markdown?

1. **Context window bet** - When LLM context grows to 1M+ tokens, we want curated knowledge ready to load
2. **Human-readable backup** - Can always rebuild indexes from markdown
3. **Version control** - Git tracks changes, enables rollback
4. **Portability** - Works everywhere, no dependencies

The markdown files are the source of truth. Memvid and SQLite are derived indexes optimized for different access patterns.

---

## Try It Yourself

```bash
# Install
pip install memvid-sdk

# Create memory
python -c "
import memvid_sdk

with memvid_sdk.use('basic', 'test.mv2', mode='create', enable_vec=True) as mem:
    mem.put(text='The quick brown fox jumps over the lazy dog')
    mem.put(text='AI memory systems are evolving rapidly')

with memvid_sdk.use('basic', 'test.mv2', enable_vec=True) as mem:
    result = mem.find('animal jumping')
    print(result['hits'][0]['snippet'])
"
```

---

## Conclusion

The AI memory landscape is evolving fast. A year ago, everyone was building RAG pipelines with vector databases. Now we have single-file solutions that outperform them.

Memvid V2's combination of speed, portability, and simplicity makes it our choice for persistent AI assistant memory. The 16x search improvement and 5x storage reduction are hard to argue with.

The insert speed tradeoff is acceptable for our use case. Memories are written occasionally; they're searched constantly.

What memory approach are you using for your AI systems?

---

## Resources

- [Memvid GitHub](https://github.com/memvid/memvid)
- [sqlite-vec](https://github.com/asg017/sqlite-vec)
- [Letta Memory Benchmark](https://www.letta.com/blog/benchmarking-ai-agent-memory)
- [A-MEM: Agentic Memory](https://arxiv.org/abs/2502.12110)

---

*This article was co-written with Lola, an AI assistant running on Claude. The benchmarks were conducted on a Mac Mini with Ubuntu.*
