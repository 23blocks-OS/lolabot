---
name: file-processing
description: Classify, file and index documents, and extract the facts in them into the user's memory. Use when a document needs classifying, filing or indexing, such as a new PDF, scan or photo of an ID, contract, certificate, medical or financial record.
allowed-tools: Bash, Read, Write, Glob
---

# File Processing

Processing a document means four things, all of them: read it, move it to its permanent folder, index it at the new path, and save the facts it contains to the user's memory. Stopping after any one of these leaves the document unfindable or its facts unknown.

## 1. Read it

Read PDFs, images and text with the Read tool. Note the document type, the people in it, dates, and the facts the user would later ask about. Convert HEIC photos first with `$LOLABOT_HOME/tools/heic-convert.sh <file-or-folder>` (JPGs go to `/tmp/heic-converted/`).

## 2. Move it to its permanent folder

| Document | Folder |
|---|---|
| The user's own ID (passport, national ID, police certificates) | `~/documents/personal/id/` |
| Military records | `~/documents/personal/military/` |
| A family member's documents | `~/documents/personal/<name>/` |
| Legal (contracts, divorce) | `~/documents/legal/<category>/` |
| Migration and immigration | `~/documents/legal/migration/` |
| Medical records and bills | `~/documents/medical/` |
| A company's documents | `~/<Company>/documents/` (the company's folder, not personal documents) |
| Someone else's documents (a contact or third party) | `~/documents/contacts/<name>/` |

The companies and their folders are listed under "Companies & Projects" in CLAUDE.md. Create folders with `mkdir -p` as needed.

New documents usually arrive in the transport folder, the instance's drop folder (if CLAUDE.md does not say where it is, ask the user). Transport is a drop zone, not storage: move each file out, and once it is indexed at its new path, delete the original from transport.

## 3. Index it

```bash
$LOLABOT_HOME/tools/files.sh add "<new path>" -d "<one-line description>" -t "<tags>"
$LOLABOT_HOME/tools/files.sh scan <folder> --tags "<tags>"     # a whole folder (--no-recursive, --pattern '*.pdf')
$LOLABOT_HOME/tools/files.sh find "<query>"                     # check it is findable
```

Tags: the document type (`personal`, `legal`, `medical`, `business`), the person's name if it is about someone, and the category (`id`, `passport`, `divorce`, `migration`...). The description is what search matches on, so say what the document is and whose it is.

## 4. Save the facts to the user's memory

```bash
$LOLABOT_HOME/tools/memory.sh add "<fact>" --type fact|event|person --tags "<tags>" \
    [--date YYYY-MM-DD] [--people "<names>"] [--files "<path>"] [--source "<document>"]
```

| The document contains | Type | Example |
|---|---|---|
| ID numbers, birth dates, addresses, balances, expiry dates | `fact` | "Sam's passport expires 2030-01-01" |
| Something that happened on a date | `event` | "Sam was born on 2012-03-03" |
| Who someone is to the user | `person` | "Jordan Rivera is Alex's cousin" |

Pass `--files` with the document's new path and `--source` with its name, so the fact can be traced back. Skip facts memory already has and trivial details. Passwords, PINs and other credentials do not go into memory. Follow the pa-memory-delegation skill for evolving facts (a new address replaces the old one) and for saving to the matching markdown file as well.

`files.sh` and `memory.sh` activate the virtualenv themselves.
