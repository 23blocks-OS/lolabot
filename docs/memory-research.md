# Memory Architecture Research

Research conducted: 2026-01-25

## The Question

Should Lola's memory system use text files, databases, or something else?

---

## Option 1: Text/Markdown Files (Current Approach)

**How it works:** Markdown files loaded directly into Claude's context window.

**Benchmarks:**
- Letta filesystem agent: **74.0%** on LoCoMo benchmark
- Beat Mem0's graph variant (68.5%) with minimal tuning

**Pros:**
- Transparent, editable, version-controllable (git)
- Loads directly into context - no retrieval layer needed
- LLMs are highly trained on filesystem operations
- Simple to implement and maintain
- Human-readable and auditable

**Cons:**
- "Fading memory" problem as files grow
- Signal gets lost in noise at scale
- Requires manual curation
- No semantic search capability
- Full file rewrite for any update

**Best for:** Curated high-level context, project instructions, key facts.

**Source:** [Letta Benchmark](https://www.letta.com/blog/benchmarking-ai-agent-memory)

---

## Option 2: SQLite Database

**How it works:** Structured storage with query capability.

**Benchmarks:**
- **2-10x faster** reads than filesystem
- **3x faster** JSON processing with JSONB
- Real case: 30 min → 10 sec startup time

**Pros:**
- Fast partial updates (don't rewrite everything)
- Complex querying (find all X related to Y)
- ACID compliance, no corruption
- Single file, portable
- Can store JSON/BLOB alongside structured data

**Cons:**
- Can't load directly into context
- Requires query layer
- More complexity than flat files

**Best for:** File indexes, searchable facts, structured metadata, anything needing queries.

**Source:** [SQLite Faster Than Filesystem](https://sqlite.org/fasterthanfs.html)

---

## Option 3: Vector Database (Semantic Search)

**How it works:** Store embeddings, retrieve by meaning similarity.

**Options:**
- sqlite-vec / sqlite-vector (embedded, 30MB)
- Chroma, Pinecone, Weaviate (standalone)
- PostgreSQL pgvector

**Pros:**
- "Show me memories about X" without exact keyword match
- Finds conceptually related information
- Scales to millions of entries

**Cons:**
- Requires embedding generation
- Can retrieve irrelevant results (semantic != relevant)
- Adds complexity and dependencies
- Embedding model choice matters

**Best for:** Large unstructured content, finding related memories, semantic search.

**Source:** [SQLite Vector](https://www.sqlite.ai/sqlite-vector)

---

## Option 4: Hybrid (SQLite + Vector + Files)

**How it works:** Combine strengths of each approach.

**Architecture:**
```
┌─────────────────────────────────────────┐
│  Curated Markdown (CLAUDE.md, etc.)     │  ← Loaded into context
├─────────────────────────────────────────┤
│  SQLite Database                        │
│  ├── Structured facts table             │
│  ├── File index table                   │
│  ├── Event/memory links                 │
│  └── Vector embeddings (sqlite-vec)     │  ← Queried on demand
├─────────────────────────────────────────┤
│  Raw Files (images, PDFs, etc.)         │  ← Referenced by path
└─────────────────────────────────────────┘
```

**Pros:**
- Best of all worlds
- Curated context + queryable facts + semantic search
- Files stay human-readable, database handles scale

**Cons:**
- More moving parts
- Need to keep systems in sync

**Source:** [SQLite RAG](https://github.com/sqliteai/sqlite-rag)

---

## Option 5: A-MEM / Zettelkasten (Self-Organizing)

**How it works:** Each memory is an atomic "note" that links to related notes. The network self-organizes as new memories arrive.

**Key principles:**
- Atomic notes (one concept per note)
- Bidirectional links (if A relates to B, B relates to A)
- Emergent structure (categories emerge from connections)
- Memory evolution (new memories can update old ones)
- "Sleep consolidation" (periodically reorganize/compress)

**Benchmark:** A-MEM paper accepted at NeurIPS 2025

**Pros:**
- Mirrors how human memory works
- Discovers non-obvious connections
- Grows organically
- Can trigger updates to historical memories

**Cons:**
- Complex to implement well
- Requires agent to manage links
- May over-link or create noise

**Best for:** Long-term knowledge accumulation, finding hidden connections.

**Source:** [A-MEM Paper](https://arxiv.org/abs/2502.12110)

---

## Option 6: TeleMem (Video/Multimodal Memory)

**How it works:** Memory as "semantic trajectories" - preserves temporal order, causal dependency, and state evolution. Supports video, audio, and text.

**Benchmarks:**
- **19% higher accuracy** than Mem0
- **43% fewer tokens**
- **2.1x faster**

**Architecture:**
- Three memory types: user profile, bot profile, event memory
- Threaded DAG structure for causal context
- Video → frames → captions → vector database
- "Closure-based retrieval" reconstructs coherent context

**Pros:**
- Handles video natively
- Preserves causality (what led to what)
- Deduplication built-in
- Drop-in replacement for Mem0

**Cons:**
- Newer, less battle-tested
- Requires multimodal LLM for full benefit
- More infrastructure

**Best for:** Future visual memory, video understanding, temporal reasoning.

**Source:** [TeleMem GitHub](https://github.com/TeleAI-UAGI/telemem)

---

## Key Insight: Agent Capability > Storage Mechanism

From Letta's research:

> "Whether an agent 'remembers' something depends on whether it successfully retrieves the right information when needed."

Simple filesystem agents outperformed specialized memory tools because:
1. LLMs are highly trained on file operations
2. Iterative search beats single-hop retrieval
3. Simple tools are more reliable than complex ones

**The storage mechanism matters less than the agent's ability to use it effectively.**

---

## Recommendation for Lola

### Phase 1: Enhanced Hybrid (Start Now)

Keep markdown for what works, add SQLite for what doesn't:

| Content Type | Storage | Why |
|--------------|---------|-----|
| High-level context | `CLAUDE.md`, `memory/*.md` | Loads into context, curated |
| File index | SQLite `files` table | Query "find photos from X", partial updates |
| Structured facts | SQLite `facts` table | Searchable, linkable |
| Memory events | SQLite `events` table | Link files to milestones |
| Raw files | Filesystem | Just store paths in SQLite |

**Implementation:**
```sql
-- files table
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE,
    name TEXT,
    type TEXT,
    size INTEGER,
    created_at DATETIME,
    modified_at DATETIME,
    tags TEXT,  -- JSON array
    thumbnail_path TEXT,
    metadata TEXT  -- JSON
);

-- events table
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    name TEXT,
    date DATE,
    description TEXT,
    tags TEXT,
    related_people TEXT  -- JSON array
);

-- file_events junction
CREATE TABLE file_events (
    file_id INTEGER,
    event_id INTEGER,
    FOREIGN KEY (file_id) REFERENCES files(id),
    FOREIGN KEY (event_id) REFERENCES events(id)
);
```

### Phase 2: Add Vector Search (When Needed)

Add sqlite-vec when we have enough content that keyword search isn't enough:
- Embed file names + descriptions
- Embed event descriptions
- Enable "find memories similar to X"

### Phase 3: Zettelkasten Links (Future)

Add bidirectional linking between memories, people, events, files. Let patterns emerge.

### Phase 4: Video/Multimodal (Future)

When we have photos/videos to index, consider TeleMem's trajectory approach.

---

## What NOT to Do

1. **Don't over-engineer upfront** - Simple filesystem agent beat complex memory systems
2. **Don't abandon markdown** - It works, it's transparent, it loads into context
3. **Don't use vector-only** - Semantic search misses exact matches
4. **Don't forget curation** - All systems suffer from noise; curation is essential

---

## Sources

- [Letta Benchmark: Is a Filesystem All You Need?](https://www.letta.com/blog/benchmarking-ai-agent-memory)
- [InfoWorld: AI Memory is a Database Problem](https://www.infoworld.com/article/4101981/ai-memory-is-just-another-database-problem.html)
- [A-MEM: Agentic Memory (NeurIPS 2025)](https://arxiv.org/abs/2502.12110)
- [TeleMem: Multimodal Memory](https://github.com/TeleAI-UAGI/telemem)
- [SQLite Faster Than Filesystem](https://sqlite.org/fasterthanfs.html)
- [SQLite Vector Extension](https://www.sqlite.ai/sqlite-vector)
- [Claude Code Memory Docs](https://code.claude.com/docs/en/memory)
- [How Claude Memory Works](https://rajiv.com/blog/2025/12/12/how-claude-memory-actually-works-and-why-claude-md-matters/)
- [VentureBeat: 2026 Data Predictions](https://venturebeat.com/data/six-data-shifts-that-will-shape-enterprise-ai-in-2026)
