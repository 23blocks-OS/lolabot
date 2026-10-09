#!/bin/bash
# Memory Integrity Checker
# Detects unauthorized modifications to critical agent files.
# Usage:
#   ./memory-integrity-check.sh init     # Generate initial checksums
#   ./memory-integrity-check.sh check    # Verify against stored checksums
#   ./memory-integrity-check.sh update   # Update checksums (after authorized changes)
#
# Cron example (check every hour):
#   0 * * * * /path/to/tools/memory-integrity-check.sh check >/dev/null 2>&1
# Alerts go to $ALERT_LOG, which is rotated at 5 MB (one previous file kept). Do not
# append the cron output to a log with ">>": nothing would ever rotate it.

set -euo pipefail

LOLABOT_HOME="${LOLABOT_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
CHECKSUM_FILE="$LOLABOT_HOME/indexes/integrity-checksums.sha256"
ALERT_LOG="${LOLABOT_ALERT_LOG:-/tmp/integrity-alerts.log}"

# shellcheck source=bounded-log.sh
source "$(dirname "${BASH_SOURCE[0]}")/bounded-log.sh"

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

        # Verify every recorded checksum. Read the list from stdin with an explicit "-":
        # GNU sha256sum accepts it, and so does macOS, whose sha256sum prints a usage error
        # (and verifies nothing) when -c has no file argument.
        CHECK_LINES=$(grep -v '^#' "$CHECKSUM_FILE" | grep -v '^$')
        RESULT=$(printf '%s\n' "$CHECK_LINES" | sha256sum -c - 2>&1) || true
        FAILURES=$(echo "$RESULT" | grep -c "FAILED" || true)
        MISSING=$(echo "$RESULT" | grep -c "No such file" || true)
        VERIFIED_OK=$(echo "$RESULT" | grep -c ': OK$' || true)
        EXPECTED=$(printf '%s\n' "$CHECK_LINES" | grep -c . || true)

        # If the tool did not account for every file (usage error, missing binary, garbled
        # output), say so. Reporting "all OK" for a check that never ran is worse than no check.
        if [ $((FAILURES + MISSING + VERIFIED_OK)) -lt "$EXPECTED" ]; then
            TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
            echo "[$TIMESTAMP] INTEGRITY CHECK COULD NOT RUN: verified $((FAILURES + MISSING + VERIFIED_OK)) of $EXPECTED files" | bounded_log_append "$ALERT_LOG"
            echo "$RESULT" | head -3 | bounded_log_append "$ALERT_LOG"
            echo "ERROR: the checksum tool did not verify all files (see $ALERT_LOG). Not reporting OK."
            exit 3
        fi

        if [ "$FAILURES" -gt 0 ] || [ "$MISSING" -gt 0 ]; then
            TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
            echo "[$TIMESTAMP] INTEGRITY ALERT: $FAILURES file(s) modified, $MISSING file(s) missing" | bounded_log_append "$ALERT_LOG"
            echo "$RESULT" | grep -E "FAILED|No such file" | bounded_log_append "$ALERT_LOG"
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
