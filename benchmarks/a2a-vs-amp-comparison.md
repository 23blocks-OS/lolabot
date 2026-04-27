# Agent Communication Landscape — Protocol Comparison

**Last updated:** 2026-02-21
**A2A:** Agent2Agent Protocol (Google / Linux Foundation) — https://github.com/a2aproject/A2A
**AMP:** Agent Messaging Protocol (23blocks / open source) — /home/jpelaez/agentmessaging/protocol/spec/
**MCP Agent Mail:** Coding agent coordination — https://github.com/Dicklesworthstone/mcp_agent_mail

---

## The Core Difference

They solve **different problems** and sit at **different layers**.

| | **AMP** (ours) | **A2A** (Google/Linux Foundation) |
|---|---|---|
| **Analogy** | Email for agents | HTTP API for agents |
| **Model** | Messaging (async, store-and-forward) | RPC (request/response, task-based) |
| **Philosophy** | Local-first, messages on your machine | Cloud-first, tasks on the server |
| **Who stores data** | The agent (locally) | The server (A2A Server) |
| **Opacity** | Messages are opaque payloads | Agents are opaque (no internal state shared) |
| **Spec version** | 0.1.1 (Draft) | RC v1.0 |

---

## Architecture

| Aspect | **AMP** | **A2A** |
|---|---|---|
| **Transport** | REST + WebSocket + Relay queue | JSON-RPC 2.0 over HTTP(S), SSE, gRPC |
| **Discovery** | DNS TXT records + well-known URL + registry | "Agent Cards" (JSON metadata at a URL) |
| **Identity** | `agent@tenant.provider` (email-like) | Agent Card with URL endpoint |
| **Authentication** | Ed25519 message signing (per-message) | Standard HTTP auth (OAuth, API keys) |
| **Federation** | Built-in (providers forward cross-domain) | Not specified (agents talk directly via URLs) |
| **Message storage** | Local on agent's machine | Server-side (A2A Server manages tasks) |
| **Delivery** | WebSocket (live) / Webhook / Relay (offline) | Sync response / SSE streaming / Push notifications |
| **Spec format** | Markdown docs (9 sections + appendix) | Protobuf (normative) + JSON Schema + OpenAPI |

---

## What Each Does Well

