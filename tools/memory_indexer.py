#!/usr/bin/env python3
"""
Lola Memory Indexer (v2 - Two-Tier Memory)

Indexes knowledge, facts, events, and learnings into Memvid V2.
Separate from file index - this stores WHAT we know, not WHERE things are.

Features:
- Deduplication: Similar memories get reinforced, not duplicated
- Reinforcement tracking: See what's mentioned repeatedly
- Access tracking: See what memories are actually used
- Confidence scores: Quality indicator for memories

Usage:
    python memory_indexer.py add --type fact "Juan's income is $215,628/year"
    python memory_indexer.py add --type event --date 2024-10-17 "Immigration waiver approved"
    python memory_indexer.py find "health issues"
    python memory_indexer.py stats
"""

import os
import sys
import argparse
import re
import sqlite3
import hashlib
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

try:
    import memvid_sdk
    MEMVID_AVAILABLE = True
except ImportError:
    MEMVID_AVAILABLE = False
    print("Warning: memvid-sdk not installed. Install with: pip install memvid-sdk")

# Ensure we can import sibling modules (config)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import get_path

# Configuration — resolved from lolabot.yaml via config.py
LONG_TERM_INDEX = get_path('long_term_index')
SHORT_TERM_INDEX = get_path('short_term_index')
METADATA_DB = get_path('metadata_db')
INDEX_PATH = LONG_TERM_INDEX  # Default to long-term for backwards compatibility
SIMILARITY_THRESHOLD = 0.85  # Memories with similarity > this are considered duplicates
DEFAULT_CONFIDENCE = 0.7     # Default confidence for new memories
REINFORCEMENT_BOOST = 0.05   # How much confidence increases on reinforcement
PROMOTION_THRESHOLD_DAYS = 7 # Days before eligible for promotion
PROMOTION_MIN_REINFORCEMENT = 2  # Minimum reinforcements to auto-promote


