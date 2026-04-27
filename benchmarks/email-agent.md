# email-agent by haasonsaas

**Repo:** https://github.com/haasonsaas/email-agent
**Reviewed:** 2026-01-31
**Stars:** 30 | **Forks:** 4 | **License:** MIT
**Created:** 2025-08-01 | **Last updated:** 2026-01-29
**Language:** Python (1.1MB)
**Stack:** CrewAI, OpenAI GPT-4, SQLite, Textual TUI, Typer CLI, Gmail API, Pydantic

---

## What It Is

AI-powered email management agent with multi-agent orchestration for intelligent email triage, categorization, and automation. Supports Gmail integration (OAuth2), IMAP, and Outlook (Microsoft Graph API). Provides CLI, interactive TUI, and Docker deployment.

---

## Architecture

Multi-agent system using CrewAI orchestration with 14 specialized agents:

```
EmailAgentCrew (crew.py - CrewAI sequential process)
├── CollectorAgent         - Email sync from Gmail/IMAP/Outlook connectors
├── CategorizerAgent       - Rule-based + AI (GPT) categorization
├── SummarizerAgent        - Content summarization
├── EnhancedSummarizer     - Narrative daily briefs (<60s read time)
├── SentimentAnalyzer      - Emotional tone analysis per email
├── ThreadAnalyzer         - Conversation thread grouping & summarization
├── TriageAgent            - Attention scoring (0.0-1.0) + routing
├── DraftAgent             - Writing style analysis + reply generation
├── ActionExtractor        - Deadline/commitment/meeting extraction via GPT
├── CommitmentTracker      - SQLite-backed deadline & follow-up tracking
├── LearningSystem         - Feedback loop for improving AI decisions
├── EnhancedCEOLabeler     - Gmail label automation with sender reputation
├── RelationshipIntel      - Strategic contact profiling (board, investors, etc.)
├── ThreadIntelligence     - Cross-thread conversation context
└── CollaborativeProcessor - Multi-agent weighted consensus decisions
```

### Data Flow

```
Email Sources → Collectors → Sanitizer → Categorizers → Action Extractors → SQLite DB
                                ↓              ↓              ↓
                          AI Processing → Smart Labels → Commitment Tracking
                                ↓              ↓              ↓
                          Daily Briefs → Thread Summaries → Learning System
```

### Storage

- **SQLite** for emails, commitments, follow-ups, waiting items, learning feedback, user preferences
- **Local filesystem** for email cache, briefs output, credentials
- No cloud dependencies for storage (privacy-first)

### Email Connectors

| Connector | Protocol | Auth |
|-----------|----------|------|
| Gmail | Gmail API | OAuth2 |
| IMAP | IMAP4 | Username/password |
| Outlook | Microsoft Graph API | OAuth2 |

---

## Key Features Analyzed

### 1. Action Extraction (ActionExtractorAgent)

Uses GPT to extract structured data from every email:

```json
{
  "action_items": [{"action": "...", "deadline": "YYYY-MM-DD", "priority": "high|medium|low", "category": "respond|schedule|review|follow_up"}],
  "commitments_made": [{"commitment": "...", "deadline": "...", "recipient": "..."}],
  "waiting_for": [{"waiting_for": "...", "from_whom": "...", "deadline": "..."}],
  "meeting_requests": [{"type": "schedule|reschedule|cancel", "proposed_times": [...], "attendees": [...]}],
  "needs_response": true,
  "response_urgency": "urgent|normal|low",
  "email_type": "receipt|notification|request|conversation|newsletter|alert"
}
```

Smart urgency classification: receipts/shipping notifications are NOT marked urgent. Only explicit deadlines today/tomorrow, security alerts, or time-sensitive requests qualify.

### 2. Commitment Tracking (CommitmentTrackerAgent)

SQLite database with three tables:

| Table | Tracks | Fields |
|-------|--------|--------|
| `commitments` | What we promised to do | description, committed_to, deadline, priority, status, reminder_sent |
| `follow_ups` | Scheduled follow-up actions | follow_up_type, follow_up_date, status, notes |
| `waiting_items` | What we're expecting from others | waiting_from, expected_date, status |

Features: overdue detection, completion marking with notes, automatic follow-up scheduling.

