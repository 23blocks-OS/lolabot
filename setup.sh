#!/usr/bin/env bash
#
# lolabot setup.sh — Interactive scaffolding for a new PA (Personal Assistant) instance
#
# Usage: ./setup.sh /path/to/new-pa-instance
#
set -euo pipefail

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# --- Helpers ---
info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }
header()  { echo -e "\n${BOLD}${CYAN}=== $* ===${NC}\n"; }

ask() {
    local prompt="$1"
    local default="${2:-}"
    local var_name="$3"
    if [[ -n "$default" ]]; then
        echo -en "${BOLD}$prompt${NC} [${default}]: "
    else
        echo -en "${BOLD}$prompt${NC}: "
    fi
    read -r input
    if [[ -z "$input" && -n "$default" ]]; then
        eval "$var_name='$default'"
    elif [[ -z "$input" ]]; then
        error "This field is required."
        ask "$prompt" "$default" "$var_name"
    else
        eval "$var_name='$input'"
    fi
}

# --- Resolve script directory (where the template lives) ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_FILE="$SCRIPT_DIR/CLAUDE.TEMPLATE.md"

if [[ ! -f "$TEMPLATE_FILE" ]]; then
    error "CLAUDE.TEMPLATE.md not found at $SCRIPT_DIR"
    error "Run this script from the lolabot repo directory."
    exit 1
fi

