#!/bin/bash
# Wrapper for file_indexer.py (all commands)
LOLABOT_HOME="${LOLABOT_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$LOLABOT_HOME"
source .venv/bin/activate
python tools/file_indexer.py "$@"
