#!/bin/bash
# bounded-log.sh - small helpers so lolabot scripts never grow a file forever.
# Source it; do not run it.
#   source "$(dirname "${BASH_SOURCE[0]}")/bounded-log.sh"
#   bounded_log_append /tmp/some.log   # stdin -> file and stdout, rotates at 5 MB
#   prune_old_files DIR DAYS 'glob'    # delete regular files older than DAYS, directly inside DIR

LOLABOT_LOG_MAX_BYTES="${LOLABOT_LOG_MAX_BYTES:-5242880}"   # 5 MB

# Move FILE to FILE.1 (replacing any older FILE.1) when it is over the cap.
rotate_log_if_large() {
    local file="$1" size
    [ -f "$file" ] && [ ! -L "$file" ] || return 0
    size=$(wc -c < "$file" | tr -d ' ')
    if [ "${size:-0}" -ge "$LOLABOT_LOG_MAX_BYTES" ]; then
        mv -f "$file" "$file.1"
    fi
}

# Like `tee -a FILE`, but rotates first. Keeps one previous file (FILE.1).
bounded_log_append() {
    rotate_log_if_large "$1"
    tee -a "$1"
}

# Delete regular files (not symlinks, not subdirectories) matching PATTERN that sit
# directly inside DIR and are older than DAYS. Refuses anything but a plain directory
# and a positive integer.
prune_old_files() {
    local dir="$1" days="$2" pattern="${3:-*}"
    case "$days" in ''|*[!0-9]*|0) return 0 ;; esac
    [ -d "$dir" ] && [ ! -L "$dir" ] || return 0
    find "$dir" -maxdepth 1 -type f -name "$pattern" -mtime +"$days" -exec rm -f {} +
}
