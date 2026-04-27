# PageIndex by VectifyAI

**Repo:** https://github.com/VectifyAI/PageIndex
**Reviewed:** 2026-02-04
**Stars:** 13,263 | **Forks:** 969 | **License:** MIT
**Created:** 2025-04-01 | **Last updated:** 2026-02-04
**Version:** Beta (2025-04-23)
**Language:** Python
**Stack:** OpenAI API (GPT-4o), PyPDF2/PyMuPDF, tiktoken
**Pricing:** Open source (self-hosted), but requires OpenAI API credits. Cloud/enterprise tiers available via pageindex.ai.

---

## What It Is

A **vectorless, reasoning-based RAG** system for professional document analysis. Instead of embedding documents into vectors and doing similarity search, PageIndex builds a hierarchical tree index (like a smart table of contents) and uses LLM reasoning to navigate it — mimicking how a human expert flips through a long document.

Their core claim: **"similarity ≠ relevance"** — vector similarity often retrieves semantically close but contextually irrelevant chunks. PageIndex solves this by having the LLM *think* about which section to drill into.

---

## Architecture

```
PDF/Markdown Input
  │
  ├── Phase 1: INDEXING
  │   ├── TOC Detection (scan first 20 pages)
  │   ├── If TOC found → extract + map to physical pages
  │   ├── If no TOC → generate structure from content via LLM
  │   ├── Verify accuracy (random sampling, 60% threshold)
  │   ├── Fix incorrect mappings (up to 3 retry cycles)
  │   └── Recursive subdivision of large nodes (>10 pages or >20K tokens)
  │
  ├── Phase 2: RETRIEVAL (agentic)
  │   ├── LLM reads tree structure
  │   ├── Reasons about which branch to explore
  │   ├── Drills into relevant sections
  │   └── Returns content with page references
  │
  └── Output: Hierarchical JSON tree with titles, page ranges, summaries
```

### Tree Structure Output Example

```json
{
  "title": "Financial Stability",
  "node_id": "0006",
  "start_index": 21,
  "end_index": 22,
  "summary": "The Federal Reserve's monitoring...",
  "nodes": [
    {
      "title": "Monitoring Financial Vulnerabilities",
      "node_id": "0007",
      "summary": "..."
    }
  ]
}
```

---

## How It Works (Technical Detail)

### Indexing Pipeline

1. **`tree_parser()`** — Main orchestrator. Branches into 3 modes:
   - `process_toc_with_page_numbers` — TOC found with page numbers (best case)
   - `process_toc_no_page_numbers` — TOC found but no page numbers
   - `process_no_toc` — No TOC, generate structure from content

2. **`check_toc()`** — Scans initial pages for table of contents. Uses LLM per-page detection.

3. **`toc_transformer()`** — Converts raw TOC text into structured JSON with hierarchical numbering.

4. **`verify_toc()`** — Samples entries and validates section locations against actual page content. If accuracy < 60%, falls back to simpler mode.

5. **`fix_incorrect_toc_with_retries()`** — Up to 3 correction cycles for misaligned entries.

6. **`process_large_node_recursively()`** — Splits nodes exceeding `max_pages_per_node` (10) or `max_tokens_per_node` (20,000) into sub-trees.

### Retrieval

The retrieval phase is agentic — the LLM navigates the tree via reasoning, not similarity. Cookbook examples show multi-step traversal with explicit "thinking" fields for auditability.

### LLM Calls

- **Synchronous** for simple checks (TOC detection, page analysis)
- **Async batching** (`asyncio.gather`) for concurrent verification across sections
- All calls use `temperature=0` for deterministic output
- Retry logic: max 10 attempts with 1-second delays (no exponential backoff)
- JSON mode with "thinking" fields for transparency

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| openai | 1.101.0 | LLM API calls |
| pymupdf | 1.26.4 | PDF parsing (fast) |
| PyPDF2 | 3.0.1 | PDF parsing (fallback) |
| python-dotenv | 1.1.0 | Environment config |
| tiktoken | 0.11.0 | Token counting |
| pyyaml | 6.0.2 | Config loading |

---

## Benchmarks (Claimed)

Mafin 2.5 (built on PageIndex) achieved **98.7% accuracy on FinanceBench** — a standard benchmark for financial document QA. They claim this significantly outperforms vector-based RAG approaches.

No independent benchmarks or third-party validations found. FinanceBench is a real benchmark but the claim is self-reported.

---

## Strengths

1. **No vector database needed** — eliminates embedding infrastructure (no Pinecone, Qdrant, pgvector, etc.)
2. **No chunking** — preserves natural document structure instead of arbitrary splits
3. **Full traceability** — every retrieval decision includes reasoning + page references
4. **Works well for structured documents** — financial reports, legal docs, regulatory filings, technical manuals
5. **Simple dependency chain** — just OpenAI + PDF parser + tiktoken
6. **MIT licensed** — fully open source

---

## Limitations & Concerns

