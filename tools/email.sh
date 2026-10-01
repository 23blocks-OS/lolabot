#!/bin/bash
# Lola Email Client - Main wrapper
#
# Usage:
#   email.sh check alex@example.com
#   email.sh read alex@example.com 12345
#   email.sh send assistant@example.com --to "user@example.com" --subject "Hello" --body "Message"
#   email.sh reply alex@example.com 12345 --body "My reply"
#   email.sh search "invoice" --account alex@example.com
#   email.sh sync alex@example.com --days 7
#   email.sh accounts

LOLABOT_HOME="${LOLABOT_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$LOLABOT_HOME/.venv"

# Activate venv if exists
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
fi

python3 "$SCRIPT_DIR/email_client.py" "$@"
