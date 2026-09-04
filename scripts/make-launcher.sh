#!/usr/bin/env bash
# make-launcher.sh — create a one-word command (and optionally a clickable icon)
# that opens Claude Code in your assistant's home directory.
#
# Usage: ./make-launcher.sh ~/assistant [command-name]
#
# Creates: ~/.local/bin/<command-name>
# Offers:  macOS  ~/Applications/<Name>.app
#          Linux  ~/.local/share/applications/<command-name>.desktop

set -euo pipefail

BOLD=$'\033[1m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; RED=$'\033[0;31m'; NC=$'\033[0m'
info()  { echo "  $*"; }
ok()    { echo "${GREEN}  ✓${NC} $*"; }
warn()  { echo "${YELLOW}  !${NC} $*"; }
die()   { echo "${RED}  ✗${NC} $*" >&2; exit 1; }

# --- arguments ---
TARGET="${1:-}"
[ -n "$TARGET" ] || die "Usage: $0 /path/to/assistant-home [command-name]"

TARGET="$(cd "$TARGET" 2>/dev/null && pwd)" || die "Not a directory: ${1}"
[ -f "$TARGET/CLAUDE.md" ] || warn "No CLAUDE.md in $TARGET — is this really your assistant's home?"

CMD="${2:-assistant}"
case "$CMD" in
  *[!a-zA-Z0-9_-]*) die "Command name must be letters, numbers, dashes or underscores: $CMD" ;;
esac

command -v claude >/dev/null 2>&1 || warn "'claude' is not on your PATH — the launcher will not work until Claude Code is installed"

BIN_DIR="$HOME/.local/bin"
LAUNCHER="$BIN_DIR/$CMD"
mkdir -p "$BIN_DIR"

if [ -e "$LAUNCHER" ]; then
  read -r -p "  $LAUNCHER already exists. Overwrite? [y/N] " reply
  [[ "$reply" =~ ^[Yy]$ ]] || die "Stopped. Nothing changed."
fi

# --- the launcher ---
cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
# Opens Claude Code in your assistant's home. Created by lolabot make-launcher.sh
cd "$TARGET" || { echo "Assistant home is missing: $TARGET" >&2; exit 1; }
export LOLABOT_HOME="$TARGET"
exec claude "\$@"
EOF
chmod +x "$LAUNCHER"
ok "Created command: $CMD  ->  $TARGET"

# --- PATH check, by effect ---
if ! command -v "$CMD" >/dev/null 2>&1; then
  warn "$BIN_DIR is not on your PATH. Add this to your shell profile:"
  echo
  echo "      export PATH=\"\$HOME/.local/bin:\$PATH\""
  echo
else
  ok "'$CMD' is on your PATH — type it in any terminal"
fi

# --- optional clickable icon ---
NAME="$(echo "${CMD:0:1}" | tr '[:lower:]' '[:upper:]')${CMD:1}"

case "$(uname -s)" in
  Darwin)
    read -r -p "  Also create a Dock icon (~/Applications/$NAME.app)? [y/N] " reply
    if [[ "$reply" =~ ^[Yy]$ ]]; then
      APP="$HOME/Applications/$NAME.app"
      mkdir -p "$APP/Contents/MacOS"
      cat > "$APP/Contents/MacOS/$NAME" <<EOF
#!/usr/bin/env bash
open -a Terminal "$LAUNCHER"
EOF
      chmod +x "$APP/Contents/MacOS/$NAME"
      cat > "$APP/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>$NAME</string>
  <key>CFBundleExecutable</key><string>$NAME</string>
  <key>CFBundleIdentifier</key><string>ai.lolabot.$CMD</string>
  <key>CFBundlePackageType</key><string>APPL</string>
</dict></plist>
EOF
      ok "Created $APP — drag it to your Dock"
    fi
    ;;
  Linux)
    read -r -p "  Also add it to your application menu? [y/N] " reply
    if [[ "$reply" =~ ^[Yy]$ ]]; then
      DESKTOP_DIR="$HOME/.local/share/applications"
      mkdir -p "$DESKTOP_DIR"
      cat > "$DESKTOP_DIR/$CMD.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=$NAME
Comment=Talk to your AI assistant
Exec=$LAUNCHER
Terminal=true
Categories=Utility;
EOF
      ok "Created $DESKTOP_DIR/$CMD.desktop — look for '$NAME' in your menu"
    fi
    ;;
esac

echo
echo "${BOLD}  Done. Type '$CMD' to talk to your assistant.${NC}"
