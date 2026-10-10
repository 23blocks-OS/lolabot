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

# Accounts may keep their password in the vault (password_secret: NAME in the credentials file).
# Then the mail client runs under `aim-secret exec`, which puts the value in its environment and
# scrubs it from the output, so the agent never sees it.
USE_ARGS=()
if [ "${1:-}" != "secrets-needed" ]; then
    if ! NEEDED="$(python3 "$SCRIPT_DIR/email_client.py" secrets-needed)"; then
        exit 1   # the reason was printed on stderr
    fi
    while IFS= read -r NAME; do
        [ -z "$NAME" ] && continue
        if [[ ! "$NAME" =~ ^[A-Z][A-Z0-9_]{0,63}$ ]]; then
            echo "Error: refusing unexpected secret name from the mail client" >&2
            exit 1
        fi
        USE_ARGS+=(--use "$NAME")
    done <<< "$NEEDED"
fi

if [ ${#USE_ARGS[@]} -gt 0 ]; then
    if ! command -v aim-secret >/dev/null 2>&1; then
        echo "Error: this account keeps its password in the vault, but aim-secret is not installed." >&2
        echo "       Install AI Maestro's aim-secret, then run: aim-secret set <NAME>" >&2
        exit 3
    fi
    exec aim-secret exec "${USE_ARGS[@]}" -- python3 "$SCRIPT_DIR/email_client.py" "$@"
fi

exec python3 "$SCRIPT_DIR/email_client.py" "$@"