class MemoryMetadataDB:
    """SQLite database for mutable memory metadata (like PostgreSQL)."""

    def __init__(self, db_path: str = METADATA_DB):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Connect and ensure schema exists."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self):
        """Create tables if they don't exist."""
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS memory_meta (
                memory_id TEXT PRIMARY KEY,
                content_hash TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                index_type TEXT NOT NULL,  -- 'long_term' or 'short_term'
                confidence REAL DEFAULT 0.7,
                access_count INTEGER DEFAULT 0,
                reinforcement_count INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                last_accessed TEXT,
                last_reinforced TEXT,
                content_preview TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_content_hash ON memory_meta(content_hash);
            CREATE INDEX IF NOT EXISTS idx_index_type ON memory_meta(index_type);
            CREATE INDEX IF NOT EXISTS idx_access_count ON memory_meta(access_count DESC);
            CREATE INDEX IF NOT EXISTS idx_reinforcement_count ON memory_meta(reinforcement_count DESC);
        ''')
        self.conn.commit()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _hash_content(self, content: str) -> str:
        """Create hash of content for deduplication."""
        normalized = content.lower().strip()[:200]
        return hashlib.md5(normalized.encode()).hexdigest()

    def find_by_content(self, content: str, index_type: str = None) -> Optional[Dict]:
        """Find metadata by content hash."""
        content_hash = self._hash_content(content)
        if index_type:
            row = self.conn.execute(
                'SELECT * FROM memory_meta WHERE content_hash = ? AND index_type = ?',
                (content_hash, index_type)
            ).fetchone()
        else:
            row = self.conn.execute(
                'SELECT * FROM memory_meta WHERE content_hash = ?',
                (content_hash,)
            ).fetchone()
        return dict(row) if row else None

    def create(self, content: str, memory_type: str, index_type: str,
               confidence: float = DEFAULT_CONFIDENCE) -> str:
        """Create metadata record for new memory."""
        content_hash = self._hash_content(content)
        memory_id = f"{index_type[:1]}_{content_hash[:12]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        now = datetime.now().isoformat()

        self.conn.execute('''
            INSERT INTO memory_meta
            (memory_id, content_hash, memory_type, index_type, confidence,
             access_count, reinforcement_count, created_at, content_preview)
            VALUES (?, ?, ?, ?, ?, 0, 1, ?, ?)
        ''', (memory_id, content_hash, memory_type, index_type, confidence,
              now, content[:100]))
        self.conn.commit()
        return memory_id

    def reinforce(self, content: str, index_type: str = None) -> Optional[Dict]:
        """Increment reinforcement count for existing memory."""
        existing = self.find_by_content(content, index_type)
        if existing:
            now = datetime.now().isoformat()
            new_count = existing['reinforcement_count'] + 1
            new_confidence = min(1.0, existing['confidence'] + REINFORCEMENT_BOOST)

            self.conn.execute('''
                UPDATE memory_meta
                SET reinforcement_count = ?, last_reinforced = ?, confidence = ?
                WHERE memory_id = ?
            ''', (new_count, now, new_confidence, existing['memory_id']))
            self.conn.commit()

            existing['reinforcement_count'] = new_count
            existing['confidence'] = new_confidence
            existing['last_reinforced'] = now
            return existing
        return None

    def record_access(self, content: str, index_type: str = None):
        """Increment access count when memory is retrieved."""
        existing = self.find_by_content(content, index_type)
        if existing:
            now = datetime.now().isoformat()
            self.conn.execute('''
                UPDATE memory_meta
                SET access_count = access_count + 1, last_accessed = ?
                WHERE memory_id = ?
            ''', (now, existing['memory_id']))
            self.conn.commit()

    def get_stats(self, index_type: str = None) -> Dict:
        """Get statistics about memories."""
        if index_type:
            row = self.conn.execute('''
                SELECT COUNT(*) as count,
                       SUM(access_count) as total_accesses,
                       AVG(confidence) as avg_confidence,
                       MAX(reinforcement_count) as max_reinforcement
                FROM memory_meta WHERE index_type = ?
            ''', (index_type,)).fetchone()
        else:
            row = self.conn.execute('''
                SELECT COUNT(*) as count,
                       SUM(access_count) as total_accesses,
                       AVG(confidence) as avg_confidence,
                       MAX(reinforcement_count) as max_reinforcement
                FROM memory_meta
            ''').fetchone()
        return dict(row) if row else {}

    def get_most_accessed(self, limit: int = 10, index_type: str = None) -> List[Dict]:
        """Get most frequently accessed memories."""
        if index_type:
            rows = self.conn.execute('''
                SELECT * FROM memory_meta
                WHERE index_type = ? AND access_count > 0
                ORDER BY access_count DESC LIMIT ?
            ''', (index_type, limit)).fetchall()
        else:
            rows = self.conn.execute('''
                SELECT * FROM memory_meta
                WHERE access_count > 0
                ORDER BY access_count DESC LIMIT ?
            ''', (limit,)).fetchall()
        return [dict(row) for row in rows]

    def get_most_reinforced(self, limit: int = 10, index_type: str = None) -> List[Dict]:
        """Get most reinforced memories."""
        if index_type:
            rows = self.conn.execute('''
                SELECT * FROM memory_meta
                WHERE index_type = ? AND reinforcement_count > 1
                ORDER BY reinforcement_count DESC LIMIT ?
            ''', (index_type, limit)).fetchall()
        else:
            rows = self.conn.execute('''
                SELECT * FROM memory_meta
                WHERE reinforcement_count > 1
                ORDER BY reinforcement_count DESC LIMIT ?
            ''', (limit,)).fetchall()
        return [dict(row) for row in rows]

    def get_for_promotion(self, min_reinforcement: int = PROMOTION_MIN_REINFORCEMENT,
                          min_confidence: float = 0.9) -> List[Dict]:
        """Get short-term memories eligible for promotion."""
        rows = self.conn.execute('''
            SELECT * FROM memory_meta
            WHERE index_type = 'short_term'
            AND (reinforcement_count >= ? OR confidence >= ?)
            ORDER BY reinforcement_count DESC, confidence DESC
        ''', (min_reinforcement, min_confidence)).fetchall()
        return [dict(row) for row in rows]

    def promote_to_long_term(self, memory_id: str):
        """Mark memory as promoted to long-term."""
        self.conn.execute('''
            UPDATE memory_meta SET index_type = 'long_term' WHERE memory_id = ?
        ''', (memory_id,))
        self.conn.commit()

# Memory types
class MemoryType:
    FACT = "fact"           # Things that are true (Juan lives in Boulder)
    EVENT = "event"         # Things that happened (Heart attack on 8/13/2024)
    LEARNING = "learning"   # Things discovered (Memvid is faster than SQLite)
    DECISION = "decision"   # Choices made and why (Chose Memvid for memory storage)
    NOTE = "note"           # General notes about topics
    PERSON = "person"       # Notes about a person
    GOAL = "goal"           # Goals and objectives
    PREFERENCE = "preference"  # User preferences
    PATTERN = "pattern"     # Recurring workflows (Run tests before deploying)
    INSIGHT = "insight"     # Understanding about systems (This codebase uses repository pattern)

    @classmethod
    def all(cls):
        return [cls.FACT, cls.EVENT, cls.LEARNING, cls.DECISION, cls.NOTE,
                cls.PERSON, cls.GOAL, cls.PREFERENCE, cls.PATTERN, cls.INSIGHT]


class MemoryIndex:
    """Memvid-based memory/knowledge index with SQLite metadata."""

    def __init__(self, index_path: str = INDEX_PATH, short_term: bool = False):
        if short_term:
            self.index_path = SHORT_TERM_INDEX
            self.index_type = 'short_term'
        else:
            self.index_path = index_path
            self.index_type = 'long_term'
        self.is_short_term = short_term
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        self.mem = None
        self._count = 0
        self.meta_db = MemoryMetadataDB()

    @classmethod
    def long_term(cls):
        """Get long-term memory index."""
        return cls(LONG_TERM_INDEX, short_term=False)

    @classmethod
    def short_term(cls):
        """Get short-term memory index."""
        return cls(SHORT_TERM_INDEX, short_term=True)

    def open(self, create: bool = False):
        """Open or create the index."""
        if not MEMVID_AVAILABLE:
            raise RuntimeError("memvid-sdk not installed")

        mode = "create" if create else "open"

        if not create and not os.path.exists(self.index_path):
            print(f"Index not found at {self.index_path}, creating new one...")
            mode = "create"

        self.mem = memvid_sdk.use(
            "basic",
            self.index_path,
            mode=mode,
            enable_vec=True,
            enable_lex=True,
        )

        # Connect SQLite metadata database
        self.meta_db.connect()

    def close(self):
        """Close the index."""
        if self.mem:
            self.mem.close()
            self.mem = None
        # Close SQLite metadata database
        self.meta_db.close()

    def find_similar(self, content: str, threshold: float = SIMILARITY_THRESHOLD) -> Optional[Dict[str, Any]]:
        """Find a similar existing memory for deduplication."""
        if not self.mem:
            self.open()

        # Normalize content for comparison
        def normalize(s):
            # Lowercase, remove extra spaces, remove punctuation for comparison
            s = s.lower().strip()
            s = re.sub(r'[^\w\s]', '', s)  # Remove punctuation
            s = re.sub(r'\s+', ' ', s)      # Normalize whitespace
            return s

        normalized_new = normalize(content[:150])

        # Search for similar content
        try:
            result = self.mem.find(content[:100], k=10)  # Search with first 100 chars
        except:
            return None

        for hit in result.get('hits', []):
            text = hit.get('text', '') or hit.get('snippet', '')

            # Extract existing memory content
            content_match = re.search(r'Memory:\s*(.+?)(?:\nType:|\nConfidence:|\n|$)', text, re.DOTALL)
            if content_match:
                existing_content = content_match.group(1).strip()
                normalized_existing = normalize(existing_content[:150])

                # Check similarity: if normalized versions are very similar
                # Simple check: same first 50 chars after normalization
                if normalized_existing[:50] == normalized_new[:50]:
                    return hit

                # Also check if one contains the other (for slight variations)
                if len(normalized_existing) > 20 and len(normalized_new) > 20:
                    if normalized_existing[:30] in normalized_new or normalized_new[:30] in normalized_existing:
                        return hit

        return None

    def add_memory(
        self,
        content: str,
        memory_type: str = MemoryType.NOTE,
        date_str: str = None,
        tags: List[str] = None,
        related_files: List[str] = None,
        related_people: List[str] = None,
        source: str = None,
        confidence: float = None,
        context: str = None,
        skip_dedup: bool = False,
    ) -> Dict[str, Any]:
        """Add a memory to the index with deduplication.

        Returns dict with:
        - action: 'created' or 'reinforced'
        - content: the memory content
        - reinforcement_count: times this has been seen (if reinforced)
        """
        if not self.mem:
            self.open(create=not os.path.exists(self.index_path))

        today = date.today().isoformat()

        # Check for existing similar memory (deduplication)
        if not skip_dedup:
            similar = self.find_similar(content)
            if similar:
                # Reinforce in SQLite metadata (this IS updated, unlike Memvid)
                if self.meta_db.conn:
                    reinforced = self.meta_db.reinforce(content, self.index_type)
                    if reinforced:
                        print(f"  → Similar memory exists (reinforcement #{reinforced['reinforcement_count']})")
                        return {
                            'action': 'reinforced',
                            'content': content[:50] + '...',
                            'reinforcement_count': reinforced['reinforcement_count'],
                            'confidence': reinforced['confidence'],
                            'note': 'Memory already exists - reinforced in SQLite metadata'
                        }

                # Fallback to text-based tracking if SQLite not available
                text = similar.get('text', '')
                reinforce_match = re.search(r'Reinforcement_count:\s*(\d+)', text)
                current_count = int(reinforce_match.group(1)) if reinforce_match else 1

                print(f"  → Similar memory exists (reinforcement #{current_count + 1})")
                return {
                    'action': 'reinforced',
                    'content': content[:50] + '...',
                    'reinforcement_count': current_count + 1,
                    'note': 'Memory already exists - reinforced'
                }

        # Parse date if provided
        memory_date = None
        if date_str:
            try:
                memory_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                try:
                    memory_date = datetime.strptime(date_str, "%Y-%m").date()
                except ValueError:
                    pass

        # Set confidence
        mem_confidence = confidence if confidence is not None else DEFAULT_CONFIDENCE

        # Build searchable text with new fields
        text_parts = [
            f"Memory: {content}",
            f"Type: {memory_type}",
            f"Confidence: {mem_confidence}",
            f"Reinforcement_count: 1",
            f"Access_count: 0",
            f"Created: {today}",
        ]

        if memory_date:
            text_parts.append(f"Date: {memory_date.isoformat()}")
            text_parts.append(f"Year: {memory_date.year}")
            if memory_date.month:
                text_parts.append(f"Month: {memory_date.strftime('%B %Y')}")

        if related_people:
            text_parts.append(f"People: {', '.join(related_people)}")

        if related_files:
            text_parts.append(f"Related files: {', '.join(related_files)}")

        if source:
            text_parts.append(f"Source: {source}")

        if context:
            text_parts.append(f"Context: {context}")

        text = "\n".join(text_parts)

        # Build tags
        auto_tags = [memory_type]
        if memory_date:
            auto_tags.append(str(memory_date.year))
        if related_people:
            auto_tags.extend([p.lower() for p in related_people])

        all_tags = list(set((tags or []) + auto_tags))

        # Generate title (first 50 chars of content)
        title = content[:50] + ("..." if len(content) > 50 else "")

        # Add to index
        frame_id = self.mem.put(
            title=title,
            label=memory_type,
            text=text,
            tags=all_tags,
            timestamp=memory_date.isoformat() if memory_date else None,
        )

        self._count += 1

        # Create SQLite metadata record for mutable tracking
        memory_id = None
        if self.meta_db.conn:
            memory_id = self.meta_db.create(
                content=content,
                memory_type=memory_type,
                index_type=self.index_type,
                confidence=mem_confidence
            )

        # Close and reopen to persist
        self.close()
        self.open()

        return {
            'action': 'created',
            'content': content[:50] + '...',
            'confidence': mem_confidence,
            'frame_id': frame_id,
            'memory_id': memory_id
        }

    def add_memories_batch(self, memories: List[Dict[str, Any]]):
        """Add multiple memories to the index."""
        if not self.mem:
            self.open(create=True)

        for i, memory in enumerate(memories):
            content = memory.get("content", "")
            if not content:
                continue

            # Build text
            text_parts = [
                f"Memory: {content}",
                f"Type: {memory.get('type', MemoryType.NOTE)}",
            ]

            if memory.get("date"):
                text_parts.append(f"Date: {memory['date']}")

            if memory.get("people"):
                text_parts.append(f"People: {', '.join(memory['people'])}")

            if memory.get("files"):
                text_parts.append(f"Related files: {', '.join(memory['files'])}")

            text = "\n".join(text_parts)

            # Tags
            tags = list(set(
                memory.get("tags", []) +
                [memory.get("type", MemoryType.NOTE)] +
                [p.lower() for p in memory.get("people", [])]
            ))

            title = content[:50] + ("..." if len(content) > 50 else "")

            self.mem.put(
                title=title,
                label=memory.get("type", MemoryType.NOTE),
                text=text,
                tags=tags,
            )

            if (i + 1) % 50 == 0:
                print(f"  Added {i + 1}/{len(memories)} memories...")

        self.close()
        self.open()

        print(f"Added {len(memories)} memories")

    def find(
        self,
        query: str,
        limit: int = 10,
        memory_type: str = None,
        year: int = None,
        person: str = None,
        track_access: bool = True,
    ) -> List[Dict[str, Any]]:
        """Search for memories with access tracking."""
        if not self.mem:
            self.open()

        # Build search query with filters
        search_parts = [query]
        if memory_type:
            search_parts.append(memory_type)
        if year:
            search_parts.append(str(year))
        if person:
            search_parts.append(person.lower())

        search_query = " ".join(search_parts)

        result = self.mem.find(search_query, k=limit * 2)

        hits = []
        seen_content = set()

        for hit in result.get('hits', []):
            text = hit.get('text', '') or hit.get('snippet', '')

            # Extract memory content (stop at " Type:" which follows the content)
            content = ""
            content_match = re.search(r'Memory:\s*(.+?)\s+Type:', text, re.DOTALL)
            if content_match:
                content = content_match.group(1).strip()
            else:
                # Fallback: try to get first line after Memory:
                content_match = re.search(r'Memory:\s*([^\n]+)', text)
                if content_match:
                    content = content_match.group(1).strip()

            # Extract type
            mem_type = MemoryType.NOTE
            type_match = re.search(r'Type:\s*(\w+)', text)
            if type_match:
                mem_type = type_match.group(1)

            # Extract date (YYYY-MM-DD format)
            mem_date = None
            date_match = re.search(r'Date:\s*(\d{4}-\d{2}-\d{2})', text)
            if date_match:
                mem_date = date_match.group(1)

            # Extract confidence
            confidence = DEFAULT_CONFIDENCE
            conf_match = re.search(r'Confidence:\s*([\d.]+)', text)
            if conf_match:
                try:
                    confidence = float(conf_match.group(1))
                except:
                    pass

            # Extract reinforcement count
            reinforcement = 1
            reinf_match = re.search(r'Reinforcement_count:\s*(\d+)', text)
            if reinf_match:
                reinforcement = int(reinf_match.group(1))

            # Extract access count
            access_count = 0
            access_match = re.search(r'Access_count:\s*(\d+)', text)
            if access_match:
                access_count = int(access_match.group(1))

            # Extract people (stop at newline, title, or labels)
            people = []
            people_match = re.search(r'People:\s*([A-Za-z, ]+?)(?:\n|title:|labels:|$)', text)
            if people_match:
                people_str = people_match.group(1).strip()
                # Only take actual names, not metadata
                people = [p.strip() for p in people_str.split(',') if p.strip() and len(p.strip()) < 30]

            # Extract related files (stop at "title:" which marks metadata)
            files = []
            files_match = re.search(r'Related files:\s*(.+?)(?:\s+title:|\s+tags:|\s+labels:|$)', text)
            if files_match:
                files_str = files_match.group(1).strip()
                # Only take URIs/paths, filter out metadata
                for f in files_str.split(','):
                    f = f.strip()
                    if ('/' in f or '://' in f) and not f.startswith('title:') and len(f) < 150:
                        files.append(f)

            # Skip duplicates (by content hash)
            content_hash = hash(content[:100])
            if content_hash in seen_content:
                continue
            seen_content.add(content_hash)

            # Apply filters
            if memory_type and mem_type != memory_type:
                continue
            if year and mem_date and str(year) not in mem_date:
                continue
            if person and person.lower() not in [p.lower() for p in people]:
                continue

            # Get actual metadata from SQLite if available
            meta_confidence = confidence
            meta_reinforcement = reinforcement
            meta_access = access_count

            if track_access and self.meta_db.conn and content:
                # Record access in SQLite (this IS updated)
                self.meta_db.record_access(content, self.index_type)

                # Get fresh metadata
                meta = self.meta_db.find_by_content(content, self.index_type)
                if meta:
                    meta_confidence = meta.get('confidence', confidence)
                    meta_reinforcement = meta.get('reinforcement_count', reinforcement)
                    meta_access = meta.get('access_count', access_count)

            hits.append({
                "content": content,
                "type": mem_type,
                "date": mem_date,
                "people": people,
                "files": files,
                "tags": hit.get('tags', [])[:5],
                "score": hit.get('score', 0),
                "confidence": meta_confidence,
                "reinforcement_count": meta_reinforcement,
                "access_count": meta_access,
            })

            if len(hits) >= limit:
                break

        return hits

    def find_by_person(self, person: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find memories related to a specific person."""
        return self.find(person, limit=limit, person=person)

    def find_by_year(self, year: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Find memories from a specific year."""
        return self.find(str(year), limit=limit, year=year)

    def stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        if not os.path.exists(self.index_path):
            return {"exists": False}

        file_size = os.path.getsize(self.index_path)

        return {
            "exists": True,
            "path": self.index_path,
            "size_kb": file_size / 1024,
            "size_mb": file_size / (1024 * 1024),
            "is_short_term": self.is_short_term,
        }

    def get_all_memories(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all memories from the index (for review/promotion)."""
        # Use a broad search with common words to get all entries
        # Search for "Memory" which appears in all entries
        return self.find("Memory", limit=limit, track_access=False)


def promote_memories(dry_run: bool = False, min_reinforcement: int = PROMOTION_MIN_REINFORCEMENT) -> Dict[str, Any]:
    """Promote mature short-term memories to long-term.

    Uses SQLite metadata for accurate reinforcement/confidence tracking.
    Returns stats about what was promoted.
    """
    short_term = MemoryIndex.short_term()
    long_term = MemoryIndex.long_term()
    meta_db = MemoryMetadataDB()

    try:
        short_term.open()
        meta_db.connect()
    except:
        return {"error": "Short-term index not found", "promoted": 0}

    # Get promotion candidates from SQLite (accurate counters)
    candidates = meta_db.get_for_promotion(min_reinforcement=min_reinforcement)

    # Also get all short-term memories from Memvid for content
    memories = short_term.get_all_memories(limit=200)

    # Build lookup by content hash
    memory_content = {}
    for mem in memories:
        content_hash = hashlib.md5(mem['content'].lower().strip()[:200].encode()).hexdigest()
        memory_content[content_hash] = mem

    promoted = []
    skipped = []

    # Process SQLite candidates (these have accurate counts)
    for candidate in candidates:
        content_hash = candidate['content_hash']
        mem = memory_content.get(content_hash)

        if not mem:
            continue  # Orphaned metadata, skip

        reinforcement = candidate.get('reinforcement_count', 1)
        confidence = candidate.get('confidence', DEFAULT_CONFIDENCE)

        if not dry_run:
            # Add to long-term
            long_term.add_memory(
                content=mem['content'],
                memory_type=mem['type'],
                date_str=mem.get('date'),
                tags=mem.get('tags'),
                related_people=mem.get('people'),
                related_files=mem.get('files'),
                confidence=confidence,
                skip_dedup=False,
            )
            # Update metadata to reflect promotion
            meta_db.promote_to_long_term(candidate['memory_id'])

        promoted.append({
            'content': mem['content'][:50] + '...',
            'type': mem['type'],
            'reinforcement': reinforcement,
            'confidence': confidence,
        })

    # Check for memories not in SQLite (old format) using Memvid data
    for mem in memories:
        content_hash = hashlib.md5(mem['content'].lower().strip()[:200].encode()).hexdigest()

        # Skip if already processed via SQLite
        if any(c['content_hash'] == content_hash for c in candidates):
            continue

        # Use Memvid-stored values (less accurate but fallback)
        reinforcement = mem.get('reinforcement_count', 1)
        confidence = mem.get('confidence', DEFAULT_CONFIDENCE)

        should_promote = (reinforcement >= min_reinforcement) or (confidence >= 0.9)

        if should_promote:
            if not dry_run:
                long_term.add_memory(
                    content=mem['content'],
                    memory_type=mem['type'],
                    date_str=mem.get('date'),
                    tags=mem.get('tags'),
                    related_people=mem.get('people'),
                    related_files=mem.get('files'),
                    confidence=confidence,
                    skip_dedup=False,
                )
            promoted.append({
                'content': mem['content'][:50] + '...',
                'type': mem['type'],
                'reinforcement': reinforcement,
                'confidence': confidence,
            })
        else:
            skipped.append({
                'content': mem['content'][:50] + '...',
                'reinforcement': reinforcement,
                'reason': f'needs {min_reinforcement} reinforcements or 90% confidence'
            })

    short_term.close()
    long_term.close()
    meta_db.close()

    return {
        'promoted': len(promoted),
        'skipped': len(skipped),
        'promoted_memories': promoted,
        'skipped_memories': skipped[:5],  # Only show first 5 skipped
        'dry_run': dry_run,
    }


# CLI Commands

def cmd_add(args):
    """Handle add command."""
    # Choose index based on --short-term flag
    if args.short_term:
        index = MemoryIndex.short_term()
        index_name = "short-term"
    else:
        index = MemoryIndex.long_term()
        index_name = "long-term"

    tags = args.tags.split(',') if args.tags else None
    files = args.files.split(',') if args.files else None
    people = args.people.split(',') if args.people else None

    result = index.add_memory(
        content=args.content,
        memory_type=args.type,
        date_str=args.date,
        tags=tags,
        related_files=files,
        related_people=people,
        source=args.source,
        confidence=args.confidence,
        context=args.context,
        skip_dedup=args.force,
    )

    if result['action'] == 'created':
        print(f"Added to {index_name}: {result['content']}")
        print(f"  Type: {args.type}, Confidence: {result['confidence']}")
    else:
        print(f"Reinforced in {index_name}: {result['content']}")
        print(f"  Reinforcement count: {result['reinforcement_count']}")

    index.close()


def cmd_find(args):
    """Handle find command."""
    # Choose index based on --short-term flag
    if args.short_term:
        index = MemoryIndex.short_term()
        index_name = "short-term"
    else:
        index = MemoryIndex.long_term()
        index_name = "long-term"

    try:
        index.open()
    except Exception as e:
        print(f"Error opening {index_name} index: {e}")
        print("Run 'add' first to create the index")
        return

    results = index.find(
        args.query,
        limit=args.limit,
        memory_type=args.type,
        year=args.year,
        person=args.person,
    )

    if not results:
        print("No memories found")
        return

    print(f"\nFound {len(results)} memories:\n")

    type_icons = {
        MemoryType.FACT: "📌",
        MemoryType.EVENT: "📅",
        MemoryType.LEARNING: "💡",
        MemoryType.DECISION: "⚖️",
        MemoryType.NOTE: "📝",
        MemoryType.PERSON: "👤",
        MemoryType.GOAL: "🎯",
        MemoryType.PREFERENCE: "⭐",
        MemoryType.PATTERN: "🔄",
        MemoryType.INSIGHT: "🧠",
    }

    for i, hit in enumerate(results, 1):
        icon = type_icons.get(hit['type'], "📝")
        # Clean content for display
        content = hit['content']
        # Remove any "Type:" suffix that leaked through
        content = re.sub(r'\s*Type:.*$', '', content)
        content = content[:80] + ('...' if len(content) > 80 else '')

        print(f"{i}. {icon} [{hit['type']}] {content}")

        if hit['date']:
            print(f"   Date: {hit['date']}")
        if hit['people']:
            # Clean people list
            clean_people = [p for p in hit['people'] if len(p) < 30 and not ':' in p]
            if clean_people:
                print(f"   People: {', '.join(clean_people)}")
        if hit['files']:
            # Clean files list - only show actual URIs
            clean_files = [f for f in hit['files'] if '/' in f and len(f) < 100][:2]
            if clean_files:
                print(f"   Files: {', '.join(clean_files)}")

        # Show new tracking fields
        meta_parts = []
        if hit.get('confidence', 0) != DEFAULT_CONFIDENCE:
            meta_parts.append(f"conf:{hit['confidence']:.0%}")
        if hit.get('reinforcement_count', 1) > 1:
            meta_parts.append(f"reinforced:{hit['reinforcement_count']}x")
        if hit.get('access_count', 0) > 0:
            meta_parts.append(f"accessed:{hit['access_count']}x")

        if meta_parts:
            print(f"   [{', '.join(meta_parts)}]")

        print(f"   Tags: {', '.join(hit['tags'])}")
        print()

    index.close()


def cmd_import_markdown(args):
    """Import memories from a markdown file."""
    index = MemoryIndex()

    if not os.path.exists(args.file):
        print(f"File not found: {args.file}")
        return

    print(f"Importing from {args.file}...")

    with open(args.file, 'r') as f:
        content = f.read()

    # Simple parser: each paragraph or list item becomes a memory
    memories = []

    # Split by double newlines (paragraphs) or list items
    chunks = re.split(r'\n\n+|\n(?=[-*] )', content)

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk or len(chunk) < 20:
            continue

        # Skip headers and metadata
        if chunk.startswith('#') or chunk.startswith('---'):
            continue

        # Clean up list markers
        chunk = re.sub(r'^[-*]\s+', '', chunk)

        # Try to extract date from content
        date_str = None
        date_match = re.search(r'(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})', chunk)
        if date_match:
            date_str = date_match.group(1)

        memories.append({
            "content": chunk,
            "type": args.type or MemoryType.NOTE,
            "date": date_str,
            "tags": args.tags.split(',') if args.tags else [],
        })

    if memories:
        index.add_memories_batch(memories)
    else:
        print("No memories found in file")

    index.close()


def cmd_stats(args):
    """Handle stats command."""
    print("=== Juan's Memory System ===\n")

    # Long-term stats
    long_term = MemoryIndex.long_term()
    lt_stats = long_term.stats()

    print("Long-term Memory (permanent):")
    if lt_stats["exists"]:
        print(f"  Path: {lt_stats['path']}")
        print(f"  Size: {lt_stats['size_kb']:.2f} KB ({lt_stats['size_mb']:.2f} MB)")
    else:
        print("  Not created yet")

    print()

    # Short-term stats
    short_term = MemoryIndex.short_term()
    st_stats = short_term.stats()

    print("Short-term Memory (staging):")
    if st_stats["exists"]:
        print(f"  Path: {st_stats['path']}")
        print(f"  Size: {st_stats['size_kb']:.2f} KB ({st_stats['size_mb']:.2f} MB)")
    else:
        print("  Not created yet")

    print()

    # SQLite metadata stats
    print("SQLite Metadata (mutable counters):")
    meta_db = MemoryMetadataDB()
    try:
        meta_db.connect()

        # Overall stats
        overall = meta_db.get_stats()
        lt_meta = meta_db.get_stats('long_term')
        st_meta = meta_db.get_stats('short_term')

        print(f"  Path: {METADATA_DB}")
        if os.path.exists(METADATA_DB):
            print(f"  Size: {os.path.getsize(METADATA_DB) / 1024:.2f} KB")
        print(f"  Total tracked: {overall.get('count', 0)} memories")
        print(f"    Long-term: {lt_meta.get('count', 0)}")
        print(f"    Short-term: {st_meta.get('count', 0)}")
        print(f"  Total accesses: {overall.get('total_accesses', 0) or 0}")
        if overall.get('avg_confidence'):
            print(f"  Avg confidence: {overall['avg_confidence']:.0%}")
        if overall.get('max_reinforcement', 1) > 1:
            print(f"  Max reinforcement: {overall['max_reinforcement']}x")

        # Most accessed
        most_accessed = meta_db.get_most_accessed(limit=3)
        if most_accessed:
            print("\n  Most accessed memories:")
            for mem in most_accessed:
                print(f"    - {mem['content_preview'][:40]}... ({mem['access_count']}x)")

        # Most reinforced
        most_reinforced = meta_db.get_most_reinforced(limit=3)
        if most_reinforced:
            print("\n  Most reinforced memories:")
            for mem in most_reinforced:
                print(f"    - {mem['content_preview'][:40]}... ({mem['reinforcement_count']}x)")

        meta_db.close()
    except Exception as e:
        print(f"  Not initialized yet (run 'add' to create)")


def cmd_promote(args):
    """Handle promote command - move short-term to long-term."""
    print("Promoting mature short-term memories to long-term...\n")

    result = promote_memories(
        dry_run=args.dry_run,
        min_reinforcement=args.min_reinforcement,
    )

    if result.get('error'):
        print(f"Error: {result['error']}")
        return

    if args.dry_run:
        print("[DRY RUN - no changes made]\n")

    print(f"Promoted: {result['promoted']}")
    print(f"Skipped: {result['skipped']}")

    if result['promoted_memories']:
        print("\nPromoted memories:")
        for mem in result['promoted_memories']:
            print(f"  ✓ [{mem['type']}] {mem['content']}")
            print(f"    (reinforced {mem['reinforcement']}x, {mem['confidence']:.0%} confidence)")

    if result['skipped_memories'] and args.verbose:
        print("\nSkipped (not mature enough):")
        for mem in result['skipped_memories']:
            print(f"  - {mem['content']}")
            print(f"    ({mem['reason']})")


def cmd_review(args):
    """Handle review command - show short-term memories for review."""
    index = MemoryIndex.short_term()

    try:
        index.open()
    except Exception as e:
        print("Short-term memory is empty. Add memories with --short-term flag.")
        return

    memories = index.get_all_memories(limit=args.limit)

    if not memories:
        print("Short-term memory is empty.")
        return

    print(f"=== Short-term Memory Review ({len(memories)} items) ===\n")

    type_icons = {
        MemoryType.FACT: "📌", MemoryType.EVENT: "📅", MemoryType.LEARNING: "💡",
        MemoryType.DECISION: "⚖️", MemoryType.NOTE: "📝", MemoryType.PERSON: "👤",
        MemoryType.GOAL: "🎯", MemoryType.PREFERENCE: "⭐",
        MemoryType.PATTERN: "🔄", MemoryType.INSIGHT: "🧠",
    }

    for i, mem in enumerate(memories, 1):
        icon = type_icons.get(mem['type'], "📝")
        content = mem['content'][:70] + ('...' if len(mem['content']) > 70 else '')
        reinf = mem.get('reinforcement_count', 1)
        conf = mem.get('confidence', DEFAULT_CONFIDENCE)

        # Show promotion eligibility
        eligible = reinf >= PROMOTION_MIN_REINFORCEMENT or conf >= 0.9
        status = "✓ ready" if eligible else f"needs {PROMOTION_MIN_REINFORCEMENT - reinf} more"

        print(f"{i}. {icon} [{mem['type']}] {content}")
        print(f"   Reinforced: {reinf}x | Confidence: {conf:.0%} | Promotion: {status}")
        print()

    index.close()

    print(f"Run 'promote' to move mature memories to long-term.")
    print(f"Run 'promote --dry-run' to preview what would be promoted.")


def cmd_migrate(args):
    """Migrate existing Memvid memories to SQLite metadata."""
    print("=== Migrating Memvid memories to SQLite metadata ===\n")

    meta_db = MemoryMetadataDB()
    meta_db.connect()

    migrated = 0
    skipped = 0
    errors = 0

    # Process both indexes
    for index_type, index_class in [('long_term', MemoryIndex.long_term),
                                     ('short_term', MemoryIndex.short_term)]:
        index = index_class()

        if not os.path.exists(index.index_path):
            print(f"{index_type}: Index not found, skipping")
            continue

        try:
            index.open()
        except Exception as e:
            print(f"{index_type}: Error opening index: {e}")
            continue

        print(f"Processing {index_type} memories...")

        # Get all memories (increase limit to get everything)
        memories = index.get_all_memories(limit=500)
        print(f"  Found {len(memories)} memories in Memvid")

        for mem in memories:
            content = mem.get('content', '')
            if not content or len(content) < 5:
                continue

            # Check if already in SQLite
            existing = meta_db.find_by_content(content, index_type)
            if existing:
                skipped += 1
                continue

            # Extract metadata from Memvid record
            mem_type = mem.get('type', MemoryType.NOTE)
            confidence = mem.get('confidence', DEFAULT_CONFIDENCE)
            reinforcement = mem.get('reinforcement_count', 1)

            try:
                # Create SQLite record
                memory_id = meta_db.create(
                    content=content,
                    memory_type=mem_type,
                    index_type=index_type,
                    confidence=confidence
                )

                # If Memvid shows reinforcement > 1, update SQLite
                if reinforcement > 1:
                    for _ in range(reinforcement - 1):
                        meta_db.reinforce(content, index_type)

                migrated += 1

                if args.verbose:
                    print(f"    ✓ {content[:50]}...")

            except Exception as e:
                errors += 1
                if args.verbose:
                    print(f"    ✗ Error: {e}")

        index.close()
        print(f"  Migrated: {migrated}, Skipped (already exists): {skipped}, Errors: {errors}")

    meta_db.close()

    print(f"\n=== Migration Complete ===")
    print(f"Total migrated: {migrated}")
    print(f"Total skipped: {skipped}")
    print(f"Total errors: {errors}")


def main():
    parser = argparse.ArgumentParser(
        description="Lola Memory Indexer - Index and search knowledge/facts/events"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a memory (with deduplication)")
    add_parser.add_argument("content", help="The memory content")
    add_parser.add_argument("--type", "-t", default=MemoryType.NOTE,
                          choices=MemoryType.all(),
                          help="Memory type")
    add_parser.add_argument("--date", "-d", help="Date (YYYY-MM-DD or YYYY-MM)")
    add_parser.add_argument("--tags", help="Comma-separated tags")
    add_parser.add_argument("--files", "-f", help="Comma-separated related file URIs")
    add_parser.add_argument("--people", "-p", help="Comma-separated related people")
    add_parser.add_argument("--source", "-s", help="Source of the information")
    add_parser.add_argument("--confidence", "-c", type=float, help=f"Confidence 0.0-1.0 (default: {DEFAULT_CONFIDENCE})")
    add_parser.add_argument("--context", help="Additional context or reasoning")
    add_parser.add_argument("--force", action="store_true", help="Skip deduplication, always add new")
    add_parser.add_argument("--short-term", "-S", action="store_true", help="Add to short-term memory (staging)")
    add_parser.set_defaults(func=cmd_add)

    # Find command
    find_parser = subparsers.add_parser("find", help="Search for memories")
    find_parser.add_argument("query", help="Search query")
    find_parser.add_argument("--limit", type=int, default=10, help="Max results")
    find_parser.add_argument("--type", help="Filter by memory type")
    find_parser.add_argument("--year", type=int, help="Filter by year")
    find_parser.add_argument("--person", help="Filter by related person")
    find_parser.add_argument("--short-term", "-S", action="store_true", help="Search short-term memory")
    find_parser.set_defaults(func=cmd_find)

    # Import command
    import_parser = subparsers.add_parser("import", help="Import memories from markdown file")
    import_parser.add_argument("file", help="Markdown file to import")
    import_parser.add_argument("--type", "-t", help="Default memory type for imported items")
    import_parser.add_argument("--tags", help="Tags to add to all imported memories")
    import_parser.set_defaults(func=cmd_import_markdown)

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show index statistics")
    stats_parser.set_defaults(func=cmd_stats)

    # Review command (short-term)
    review_parser = subparsers.add_parser("review", help="Review short-term memories")
    review_parser.add_argument("--limit", type=int, default=20, help="Max items to show")
    review_parser.set_defaults(func=cmd_review)

    # Promote command
    promote_parser = subparsers.add_parser("promote", help="Promote mature short-term to long-term")
    promote_parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    promote_parser.add_argument("--min-reinforcement", type=int, default=PROMOTION_MIN_REINFORCEMENT,
                               help=f"Minimum reinforcements needed (default: {PROMOTION_MIN_REINFORCEMENT})")
    promote_parser.add_argument("--verbose", "-v", action="store_true", help="Show skipped memories too")
    promote_parser.set_defaults(func=cmd_promote)

    # Migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Migrate existing Memvid memories to SQLite metadata")
    migrate_parser.add_argument("--verbose", "-v", action="store_true", help="Show each migrated memory")
    migrate_parser.set_defaults(func=cmd_migrate)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
