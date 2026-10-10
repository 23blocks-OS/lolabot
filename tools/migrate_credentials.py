#!/usr/bin/env python3
"""Move plaintext mailbox passwords out of the credentials file and into the vault (aim-secret).

  python3 tools/migrate_credentials.py            show what would change (no values printed)
  python3 tools/migrate_credentials.py --apply    store each password, verify it, then rewrite the file

Each password is handed to `aim-secret set NAME --stdin` on standard input, never as an argument.
The file is rewritten only after every password has been stored and found again in the vault.
PyYAML rewrites the file, so comments in it are lost; the passwords are not.
"""

import os
import re
import subprocess
import sys
import tempfile
from typing import Any, Callable, Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import get_path


def secret_name_for(key: str) -> str:
    base = re.sub(r"[^A-Z0-9]+", "_", key.upper()).strip("_") or "ACCOUNT"
    if not base[0].isalpha():
        base = "A_" + base
    return f"LOLABOT_{base}_PASSWORD"[:64]


def plan(credentials: Dict[str, Any]) -> List[Tuple[str, str]]:
    """(account key, secret name) for every account that still has a plaintext password."""
    out = []
    for key, acct in credentials.items():
        if isinstance(acct, dict) and acct.get("password") and not acct.get("password_secret"):
            out.append((key, secret_name_for(key)))
    return out


def aim_secret_set(name: str, value: str) -> bool:
    r = subprocess.run(["aim-secret", "set", name, "--stdin"], input=value, text=True, capture_output=True)
    if r.returncode != 0:
        return False
    return subprocess.run(["aim-secret", "has", name], capture_output=True).returncode == 0


def apply(path: str, set_secret: Callable[[str, str], bool] = aim_secret_set) -> List[Tuple[str, str]]:
    import yaml
    with open(path) as f:
        doc = yaml.safe_load(f) or {}
    accounts = doc.get("email_accounts", {})
    todo = plan(accounts)
    for key, name in todo:
        if not set_secret(name, accounts[key]["password"]):
            raise RuntimeError(f"could not store the password for {key} in the vault; nothing was changed")
    for key, name in todo:
        accounts[key]["password_secret"] = name
        del accounts[key]["password"]
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".creds-")
    try:
        with os.fdopen(fd, "w") as f:
            yaml.safe_dump(doc, f, default_flow_style=False, sort_keys=False)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return todo


def main() -> int:
    path = get_path("credentials")
    if not os.path.exists(path):
        print(f"No credentials file at {path}")
        return 1
    import yaml
    with open(path) as f:
        todo = plan((yaml.safe_load(f) or {}).get("email_accounts", {}))
    if not todo:
        print("Nothing to migrate: no plaintext passwords found.")
        return 0
    for key, name in todo:
        print(f"  {key}: password -> vault secret {name}")
    if "--apply" not in sys.argv:
        print("\nDry run. Re-run with --apply to store them and rewrite the file.")
        return 0
    try:
        apply(path)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(f"\nDone. {len(todo)} password(s) moved to the vault and removed from {path}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
