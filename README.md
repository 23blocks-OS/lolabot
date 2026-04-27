# lolabot

A Personal Assistant framework for Claude Code. Deploy your own AI Chief of Staff with built-in email handling, semantic memory, file indexing, task management, and content security.

## What is lolabot?

lolabot is a batteries-included framework for running a persistent AI Personal Assistant using [Claude Code](https://docs.anthropic.com/en/docs/claude-code). It provides:

- **Email Client** — IMAP/SMTP with multi-account support, content security, injection defense (34 patterns), SPF/DKIM/DMARC verification
- **Semantic Memory** — Hybrid Memvid + SQLite system for fast search over facts, events, learnings, decisions, and more
- **File Index** — Track files across local, remote, cloud (OneDrive, Google Drive, S3, iCloud) locations
- **Task Management** — Eisenhower Matrix prioritization system
- **Content Security** — Email sanitizer, prompt injection defense, attachment risk assessment
- **Skills** — File processing, mail handling, memory delegation
- **HEIC/Image Processing** — Convert Apple image formats for AI consumption

## Quick Start

```bash
# Clone the repo
git clone https://github.com/23blocks/lolabot.git

# Scaffold a new PA instance
./lolabot/setup.sh ~/my-assistant

# Configure your instance
cd ~/my-assistant
cp lolabot.yaml.example lolabot.yaml
# Edit lolabot.yaml with your settings

# Set environment
export LOLABOT_HOME=~/my-assistant

# Start Claude Code in your instance directory
cd ~/my-assistant && claude
```

## Project Structure

```
your-assistant/          # Your PA instance (private, never pushed)
├── CLAUDE.md            # Generated from template
├── lolabot.yaml         # Your config (git-ignored)
├── tools/               # From lolabot (symlinked or copied)
├── skills/              # From lolabot
├── brain/               # Your tasks, notes, company info
├── memory/              # Your journals, profiles, goals
├── emails/              # Your cached emails
└── indexes/             # Your search indexes
```

## Tools

| Tool | Purpose |
|------|---------|
| `tools/email_client.py` | Read, send, reply, forward, search emails |
| `tools/email_sanitizer.py` | Content security for inbound email |
| `tools/memory_indexer.py` | Semantic memory with Memvid + SQLite |
| `tools/file_indexer.py` | Multi-location file discovery and search |
| `tools/heic-convert.sh` | Apple HEIC to JPEG conversion |
| `tools/memory-integrity-check.sh` | Detect unauthorized file modifications |

## Skills

| Skill | Purpose |
|-------|---------|
| `file-processing` | Document classification, organization, indexing |
| `mail-handler` | Safe email interaction rules and trust model |
| `pa-memory-delegation` | User memory management (facts, events, learnings) |

## Configuration

All configuration lives in `lolabot.yaml`. See `lolabot.yaml.example` for all options.

The single required environment variable is `LOLABOT_HOME`, pointing to your PA instance directory.

## Security

lolabot includes defense-in-depth for AI assistants:

- **Prompt injection scanning** — 34 patterns detected in inbound email
- **Trust model** — Operator (verified sender) vs. external content separation
- **Email authentication** — SPF/DKIM/DMARC verification
- **Content wrapping** — External content tagged as data-only, never executed
- **Attachment risk assessment** — Dangerous file types blocked
- **File integrity monitoring** — SHA256 checksums on critical files

## Requirements

- Claude Code (Claude Max or API key)
- Python 3.10+
- `uv` (recommended) or `pip`
- Python packages: `memvid-sdk`, `pyyaml`, `pillow-heif`

## License

MIT - 23blocks Inc.
