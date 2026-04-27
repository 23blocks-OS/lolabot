#!/usr/bin/env python3
"""
Lola File Indexer

Indexes files from multiple sources into Memvid V2 for fast retrieval.
Supports local files, remote hosts, OneDrive, cloud apps, and URLs.

Usage:
    python file_indexer.py scan /path/to/directory [--pattern "*.jpg"]
    python file_indexer.py scan-onedrive /Photos/2024
    python file_indexer.py add-url "https://example.com/doc.pdf" --tags "work,reference"
    python file_indexer.py add-remote macbook:/Users/juan/Documents/file.pdf
    python file_indexer.py find "query string"
    python file_indexer.py stats
"""

import os
import sys
import argparse
import hashlib
import mimetypes
import re
from datetime import datetime
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
INDEX_PATH = get_path('files_index')

# Location types
class LocationType:
    LOCAL = "local"           # Local filesystem
    REMOTE = "remote"         # Another computer (via Tailscale, SSH, etc.)
    ONEDRIVE = "onedrive"     # Microsoft OneDrive
    GDRIVE = "gdrive"         # Google Drive
    DROPBOX = "dropbox"       # Dropbox
    ICLOUD = "icloud"         # Apple iCloud
    PHOTOS_APP = "photos"     # Apple/Google Photos library
    S3 = "s3"                 # AWS S3
    URL = "url"               # Direct URL
    OTHER = "other"           # Other cloud service

# File type categories
FILE_CATEGORIES = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".raw", ".cr2", ".nef"],
    "document": [".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt"],
    "spreadsheet": [".xls", ".xlsx", ".csv", ".ods"],
    "presentation": [".ppt", ".pptx", ".odp"],
    "video": [".mp4", ".mov", ".avi", ".mkv", ".webm"],
    "audio": [".mp3", ".wav", ".flac", ".m4a", ".ogg"],
    "code": [".py", ".js", ".ts", ".go", ".rs", ".java", ".c", ".cpp", ".h"],
    "archive": [".zip", ".tar", ".gz", ".rar", ".7z"],
    "data": [".json", ".yaml", ".yml", ".xml", ".sql"],
}

def get_file_category(ext: str) -> str:
    """Get category for a file extension."""
    ext = ext.lower()
    for category, extensions in FILE_CATEGORIES.items():
        if ext in extensions:
            return category
    return "other"

def get_file_hash(path: str, chunk_size: int = 8192) -> str:
    """Get MD5 hash of first 1MB of file for quick dedup check."""
    hasher = hashlib.md5()
    try:
        with open(path, 'rb') as f:
            data = f.read(1024 * 1024)
            hasher.update(data)
    except Exception:
        return ""
    return hasher.hexdigest()[:16]

def extract_exif(path: str) -> Dict[str, Any]:
    """Extract EXIF data from images (if available)."""
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS

        img = Image.open(path)
        exif_data = img._getexif()
        if not exif_data:
            return {}

        result = {}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag in ["DateTimeOriginal", "DateTime", "Make", "Model"]:
                result[tag] = str(value)
        return result
    except Exception:
        return {}