1. **OpenAI-only** — Hardcoded to OpenAI client library. No abstraction for Anthropic, local models, or other providers. Would need forking to use Claude API.
2. **High LLM cost per document** — Indexing a single document requires many LLM calls: TOC detection, extraction, verification, fixing, summarization. A 100-page PDF could easily cost $5-15+ in API calls just to index.
3. **Indexing is slow** — Each document goes through multiple LLM round-trips. Not suitable for real-time or high-volume ingestion.
4. **English-centric prompts** — All system prompts are in English. Likely struggles with non-English documents.
5. **Beta quality** — Only 2 changelog entries. Last code update April 2025. Core retry/error handling is basic.
6. **No rate limiting or cost tracking** — Could burn through API credits unexpectedly on large documents.
7. **Memory-bound for very large docs** — Keeps full page lists in memory. No streaming or disk-swapping.
8. **Retrieval requires LLM too** — Unlike vector search (instant lookup), every query also needs LLM reasoning calls. Higher per-query latency and cost.
9. **No caching** — Repeated queries on the same document re-run the reasoning chain.

---

## Relevance to Our Projects

### Where PageIndex Could Add Value

| Project | Use Case | Fit |
|---------|----------|-----|
| **Lola (file processing)** | Processing long PDFs Juan receives (legal, financial, immigration docs) | Medium — good for one-off deep analysis of important docs, but too expensive for routine processing |
| **23blocks** | Document analysis features for enterprise customers | Medium — could be a premium feature, but OpenAI lock-in conflicts with multi-provider strategy |
| **AI Maestro** | Agent skill for document navigation | Low-Medium — interesting as an agent capability, but adds OpenAI dependency |
| **Fluidmind / Energy Foundation** | Analyzing regulatory documents, memos | Medium-High — structured government/regulatory docs are PageIndex's sweet spot |

### Comparison with Our Current Approach

| Dimension | PageIndex | Our Stack (Memvid) |
|-----------|-----------|---------------------|
| Storage | JSON tree files | Memvid V2 (.mv2) + SQLite |
| Search method | LLM reasoning (slow, expensive) | Vector similarity (fast, cheap) |
| Indexing cost | $5-15+ per document (LLM calls) | Near-zero (local embeddings) |
| Query cost | LLM call per query | Near-zero (local search) |
| Query speed | Seconds (LLM round-trip) | Milliseconds (16x faster with V2) |
| Accuracy on structured docs | Very high (98.7% claimed) | Good for semantic recall, weaker on structured navigation |
| Infrastructure | OpenAI API only | Self-hosted, no external dependencies |
| Best for | Deep analysis of complex structured docs | Fast recall across many memories/files |

### Honest Assessment

PageIndex solves a real problem — vector search *does* struggle with structured professional documents where you need to reason about *where* information is, not just *what's similar*. The hierarchical tree approach is elegant.

However, for our use cases:

- **Cost is prohibitive at scale.** We process many documents; paying $5-15 per doc to index + per-query LLM costs doesn't make sense for routine work.
- **OpenAI lock-in is a dealbreaker** for 23blocks (multi-provider) and Lola (we use Anthropic).
- **Speed matters for us.** Memvid gives us millisecond search. PageIndex needs seconds per query.
- **Our docs are mostly short-to-medium.** Juan's immigration docs, invoices, and memos don't need this level of hierarchical reasoning. It shines on 200+ page regulatory filings.

### Potential Adoption Path

**Not recommended for direct integration.** Instead, consider:

1. **Borrow the concept** — The hierarchical tree index idea is valuable. We could build a lightweight version that generates tree structures using local models or simpler heuristics (heading detection, PDF outline extraction) without the heavy LLM indexing cost.
2. **Use for specific high-value docs** — If a Fluidmind client needs deep analysis of a 500-page regulatory filing, PageIndex (or its cloud API) could be used as a one-off tool.
3. **Watch for provider expansion** — If they add Anthropic/Claude support, reconsider. The architecture is sound; the OpenAI lock-in is the main blocker.

---

## Quick Start (If We Want to Test)

```bash
# Clone
git clone https://github.com/VectifyAI/PageIndex.git
cd PageIndex

# Install
pip3 install -r requirements.txt

# Configure
echo "CHATGPT_API_KEY=sk-..." > .env

# Run on a PDF
python3 run_pageindex.py --pdf_path /path/to/document.pdf

# Run on markdown
python3 run_pageindex.py --md_path /path/to/document.md

# Output → ./results/{filename}_structure.json
```

### Parameters

| Flag | Default | Description |
|------|---------|-------------|
| `--model` | gpt-4o-2024-11-20 | LLM model |
| `--toc-check-pages` | 20 | Pages to scan for TOC |
| `--max-pages-per-node` | 10 | Max pages per tree node |
| `--max-tokens-per-node` | 20,000 | Max tokens per tree node |
| `--if-add-node-id` | yes | Include node IDs |
| `--if-add-node-summary` | yes | Generate summaries |

---

## Verdict

**Interesting concept, not for us right now.** The hierarchical reasoning approach is genuinely innovative and the right solution for deep analysis of large structured documents. But the OpenAI lock-in, high per-document cost, and query latency make it impractical for our current needs. Worth revisiting if they add multi-provider support or if we land a project requiring heavy regulatory document analysis (like Fluidmind/Energy Foundation work).

**Score: 6/10** — Good idea, wrong fit for our stack today.
