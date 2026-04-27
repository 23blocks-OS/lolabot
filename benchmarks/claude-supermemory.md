# claude-supermemory by supermemoryai

**Repo:** https://github.com/supermemoryai/claude-supermemory
**Reviewed:** 2026-01-31
**Stars:** 660 | **Forks:** 35 | **License:** MIT
**Created:** 2026-01-22 | **Last updated:** 2026-01-31 (9 days old)
**Language:** JavaScript (1.1MB) + HTML (149KB)
**Stack:** Node.js, Supermemory API (cloud service), Claude Code Plugins/Hooks
**Pricing:** Requires Supermemory Pro or above (paid cloud service)

---

## What It Is

A Claude Code plugin that gives persistent memory across sessions by sending conversation data to Supermemory's cloud API. Uses Claude Code's hook system (SessionStart, PostToolUse, Stop) to automatically capture and recall context.

This is a **thin client** — the plugin itself is ~400 lines of JS. All intelligence (embeddings, search, knowledge graph, profile extraction) lives in Supermemory's cloud service.

---

## Architecture

```
Claude Code Session
  ├── SessionStart hook → calls Supermemory API → injects <supermemory-context> into prompt
  ├── PostToolUse hook → observes Edit/Write/Bash/Task calls (currently no-op)
  ├── Stop hook → reads transcript JSONL → formats new entries → sends to Supermemory API
  └── super-search skill → manual search via `node search-memory.cjs "query"`
```

### Supermemory Cloud Service (Behind the API)

| Component | Technology |
|-----------|-----------|
| API Framework | Hono (HTTP) |
| Database | PostgreSQL + vector extensions |
| ORM | Drizzle |
| Search | Cosine similarity on vector embeddings |
| Profile | Auto-extracted static/dynamic facts |
| Knowledge Graph | Mentioned but details undisclosed |
| Auth | better-auth + OAuth2 |
| Infrastructure | Cloudflare Durable Objects |

### Data Flow

```
Session Stop
  → Read transcript JSONL from Claude Code
  → Filter to user + assistant messages since last capture
  → Strip system reminders, supermemory tags
  → Format as [role:user]...[user:end] / [role:assistant]...[assistant:end]
  → Truncate tool results to 500 chars, skip Read tool results
  → POST to api.supermemory.ai/add (with containerTag = project hash)

Session Start
  → GET api.supermemory.ai/profile (with containerTag)
  → Receive: static facts (persistent) + dynamic facts (recent)
  → Format as <supermemory-context>...</supermemory-context>
  → Inject into Claude's system prompt via SessionStart hook
```

---

## Key Components Analyzed

### 1. Context Injection (context-hook.js)

On every session start:
- Fetches user profile from Supermemory API using project-specific `containerTag`
- containerTag = `claudecode_project_` + SHA256(git root path)[:16]
- Returns two categories of facts:
  - **Static** (persistent): "User prefers TypeScript", "Uses Bun as package manager"
  - **Dynamic** (recent): "Working on authentication flow"
- Injected as `<supermemory-context>` block with instructions to "reference only when relevant"

### 2. Transcript Capture (summary-hook.js + transcript-formatter.js)

On session stop:
- Reads the raw Claude Code transcript JSONL file
- Tracks last-captured UUID per session in `~/.supermemory-claude/trackers/`
- Formats new entries since last capture:
  - User messages: `[role:user]\n...\n[user:end]`
  - Assistant text: `[role:assistant]\n...\n[assistant:end]`
  - Tool uses: `[tool:Edit]\nfile_path: ...\n[tool:end]`
  - Tool results: `[tool_result:Bash status="success"]\n...\n[tool_result:end]`
- Skips: Read tool results, thinking blocks, entries < 100 chars
- Truncates tool inputs to 200 chars, tool results to 500 chars
- Strips `<system-reminder>` and `<supermemory-context>` tags
- Sends formatted text to Supermemory API as a single memory entry

### 3. Observation Compression (compress.js)

