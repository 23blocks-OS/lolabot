# Wraps by wraps-team

**Website:** https://wraps.dev
**Repo:** https://github.com/wraps-team/wraps
**Reviewed:** 2026-01-31
**Stars:** 11 | **Forks:** 3 | **License:** AGPLv3 (core) + Commercial (/ee)
**Created:** 2025-11-07 | **Last updated:** 2026-01-31
**Language:** TypeScript (9.5MB) + CSS + Shell
**Stack:** Next.js, Elysia (API), Drizzle ORM, PostgreSQL, AWS SES/DynamoDB/Lambda/EventBridge, TipTap (editor), Pulumi (IaC), Turborepo monorepo
**Pricing:** Free (CLI/SDK) → $10-$149/mo for hosted dashboard + features

---

## What It Is

Email infrastructure platform that deploys to YOUR AWS account. Not an email SaaS — it's a developer tool that sets up SES, DynamoDB, Lambda, and EventBridge in your account, then provides a hosted dashboard for templates, analytics, workflows, and campaigns on top. You pay AWS directly for sending ($0.10/1K emails) plus optionally pay Wraps for the dashboard/tooling.

**Core proposition:** "AWS pricing with modern developer experience." Own your infrastructure, no vendor lock-in.

---

## Architecture

### Monorepo Structure

```
wraps/
├── apps/
│   ├── web/         - Next.js dashboard (templates, contacts, campaigns, analytics)
│   ├── api/         - Elysia API server (batch sending, contacts, events, webhooks)
│   └── website/     - Marketing site
├── packages/
│   ├── cli/         - @wraps.dev/cli (deploy infra to AWS)
│   ├── email/       - @wraps.dev/email (TypeScript SDK for sending)
│   ├── db/          - Drizzle ORM schema + migrations (PostgreSQL)
│   ├── core/        - Shared constants, types, SMTP validation
│   ├── ui/          - Shared UI components
│   ├── auth/        - Authentication (better-auth)
│   ├── pulumi/      - Infrastructure as Code
│   └── console/     - Console utilities
├── infra/           - SST config (API, queues, scheduler, tables)
├── cloudformation/  - Vercel OIDC IAM role template
└── ee/              - Enterprise features (commercial license)
```

### What Gets Deployed to Your AWS

```bash
npx @wraps.dev/cli email init
```

Deploys:
- **SES** — Domain verification, DKIM, SPF, DMARC
- **DynamoDB** — Email event history (90-day TTL)
- **Lambda** — Event processing, webhook handling
- **EventBridge** — Event routing
- **IAM Roles** — Least-privilege, OIDC support for Vercel
- **CloudWatch** — Metrics and alarms

All resources namespaced `wraps-email-*`.

### Hosted Platform (Optional, Paid)

- **Dashboard** — Next.js app on Vercel
- **API** — Elysia server handling batch sends, contacts, events
- **Database** — PostgreSQL (via Drizzle) for templates, contacts, workflows, analytics
- **Workers** — Batch sender, schedule trigger processor
- **Auth** — better-auth with org/team management

---

## Key Features Analyzed

### 1. Template Editor (TipTap-based WYSIWYG)

Full visual email builder built on TipTap (ProseMirror):

**Block types:**
- Section, Row, Column (layout)
- Button, Image, Avatar, Icon (interactive)
- Divider, Spacer (structure)
- Code Block, Social Links (content)
- Conditional blocks (show/hide based on variables)
- Variables with suggestions ({{firstName}}, etc.)

**Features:**
- Drag-and-drop block positioning
- Block library with reusable saved blocks
- Brand kit integration (colors, fonts, logo, button styles)
- Code view (raw HTML)
- Preview panel (desktop/mobile)
- Test data panel (preview with sample variables)
- Version history with changesets
- AI chat panel for generating/modifying templates
- Import from HTML
- Send test emails
- Publish to SES (creates/updates SES template)

**Technical:**
- Content stored as TipTap JSON (JSONContent)
- Compiled to HTML + plaintext for SES
- Variables transformed for SES syntax (`{{var}}` → `{{var}}`)
- Organization-scoped, multi-tenant
- Template versions with full history

### 2. Workflow Automation (Enterprise, Visual Builder)

Visual workflow builder using React Flow:

**Trigger nodes:**
- Event (custom events)
- Contact created/updated
- Segment entry/exit
- Schedule (cron)
- API trigger
- Topic subscribed/unsubscribed

**Action nodes:**
- Send email (with template selection)
- Send SMS
- Delay (wait X time)
- Condition (if/else branching)
- Webhook (external HTTP call)
- Update contact properties
- Wait for event
- Wait for email engagement (open/click)
- Subscribe/unsubscribe from topic
- Exit

**Execution:**
- Steps stored as JSONB in PostgreSQL
- Workflow queue processes steps sequentially
- Schedule triggers via EventBridge scheduler
- Contact enrollment tracking
- Pause/resume support

### 3. Contact Management

