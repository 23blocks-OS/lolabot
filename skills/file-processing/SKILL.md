---
name: File Processing
description: Process, classify, organize, and index documents. Extracts relevant information to user's memory.
allowed-tools: Bash, Read, Write, Glob
---

# File Processing Skill

When asked to "process", "organize", or "file" documents, follow this complete workflow.

---

## The Workflow

### 1. Read & Understand

Read each document to understand its content:
- PDFs: Use Read tool (supports PDF extraction)
- Images: Use Read tool (multimodal)
- Text files: Use Read tool

Extract key information:
- Document type (ID, legal, medical, business, personal)
- People involved
- Dates and events
- Important facts

### 2. Classify & Organize

Move files to the appropriate folder based on content:

| Document Type | Destination |
|---------------|-------------|
| Personal ID (cédula, passport, police certs) | `/home/jpelaez/documents/personal/id/` |
| Military records | `/home/jpelaez/documents/personal/military/` |
| Family member docs | `/home/jpelaez/documents/personal/{name}/` |
| Legal (divorces, contracts) | `/home/jpelaez/documents/legal/{category}/` |
| Migration/immigration | `/home/jpelaez/documents/legal/migration/` |
| Medical records, billing | `/home/jpelaez/documents/medical/` |
| Company documents | `/home/jpelaez/{CompanyName}/documents/` |
| Contact/third-party docs | `/home/jpelaez/documents/contacts/{name}/` |

**Important:** Company documents go in the company folder, not personal documents.

### 3. Index Files

Use `file_indexer.py` to add files to the searchable index:

```bash
$LOLABOT_HOME/tools/files.sh scan /path/to/folder --tags "tag1,tag2"
$LOLABOT_HOME/tools/files.sh add "/path/to/file.pdf" -d "Description" -t "tags"
```

Or with full command:
```bash
source $LOLABOT_HOME/.venv/bin/activate
python $LOLABOT_HOME/tools/file_indexer.py scan /path --tags "tags"
```

**Tagging guidelines:**
- Always include document type: `personal`, `legal`, `medical`, `business`
- Include person name if relevant: `juan`, `felipe`, `marco`
- Include category: `id`, `passport`, `divorce`, `migration`

### 4. Extract to Memory

For documents containing personal information about Juan or his family, add relevant facts to memory:

```bash
$LOLABOT_HOME/tools/memory.sh add "Fact extracted from document" --type fact --tags "relevant,tags"
```

Or with full command:
```bash
source $LOLABOT_HOME/.venv/bin/activate
python $LOLABOT_HOME/tools/memory_indexer.py add "..." --type fact --tags "..."
```

**What to extract:**
| Document Contains | Memory Type | Example |
|-------------------|-------------|---------|
| Birth date, ID numbers | fact | "Juan's cédula is 79,672,150" |
| Events with dates | event | "Felipe born December 26, 2007" |
| Relationships | person | "Jose Miguel Nunes Pelaez is Juan's cousin" |
| Addresses | fact | "Current address: 2852 Kalmia Ave..." |
| Financial info | fact | "BCH medical debt: $12,171.78" |
| Expiration dates | fact | "Felipe's passport expires Feb 14, 2026" |

**Don't extract:**
- Redundant information already in memory
- Trivial details
- Sensitive credentials (store securely elsewhere)

---

## Folder Structure Reference

```
/home/jpelaez/
├── documents/
│   ├── personal/
│   │   ├── id/           # Juan's ID documents
│   │   ├── military/     # Military records
│   │   ├── felipe/       # Son's documents
│   │   ├── marco/        # Father's documents
│   │   └── {family}/     # Other family members
│   ├── legal/
│   │   ├── divorces/
│   │   ├── migration/
│   │   └── contracts/
│   ├── medical/
│   └── contacts/
│       └── {name}/       # Third-party documents
├── 3Metas/
│   └── documents/        # 3Metas company docs
├── PPM/
│   └── documents/        # PPM company docs
└── {Company}/
    └── documents/        # Other company docs
```

---

## Transport Folder

New documents typically arrive in `/srv/fileserver/transport/` (local fileserver on mini-lola).

When processing transport:
1. List all files in transport
2. Process each file through the workflow
3. After successful copy and indexing, originals can remain or be removed

---

## Example Session

```bash
# 1. List what's in transport
ls /mnt/fileserver/transport/

# 2. Read a PDF
# (Use Read tool on each file)

# 3. Create destination folder if needed
mkdir -p /home/jpelaez/documents/personal/felipe

# 4. Copy file to destination
cp "/mnt/fileserver/transport/Felipe Birth Certificate.pdf" \
   "/home/jpelaez/documents/personal/felipe/"

# 5. Index the file
source $LOLABOT_HOME/.venv/bin/activate
python $LOLABOT_HOME/tools/file_indexer.py scan \
  /home/jpelaez/documents/personal/felipe --tags "personal,felipe,family"

# 6. Add to memory
python $LOLABOT_HOME/tools/memory_indexer.py add \
  "Felipe Pelaez born December 26, 2007. Mother: Claudia Patricia Huertas Diaz" \
  --type fact --tags "family,felipe"
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| Scan folder | `files.sh scan /path --tags "tags"` |
| Add single file | `files.sh add "/path" -d "desc" -t "tags"` |
| Search files | `files.sh find "query"` |
| Add memory | `memory.sh add "fact" --type TYPE --tags "tags"` |
| Search memory | `memory.sh find "query"` |
