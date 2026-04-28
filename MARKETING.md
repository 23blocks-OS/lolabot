# lolabot — Marketing & Positioning

## Tagline

**Your AI Chief of Staff. Local-first. Memory that learns. Email that's secure.**

## One-liner

Open-source Personal Assistant framework for Claude Code — with auto-memory, email security, file indexing, and task management. Everything runs on your machine. Your data never leaves.

---

## Why lolabot?

### Memory That Actually Works

Most PA frameworks treat memory as an afterthought — flat markdown files you manually maintain, or cloud APIs that send your life to someone else's server.

**lolabot has the most sophisticated memory system in the PA space:**

- **Auto-capture** — lolabot remembers facts, events, decisions, and preferences from your conversations without being asked. Say "my daughter starts school in September" once — it's saved forever.
- **Auto-recall** — Every conversation starts with your full context loaded. lolabot knows who you are, what you're working on, and what happened yesterday.
- **Semantic search** — Not keyword matching. Ask "what did we discuss about the Spain project?" and get relevant results even if you never used the word "Spain" in the original note.
- **Deduplication & reinforcement** — Mention the same fact twice? lolabot doesn't create duplicates. It reinforces the existing memory and boosts its confidence score.
- **10 memory types** — Facts, events, learnings, decisions, notes, people, goals, preferences, patterns, insights. Each with metadata, tags, dates, and confidence tracking.
- **Dual-save architecture** — Every memory is stored in both a semantic index (Memvid, for fast AI search) AND human-readable markdown files (for you to read and edit). No lock-in, no black boxes.
- **100% local** — Your memories live on your machine. Not on someone else's cloud. Not behind an API paywall. Yours.

*No other PA framework offers all of this. OpenClaw uses flat markdown. Supermemory sends everything to their cloud. nanobot's memory is basic two-stage. lolabot's memory is production-grade.*

---

### Email Security Nobody Else Has

Your PA reads your email. That means attackers can reach your AI through your inbox.

**lolabot is the only PA framework with a real email security pipeline:**

- **34 prompt injection patterns** detected and flagged before content reaches the AI
- **Trust model** — Operator (you) vs. external senders, with different handling for each
- **SPF/DKIM/DMARC verification** — Spoofed emails are caught and quarantined
- **Content wrapping** — External email content is tagged as data-only. The AI reads it but never executes instructions found inside
- **URL analysis** — Links classified as safe, suspicious, or dangerous
- **Attachment risk assessment** — Dangerous file types blocked automatically
- **89 automated tests** — The security pipeline is tested, not hoped

*No competitor has anything close to this. OpenClaw has sandboxed execution but no email-specific security. nanobot and gstack don't touch email security at all.*

---

### Find Any File, Anywhere

lolabot indexes files across every location you use:

- Local drives
- Remote machines (SSH/Tailscale)
- OneDrive, Google Drive, Dropbox, iCloud
- Amazon S3
- URLs and web resources

Ask "where's that tax document from 2024?" and lolabot finds it — whether it's on your laptop, your NAS, or buried in OneDrive.

*No other PA framework has multi-location file indexing.*

---

### Task Management Built In

Eisenhower Matrix prioritization with agent delegation:

- **Q1 (Do First)** — Urgent + Important
- **Q2 (Schedule)** — Important, not urgent
- **Q3 (Delegate)** — Urgent, not important — assign to other agents
- **Q4 (Delete)** — Neither urgent nor important — eliminate

Track tasks with IDs, due dates, owners, and status. Your PA reviews the matrix at the start of every session and keeps you focused on what matters.

---

## Competitive Positioning

### vs OpenClaw (347K stars)

> "OpenClaw connects to 25 channels but stores memory in flat markdown files. lolabot has semantic memory with auto-capture, deduplication, and reinforcement — plus an email security pipeline that OpenClaw doesn't have. If you handle sensitive data, lolabot is the professional choice."

### vs nanobot (17K stars)

> "nanobot is a research prototype in 4K lines. lolabot is a production-tested toolkit built from months of daily real-world use — handling invoices, managing multi-company operations, and protecting email from prompt injection."

### vs gstack (Garry Tan / YC)

> "gstack gives you 23 dev workflow tools. lolabot gives you a full personal assistant — memory, email, files, tasks, invoices, and communication channels. gstack helps you code. lolabot helps you run your life."

### vs Supermemory

> "Supermemory sends your memories to their cloud and charges you for the privilege. lolabot's memory is local, free, and more sophisticated — with deduplication, reinforcement tracking, confidence scores, and dual-save to both semantic index and readable markdown."

---

## Key Stats

| Metric | Value |
|--------|-------|
| Lines of code | ~12,000 |
| Python tools | 5 (email client, email sanitizer, memory indexer, file indexer, config) |
| Shell scripts | 9 (wrappers and utilities) |
| Skills | 3 (file processing, mail handling, memory delegation) |
| Email security patterns | 34 injection patterns |
| Automated tests | 89 (email sanitizer) |
| Memory types | 10 (fact, event, learning, decision, note, person, goal, preference, pattern, insight) |
| Supported file locations | 8 (local, remote, OneDrive, Google Drive, Dropbox, iCloud, S3, URLs) |
| License | MIT |
| Cloud dependency | Zero |
| Data that leaves your machine | None |

---

## Target Audience

1. **Founders & executives** — Managing multiple companies, contacts, invoices, and communication channels. Need a PA that handles sensitive financial and legal data locally.

2. **Solo professionals** — Consultants, lawyers, accountants who need email security, document management, and task tracking without trusting cloud services.

3. **AI agent developers** — Building on AI Maestro, CrabMail/AMP, or similar orchestration platforms. lolabot provides the PA layer that plugs into agent meshes.

4. **Privacy-conscious users** — Anyone who wants a powerful AI assistant but refuses to send their data to third-party clouds.

---

## Ecosystem

lolabot is part of the **23blocks** open-source ecosystem:

- **AI Maestro** — Agent orchestration platform. Agents run as lolabot instances in a mesh network.
- **CrabMail / AMP** — Agent Messaging Protocol for inter-agent communication. lolabot agents message each other via AMP.
- **23blocks** — Backend-as-a-Service platform providing auth, users, files, CRM, and multi-tenant infrastructure.

---

## Getting Started

```bash
git clone https://github.com/23blocks-OS/lolabot.git
./lolabot/setup.sh ~/my-assistant
cd ~/my-assistant && claude
```

That's it. Your AI Chief of Staff is ready.

---

*lolabot — Built by people who actually use their PA every day.*
