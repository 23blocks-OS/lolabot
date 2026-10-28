#!/bin/bash
# heic-convert.sh - Convert HEIC/HEIF images to JPG for processing
# Usage:
#   heic-convert.sh                          # Convert all HEIC in transport folder, output to /tmp/heic-converted/ (JPGs older than 7 days are removed there on each run)
#   heic-convert.sh /path/to/file.HEIC       # Convert single file
#   heic-convert.sh /path/to/folder          # Convert all HEIC in folder
#   heic-convert.sh /path/to/source /dest    # Convert and output to custom destination

set -euo pipefail

LOLABOT_HOME="${LOLABOT_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
TRANSPORT="/srv/fileserver/transport"
DEFAULT_OUTPUT="${LOLABOT_HEIC_OUTPUT:-/tmp/heic-converted}"
HEIC_TTL_DAYS=7
VENV="$LOLABOT_HOME/.venv/bin/activate"
QUALITY=85
MAX_WIDTH=2000

source "$LOLABOT_HOME/tools/bounded-log.sh"
source "$VENV"

SOURCE="${1:-$TRANSPORT}"
OUTPUT="${2:-$DEFAULT_OUTPUT}"

if [ -L "$OUTPUT" ]; then
    echo "Error: $OUTPUT is a symlink; refusing to write through it"
    exit 1
fi
# Private directory: the default lives in a shared /tmp
(umask 077; mkdir -p "$OUTPUT")

# Converted JPGs are scratch files. Clean up old ones, but only in the default output
# directory this script owns, never in a destination the caller chose.
if [ "$OUTPUT" = "$DEFAULT_OUTPUT" ]; then
    prune_old_files "$OUTPUT" "$HEIC_TTL_DAYS" '*.jpg'
fi

convert_file() {
    local src="$1"
    local dest_dir="$2"
    local base name dest
    base=$(basename "$src")
    name="${base%.*}"
    dest="$dest_dir/${name}.jpg"

    # Paths go in as arguments, never pasted into the Python source: file names
    # come from outside and may contain quotes.
    python3 - "$src" "$dest" "$MAX_WIDTH" "$QUALITY" "$base" "${name}.jpg" <<'PY'
import sys
from pillow_heif import register_heif_opener
from PIL import Image
src, dest, max_width, quality, base, out_name = sys.argv[1:7]
max_width, quality = int(max_width), int(quality)
register_heif_opener()
img = Image.open(src)
if img.width > max_width:
    ratio = max_width / img.width
    img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
img.convert('RGB').save(dest, 'JPEG', quality=quality)
print(f'Converted: {base} -> {out_name}')
PY
}

if [ -f "$SOURCE" ]; then
    convert_file "$SOURCE" "$OUTPUT"
elif [ -d "$SOURCE" ]; then
    count=0
    for f in "$SOURCE"/*.HEIC "$SOURCE"/*.heic "$SOURCE"/*.HEIF "$SOURCE"/*.heif; do
        [ -f "$f" ] || continue
        convert_file "$f" "$OUTPUT"
        count=$((count + 1))
    done
    if [ "$count" -eq 0 ]; then
        echo "No HEIC/HEIF files found in $SOURCE"
        exit 1
    fi
    echo "Done: $count files converted to $OUTPUT"
else
    echo "Error: $SOURCE not found"
    exit 1
fi
