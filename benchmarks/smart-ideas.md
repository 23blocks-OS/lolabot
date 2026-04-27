# Smart Ideas

Notes on patterns, techniques, and approaches worth remembering.

---

## Every Product Needs an SDK

Every product, service, or data source we build or use should ship with a proper SDK — something both humans and agents can consume.

**SDK = scripts = CLI = llm.txt = whatever the consumer needs to interact with it programmatically.**

The naming doesn't matter. What matters:
- Any product without an agent-consumable interface is invisible to the agentic world
- Humans are the less likely consumer now — agents are the primary audience
- If a service only has a web UI, it's a dead end for automation

**For our own products (23blocks, 3Metas, Fluidmind):**
- Ship scripts/CLIs alongside the product
- Provide llm.txt or equivalent for agent discovery
- Treat the SDK as a first-class deliverable, not an afterthought

**For third-party services we use:**
- If they don't have an SDK, build one from their API docs (~10 min with CC)
- For native apps with local data (JSON/SQLite), wrap in a local HTTP endpoint on the host machine, then script it
