# lolabot

**Your First Hire** — AI Chief of Staff framework for [AI Maestro](https://github.com/23blocks-OS/ai-maestro).

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: macOS](https://img.shields.io/badge/Platform-macOS-lightgrey.svg)]()
[![AI Maestro](https://img.shields.io/badge/AI%20Maestro-compatible-orange.svg)](https://github.com/23blocks-OS/ai-maestro)

---

## Why Lola?

You installed [AI Maestro](https://github.com/23blocks-OS/ai-maestro) to run your AI-first organization. Now you need your first agent. Lola is a batteries-included Chief of Staff — she handles email, remembers everything, manages your tasks, and keeps your files organized. Deploy her in minutes, then add more agents as your org grows.

Lola works standalone with Claude Code, but she shines on AI Maestro: persistent memory across sessions, inter-agent messaging via AMP, and multi-machine orchestration.

## What You Get

- **Email Client** — IMAP/SMTP with multi-account support, SPF/DKIM/DMARC verification
- **Semantic Memory** — Hybrid Memvid + SQLite for fast search over facts, events, learnings, decisions
- **File Index** — Track files across local, remote, and cloud locations (OneDrive, Google Drive, S3, iCloud)
- **Task Management** — Eisenhower Matrix prioritization system
- **Content Security** — 34-pattern prompt injection defense, email sanitizer, attachment risk assessment
- **Skills** — File processing, mail handling, memory delegation
- **HEIC/Image Processing** — Convert Apple image formats for AI consumption

## Quick Start

> **Recommended:** Install [AI Maestro](https://github.com/23blocks-OS/ai-maestro) first for persistent memory, messaging, and multi-agent orchestration. Lola also works standalone with just Claude Code.

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

1. **Install AI Maestro** — Your control plane for AI agents
2. **Deploy Lola** — Clone this repo, run `setup.sh`, point Claude Code at it
3. **She gets to work** — Terminal access, semantic memory, email, file indexing — all wired up
4. **Add more agents** — Lola can message other agents via AMP, delegate tasks, and coordinate

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
- [AI Maestro](https://github.com/23blocks-OS/ai-maestro) (recommended — persistent memory, messaging, multi-machine)
- Python 3.10+
- `uv` (recommended) or `pip`
- Python packages: `memvid-sdk`, `pyyaml`, `pillow-heif`

## License

MIT — [23blocks Inc.](https://23blocks.com)

Built for [AI Maestro](https://github.com/23blocks-OS/ai-maestro) — the OS for AI-first organizations.
