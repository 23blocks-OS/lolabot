#!/bin/bash
# Quick email send
#
# Usage:
#   email-send.sh --to "user@example.com" --subject "Hello" --body "Message"
#   email-send.sh --from lola@3metas.com --to "user@example.com" --subject "Hello" --body "Message"

LOLABOT_HOME="${LOLABOT_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default to Lola's account for sending
ACCOUNT="lola@3metas.com"

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

"$SCRIPT_DIR/email.sh" send "$ACCOUNT" "${ARGS[@]}"