def parse_location(location_str: str) -> Dict[str, str]:
    """Parse a location string into components.

    Examples:
        /home/jpelaez/file.pdf -> local
        macbook:/Users/juan/file.pdf -> remote (host: macbook)
        onedrive://Documents/file.pdf -> onedrive
        https://example.com/file.pdf -> url
        s3://bucket/key -> s3
        photos://Albums/Trip -> photos app
    """
    # Check for URL schemes
    if location_str.startswith("http://") or location_str.startswith("https://"):
        return {
            "type": LocationType.URL,
            "uri": location_str,
            "host": None,
            "path": location_str,
        }

    if location_str.startswith("onedrive://"):
        return {
            "type": LocationType.ONEDRIVE,
            "uri": location_str,
            "host": None,
            "path": location_str.replace("onedrive://", ""),
        }

    if location_str.startswith("gdrive://"):
        return {
            "type": LocationType.GDRIVE,
            "uri": location_str,
            "host": None,
            "path": location_str.replace("gdrive://", ""),
        }

    if location_str.startswith("s3://"):
        return {
            "type": LocationType.S3,
            "uri": location_str,
            "host": None,
            "path": location_str.replace("s3://", ""),
        }

    if location_str.startswith("photos://"):
        return {
            "type": LocationType.PHOTOS_APP,
            "uri": location_str,
            "host": None,
            "path": location_str.replace("photos://", ""),
        }

    if location_str.startswith("icloud://"):
        return {
            "type": LocationType.ICLOUD,
            "uri": location_str,
            "host": None,
            "path": location_str.replace("icloud://", ""),
        }

    # Check for remote host format: hostname:/path
    if ":" in location_str and not location_str.startswith("/"):
        parts = location_str.split(":", 1)
        if len(parts) == 2 and parts[1].startswith("/"):
            return {
                "type": LocationType.REMOTE,
                "uri": location_str,
                "host": parts[0],
                "path": parts[1],
            }

    # Default: local file
    return {
        "type": LocationType.LOCAL,
        "uri": location_str,
        "host": None,
        "path": location_str,
    }

def scan_local_directory(
    directory: str,
    pattern: str = "*",
    recursive: bool = True,
    exclude_hidden: bool = True
) -> List[Dict[str, Any]]:
    """Scan local directory and collect file metadata."""
    files = []
    directory = os.path.abspath(os.path.expanduser(directory))

    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a directory")
        return []

    print(f"Scanning {directory}...")

    path = Path(directory)
    glob_pattern = f"**/{pattern}" if recursive else pattern

    for file_path in path.glob(glob_pattern):
        if not file_path.is_file():
            continue

        if exclude_hidden and any(part.startswith('.') for part in file_path.parts):
            continue

        try:
            stat = file_path.stat()
            ext = file_path.suffix.lower()
            category = get_file_category(ext)
            mime_type, _ = mimetypes.guess_type(str(file_path))

            file_info = {
                "location_type": LocationType.LOCAL,
                "uri": str(file_path),
                "host": None,
                "path": str(file_path),
                "name": file_path.name,
                "ext": ext,
                "category": category,
                "mime_type": mime_type or "application/octet-stream",
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "hash": get_file_hash(str(file_path)),
                "accessible": True,
            }

            if category == "image":
                exif = extract_exif(str(file_path))
                if exif:
                    file_info["exif"] = exif

            files.append(file_info)

        except Exception as e:
            print(f"  Warning: Could not process {file_path}: {e}")

    print(f"Found {len(files)} files")
    return files


