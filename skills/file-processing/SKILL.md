---
name: file-processing
description: Classify, file and index documents, and extract the facts in them into the user's memory. Use when a document needs classifying, filing or indexing, such as a new PDF, scan or photo of an ID, contract, certificate, medical or financial record.
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
| Personal ID (cédula, passport, police certs) | `~/documents/personal/id/` |
| Military records | `~/documents/personal/military/` |
| Family member docs | `~/documents/personal/{name}/` |
| Legal (divorces, contracts) | `~/documents/legal/{category}/` |
| Migration/immigration | `~/documents/legal/migration/` |
| Medical records, billing | `~/documents/medical/` |
| Company documents | `~/{CompanyName}/documents/` |
| Contact/third-party docs | `~/documents/contacts/{name}/` |

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
- Include person name if relevant: `alex`, `sam`, `jordan`
- Include category: `id`, `passport`, `divorce`, `migration`

### 4. Extract to Memory

For documents containing personal information about the user or their family, add relevant facts to memory:

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
| Birth date, ID numbers | fact | "Alex's ID number is 00,000,000" |
| Events with dates | event | "Sam born March 3, 2012" |
| Relationships | person | "Jordan Rivera is Alex's cousin" |
| Addresses | fact | "Current address: 123 Example St..." |
| Financial info | fact | "Clinic balance: $1,250.00" |
| Expiration dates | fact | "Sam's passport expires Jan 1, 2030" |

**Don't extract:**
- Redundant information already in memory
- Trivial details
- Sensitive credentials (store securely elsewhere)

---

## Folder Structure Reference

```
~/
├── documents/
│   ├── personal/
│   │   ├── id/           # Juan's ID documents
│   │   ├── military/     # Military records
│   │   ├── sam/          # Child's documents
│   │   ├── jordan/       # Parent's documents
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
mkdir -p ~/documents/personal/sam

# 4. Copy file to destination
cp "/mnt/fileserver/transport/Sam Birth Certificate.pdf" \
   "~/documents/personal/sam/"

# 5. Index the file
source $LOLABOT_HOME/.venv/bin/activate
python $LOLABOT_HOME/tools/file_indexer.py scan \
  ~/documents/personal/sam --tags "personal,sam,family"

# 6. Add to memory
python $LOLABOT_HOME/tools/memory_indexer.py add \
  "Sam Rivera born March 3, 2012. Mother: Taylor Rivera" \
  --type fact --tags "family,sam"
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