Compresses tool observations into one-liners:
- `Edit`: `Edited src/file.ts: "old..." → "new..."`
- `Write`: `Created src/file.ts (1234 chars)`
- `Bash`: `Ran: npm test - Run unit tests [FAILED]`
- `Task`: `Spawned Explore: find auth files`
- Currently NOT actively used in hooks (observation-hook.js is a no-op)

### 4. Search Skill (search-memory.js)

Manual search triggered by the `super-search` skill:
- Calls `client.getProfile(containerTag, query)` — profile API doubles as search
- Falls back to `client.search(query, containerTag)` if profile returns no search results
- Displays: static facts, dynamic facts, relevant memories with similarity scores

### 5. Codebase Indexing (index command)

Slash command `/claude-supermemory:index` that:
- Instructs Claude to explore the codebase in 4 phases (overview, architecture, conventions, key files)
- Makes 20-50 tool calls to read and analyze files
- Compiles findings into a single summary
- Saves to Supermemory via `add-memory.cjs`

### 6. Authentication (auth.js)

- Starts local HTTP server on port 19876
- Opens browser to `console.supermemory.ai/auth/connect`
- Receives API key via callback
- Stores in `~/.supermemory-claude/credentials.json`
- 25-second timeout for auth flow

---

## Supermemory Cloud: What's Behind the API

Based on research (documentation, DeepWiki analysis, web):

| Feature | Detail |
|---------|--------|
| Storage | PostgreSQL + vector extensions (embeddings stored alongside metadata) |
| Search | Hybrid: semantic (cosine similarity on embeddings) + keyword |
| Profile | Auto-extracted static + dynamic facts from stored memories |
| Knowledge Graph | Claimed but implementation details undisclosed |
| Temporal Reasoning | Dual timestamps: `documentDate` (when captured) + `eventDate` (when happened) |
| Deduplication | Built into memory engine (handles updates, conflicting info) |
| Scale | Claims 50M tokens per user, 5B tokens daily globally |
| Recall Speed | Claims sub-300ms |
| Benchmark | Claims SOTA on LongMemEval (71.43% multi-session, 76.69% temporal reasoning) |
| Compared to | Claims 41.4% faster than Mem0 |
| Connectors | GitHub, Gmail, Google Drive, Notion, OneDrive, S3, web crawlers |

### Pricing (Not Transparent)

- Free tier: Exists but limits unclear
- **Pro required** for Claude Code plugin (stated in README)
- Pricing page not publicly indexed with specific numbers

---

## Honest Assessment: Do Their Claims Hold Up?

### Claim 1: "Persistent memory across sessions"
**Verdict: YES, but with caveats.**
The mechanism works: conversation data is captured at session end, recalled at session start. However:
- Recall quality depends entirely on Supermemory's cloud processing
- Only captures since last stop — if Claude Code crashes, that session is lost
- Profile injection is limited to `maxProfileItems` (default 5 static + 5 dynamic facts per session)
- No way to verify what was actually stored or how it was processed

### Claim 2: "Your agent remembers what you worked on"
**Verdict: PARTIALLY.**
- Captures user messages and assistant responses
- Captures tool uses (Edit, Write, Bash, Task) but NOT Read/Glob/Grep results
- Truncates tool results to 500 chars — significant context loss
- Observation hook is a no-op — tool compression exists but isn't used
- Thinking blocks are skipped entirely (huge loss of reasoning context)
- Only captures text from transcript — no understanding of what was actually accomplished

### Claim 3: "State of the art memory"
**Verdict: UNVERIFIABLE.**
- LongMemEval benchmark scores are self-reported
- No independent reproduction available
- The benchmark repo (MemoryBench) is their own
- No peer review or third-party validation
- "41.4% faster than Mem0" — speed isn't the primary concern for accuracy

### Claim 4: "Context injection" with relevant memories
**Verdict: SHALLOW.**
- Injects at most 10 static + 10 dynamic facts (configurable)
- No semantic routing — same profile regardless of what you're working on
- The query to profile API is just the project name, not the current task
- No way to inject context mid-session based on what you're discussing
- Search requires manual skill invocation