### 3. Triage Agent (Attention Scoring)

Scores every email 0.0-1.0 on attention-worthiness using multiple factors:

| Factor | Signal |
|--------|--------|
| Sender importance | Learned from interaction history |
| Content urgency | Keyword detection (urgent, ASAP, deadline) |
| Time sensitivity | Due dates, meeting requests |
| Thread context | Ongoing conversation vs new thread |
| User preferences | Learned from feedback |

Routes to: `priority_inbox`, `regular_inbox`, `auto_archive`, `spam_folder`.

### 4. Learning Feedback System

SQLite-backed continuous improvement:

- **feedback** table: Records AI decision vs user correction (original_decision, correct_decision, confidence)
- **learning_patterns** table: Extracted patterns with success_rate, usage_count
- **user_preferences** table: Inferred preferences with confidence scores
- **Advanced rules engine**: Auto-generates categorization rules from learned sender/subject/content/temporal patterns

Minimum thresholds: 3+ emails from sender before learning pattern, 5+ subject keyword occurrences, 70% confidence threshold for auto-rules.

### 5. Collaborative Decision Making

Multi-agent consensus system with weighted voting:

| Agent | Weight | What It Assesses |
|-------|--------|------------------|
| CEO Strategic | 35% | Business importance, board/investor relevance |
| Relationship Intel | 25% | Contact profile, interaction history |
| Thread Context | 20% | Conversation continuity, unresolved items |
| Triage Baseline | 20% | Urgency, sender importance, content analysis |

Each agent returns: `priority_score`, `confidence`, `suggested_labels`, `urgency_level`, `risk_factors`, `opportunities`. Conflicts resolved by weighted vote.

### 6. Draft Reply Generation (DraftAgent)

Two-phase system:

**Phase 1 - Writing Style Analysis** (from sent emails):
- Average length, formality score (0-1), greeting/closing preferences
- Common phrases, tone keywords, sentence complexity
- Temporal patterns (preferred sending times)
- Contextual patterns (work vs personal style)
- Minimum 10 sent emails for analysis, cached for 7 days

**Phase 2 - Draft Generation**:
- Generates N draft suggestions per email
- Each draft includes: subject, body, confidence score, style_match score, suggested_tone
- Respects user's detected writing style

### 7. Relationship Intelligence

Contact profiling system:

```
ContactProfile:
  - relationship_type: board | investor | customer | team | vendor | advisor | partner
  - importance_level: critical | high | medium | low
  - interaction_frequency: daily | weekly | monthly | rare
  - response_pattern: immediate | fast | slow | rare
  - decision_maker: boolean
  - escalation_priority: 1-5
```

Pattern-based role detection using regex (e.g., "board meeting" → board, "term sheet" → investor).

Auto-escalation rules:
- Board members → immediate escalation
- Critical sender + urgent keywords → high priority
- Investor communication → strategic attention
- Legal/signature keywords → signature required

### 8. CEO Intelligence System

Gmail-specific enhanced labeling with:
- Sender reputation scoring
- Thread continuity tracking
- Auto-label creation (color-coded in Gmail)
- Strategic analysis for board/investor communication
- Predictive patterns from historical email handling

### 9. Daily Briefs (Enhanced Summarizer)

Narrative-style daily email summaries:
- Statistics: total, unread, high priority, action items count
- Urgent actions with deadlines
- Meetings & events extracted
- Key insights and trends
- Reading time target: <60 seconds
- "Story arcs" and "key characters" for narrative structure

---

## Technical Decisions

| Decision | Choice | Notes |
|----------|--------|-------|
| AI Provider | OpenAI GPT-4 | Required for all AI features. No local model support |
| Orchestration | CrewAI | Multi-agent framework with sequential/parallel processing |
| Data Models | Pydantic | Typed models with validation |
| Storage | SQLite | Multiple databases (emails, commitments, learning) |
| CLI | Typer | Rich command system with subcommands |
| TUI | Textual | Interactive terminal dashboard |
| Email Auth | OAuth2 (Gmail, Outlook) + IMAP passwords | |
| Credential Storage | keyring | System keychain integration |
| Deployment | Docker + docker-compose | With persistent volumes |

---

## Strengths

