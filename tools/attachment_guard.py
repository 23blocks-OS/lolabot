#!/usr/bin/env python3
"""Decide which local files an email may carry out.

A prompt-injected agent could otherwise mail ~/.ssh, the credentials file or anything else the
user can read. Attachments must live in an allowed directory (default: outbox/ inside
LOLABOT_HOME) and must not look like secrets. Every problem is reported and the whole send is
refused; nothing is skipped silently.

The allowlist lives in lolabot.yaml, which the agent can edit. This stops accidents and simple
injection, not an agent that is already fully compromised.
"""

import fnmatch
import os
from pathlib import Path
from typing import Iterable, List, Optional

DEFAULT_DIRS = ["outbox"]
DEFAULT_MAX_MB = 25

# Directories whose contents are never attached, wherever they are.
DENY_DIR_NAMES = {".ssh", ".aws", ".gnupg", ".kube", ".docker", ".azure", ".gcloud", ".terraform", ".venv", ".git"}

# File names that look like secrets, even inside an allowed directory.
DENY_NAME_PATTERNS = [
    "id_rsa*", "id_ed25519*", "id_ecdsa*", "id_dsa*", "*.pem", "*.key", "*.p12", "*.pfx", "*.kdbx",
    ".env", ".env.*", "*.env", ".netrc", ".npmrc", ".pypirc", "known_hosts", "authorized_keys",
    "*credential*", "*secret*", "*password*", "*token*",
]


class AttachmentRefused(Exception):
    def __init__(self, problems: List[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def allowed_roots(home: str, dirs: Optional[Iterable[str]] = None) -> List[Path]:
    roots = []
    for d in (dirs if dirs is not None else DEFAULT_DIRS):
        p = Path(d) if os.path.isabs(d) else Path(home) / d
        roots.append(p.resolve())
    return roots


def check_attachments(paths: Iterable[str], home: str, dirs: Optional[Iterable[str]] = None,
                      max_mb: float = DEFAULT_MAX_MB, credentials_file: Optional[str] = None,
                      hint: str = "ask the owner to add the folder to the allowed attachment folders") -> List[Path]:
    """Return resolved paths that may be attached, or raise AttachmentRefused with every problem."""
    roots = allowed_roots(home, dirs)
    cred = Path(credentials_file).resolve() if credentials_file else None
    ok: List[Path] = []
    problems: List[str] = []
    for raw in paths:
        shown = raw
        try:
            p = Path(raw).expanduser().resolve(strict=True)  # follows symlinks, so a link out is caught
        except (FileNotFoundError, OSError):
            problems.append(f"{shown}: file not found")
            continue
        if not p.is_file():
            problems.append(f"{shown}: not a regular file")
            continue
        if not any(_inside(p, r) for r in roots):
            where = ", ".join(str(r) for r in roots) or "(none configured)"
            problems.append(f"{shown}: outside the allowed attachment folders ({where}). "
                            f"Copy the file there first, or {hint}")
            continue
        if cred is not None and p == cred:
            problems.append(f"{shown}: this is the credentials file")
            continue
        if any(part in DENY_DIR_NAMES for part in p.parts):
            problems.append(f"{shown}: lives in a folder that holds secrets or tooling")
            continue
        name = p.name.lower()
        if any(fnmatch.fnmatch(name, pat) for pat in DENY_NAME_PATTERNS):
            problems.append(f"{shown}: the file name looks like a secret. Rename it if this is a mistake")
            continue
        if p.stat().st_size > max_mb * 1024 * 1024:
            problems.append(f"{shown}: larger than {max_mb:g} MB")
            continue
        ok.append(p)
    if problems:
        raise AttachmentRefused(problems)
    return ok
