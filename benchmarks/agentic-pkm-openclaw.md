# Agentic PKM with OpenClaw, PARA, and QMD by Nat Eliason

**Source:** https://x.com/nateliason/status/2017636775347331276
**Author:** Nat Eliason
**Reviewed:** 2026-01-31
**Type:** Article / Framework Design (not a product/repo)
**Engagement:** 63.5K views, 239 likes, 756 bookmarks (as of review date)
**Based on:** "Building a Second Brain" by Tiago Forte (PARA method)
**Tools mentioned:** OpenClaw (AI assistant), QMD (vector embedding tool)

---

## What It Is

A framework for giving AI coding agents persistent, structured memory using the PARA organizational method, atomic facts, and weekly synthesis. The core idea: no database, no special tooling, no vendor lock-in — just plain files that any AI assistant can read and write.

**Core proposition:** "Your AI assistant reads and writes plain files. If you switch assistants tomorrow, your memory comes with you."

---

## Architecture: Three Layers

### Layer 1: PARA Directory Structure

Based on Tiago Forte's PARA method (Projects, Areas, Resources, Archive):

```
knowledge/
├── Projects/          - Active projects with defined outcomes
│   └── project-name/
│       └── index.md   - Project context, goals, status
├── Areas/             - Ongoing responsibilities
│   └── area-name/
│       └── index.md   - Area description, key info
├── Resources/         - Reference material by topic
│   └── topic/
│       └── index.md   - Collected knowledge on topic
├── Archive/           - Completed/inactive items
│   └── item/
│       └── index.md   - Preserved for reference
└── Daily/             - Daily notes (working memory)
    └── YYYY-MM-DD.md  - What happened today
```

Each entity gets a folder with an `index.md` containing the current understanding summary.

### Layer 2: Atomic Facts (items.json)

Each entity folder has an `items.json` file containing granular, typed facts:

```json
{
  "items": [
    {
      "fact": "Juan's income is $215,628/year",
      "category": "finance",
      "status": "active",
      "dateAdded": "2026-01-15",
      "lastAccessed": "2026-01-30",
      "accessCount": 7,
      "relatedEntities": ["3Metas", "immigration"],
      "supersededBy": null
    },
    {
      "fact": "Juan's income was $180,000/year",
      "category": "finance",
      "status": "superseded",
      "dateAdded": "2025-06-01",
      "supersededBy": "Juan's income is $215,628/year",
      "relatedEntities": ["3Metas"]
    }
  ]
}
```

**Key fields:**
- `category` — Type classification for the fact
- `status` — `active` or `superseded` (never deleted)
- `supersededBy` — Pointer to the replacement fact (preserves full history)
- `relatedEntities` — Graph-like connections to other entities
- `lastAccessed` / `accessCount` — Memory decay signals

**No-deletion rule:** Facts are NEVER deleted, only superseded with a pointer to the replacement. This preserves full history and allows understanding how knowledge evolved.

### Layer 3: Weekly Synthesis

Periodic process that rewrites `summary.md` (or `index.md`) per entity:

1. Load all active facts from `items.json`
2. Sort by recency tier:
   - **Hot** — Accessed in last 7 days
   - **Warm** — Accessed in last 30 days
   - **Cold** — Not accessed in 30+ days
3. Sort by `accessCount` within each tier
4. Rewrite `summary.md` emphasizing hot facts, briefly mentioning warm, and archiving cold
5. Cold entities may be moved to Archive/

This mimics how human memory works: frequently accessed information stays vivid, unused information fades but isn't lost.

---

## Entity Creation Heuristics

When should a new entity (folder) be created vs. keeping notes in daily files?

**Create entity if:**
- Mentioned 3+ times across different days
- Is a significant project, company, or person
- Has multiple distinct facts worth tracking
- Will likely be referenced again

**Keep in daily notes if:**
- One-off mention
- No clear ongoing relevance
- Purely ephemeral context

---

## QMD Tool (Vector Embeddings)

QMD (Quartz Markdown) provides semantic search over the plain-file knowledge base:

```bash
qmd update --pull    # Re-index all markdown files
qmd embed            # Rebuild vector embeddings
```

This gives the AI assistant the ability to find relevant knowledge semantically, not just by filename or keyword.

---

