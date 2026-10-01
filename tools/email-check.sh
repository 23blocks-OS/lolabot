#!/bin/bash
# Quick inbox check
#
# Usage:
#   email-check.sh                    # Check the default inbox (LOLA_EMAIL_ACCOUNT)
#   email-check.sh alex@example.com # Check specific account
#   email-check.sh assistant@example.com    # Check the assistant's inbox

LOLABOT_HOME="${LOLABOT_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ACCOUNT="${1:-${LOLA_EMAIL_ACCOUNT:-}}"
if [ -z "$ACCOUNT" ]; then
  echo "Usage: email-check.sh <account> (or set LOLA_EMAIL_ACCOUNT)" >&2
  exit 1
fi
shift 2>/dev/null

"$SCRIPT_DIR/email.sh" check "$ACCOUNT" "$@"
