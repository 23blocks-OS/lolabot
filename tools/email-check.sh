#!/bin/bash
# Quick inbox check
#
# Usage:
#   email-check.sh                    # Check Juan's inbox
#   email-check.sh jpelaez@3metas.com # Check specific account
#   email-check.sh lola@3metas.com    # Check Lola's inbox

LOLABOT_HOME="${LOLABOT_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ACCOUNT="${1:-jpelaez@3metas.com}"
shift 2>/dev/null

"$SCRIPT_DIR/email.sh" check "$ACCOUNT" "$@"