class FileIndex:
    """Memvid-based file index supporting multiple location types."""

    def __init__(self, index_path: str = INDEX_PATH):
        self.index_path = index_path
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        self.mem = None
        self._count = 0

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

    def close(self):
        """Close the index."""
        if self.mem:
            self.mem.close()
            self.mem = None

    def add_file(self, file_info: Dict[str, Any], tags: List[str] = None, description: str = None):
        """Add a file to the index."""
        if not self.mem:
            self.open()

        loc_type = file_info.get('location_type', LocationType.LOCAL)
        uri = file_info.get('uri', file_info.get('path', ''))
        host = file_info.get('host')

        # Build searchable text
        text_parts = [
            f"File: {file_info.get('name', 'unknown')}",
            f"Location: {loc_type}",
            f"URI: {uri}",
        ]

        if host:
            text_parts.append(f"Host: {host}")

        if file_info.get('category'):
            text_parts.append(f"Type: {file_info['category']} ({file_info.get('mime_type', 'unknown')})")

        if file_info.get('size'):
            text_parts.append(f"Size: {file_info['size']} bytes")

        if file_info.get('modified'):
            text_parts.append(f"Modified: {file_info['modified']}")

        if description:
            text_parts.append(f"Description: {description}")

        if file_info.get('exif'):
            exif = file_info['exif']
            if exif.get('DateTimeOriginal'):
                text_parts.append(f"Photo taken: {exif['DateTimeOriginal']}")
            if exif.get('Make') and exif.get('Model'):
                text_parts.append(f"Camera: {exif['Make']} {exif['Model']}")

        text = "\n".join(text_parts)

        # Auto-generate tags
        auto_tags = [loc_type]
        if host:
            auto_tags.append(host)

        # Add path-based tags for local/remote files
        if loc_type in [LocationType.LOCAL, LocationType.REMOTE]:
            path_parts = Path(file_info.get('path', '')).parts
            for part in path_parts[-4:-1]:
                if not part.startswith('.') and len(part) > 2:
                    auto_tags.append(part.lower())

        if file_info.get('category'):
            auto_tags.append(file_info['category'])

        all_tags = list(set((tags or []) + auto_tags))

        # Add to index
        self.mem.put(
            title=file_info.get('name', 'unknown'),
            label=file_info.get('category', 'file'),
            text=text,
            tags=all_tags,
            metadata={
                "location_type": loc_type,
                "uri": uri,
                "host": host,
            },
        )
        self._count += 1

    def add_files(self, files: List[Dict[str, Any]], batch_tags: List[str] = None):
        """Add multiple files to the index."""
        if not self.mem:
            self.open(create=True)

        for i, file_info in enumerate(files):
            self.add_file(file_info, batch_tags)
            if (i + 1) % 100 == 0:
                print(f"  Indexed {i + 1}/{len(files)} files...")

        self.close()
        self.open()

        print(f"Indexed {len(files)} files")

    def add_manual_entry(
        self,
        location: str,
        name: str = None,
        description: str = None,
        tags: List[str] = None,
        category: str = None,
    ):
        """Add a manual file entry (for cloud files, URLs, etc.)."""
        if not self.mem:
            # Open existing or create new if doesn't exist
            self.open(create=not os.path.exists(self.index_path))

        loc = parse_location(location)

        # Infer name from path if not provided
        if not name:
            name = Path(loc['path']).name or location

        # Infer category from extension
        ext = Path(name).suffix.lower()
        if not category:
            category = get_file_category(ext)

        file_info = {
            "location_type": loc['type'],
            "uri": loc['uri'],
            "host": loc['host'],
            "path": loc['path'],
            "name": name,
            "ext": ext,
            "category": category,
            "accessible": True,
        }

        self.add_file(file_info, tags, description)

        self.close()
        self.open()

        print(f"Added: {name} ({loc['type']})")

    def find(self, query: str, limit: int = 10, location_type: str = None) -> List[Dict[str, Any]]:
        """Search for files."""
        if not self.mem:
            self.open()

        # Add location type to query if specified
        search_query = query
        if location_type:
            search_query = f"{query} {location_type}"

        result = self.mem.find(search_query, k=limit * 2)  # Get extra to handle dedup

        hits = []
        seen_uris = set()

        for hit in result.get('hits', []):
            text = hit.get('text', '') or hit.get('snippet', '')

            # Extract URI
            uri = ''
            uri_match = re.search(r'URI:\s*(\S+)', text)
            if uri_match:
                uri = uri_match.group(1)

            # Extract location type
            loc_type = LocationType.LOCAL
            loc_match = re.search(r'Location:\s*(\S+)', text)
            if loc_match:
                loc_type = loc_match.group(1)

            # Extract host
            host = None
            host_match = re.search(r'Host:\s*(\S+)', text)
            if host_match:
                host = host_match.group(1)

            # Skip duplicates
            if uri and uri in seen_uris:
                continue
            if uri:
                seen_uris.add(uri)

            # Filter by location type if specified
            if location_type and loc_type != location_type:
                continue

            hits.append({
                "name": hit.get('title', ''),
                "location_type": loc_type,
                "uri": uri,
                "host": host,
                "snippet": hit.get('snippet', '')[:200],
                "score": hit.get('score', 0),
                "tags": hit.get('tags', [])[:5],
            })

            if len(hits) >= limit:
                break

        return hits

    def stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        if not os.path.exists(self.index_path):
            return {"exists": False}

        file_size = os.path.getsize(self.index_path)

        stats = {
            "exists": True,
            "path": self.index_path,
            "size_kb": file_size / 1024,
            "size_mb": file_size / (1024 * 1024),
        }

        return stats


