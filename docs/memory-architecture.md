# Lola Memory Architecture

## Overview

Two separate Memvid indexes, linked by references:

```
┌─────────────────────────────────────────────────────────────┐
│  Curated Context (Markdown - loaded into LLM context)       │
│  ├── CLAUDE.md          # System instructions               │
│  ├── memory/goals.md    # Current priorities                │
│  ├── memory/journal-*.md # Key events by year               │
│  └── brain/eisenhower.md # Task management                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Queryable Storage (Memvid V2 - searched on demand)         │
│                                                             │
│  ┌─────────────────────┐    ┌─────────────────────┐        │
│  │  files.mv2          │    │  memories.mv2       │        │
│  │                     │    │                     │        │
│  │  - File paths       │◄──►│  - Facts            │        │
│  │  - Metadata         │    │  - Events           │        │
│  │  - Tags             │    │  - Learnings        │        │
│  │  - Thumbnails       │    │  - Decisions        │        │
│  │  - EXIF data        │    │  - People notes     │        │
│  └─────────────────────┘    └─────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Index 1: Files (`files.mv2`)

**Purpose:** Find files by content, context, or association.

**What gets indexed:**
- File path (absolute)
- File name
- File type (image, document, video, etc.)
- Size, created/modified dates
- Tags (manual and auto-generated)
- Description (manual or AI-generated)
- EXIF data for photos (date, location, camera)
- Thumbnail path (for images)
- Content hash (for deduplication)

**Example queries:**
- "Find photos from the Ecuador trip"
- "Where is the immigration approval letter?"
- "Show me architecture diagrams"
- "Files modified this week"

**Example entry:**
```json
{
  "path": "/home/jpelaez/photos/2024/ecuador/IMG_0312.jpg",
  "name": "IMG_0312.jpg",
  "type": "image/jpeg",
  "size": 4521984,
  "created": "2024-03-12T14:32:00",
  "tags": ["ecuador", "family", "travel", "2024"],
  "description": "Juan with family at Mitad del Mundo monument",
  "exif": {"date": "2024-03-12", "location": "Quito, Ecuador"},
  "thumbnail": "/home/jpelaez/.lola/thumbnails/abc123.jpg"
}
```

## Index 2: Memories (`memories.mv2`)

**Purpose:** Store and retrieve knowledge, not files.

**What gets indexed:**
- Facts (things that are true)
- Events (things that happened)
- Learnings (things discovered)
- Decisions (choices made and why)
- People notes (context about individuals)

**Example queries:**
- "What health issues has Juan had?"
- "When was the immigration waiver approved?"
- "What did we learn about AI memory systems?"
- "What decisions were made about the architecture?"

**Example entry:**
```json
{
  "type": "event",
  "content": "Ecuador trip in March 2024 - visited family in Quito and explored the Amazon rainforest",
  "date": "2024-03-10",
  "tags": ["travel", "family", "ecuador"],
  "related_files": ["files://ecuador/IMG_0312.jpg", "files://ecuador/IMG_0315.jpg"],
  "related_people": ["Juan", "Yuliana", "family"]
}
```

## Linking Between Indexes

Memories can reference files, and files can be tagged with memory contexts:

```
Memory: "Ecuador trip March 2024..."
  └── related_files: ["files://ecuador/*"]

File: "/photos/2024/ecuador/IMG_0312.jpg"
  └── memory_refs: ["memory://events/ecuador-2024"]
```

When I find a memory about Ecuador, I can also pull related files.
When I find a photo from Ecuador, I can pull the memory context.

## Query Flow

```
User: "Show me photos from Felipe's graduation"

1. Search memories.mv2 for "Felipe graduation"
   → Found: Event "Felipe's graduation June 2025..."
   → Has related_files reference

2. Search files.mv2 for:
   a. Direct query "Felipe graduation photos"
   b. Files tagged with event reference

3. Return combined results:
   - Context from memory
   - Actual file paths from files index
```

## Directory Structure

```
/home/jpelaez/lola/
├── indexes/
│   ├── files.mv2          # File index
│   └── memories.mv2       # Knowledge index
├── memory/                 # Curated markdown (loaded into context)
│   ├── journal-2024.md
│   ├── journal-2025.md
│   ├── journal-2026.md
│   ├── goals.md
│   └── ...
├── brain/                  # Task management, company info
│   ├── eisenhower.md
│   ├── companies.md
│   └── ...
└── articles/               # Content for publishing
    ├── drafts/
    └── published/
```

## Tools

### File Indexer (`lola-index-files`)
```bash
# Scan directories and update files.mv2
lola-index-files /home/jpelaez/photos
lola-index-files /home/jpelaez/documents

# Query files
lola-find-files "Ecuador trip photos"
```

### Memory Manager (`lola-memory`)
```bash
# Add memory
lola-memory add --type fact "Juan's income is $215,628/year"

# Query memories
lola-memory find "health issues"

# Link file to memory
lola-memory link --file /path/to/photo.jpg --memory "Ecuador trip"
```

## Migration from Current System

Current markdown files in `memory/` stay as curated context. We add:
1. `indexes/` folder with Memvid files
2. CLI tools for indexing and querying
3. Skill for Lola to use during conversations

## When to Use What

| Need | Solution |
|------|----------|
| High-level context for every conversation | Markdown (CLAUDE.md, memory/*.md) |
| Find specific files | files.mv2 |
| Recall facts, events, learnings | memories.mv2 |
| Complex SQL-like queries | Consider adding SQLite for edge cases |