1. **Comprehensive feature set** - Covers the full email lifecycle from sync to triage to reply
2. **Structured action extraction** - The JSON output format for actions/commitments is well-designed
3. **Persistent tracking** - Commitments, follow-ups, waiting items survive across sessions
4. **Learning loop** - Feedback system genuinely improves over time
5. **Multi-agent consensus** - Weighted voting prevents single-agent blind spots
6. **Privacy-first storage** - All data stays local in SQLite

## Weaknesses

1. **Heavy OpenAI dependency** - Every email requires API call. No offline/local model fallback
2. **No content security** - No prompt injection defense, no email sanitization, no trust model
3. **Gmail-centric** - Many features (labels, calendar) only work with Gmail API
4. **Over-engineered orchestration** - CrewAI adds complexity without clear benefit over simpler patterns
5. **No sender authentication** - No SPF/DKIM/DMARC verification
6. **No attachment security** - No dangerous file detection or blocking

---

## Comparison to Our System

| Aspect | email-agent (haasonsaas) | Lola Email System |
|--------|--------------------------|-------------------|
| **AI Model** | External GPT-4 via API | Lola IS the AI (in-context) |
| **Orchestration** | CrewAI framework | AI Maestro mesh network |
| **Security** | None | Full sanitizer + auth verification + quarantine |
| **Trust Model** | None | Operator/External/Spoofed/Quarantined |
| **Injection Defense** | None | 34 patterns, 8 categories |
| **Auth Verification** | None | SPF/DKIM/DMARC + Messages Jail |
| **Action Extraction** | GPT-powered, structured | Not yet implemented |
| **Commitment Tracking** | SQLite-backed | Not yet (Eisenhower matrix is manual) |
| **Daily Briefs** | Full narrative generation | Not yet implemented |
| **Draft Replies** | Style-matched generation | Not yet implemented |
| **Learning System** | Feedback loop + auto-rules | Not yet implemented |
| **Email Connectors** | Gmail API + IMAP + Outlook | IMAP + SMTP |
| **Storage** | SQLite | JSON cache + Memvid |

**Key Insight:** They have better intelligence features (action extraction, commitment tracking, learning). We have better security (sanitization, auth verification, quarantine). The ideal system combines both.

---

## Applicable Learnings

### For Lola's Email Solution

| Feature | Priority | Effort | How to Implement |
|---------|----------|--------|------------------|
| Action extraction | HIGH | Medium | Lola extracts actions during email read, stores to Eisenhower |
| Commitment tracking | HIGH | Medium | Extend memory_indexer or add SQLite table |
| Daily email brief | HIGH | Low | New `email.sh brief` command, Lola generates summary |
| Email type classification | MEDIUM | Low | receipt/request/newsletter affects presentation |
| Draft reply generation | MEDIUM | Medium | Analyze Juan's sent folder, generate style-matched drafts |
| Learning from corrections | MEDIUM | Low | Record when Juan corrects categorization |
| Triage/attention scoring | MEDIUM | Medium | Score on read, flag high-attention emails |

### For Agent-to-Agent Communication (AI Maestro)

| Feature | Priority | Effort | How to Implement |
|---------|----------|--------|------------------|
| Structured action items in messages | HIGH | Low | Add action_items/deadline fields to message format |
| Cross-agent commitment tracking | HIGH | Medium | Track agent promises in AI Maestro |
| Priority routing from content | MEDIUM | Low | Auto-score messages, escalate urgent |
| Collaborative decision making | LOW | High | Multi-agent voting for complex decisions |

### What NOT to Adopt

| Feature | Reason |
|---------|--------|
| CrewAI framework | Over-engineered; AI Maestro handles orchestration |
| OpenAI API calls | Lola IS the AI; no need for external API |
| Gmail-specific labeling | We use IMAP universally |
| Textual TUI | CLI-based workflow works for us |
| Pydantic models | Dict-based approach is simpler at our scale |
| Sender reputation scoring | Our SPF/DKIM/DMARC auth is more rigorous |

---

## Summary

A feature-rich email agent with strong intelligence features but no security layer. The structured output formats (action extraction, commitment tracking) and learning feedback loop are the most valuable patterns to adopt. Their architecture of external AI calls doesn't apply to us since Lola processes emails in-context, but the data structures and tracking patterns translate directly.
