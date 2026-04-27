#!/bin/bash
# Memory Integrity Checker
# Detects unauthorized modifications to critical agent files.
# Usage:
#   ./memory-integrity-check.sh init     # Generate initial checksums
#   ./memory-integrity-check.sh check    # Verify against stored checksums
#   ./memory-integrity-check.sh update   # Update checksums (after authorized changes)
#
# Cron example (check every hour):
#   0 * * * * /path/to/tools/memory-integrity-check.sh check >> /tmp/integrity-check.log 2>&1

set -euo pipefail

LOLABOT_HOME="${LOLABOT_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
CHECKSUM_FILE="$LOLABOT_HOME/indexes/integrity-checksums.sha256"
ALERT_LOG="/tmp/integrity-alerts.log"

# Files to monitor
WATCHED_FILES=(
    "$LOLABOT_HOME/CLAUDE.md"
)

# Dynamically add brain/*.md and memory auto-memory files
for f in "$LOLABOT_HOME"/brain/*.md; do
    [ -f "$f" ] && WATCHED_FILES+=("$f")
done
for f in "$HOME"/.claude/projects/*/memory/*.md; do
    [ -f "$f" ] && WATCHED_FILES+=("$f")
done

# Skills SKILL.md files
for f in "$HOME"/.claude/skills/*/SKILL.md; do
    [ -f "$f" ] && WATCHED_FILES+=("$f")
done

generate_checksums() {
    echo "# Memory Integrity Checksums"
    echo "# Generated: $(date -Iseconds)"
    echo "# Files: ${#WATCHED_FILES[@]}"
    echo ""
    for f in "${WATCHED_FILES[@]}"; do
        if [ -f "$f" ]; then
            sha256sum "$f"
        fi
    done
}

cmd="${1:-check}"

case "$cmd" in
    init)
        generate_checksums > "$CHECKSUM_FILE"
        echo "Checksums initialized for ${#WATCHED_FILES[@]} files."
        echo "Stored at: $CHECKSUM_FILE"
        ;;

    update)
        generate_checksums > "$CHECKSUM_FILE"
        echo "Checksums updated for ${#WATCHED_FILES[@]} files."
        ;;

    check)
        if [ ! -f "$CHECKSUM_FILE" ]; then
            echo "ERROR: No checksum file found. Run '$0 init' first."
            exit 1
        fi

        # Run sha256sum check, filtering out comment lines
        RESULT=$(grep -v '^#' "$CHECKSUM_FILE" | grep -v '^$' | sha256sum -c 2>&1) || true
        FAILURES=$(echo "$RESULT" | grep -c "FAILED" || true)
        MISSING=$(echo "$RESULT" | grep -c "No such file" || true)

        if [ "$FAILURES" -gt 0 ] || [ "$MISSING" -gt 0 ]; then
            TIMESTAMP=$(date -Iseconds)
            echo "[$TIMESTAMP] INTEGRITY ALERT: $FAILURES file(s) modified, $MISSING file(s) missing" | tee -a "$ALERT_LOG"
            echo "$RESULT" | grep -E "FAILED|No such file" | tee -a "$ALERT_LOG"
            echo ""
            echo "If these changes were authorized, run: $0 update"
            exit 2
        else
            echo "All ${#WATCHED_FILES[@]} files OK — no unauthorized modifications detected."
        fi
        ;;

    list)
        echo "Monitored files (${#WATCHED_FILES[@]}):"
        for f in "${WATCHED_FILES[@]}"; do
            if [ -f "$f" ]; then
                echo "  [OK] $f"
            else
                echo "  [MISSING] $f"
            fi
        done
        ;;

    *)
        echo "Usage: $0 {init|check|update|list}"
        exit 1
        ;;
esac