## Comparison: Eliason's Framework vs Lola's Memory System

| Aspect | Eliason (PARA + Atomic Facts) | Lola (Memvid + SQLite + Markdown) |
|--------|-------------------------------|-----------------------------------|
| **Storage** | Plain files (JSON + Markdown) | Memvid V2 (.mv2) + SQLite + Markdown |
| **Search** | QMD vector embeddings on markdown | Memvid semantic search (16x faster than v1) |
| **Structure** | PARA directory hierarchy | Flat semantic index + typed memories |
| **Memory Types** | Category field on atomic facts | Explicit types: fact, event, learning, decision, person, goal, preference, pattern, insight |
| **Deduplication** | Supersede model (old fact → superseded, new fact → active) | Similarity detection (0.85 threshold) + reinforcement counting |
| **Decay** | Hot/Warm/Cold tiers by lastAccessed + accessCount | Two-tier: short-term → long-term promotion (7 days + 2 reinforcements) |
| **History** | Full (never deleted, supersededBy pointer) | Partial (duplicates detected but original not explicitly linked) |
| **Graph** | relatedEntities field on each fact | None (flat index) |
| **Human-Readable** | Yes (markdown + JSON, plain files) | Yes (dual-save to markdown + index) |
| **Synthesis** | Weekly rewrite of summaries from active facts | Manual (operator decides when to update profile/journal) |
| **Data Sovereignty** | 100% local files | 100% local |
| **Vendor Lock-in** | None (plain files) | Low (Memvid SDK, but data is exportable) |
| **AI Integration** | Agent reads/writes files directly | Agent calls memory_indexer.py CLI |
| **Offline** | Yes | Yes |
| **Cost** | Free | Free |

---

## What They Do Better Than Us

### 1. Supersession Model (History Preservation)
**Their advantage:** When a fact changes (e.g., income goes from $180K to $215K), the old fact isn't deleted — it's marked `superseded` with a pointer to the new fact. You can trace how knowledge evolved.
**Our gap:** When we detect a duplicate/updated fact (0.85 similarity), we increment reinforcement_count but don't explicitly link old → new. The original stays in the index but there's no supersededBy relationship.
**Should we adopt?** YES — Add a `supersedes` field to memory metadata. When adding a fact that's similar to an existing one but with updated info, mark the old as superseded and link to the new one.

### 2. Entity-Based Organization (Graph Relationships)
**Their advantage:** relatedEntities field creates a lightweight knowledge graph. "Juan's income" is linked to "3Metas" and "immigration" — you can traverse related knowledge.
**Our gap:** Our memories have tags but no explicit entity relationships. Searching for related context relies entirely on semantic similarity.
**Should we adopt?** MAYBE — Tags partially serve this purpose. A full relatedEntities system adds complexity. Could be valuable for people/company profiles where relationships matter. Low priority for now.

### 3. Weekly Synthesis (Automatic Summary Refresh)
**Their advantage:** Weekly process rewrites entity summaries from active facts, naturally pushing cold info to the background. Summaries stay fresh and relevant.
**Our gap:** Our markdown files (juan-profile.md, journal-2026.md) are updated manually. Stale info doesn't automatically fade.
**Should we adopt?** PARTIALLY — An automated monthly review of short-term memory + journal updates would help. But our manual curation has higher signal quality than automated synthesis.

### 4. Decay Tiers (Hot/Warm/Cold)
**Their advantage:** Three-tier decay (7d/30d/30d+) with accessCount weighting. Frequently accessed facts stay prominent regardless of age.
**Our gap:** We have two tiers (short-term/long-term) with promotion logic, plus SQLite access_count tracking. But we don't use the access patterns to weight search results or reorganize information.
**Should we adopt?** YES — We already track access_count in SQLite. We should use it to weight search relevance (more-accessed memories should rank higher in results).

### 5. No Database Philosophy
**Their advantage:** "No database, no special tooling" — pure files that any tool can read. Maximum portability.
**Our position:** We use Memvid (binary .mv2 files) + SQLite — not directly human-readable for the index, but we dual-save to markdown. The markdown files are the "plain files" equivalent.
**Should we adopt?** NO — We already have the best of both worlds. Memvid gives us fast semantic search that plain JSON can't match. Markdown files give us the portability. Switching to pure JSON + QMD embeddings would be a downgrade in search performance.