# CLI Commands

def cmd_scan(args):
    """Handle scan command."""
    index = FileIndex()

    files = scan_local_directory(
        args.directory,
        pattern=args.pattern,
        recursive=not args.no_recursive,
        exclude_hidden=not args.include_hidden,
    )

    if not files:
        print("No files found")
        return

    print(f"\nIndexing {len(files)} files...")
    index.add_files(files, batch_tags=args.tags.split(',') if args.tags else None)

    stats = index.stats()
    print(f"\nIndex size: {stats['size_kb']:.2f} KB")
    index.close()


def cmd_add(args):
    """Handle add command for manual entries."""
    index = FileIndex()

    tags = args.tags.split(',') if args.tags else None

    index.add_manual_entry(
        location=args.location,
        name=args.name,
        description=args.description,
        tags=tags,
        category=args.category,
    )

    index.close()


def cmd_find(args):
    """Handle find command."""
    index = FileIndex()

    try:
        index.open()
    except Exception as e:
        print(f"Error opening index: {e}")
        print("Run 'scan' first to create the index")
        return

    results = index.find(args.query, limit=args.limit, location_type=args.type)

    if not results:
        print("No files found")
        return

    print(f"\nFound {len(results)} files:\n")
    for i, hit in enumerate(results, 1):
        loc_icon = {
            LocationType.LOCAL: "📁",
            LocationType.REMOTE: "🖥️",
            LocationType.ONEDRIVE: "☁️",
            LocationType.GDRIVE: "📂",
            LocationType.URL: "🌐",
            LocationType.PHOTOS_APP: "📷",
            LocationType.S3: "🪣",
        }.get(hit['location_type'], "📄")

        print(f"{i}. {loc_icon} {hit['name']}")
        print(f"   Location: {hit['location_type']}" + (f" ({hit['host']})" if hit['host'] else ""))
        print(f"   URI: {hit['uri']}")
        print(f"   Tags: {', '.join(hit['tags'])}")
        print()

    index.close()


def cmd_stats(args):
    """Handle stats command."""
    index = FileIndex()
    stats = index.stats()

    if not stats["exists"]:
        print("Index does not exist. Run 'scan' first.")
        return

    print(f"Index path: {stats['path']}")
    print(f"Size: {stats['size_kb']:.2f} KB ({stats['size_mb']:.2f} MB)")


def main():
    parser = argparse.ArgumentParser(
        description="Lola File Indexer - Index and search files from any location"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Scan command (local directories)
    scan_parser = subparsers.add_parser("scan", help="Scan local directory and index files")
    scan_parser.add_argument("directory", help="Directory to scan")
    scan_parser.add_argument("--pattern", default="*", help="Glob pattern (default: *)")
    scan_parser.add_argument("--tags", help="Comma-separated tags to add to all files")
    scan_parser.add_argument("--no-recursive", action="store_true", help="Don't scan subdirectories")
    scan_parser.add_argument("--include-hidden", action="store_true", help="Include hidden files")
    scan_parser.set_defaults(func=cmd_scan)

    # Add command (manual entries)
    add_parser = subparsers.add_parser("add", help="Add a file entry manually")
    add_parser.add_argument("location", help="File location (path, URL, or URI scheme)")
    add_parser.add_argument("--name", help="Display name (inferred from path if not provided)")
    add_parser.add_argument("--description", "-d", help="Description of the file")
    add_parser.add_argument("--tags", "-t", help="Comma-separated tags")
    add_parser.add_argument("--category", "-c", help="File category (image, document, etc.)")
    add_parser.set_defaults(func=cmd_add)

    # Find command
    find_parser = subparsers.add_parser("find", help="Search for files")
    find_parser.add_argument("query", help="Search query")
    find_parser.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")
    find_parser.add_argument("--type", help="Filter by location type (local, remote, onedrive, url, etc.)")
    find_parser.set_defaults(func=cmd_find)

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show index statistics")
    stats_parser.set_defaults(func=cmd_stats)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
