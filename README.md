# lolabot

**Your AI Chief of Staff** — Personal Assistant framework for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Email, semantic memory, task management, content security.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: macOS](https://img.shields.io/badge/Platform-macOS-lightgrey.svg)]()
[![AI Maestro](https://img.shields.io/badge/AI%20Maestro-compatible-orange.svg)](https://github.com/23blocks-OS/ai-maestro)

---

## Why Lola?

Lola is a batteries-included AI Chief of Staff. She handles email, remembers everything, manages your tasks, and keeps your files organized. Clone the repo, run `setup.sh`, and point Claude Code at it — she's ready in minutes.

Lola runs standalone with just Claude Code. Optionally, deploy her on [AI Maestro](https://github.com/23blocks-OS/ai-maestro) for persistent memory across sessions, inter-agent messaging via AMP, and multi-machine orchestration.

## What You Get

- **Email Client** — IMAP/SMTP with multi-account support, SPF/DKIM/DMARC verification
- **Semantic Memory** — Hybrid Memvid + SQLite for fast search over facts, events, learnings, decisions
- **File Index** — Track files across local, remote, and cloud locations (OneDrive, Google Drive, S3, iCloud)
- **Task Management** — Eisenhower Matrix prioritization system
- **Content Security** — 34-pattern prompt injection defense, email sanitizer, attachment risk assessment
- **Skills** — File processing, mail handling, memory delegation
- **HEIC/Image Processing** — Convert Apple image formats for AI consumption

## Quick Start

> **Optional:** For persistent memory, inter-agent messaging, and multi-machine orchestration, deploy Lola on [AI Maestro](https://github.com/23blocks-OS/ai-maestro).

```bash
# Clone the repo
git clone https://github.com/23blocks-OS/lolabot.git

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

## How It Works

1. **Clone & scaffold** — `setup.sh` creates your PA instance directory with config, tools, and skills
2. **Configure** — Edit `lolabot.yaml` with your email accounts, preferences, and paths
3. **Launch** — Run `claude` in your instance directory — Lola has everything she needs
4. **Scale up** (optional) — Deploy on [AI Maestro](https://github.com/23blocks-OS/ai-maestro) to add more agents, messaging, and orchestration

Lola is a framework, not a product. Fork it, customize `CLAUDE.TEMPLATE.md`, swap tools in and out, and make her yours.

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

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (Claude Max or API key)
- [AI Maestro](https://github.com/23blocks-OS/ai-maestro) (optional — persistent memory, messaging, multi-machine)
- Python 3.10+
- `uv` (recommended) or `pip`
- Python packages: `memvid-sdk`, `pyyaml`, `pillow-heif`

## License

MIT — [23blocks Inc.](https://23blocks.com)

Works standalone or on [AI Maestro](https://github.com/23blocks-OS/ai-maestro) — the OS for AI-first organizations.