### AMP Strengths
- True federation (like email — any provider can talk to any other)
- Local-first storage (you own your data)
- Cryptographic identity (Ed25519 signatures on every message)
- Offline support (relay queues hold messages for 7 days)
- Simple mental model (it's email, everyone gets it)
- Channel bridging (Slack, Discord, WhatsApp, Email built into the spec)
- Privacy by design (providers route, they don't store)

### A2A Strengths
- Task lifecycle management (submitted -> working -> completed/failed)
- Streaming (SSE for real-time progress updates)
- Rich media negotiation (text, forms, files, structured data)
- Enterprise-ready auth (OAuth, standard HTTP security)
- Multi-language SDKs (Python, Go, JS, Java, .NET)
- Backed by Google + Linux Foundation (adoption momentum)
- Formal spec with protobuf definitions
- Agent capability discovery (skills, supported modalities)

---

## What Each Lacks

### AMP Doesn't Have
- Task lifecycle (no concept of "task in progress" — it's just messages)
- Streaming (no SSE or real-time progress)
- Structured capability negotiation (no "Agent Card" equivalent)
- SDKs in multiple languages (bash + Python only today)
- Formal spec tooling (no protobuf, no OpenAPI)

### A2A Doesn't Have
- True federation (no DNS discovery, no provider-to-provider routing)
- Local-first storage (tasks live on the server)
- Cryptographic message signing (relies on transport-level auth)
- Offline queuing (no relay mechanism for disconnected agents)
- Channel bridging (no built-in Slack/Discord/Email bridges)
- Email-like addressing (agents are URLs, not addresses)
- Message threading (conversations are implicit via task context)

---

## Where They Overlap

Both protocols provide:
- Agent-to-agent communication
- Capability discovery (Agent Card vs Provider registry)
- Async support (push notifications vs relay queues)
- Structured metadata exchange
- Security considerations (auth, content validation)

---

## MCP Agent Mail — Local Coordination Layer

**Not a protocol** — a coordination tool for coding agents working in the same codebase. Created by Jeffrey Emanuel.

### What It Does
- Agents get friendly identities (e.g., "GreenCastle")
- Inbox/outbox for async messaging between agents in the same project
- **File reservation/leases** — agents claim files before editing to avoid conflicts
- Searchable message threads
- Git-backed storage (auditable), SQLite for indexing
- Runs as FastMCP server on localhost (port 8765)
- Works with Claude Code, Codex, Gemini CLI, etc.
- Includes Beads task tracker integration for dependency-aware work planning

### Three-Way Comparison

| | **AMP** (ours) | **A2A** (Google) | **MCP Agent Mail** |
|---|---|---|---|
| **Scope** | Cross-provider messaging | Cross-agent task delegation | Same-project coordination |
| **Scale** | Internet (federated) | Internet (HTTP endpoints) | Single machine / project |
| **Identity** | `agent@tenant.provider` | Agent Card URL | Friendly name ("GreenCastle") |
| **Discovery** | DNS + registry | Agent Cards | Local directory listing |
| **Federation** | Yes (cross-provider) | No (direct URLs) | No (localhost only) |
| **Transport** | REST + WebSocket + Relay | JSON-RPC / gRPC / SSE | FastMCP (HTTP, localhost) |
| **Storage** | Local (agent's machine) | Server-side | Git + SQLite (project dir) |
| **Key feature** | Email-like messaging at scale | Task lifecycle + streaming | **File reservations/leases** |
| **Security** | Ed25519 signatures | OAuth / API keys | Bearer token |
| **Backing** | 23blocks (us) | Google + Linux Foundation | Solo dev (Jeffrey Emanuel) |
| **Use case** | Agents talking across the internet | Agent A delegates task to Agent B | 3 agents editing the same repo |

### The Interesting Bit: File Leases

The one thing MCP Agent Mail has that neither AMP nor A2A addresses is **file-level conflict prevention**. When multiple coding agents work on the same codebase, they can claim files with advisory leases so others don't overwrite their work. This is a real problem when running parallel agents.

---

## Layer Model: Three Layers, Three Tools

They complement each other — they sit at different layers:

```
┌─────────────────────────────────────────────┐
│  A2A = How agents COLLABORATE on tasks      │  <- "Do this work for me"
│  (RPC, task lifecycle, streaming)           │
├─────────────────────────────────────────────┤
│  AMP = How agents COMMUNICATE               │  <- "I have something to tell you"
│  (Messaging, federation, local storage)     │
├─────────────────────────────────────────────┤
│  MCP Agent Mail = How agents COORDINATE     │  <- "I'm editing this file"
│  (File leases, local inbox, same project)   │
└─────────────────────────────────────────────┘
```

An agent could use **AMP to receive a message** ("Hey, I need you to analyze this data"), use **A2A to delegate a task** to a specialized agent ("Run this analysis and stream me the results"), and use **MCP Agent Mail** to coordinate with other agents working in the same repo.

---

## Strategic Implications

1. **AMP fills a gap A2A doesn't cover** — federation, local-first, cryptographic identity, channel bridging. Google didn't build that.
2. **A2A has momentum** — Google, Linux Foundation, SDKs in 5 languages, DeepLearning.AI course. Hard to ignore.
3. **Possible play: AMP as transport for A2A** — An A2A task notification arrives via AMP message. Best of both worlds.
4. **Or: AMP-to-A2A bridge** — Like our Slack/Email gateways, build a bridge so AMP agents can interact with A2A agents and vice versa.
5. **AMP's unique value** — Even in a world where A2A wins for task delegation, agents still need a way to receive messages, be discovered via DNS, bridge to Slack/Email, and store data locally. That's AMP.

---

## Key Specs Reference

### AMP
- Introduction: `agentmessaging/protocol/spec/01-introduction.md`
- Identity: `agentmessaging/protocol/spec/02-identity.md`
- Messages: `agentmessaging/protocol/spec/04-messages.md`
- Federation: `agentmessaging/protocol/spec/06-federation.md`
- Security: `agentmessaging/protocol/spec/07-security.md`
- Channel Bridging: `agentmessaging/protocol/spec/09-channel-bridging.md`

### A2A
- Spec: https://a2a-protocol.org/latest/specification/
- GitHub: https://github.com/a2aproject/A2A
- Python SDK: `pip install a2a-sdk`
- Key Concepts: https://a2a-protocol.org/latest/topics/key-concepts/

### MCP Agent Mail
- GitHub: https://github.com/Dicklesworthstone/mcp_agent_mail
- Site: https://mcpagentmail.com/
- Install: `curl -fsSL "https://raw.githubusercontent.com/Dicklesworthstone/mcp_agent_mail/main/scripts/install.sh" | bash -s -- --yes`
- Runs on: localhost:8765 (FastMCP server)