### Claim 5: "Automatic capture"
**Verdict: LOSSY.**
- Captures raw transcript text, not semantic understanding
- No extraction of: decisions made, patterns learned, problems solved, file relationships
- No categorization of memory types (fact vs event vs decision vs preference)
- No confidence scoring or reinforcement
- No deduplication at capture time (relies on Supermemory cloud to handle)

---

## Comparison: Supermemory vs Lola's Memory System

| Aspect | claude-supermemory | Lola Memory System |
|--------|-------------------|-------------------|
| **Architecture** | Cloud API (Supermemory.ai) | Local (Memvid V2 + SQLite + Markdown) |
| **Data Sovereignty** | All data sent to third-party cloud | 100% local, on our machine |
| **Cost** | Paid subscription (Pro required) | Free (open-source Memvid SDK) |
| **Privacy** | Conversation data leaves the machine | Nothing leaves mini-lola |
| **Offline** | Requires internet for every operation | Fully offline capable |
| **Latency** | Network round-trip per operation | Local disk, sub-millisecond |
| **Storage** | PostgreSQL + vector extensions (cloud) | Memvid V2 (.mv2 files) + SQLite |
| **Search** | Hybrid semantic + keyword (cloud) | Semantic search (Memvid, 16x faster than v1) |
| **Memory Types** | Untyped text blobs | Typed: fact, event, learning, decision, person, goal, preference, pattern, insight |
| **Deduplication** | Cloud-side (opaque) | Local similarity check (0.85 threshold) with reinforcement counting |
| **Confidence** | None visible | Explicit confidence scores (0.0-1.0) with reinforcement boost |
| **Access Tracking** | None visible | SQLite tracks access_count per memory |
| **Reinforcement** | None visible | Duplicate mentions boost confidence + reinforcement_count |
| **Two-Tier Memory** | Static/dynamic (auto-classified in cloud) | Long-term (.mv2) + Short-term (.mv2) with explicit promotion |
| **Promotion Logic** | Opaque (cloud decides) | Explicit: 7 days + 2 reinforcements → promote |
| **Temporal** | documentDate + eventDate (cloud) | Explicit --date flag per memory, searchable by year |
| **Human-Readable** | No local copy | Dual-save: index + markdown files (journal, profile, goals) |
| **Context Injection** | Auto at session start (hook) | Manual: read CLAUDE.md + brain/*.md files |
| **Session Capture** | Auto at session stop (transcript parsing) | Manual: operator decides what to remember |
| **Codebase Indexing** | /index command → saves to cloud | file_indexer.py → local .mv2 index |
| **Knowledge Graph** | Claimed (cloud, opaque) | None (flat semantic index) |
| **Profile System** | Auto-extracted static + dynamic facts | Manual: juan-profile.md + memory_indexer.py |
| **Integration** | Claude Code plugin (hooks) | Direct tool access in session |

---

## What They Do Better Than Us

### 1. Automatic Session Capture
**Their advantage:** Every session is automatically captured at stop. No manual action needed.
**Our gap:** We only remember what we explicitly `memory_indexer.py add`. If I forget to save something, it's lost.
**Should we adopt?** YES — but locally. We could hook into Claude Code's transcript JSONL to extract key decisions and learnings automatically at session end. No cloud needed.

### 2. Automatic Context Injection at Session Start
**Their advantage:** Every new session starts with relevant context automatically loaded.
**Our gap:** We rely on CLAUDE.md being read (happens automatically) and manually reading brain/*.md files.
**Should we adopt?** PARTIALLY — We already have CLAUDE.md auto-loaded. We could add a SessionStart hook that runs `memory_indexer.py find` with the project context and injects relevant memories. But our current system (reading CLAUDE.md + brain/ files) is arguably better because it's predictable and complete rather than AI-selected snippets.

### 3. Profile System (Static vs Dynamic Facts)
**Their advantage:** Automatic classification of persistent facts vs recent context.
**Our gap:** We have typed memories (fact, event, learning) but no automatic "what's recent" filtering.
**Should we adopt?** MAYBE — The two-tier long-term/short-term memory we already have serves a similar purpose. Short-term = recent, long-term = persistent. The difference is theirs auto-classifies; ours requires explicit placement.

### 4. Codebase Indexing as Memory
**Their advantage:** `/index` command explores and summarizes the codebase into memory.
**Our gap:** We have file_indexer.py for file locations, but no "codebase understanding" memory.
**Should we adopt?** LOW PRIORITY — As Lola, I read codebases directly. Storing a summary of a codebase is less useful when you can just read the code.

---

## What We Do Better Than Them

### 1. Data Sovereignty (MAJOR)
All our data stays on mini-lola. Their system sends every conversation to a third-party cloud. For a personal assistant managing emails, finances, immigration documents, and health records, this is a dealbreaker. **Our approach is categorically better for privacy.**

### 2. Typed Memory with Metadata
They store untyped text blobs. We store typed memories (fact, event, learning, decision, goal, preference, pattern, insight) with dates, tags, confidence scores, and access tracking. Our memories are structured and queryable by type. **Our approach gives much richer recall.**

### 3. Deduplication + Reinforcement
They rely on opaque cloud-side dedup. We detect duplicates locally (0.85 similarity threshold) and increment reinforcement_count + boost confidence. Frequently mentioned facts get higher confidence scores. **Our approach makes frequently-repeated information more trustworthy.**

### 4. Human-Readable Persistence
We dual-save: index (semantic search) + markdown files (human-readable). Juan can open `journal-2026.md` or `juan-profile.md` in any text editor. Their system has no local human-readable copy. **Our approach survives tool failure, API changes, and service shutdowns.**

### 5. Explicit Memory Control
We choose what to remember. They capture everything automatically, which means noise (debugging output, failed attempts, irrelevant exploration) gets stored alongside valuable decisions. **Our approach has higher signal-to-noise ratio.**

### 6. Cost and Availability
Ours is free, works offline, and has no vendor dependency. Theirs requires a paid subscription and internet connectivity. If Supermemory.ai goes down or changes pricing, their memory system stops working. **Our approach has zero external dependencies.**

### 7. Two-Tier with Promotion Logic
Our short-term → long-term promotion (7 days + 2 reinforcements) ensures only validated information makes it to permanent memory. Their cloud decides internally with no visibility. **Our approach is more transparent and controllable.**

---

## What We Should Consider Adopting

| Feature | Priority | How |
|---------|----------|-----|
| **Auto-capture at session end** | HIGH | Hook into Claude Code's Stop event, extract key decisions/learnings from transcript, auto-add to short-term memory |
| **Auto-inject at session start** | MEDIUM | Hook into SessionStart, run memory search for project context, inject as system prompt addition |
| **Recent context filter** | LOW | Add a "recently accessed" or "recently added" query to memory_indexer.py |

### What NOT to Adopt

| Feature | Why Not |
|---------|---------|
| Cloud storage | Privacy dealbreaker. We handle personal data. |
| Paid API dependency | We already have a working free local solution |
| Untyped memory | We have better structured types |
| Opaque profile extraction | Our explicit typing is more reliable |
| Auto-capture of everything | High noise. Our selective approach is better. |
| Knowledge graph (cloud) | Complexity without clear benefit at our scale |

---

## Verdict

**claude-supermemory is a convenience wrapper around a cloud API, not a memory system.**

The actual intelligence lives in Supermemory's cloud service — the plugin is just a thin client that reads transcripts and calls APIs. For someone who wants zero-setup memory for Claude Code, it works. But the trade-offs are significant:

1. **Privacy:** All your coding conversations go to a third-party server
2. **Cost:** Requires paid subscription
3. **Control:** You can't see or modify how memories are processed
4. **Durability:** If the service shuts down, your memories are gone
5. **Quality:** Auto-capture is lossy (500-char truncation, skipped tool results, no semantic extraction)
6. **Depth:** Untyped text blobs vs our structured, typed, scored memories

**Lola's memory system is fundamentally superior for our use case** — a personal assistant handling sensitive data. The only feature worth borrowing is automatic session capture via Claude Code hooks, which we can implement locally without any cloud dependency.

The 660 stars (in 9 days) reflect good marketing and the convenience factor, not technical superiority. The system is well-packaged for people who want plug-and-play memory, but for anyone who cares about data sovereignty, cost, or memory quality, a local solution like ours is the better path.