- Contacts with custom properties (JSONB)
- Topics (subscription lists) with double opt-in
- Segments (property-based + event-based filtering)
- Nested filter groups for advanced targeting
- Bulk operations
- Preference center (branded unsubscribe pages)

### 4. Campaign/Batch Sending

- Audience targeting: all contacts, topic subscribers, segment members
- Template or raw HTML
- Scheduling (immediate or future)
- Queue-based processing (SQS)
- Rate limiting
- SMS support (AWS End User Messaging)

### 5. Analytics & Events

- DynamoDB-backed event tracking
- Bounces, complaints, deliveries, opens, clicks
- Event-based segmentation
- Usage tracking per organization
- Retention policies (30d/90d/1yr by tier)

### 6. Brand Kits

- Logo, colors (primary, secondary, background, text)
- Typography (body + heading fonts)
- Button styles (rounded, square, pill)
- Company info (name, address, social links)
- Auto-extraction from domain
- Applied globally to all templates in org

---

## Pricing Breakdown

| Tier | Price | Events/mo | Retention | Workflows | AI Generations |
|------|-------|-----------|-----------|-----------|----------------|
| Free | $0 | — | — | — | — |
| Starter | $10/mo | 50K | 30 days | 5 | 50/mo |
| Growth | $49/mo | 250K | 90 days | 25 | 250/mo |
| Scale | $149/mo | 1M | 1 year | Unlimited | 1,000/mo |

**Plus AWS costs:** ~$0.10/1K emails + ~$2-5/mo Lambda/DynamoDB.

**Free tier:** CLI + SDK only. Self-host dashboard (AGPLv3). No hosted dashboard, no analytics.

**vs Mandrill pricing:** Mandrill charges blocks of 25K emails. At scale, Mandrill gets expensive fast. AWS SES at $0.10/1K is 10-40x cheaper than most managed services.

---

## Evaluation for Our Use Cases

### A. Outreach Block (`/home/jpelaez/23blocks/blocks/outreach`)

Our outreach block handles: campaigns, accounts (Gmail OAuth), analytics, scheduling, spintax.

| Feature | Outreach Block | Wraps |
|---------|---------------|-------|
| **Email sending** | Gmail API (per-account OAuth) | AWS SES (bulk, domain-level) |
| **Use case** | Cold outreach, personalized 1:1 | Marketing/transactional bulk |
| **Campaigns** | Yes (with accounts, scheduling) | Yes (with templates, segments) |
| **Accounts** | Multi-account Gmail rotation | Multi-AWS account support |
| **Templates** | Not yet (planned) | Full WYSIWYG + AI + brand kits |
| **Spintax** | Yes (rotation for deliverability) | No |
| **Workflows** | Via scheduler service | Full visual workflow builder |
| **Analytics** | Basic campaign analytics | Full event tracking (opens, clicks, bounces) |
| **Segments** | Not yet | Property + event-based segments |
| **Contacts** | Via 23blocks CRM | Built-in contact management |

**Verdict for Outreach:** **Different tools for different jobs.** Wraps is for marketing/transactional email at scale via SES. Our outreach block is for cold outreach via Gmail (different deliverability profile, different compliance model). They're complementary, not competitive.

**What we could borrow:**
- Template editor concept (TipTap-based) for campaign email design
- Workflow automation patterns for multi-step campaigns
- Event tracking model (opens, clicks, bounces) for our analytics
- Segment-based targeting for campaign audiences

### B. Mandrill Replacement

Our current Mandrill usage: 23blocks email-gateway receives webhooks, processes inbound email, forwards to AI Maestro agents.

| Aspect | Mandrill | Wraps (via SES) |
|--------|---------|-----------------|
| **Sending** | Mandrill API | AWS SES (via @wraps.dev/email SDK) |
| **Inbound** | Mandrill webhooks | SES receipt rules + Lambda |
| **Templates** | Mandrill templates (limited) | TipTap WYSIWYG + AI + brand kits |
| **Cost** | $$$ at scale (per-block pricing) | $0.10/1K emails (AWS) + $0-149 platform |
| **Transactional** | Yes (core use case) | Yes (email type: transactional) |
| **Domain auth** | SPF/DKIM via Mandrill | SPF/DKIM/DMARC via SES (you own it) |
| **Webhooks** | Open, click, bounce events | Same via SES + EventBridge |
| **Infrastructure** | Mandrill's servers | Your AWS account |
| **Lock-in** | Mandrill API | No lock-in (SES is standard AWS) |
| **Setup** | Quick (API key) | One CLI command but needs AWS account |

**Verdict for Mandrill replacement: YES, viable, with caveats.**

**Pros:**
- 10-40x cheaper at scale
- Own your infrastructure
- Better template tooling
- No vendor lock-in
- Full event tracking included

