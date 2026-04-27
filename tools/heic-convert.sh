#!/bin/bash
# heic-convert.sh - Convert HEIC/HEIF images to JPG for processing
# Usage:
#   heic-convert.sh                          # Convert all HEIC in transport folder, output to /tmp/heic-converted/
#   heic-convert.sh /path/to/file.HEIC       # Convert single file
#   heic-convert.sh /path/to/folder          # Convert all HEIC in folder
#   heic-convert.sh /path/to/source /dest    # Convert and output to custom destination

set -euo pipefail

LOLABOT_HOME="${LOLABOT_HOME:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
TRANSPORT="/srv/fileserver/transport"
DEFAULT_OUTPUT="/tmp/heic-converted"
VENV="$LOLABOT_HOME/.venv/bin/activate"
QUALITY=85
MAX_WIDTH=2000

source "$VENV"

SOURCE="${1:-$TRANSPORT}"
OUTPUT="${2:-$DEFAULT_OUTPUT}"

mkdir -p "$OUTPUT"

convert_file() {
    local src="$1"
    local dest_dir="$2"
    local basename=$(basename "$src")
    local name="${basename%.*}"
    local dest="$dest_dir/${name}.jpg"

    python3 -c "
from pillow_heif import register_heif_opener
from PIL import Image
register_heif_opener()
img = Image.open('$src')
if img.width > $MAX_WIDTH:
    ratio = $MAX_WIDTH / img.width
    img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
img.convert('RGB').save('$dest', 'JPEG', quality=$QUALITY)
print('Converted: $basename -> ${name}.jpg')
"
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
