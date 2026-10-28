#!/bin/bash
# Wrapper for memory_indexer.py add command
LOLABOT_HOME="${LOLABOT_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$LOLABOT_HOME" || exit 1
source .venv/bin/activate
python tools/memory_indexer.py add "$@"
