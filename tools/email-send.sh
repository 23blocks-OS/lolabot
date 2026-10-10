#!/bin/bash
# Quick email send
#
# Usage:
#   email-send.sh --to "user@example.com" --subject "Hello" --body "Message"
#   email-send.sh --from assistant@example.com --to "user@example.com" --subject "Hello" --body "Message"

LOLABOT_HOME="${LOLABOT_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default sender: the first account in lolabot.yaml (email.accounts), unless --from is given.
ACCOUNT="$(LOLABOT_HOME="$LOLABOT_HOME" python3 -c "
import sys; sys.path.insert(0, '$SCRIPT_DIR')
from config import load_config
accts = load_config().get('email', {}).get('accounts', [])
print(accts[0]['address'] if accts and 'address' in accts[0] else '')
" 2>/dev/null)"

# Parse --from if provided
ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --from)
            ACCOUNT="$2"
            shift 2
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

if [ -z "$ACCOUNT" ]; then
    echo "Error: no sender. Pass --from, or list an account under email.accounts in lolabot.yaml." >&2
    exit 1
fi

"$SCRIPT_DIR/email.sh" send "$ACCOUNT" "${ARGS[@]}"