**Cons:**
- Need AWS account + SES out of sandbox (production approval required)
- Inbound email needs separate SES receipt rules setup (Wraps focuses on outbound)
- More infrastructure to manage (DynamoDB, Lambda, etc.)
- Our email-gateway currently uses Mandrill webhooks — would need rewrite for SES events
- SES sandbox approval can be painful (Wraps claims to help but it's still AWS)

**Migration path:**
1. Deploy Wraps CLI to set up SES infrastructure
2. Migrate templates from Mandrill to Wraps template editor
3. Update 23blocks Notify Block to use `@wraps.dev/email` SDK instead of Mandrill API
4. Set up SES receipt rules for inbound (replacing Mandrill inbound webhooks)
5. Update email-gateway to receive SES events instead of Mandrill webhooks
6. Keep Mandrill as fallback during transition

### C. Template Builder for 23blocks Mail Notifications

Our current state: 23blocks Notify Block sends transactional emails (password resets, invitations, etc.) via Mandrill with basic HTML templates. No visual editor.

**What Wraps offers:**
- Full TipTap WYSIWYG email editor (open source, AGPLv3)
- Block-based: sections, rows, columns, buttons, images, dividers
- Variables with fallbacks: `{{firstName|"there"}}`
- Conditional blocks: show/hide based on variable values
- Brand kits: consistent styling across all templates
- Reusable blocks: save headers/footers/CTAs, use across templates
- AI generation: describe email → get template
- Version history
- Test data preview
- Publish to SES templates
- Multi-tenant (organization-scoped)

**Verdict: HIGH VALUE — this is the strongest match.**

The template editor is the most directly useful piece for 23blocks:

1. **As a standalone component:** Extract the TipTap-based editor from Wraps (AGPLv3 allows this for open-source projects) and integrate into 23blocks admin dashboard for designing notification templates.

2. **As a template design tool:** Use the Wraps dashboard (even free self-hosted) to design templates, export the compiled HTML, and use that HTML in Mandrill templates. This gives us the visual builder without changing our sending infrastructure.

3. **As a full replacement:** If we migrate to SES, use Wraps' template → SES publishing pipeline directly. Templates designed in the editor get pushed to SES, and 23blocks sends via SES templates with variable substitution.

**Key components to study/extract:**
- `apps/web/src/components/template-editor/` — Full WYSIWYG editor
- `apps/web/src/components/template-editor/extensions/` — Email-specific TipTap nodes
- `packages/email/src/lib/ses-templates.ts` — SES template management
- `packages/email/src/lib/ses-variables.ts` — Variable transformation
- `packages/db/src/schema/templates.ts` — Template data model (with versions, brand kits, reusable blocks)

---

## Technical Quality Assessment

### Strengths

1. **Clean monorepo architecture** — Turborepo + pnpm workspaces, well-separated packages
2. **Modern stack** — Next.js 15, Elysia, Drizzle, TipTap, React Flow
3. **Type-safe throughout** — Strict TypeScript, Drizzle typed queries
4. **Well-designed schema** — Multi-tenant, proper indexes, relations, version history
5. **Template editor is genuinely good** — Block-based, brand kits, variables, conditionals, AI assist
6. **Workflow builder is comprehensive** — Covers common automation patterns
7. **Infrastructure as code** — Pulumi for reproducible deployments
8. **OIDC auth** — No AWS credentials stored, Vercel-native

### Weaknesses

1. **Very young** — Created Nov 2025, 11 stars, likely pre-stable
2. **AGPLv3 license** — Restricts commercial use without open-sourcing your code (or buying enterprise)
3. **AWS-only** — No support for other cloud providers or non-SES sending
4. **SES sandbox problem** — Production approval is notoriously difficult
5. **No inbound email** — Focused entirely on outbound; inbound would need custom SES receipt rules
6. **Dashboard requires Vercel** — OIDC auth flow is Vercel-specific in production
7. **Enterprise features are closed** — Workflows, advanced segments behind commercial license

---

## Summary Table

| Use Case | Fit | Priority | Action |
|----------|-----|----------|--------|
| **Outreach Block** | LOW | — | Different purpose (cold outreach vs marketing). Borrow template/workflow patterns only |
| **Mandrill Replacement** | MEDIUM | Future | Viable when Mandrill costs become a problem. Migration is non-trivial but path is clear |
| **Template Builder for 23blocks** | HIGH | Near-term | TipTap editor is excellent. Can use standalone, self-hosted, or extract components |

---

## Recommended Actions

### Near-term (Template Builder)
1. Self-host Wraps dashboard (AGPLv3, free) to design notification templates
2. Export compiled HTML for use in existing Mandrill templates
3. Evaluate extracting TipTap email editor components for 23blocks admin UI

### Future (If Mandrill gets expensive)
1. Deploy Wraps CLI to set up SES in our AWS account
2. Migrate transactional templates to SES via Wraps
3. Update Notify Block to send via `@wraps.dev/email` SDK
4. Set up SES receipt rules + Lambda for inbound (replacing Mandrill webhooks)
5. Keep Mandrill as fallback during migration

### For Outreach Block
1. Study their workflow builder patterns for multi-step campaign automation
2. Study their event tracking model for open/click analytics
3. Consider their segment system for campaign targeting
4. Do NOT replace Gmail sending with SES — different deliverability profile for cold outreach