# --- Parse target directory ---
if [[ $# -lt 1 ]]; then
    echo -e "${BOLD}Usage:${NC} $0 /path/to/new-pa-instance"
    echo ""
    echo "Creates a new Personal Assistant instance with the lolabot framework."
    echo ""
    echo "Example:"
    echo "  $0 ~/my-assistant"
    echo "  $0 /home/user/jarvis"
    exit 1
fi

TARGET_DIR="$(realpath -m "$1")"
INSTANCE_NAME="$(basename "$TARGET_DIR")"

# --- Check if target exists ---
if [[ -d "$TARGET_DIR" ]]; then
    if [[ -f "$TARGET_DIR/CLAUDE.md" ]]; then
        error "Directory $TARGET_DIR already contains a CLAUDE.md file."
        error "This looks like an existing PA instance. Aborting to avoid overwriting."
        exit 1
    fi
    warn "Directory $TARGET_DIR already exists. Files will be created inside it."
    echo -en "Continue? [y/N]: "
    read -r confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        info "Aborted."
        exit 0
    fi
fi

# --- Header ---
echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║    lolabot — PA Framework Setup           ║${NC}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════╝${NC}"
echo ""
info "Setting up new PA instance at: ${BOLD}$TARGET_DIR${NC}"
echo ""

# --- Interactive questions ---
header "Agent Configuration"

ask "Agent name (e.g., Lola, Jarvis, Friday)" "" AGENT_NAME
ask "Agent role (e.g., Chief of Staff, Personal Assistant)" "Personal Assistant" AGENT_ROLE

header "User Configuration"

ask "User's full name" "" USER_NAME
# Derive first name lowercase for profile file
USER_FIRST_NAME="${USER_NAME%% *}"
USER_FIRST_NAME_LOWER="$(echo "$USER_FIRST_NAME" | tr '[:upper:]' '[:lower:]')"
USER_PROFILE_FILE="${USER_FIRST_NAME_LOWER}-profile.md"

ask "Preferred language" "English" USER_PREFERRED_LANGUAGE
ask "Native language (or same as preferred)" "$USER_PREFERRED_LANGUAGE" USER_NATIVE_LANGUAGE

header "System Configuration"

ask "System hostname (e.g., mini-lola, homelab, macbook)" "$(hostname)" SYSTEM_NAME
ask "Operating system" "$(uname -s)" SYSTEM_OS
ask "RAM (e.g., 4 GB, 16 GB)" "" SYSTEM_RAM
ask "Storage (e.g., 256 GB, 1 TB)" "" SYSTEM_STORAGE
ask "System hardware (e.g., Mac Mini, Raspberry Pi, Desktop)" "" SYSTEM_HARDWARE
ask "Timezone (e.g., America/Denver, UTC)" "$(cat /etc/timezone 2>/dev/null || echo 'UTC')" SYSTEM_TIMEZONE

header "Email Configuration (optional — press Enter to skip)"

echo -en "${BOLD}User's email account${NC} (e.g., user@example.com) [skip]: "
read -r EMAIL_ACCOUNT_1
EMAIL_ACCOUNT_1="${EMAIL_ACCOUNT_1:-user@example.com}"

echo -en "${BOLD}Agent's email account${NC} (e.g., agent@example.com) [skip]: "
read -r EMAIL_ACCOUNT_2
EMAIL_ACCOUNT_2="${EMAIL_ACCOUNT_2:-agent@example.com}"

# --- Derived values ---
HOME_DIR="$(dirname "$TARGET_DIR")"
INSTANCE_DIR="$TARGET_DIR"
AGENT_ID="pa-$(echo "$AGENT_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')"
CURRENT_YEAR="$(date +%Y)"

# --- Confirm ---
header "Review Configuration"

echo -e "  Agent:     ${GREEN}$AGENT_NAME${NC} ($AGENT_ROLE)"
echo -e "  User:      ${GREEN}$USER_NAME${NC} ($USER_PREFERRED_LANGUAGE / $USER_NATIVE_LANGUAGE)"
echo -e "  System:    ${GREEN}$SYSTEM_NAME${NC} ($SYSTEM_OS, $SYSTEM_RAM RAM, $SYSTEM_STORAGE)"
echo -e "  Hardware:  ${GREEN}$SYSTEM_HARDWARE${NC}"
echo -e "  Timezone:  ${GREEN}$SYSTEM_TIMEZONE${NC}"
echo -e "  Email 1:   ${GREEN}$EMAIL_ACCOUNT_1${NC}"
echo -e "  Email 2:   ${GREEN}$EMAIL_ACCOUNT_2${NC}"
echo -e "  Target:    ${GREEN}$TARGET_DIR${NC}"
echo -e "  Agent ID:  ${GREEN}$AGENT_ID${NC}"
echo ""
echo -en "${BOLD}Proceed with setup? [Y/n]:${NC} "
read -r proceed
if [[ "$proceed" == "n" || "$proceed" == "N" ]]; then
    info "Aborted."
    exit 0
fi

# --- Create directory structure ---
header "Creating Directory Structure"

dirs=(
    "$TARGET_DIR/brain"
    "$TARGET_DIR/memory"
    "$TARGET_DIR/indexes"
    "$TARGET_DIR/emails/$EMAIL_ACCOUNT_1/inbox"
    "$TARGET_DIR/emails/$EMAIL_ACCOUNT_1/sent"
    "$TARGET_DIR/emails/$EMAIL_ACCOUNT_1/drafts"
    "$TARGET_DIR/emails/$EMAIL_ACCOUNT_1/attachments"
    "$TARGET_DIR/emails/$EMAIL_ACCOUNT_2/inbox"
    "$TARGET_DIR/emails/$EMAIL_ACCOUNT_2/sent"
    "$TARGET_DIR/emails/$EMAIL_ACCOUNT_2/drafts"
    "$TARGET_DIR/emails/$EMAIL_ACCOUNT_2/attachments"
    "$TARGET_DIR/articles/drafts"
    "$TARGET_DIR/articles/published"
    "$TARGET_DIR/prompts"
    "$TARGET_DIR/tools"
    "$TARGET_DIR/scripts"
    "$TARGET_DIR/skills"
    "$TARGET_DIR/tests"
    "$TARGET_DIR/docs"
)

for dir in "${dirs[@]}"; do
    mkdir -p "$dir"
done
success "Directory structure created (${#dirs[@]} directories)"

# --- Copy tools from lolabot repo ---
header "Copying Tools & Templates"

# Copy tools if they exist in the repo
if [[ -d "$SCRIPT_DIR/tools" ]]; then
    cp -n "$SCRIPT_DIR/tools/"* "$TARGET_DIR/tools/" 2>/dev/null || true
    success "Copied tools from lolabot repo"
fi

# Copy skills if they exist
if [[ -d "$SCRIPT_DIR/skills" ]]; then
    cp -rn "$SCRIPT_DIR/skills/"* "$TARGET_DIR/skills/" 2>/dev/null || true
    success "Copied skills from lolabot repo"
fi

# Copy brain templates
cp -n "$SCRIPT_DIR/brain/eisenhower.md" "$TARGET_DIR/brain/eisenhower.md" 2>/dev/null || true
cp -n "$SCRIPT_DIR/brain/agents.md" "$TARGET_DIR/brain/agents.md" 2>/dev/null || true
cp -n "$SCRIPT_DIR/brain/README.md" "$TARGET_DIR/brain/README.md" 2>/dev/null || true
success "Copied brain templates"

# Copy memory README
cp -n "$SCRIPT_DIR/memory/README.md" "$TARGET_DIR/memory/README.md" 2>/dev/null || true
success "Copied memory README"

# --- Generate lolabot.yaml ---
header "Generating Configuration"

cat > "$TARGET_DIR/lolabot.yaml" <<YAML
# lolabot.yaml — PA instance configuration
# Generated by lolabot setup.sh on $(date -Iseconds)

agent:
  name: "$AGENT_NAME"
  role: "$AGENT_ROLE"
  id: "$AGENT_ID"

user:
  name: "$USER_NAME"
  preferred_language: "$USER_PREFERRED_LANGUAGE"
  native_language: "$USER_NATIVE_LANGUAGE"
  profile_file: "$USER_PROFILE_FILE"

system:
  name: "$SYSTEM_NAME"
  hardware: "$SYSTEM_HARDWARE"
  os: "$SYSTEM_OS"
  ram: "$SYSTEM_RAM"
  storage: "$SYSTEM_STORAGE"
  timezone: "$SYSTEM_TIMEZONE"

email:
  account_1: "$EMAIL_ACCOUNT_1"
  account_2: "$EMAIL_ACCOUNT_2"

paths:
  home_dir: "$HOME_DIR"
  instance_dir: "$INSTANCE_DIR"
  instance_name: "$INSTANCE_NAME"
YAML
success "Generated lolabot.yaml"

# --- Generate CLAUDE.md from template ---
info "Generating CLAUDE.md from template..."

sed \
    -e "s|{{AGENT_NAME}}|$AGENT_NAME|g" \
    -e "s|{{AGENT_ROLE}}|$AGENT_ROLE|g" \
    -e "s|{{AGENT_ID}}|$AGENT_ID|g" \
    -e "s|{{USER_NAME}}|$USER_NAME|g" \
    -e "s|{{USER_PREFERRED_LANGUAGE}}|$USER_PREFERRED_LANGUAGE|g" \
    -e "s|{{USER_NATIVE_LANGUAGE}}|$USER_NATIVE_LANGUAGE|g" \
    -e "s|{{USER_FIRST_NAME_LOWER}}|$USER_FIRST_NAME_LOWER|g" \
    -e "s|{{USER_PROFILE_FILE}}|$USER_PROFILE_FILE|g" \
    -e "s|{{SYSTEM_NAME}}|$SYSTEM_NAME|g" \
    -e "s|{{SYSTEM_HARDWARE}}|$SYSTEM_HARDWARE|g" \
    -e "s|{{SYSTEM_OS}}|$SYSTEM_OS|g" \
    -e "s|{{SYSTEM_RAM}}|$SYSTEM_RAM|g" \
    -e "s|{{SYSTEM_STORAGE}}|$SYSTEM_STORAGE|g" \
    -e "s|{{SYSTEM_TIMEZONE}}|$SYSTEM_TIMEZONE|g" \
    -e "s|{{HOME_DIR}}|$HOME_DIR|g" \
    -e "s|{{INSTANCE_DIR}}|$INSTANCE_DIR|g" \
    -e "s|{{INSTANCE_NAME}}|$INSTANCE_NAME|g" \
    -e "s|{{EMAIL_ACCOUNT_1}}|$EMAIL_ACCOUNT_1|g" \
    -e "s|{{EMAIL_ACCOUNT_2}}|$EMAIL_ACCOUNT_2|g" \
    -e "s|{{YEAR}}|$CURRENT_YEAR|g" \
    "$TEMPLATE_FILE" > "$TARGET_DIR/CLAUDE.md"

success "Generated CLAUDE.md"

# --- Also replace placeholders in brain templates ---
for brain_file in "$TARGET_DIR/brain/eisenhower.md" "$TARGET_DIR/brain/agents.md"; do
    if [[ -f "$brain_file" ]]; then
        sed -i \
            -e "s|{{AGENT_NAME}}|$AGENT_NAME|g" \
            -e "s|{{USER_NAME}}|$USER_NAME|g" \
            "$brain_file"
    fi
done
success "Updated brain templates with agent/user names"

# --- Create starter memory files ---
if [[ ! -f "$TARGET_DIR/memory/$USER_PROFILE_FILE" ]]; then
    cat > "$TARGET_DIR/memory/$USER_PROFILE_FILE" <<EOF
# $USER_NAME - Profile

## Basic Info
- **Name:** $USER_NAME
- **Preferred language:** $USER_PREFERRED_LANGUAGE
- **Native language:** $USER_NATIVE_LANGUAGE

## Family

<!-- Add family members here -->

## Background

<!-- Add background information here -->

## Health

<!-- Add health information here -->

## Preferences

<!-- Add preferences here -->
EOF
    success "Created memory/$USER_PROFILE_FILE"
fi

if [[ ! -f "$TARGET_DIR/memory/goals.md" ]]; then
    cat > "$TARGET_DIR/memory/goals.md" <<EOF
# Goals

$USER_NAME's current goals and priorities.

**Last updated:** $(date +%Y-%m-%d)

---

## Active Goals

<!-- Add goals here -->

---

## Completed Goals

(None yet)
EOF
    success "Created memory/goals.md"
fi

if [[ ! -f "$TARGET_DIR/memory/journal-$CURRENT_YEAR.md" ]]; then
    cat > "$TARGET_DIR/memory/journal-$CURRENT_YEAR.md" <<EOF
# Journal $CURRENT_YEAR

Life events and milestones for $USER_NAME.

---

## $(date +%B) $CURRENT_YEAR

- **$(date +%Y-%m-%d):** PA instance set up with lolabot framework
EOF
    success "Created memory/journal-$CURRENT_YEAR.md"
fi

# --- Create .gitignore ---
header "Creating .gitignore"

cat > "$TARGET_DIR/.gitignore" <<'GITIGNORE'
# Credentials & secrets
brain/credentials.yaml
brain/*-credentials.yaml
brain/*-credentials.yml
*.env
.env
.env.*

# Python
.venv/
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/

# Indexes (large binary files - rebuild from tools)
indexes/*.mv2
indexes/*.db

# Email cache (can be re-synced)
emails/*/inbox/
emails/*/sent/
emails/*/drafts/
emails/*/attachments/

# OS
.DS_Store
Thumbs.db
*.swp
*.swo
*~

# IDE
.idea/
.vscode/
*.code-workspace

# Logs
*.log
/tmp/

# Node
node_modules/
GITIGNORE

success "Created .gitignore"

# --- Set up Python venv ---
header "Setting Up Python Environment"

if command -v uv &>/dev/null; then
    info "Using uv for Python environment..."
    (cd "$TARGET_DIR" && uv venv .venv 2>&1) && success "Created .venv with uv" || warn "Failed to create venv with uv"
    if [[ -f "$TARGET_DIR/.venv/bin/activate" ]]; then
        info "Installing base dependencies..."
        (cd "$TARGET_DIR" && source .venv/bin/activate && uv pip install memvid-sdk 2>&1) && success "Installed memvid-sdk" || warn "memvid-sdk install failed (can install later)"
    fi
elif command -v python3 &>/dev/null; then
    info "uv not found, using python3 venv..."
    python3 -m venv "$TARGET_DIR/.venv" 2>&1 && success "Created .venv with python3" || warn "Failed to create venv"
    if [[ -f "$TARGET_DIR/.venv/bin/activate" ]]; then
        info "Installing base dependencies..."
        (cd "$TARGET_DIR" && source .venv/bin/activate && pip install memvid-sdk 2>&1) && success "Installed memvid-sdk" || warn "memvid-sdk install failed (can install later)"
    fi
else
    warn "Neither uv nor python3 found. Skipping venv setup."
    warn "Install Python and run: cd $TARGET_DIR && uv venv .venv && source .venv/bin/activate && uv pip install memvid-sdk"
fi

# --- Initialize git repo if not already ---
header "Git Repository"

if [[ -d "$TARGET_DIR/.git" ]]; then
    info "Git repo already exists"
else
    if command -v git &>/dev/null; then
        (cd "$TARGET_DIR" && git init 2>&1) && success "Initialized git repository" || warn "Failed to init git repo"
    else
        warn "git not found. Initialize manually: cd $TARGET_DIR && git init"
    fi
fi

# --- Print summary ---
header "Setup Complete!"

echo -e "${GREEN}${BOLD}Your new PA instance is ready at:${NC}"
echo -e "  ${BOLD}$TARGET_DIR${NC}"
echo ""
echo -e "${BOLD}Directory structure:${NC}"
echo "  $INSTANCE_NAME/"
echo "  ├── CLAUDE.md              # Agent instructions (generated)"
echo "  ├── lolabot.yaml           # Instance configuration"
echo "  ├── .gitignore"
echo "  ├── brain/"
echo "  │   ├── eisenhower.md      # Task management"
echo "  │   ├── agents.md          # Agent registry"
echo "  │   └── README.md"
echo "  ├── memory/"
echo "  │   ├── $USER_PROFILE_FILE"
echo "  │   ├── goals.md"
echo "  │   ├── journal-$CURRENT_YEAR.md"
echo "  │   └── README.md"
echo "  ├── indexes/               # Memvid indexes (gitignored)"
echo "  ├── emails/                # Email cache (gitignored)"
echo "  ├── articles/"
echo "  │   ├── drafts/"
echo "  │   └── published/"
echo "  ├── tools/"
echo "  ├── scripts/"
echo "  ├── skills/"
echo "  ├── tests/"
echo "  ├── docs/"
echo "  └── prompts/"
echo ""
echo -e "${BOLD}Next steps:${NC}"
echo -e "  1. ${CYAN}cd $TARGET_DIR${NC}"
echo -e "  2. Review and customize ${CYAN}CLAUDE.md${NC} (uncomment sections you need)"
echo -e "  3. Add credentials to ${CYAN}brain/credentials.yaml${NC} (gitignored)"
echo -e "  4. Copy/configure tools (file_indexer.py, memory_indexer.py, email.sh)"
echo -e "  5. Set up email accounts in ${CYAN}tools/email.sh${NC}"
echo -e "  6. ${CYAN}git add -A && git commit -m 'Initial PA setup'${NC}"
echo ""
echo -e "${BOLD}Quick start with Claude Code:${NC}"
echo -e "  ${CYAN}cd $TARGET_DIR && claude${NC}"
echo ""
echo -e "${GREEN}${BOLD}Happy automating!${NC}"