---

## What We Do Better Than Them

### 1. Typed Memory System
They have a single `category` string. We have 10 distinct memory types (fact, event, learning, decision, person, goal, preference, pattern, insight) that carry semantic meaning and allow type-filtered search. Our system is more expressive.

### 2. Confidence Scoring + Reinforcement
They have accessCount. We have confidence scores (0.0-1.0) that get boosted when facts are reinforced by repeated mentions. This gives us a quality signal, not just a frequency signal.

### 3. Short-term → Long-term Promotion
Their model puts everything in the same pool with decay. Ours has explicit staging: new info goes to short-term, and only gets promoted to long-term after 7 days + 2 reinforcements. This filters noise more aggressively.

### 4. Semantic Search Performance
Memvid V2 provides fast semantic search without needing to rebuild embeddings (`qmd embed`). Their system requires periodic re-embedding. Ours is always up-to-date after an `add`.

### 5. CLI Tool vs File Manipulation
Our memory_indexer.py provides a clean CLI with deduplication, type validation, confidence tracking, and search — all in one tool. Their approach requires the AI to directly manipulate JSON files, which is more error-prone (malformed JSON, missing fields, concurrent writes).

### 6. Integration with Life Systems
Our memory integrates with email (security metadata), Eisenhower task matrix, file index, and agent messaging. It's part of a larger operational system. Their approach is purely a knowledge management tool.

---

## What We Should Consider Adopting

| Feature | Priority | How |
|---------|----------|-----|
| **Supersession model** | HIGH | Add `supersedes` field to memory metadata. When updating a fact, mark old as superseded, link to new |
| **Access-weighted search** | MEDIUM | Use existing SQLite access_count to boost search result ranking |
| **Periodic synthesis** | LOW | Monthly automated review: check short-term memory, update journal/profile markdown from active memories |
| **Entity heuristic** | LOW | When a topic is mentioned 3+ times in short-term, consider creating a dedicated brain/*.md file for it |

### What NOT to Adopt

| Feature | Why Not |
|---------|---------|
| Plain JSON storage | Memvid V2 gives us better search performance than JSON + QMD |
| PARA directory hierarchy | Our flat index + typed memories is simpler and works well at our scale |
| relatedEntities graph | Tags + semantic search handle relationships adequately; graph adds complexity |
| Weekly synthesis | Manual curation has higher signal quality; monthly review is sufficient |
| No-database philosophy | Our hybrid (Memvid + SQLite + Markdown) outperforms pure files |

---

## Key Ideas Worth Remembering

1. **"Never delete, only supersede"** — Preserving history of how knowledge evolved is valuable. Adding a supersededBy pointer is cheap and enables tracing knowledge changes.

2. **"Memory decay tiers"** — Hot/Warm/Cold is a good mental model. We already have the data (access_count, timestamps). We should use it to weight results.

3. **"Entity creation heuristic: 3+ mentions"** — Simple rule for when a topic deserves its own dedicated tracking. Could apply to brain/*.md file creation.

4. **"Plain files as the ultimate portability"** — Our markdown dual-save already achieves this. If Memvid ever becomes unmaintained, the markdown files survive.

5. **"Weekly synthesis refreshes summaries"** — Even if we don't automate it, periodically re-reading and updating profile/journal files with latest knowledge is a good practice.

---

## Verdict

**A thoughtful framework that validates many of our design choices while offering a few genuinely useful ideas.**

Eliason's approach is philosophically aligned with ours: local-first, privacy-respecting, vendor-independent, human-readable. The main differences are in implementation: they chose simplicity (plain files, no database) while we chose performance (Memvid + SQLite with markdown backup).

The two most actionable takeaways are:
1. **Supersession model** — cheap to implement, valuable for fact evolution tracking
2. **Access-weighted search** — we already collect the data, just need to use it

The PARA directory structure and weekly synthesis are interesting but don't offer enough improvement over our current system to justify the migration cost. Our typed memories, confidence scoring, and short-term/long-term promotion are arguably more sophisticated than their category + decay model.

**Bottom line:** We're in a good position. Our system is more feature-rich and better integrated than this framework. The supersession idea is the main thing worth stealing.
