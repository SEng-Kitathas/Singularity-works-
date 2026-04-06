#!/usr/bin/env bash
# =============================================================================
# Singularity Works Forge — One-Touch Installer
# Tested: Ubuntu 22.04+, macOS 13+, WSL2
# Requirements: Python 3.11+, git
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; AMBER='\033[0;33m'; GREEN='\033[0;32m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

REPO_URL="https://github.com/SEng-Kitathas/Singularity-works-.git"
INSTALL_DIR="${SW_INSTALL_DIR:-$HOME/.singularity-works}"
VENV_DIR="$INSTALL_DIR/.venv"
MIN_PYTHON="3.11"

banner() {
  echo -e "${CYAN}${BOLD}"
  echo "  ╔══════════════════════════════════════════════════╗"
  echo "  ║   SINGULARITY WORKS FORGE — Installer v1.0      ║"
  echo "  ║   Bug Bounty Engine · Security Analysis Forge    ║"
  echo "  ╚══════════════════════════════════════════════════╝"
  echo -e "${RESET}"
}

die()  { echo -e "${RED}✗ ERROR: $*${RESET}" >&2; exit 1; }
ok()   { echo -e "${GREEN}✓ $*${RESET}"; }
info() { echo -e "${CYAN}· $*${RESET}"; }
warn() { echo -e "${AMBER}~ $*${RESET}"; }
step() { echo -e "\n${BOLD}── $* ──${RESET}"; }

# ── 1. Python version check ───────────────────────────────────────────────────
step "Checking Python"
PYTHON=$(command -v python3 || command -v python || die "Python 3.11+ not found")
PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_OK=$("$PYTHON" -c "import sys; print('ok' if sys.version_info >= (3,11) else 'fail')")
[[ "$PY_OK" == "ok" ]] || die "Python $MIN_PYTHON+ required, found $PY_VER. Install from python.org"
ok "Python $PY_VER"

# ── 2. Git ────────────────────────────────────────────────────────────────────
step "Checking git"
command -v git &>/dev/null || die "git not found. Install: apt install git / brew install git"
ok "git $(git --version | awk '{print $3}')"

# ── 3. Clone / update ─────────────────────────────────────────────────────────
step "Installing forge"
if [[ -d "$INSTALL_DIR/.git" ]]; then
  info "Existing install found at $INSTALL_DIR — updating"
  cd "$INSTALL_DIR"
  git pull --ff-only origin main
  ok "Updated to $(git rev-parse --short HEAD)"
else
  info "Cloning to $INSTALL_DIR"
  git clone "$REPO_URL" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
  ok "Cloned $(git rev-parse --short HEAD)"
fi

# ── 4. Virtual environment ────────────────────────────────────────────────────
step "Setting up Python environment"
if [[ ! -d "$VENV_DIR" ]]; then
  info "Creating virtual environment"
  "$PYTHON" -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
ok "venv active: $VIRTUAL_ENV"

# ── 5. Core dependencies ──────────────────────────────────────────────────────
step "Installing dependencies"
pip install --quiet --upgrade pip wheel
pip install --quiet \
  "flask>=3.0" "flask-cors>=4.0" "flask-socketio>=5.3" \
  "mcp>=0.9" \
  "watchdog>=3.0"
ok "Core dependencies installed"

# Optional: rich terminal output
pip install --quiet "rich>=13.0" 2>/dev/null && ok "rich installed" || warn "rich optional — skipping"

# ── 6. Install forge package ──────────────────────────────────────────────────
step "Installing Singularity Works package"
pip install --quiet -e .
ok "singularity-works installed (editable)"

# ── 7. Verify ─────────────────────────────────────────────────────────────────
step "Verifying installation"
python3 -c "
import sys
sys.path.insert(0, '.')
from singularity_works.orchestration import Orchestrator
from singularity_works.hud import ConsoleHUD
from singularity_works.bounty_reporter import build_report
from singularity_works.local_model_adapter import LocalModelAdapter
print('  forge core:     OK')
print('  hud v3:         OK')
print('  bounty reporter:OK')
print('  model adapter:  OK')
" && ok "All forge modules verified"

# ── 8. Write launcher scripts ─────────────────────────────────────────────────
step "Writing launchers"

# forge command
FORGE_BIN="$INSTALL_DIR/forge"
cat > "$FORGE_BIN" << 'EOF'
#!/usr/bin/env bash
source "$(dirname "$0")/.venv/bin/activate"
cd "$(dirname "$0")"
python3 -m singularity_works.bounty_reporter "$@"
EOF
chmod +x "$FORGE_BIN"
ok "forge launcher → $FORGE_BIN"

# forge-health command
HEALTH_BIN="$INSTALL_DIR/forge-health"
cat > "$HEALTH_BIN" << 'EOF'
#!/usr/bin/env bash
source "$(dirname "$0")/.venv/bin/activate"
cd "$(dirname "$0")"
python3 -m singularity_works.local_model_adapter health "$@"
EOF
chmod +x "$HEALTH_BIN"
ok "forge-health launcher → $HEALTH_BIN"

# forge-hud command
HUD_BIN="$INSTALL_DIR/forge-hud"
cat > "$HUD_BIN" << 'EOF'
#!/usr/bin/env bash
source "$(dirname "$0")/.venv/bin/activate"
cd "$(dirname "$0")"
python3 -m singularity_works.hud "$@"
EOF
chmod +x "$HUD_BIN"
ok "forge-hud launcher → $HUD_BIN"

# ── 9. PATH hint ──────────────────────────────────────────────────────────────
step "PATH configuration"
SHELL_RC="$HOME/.bashrc"
[[ "$SHELL" == *zsh* ]] && SHELL_RC="$HOME/.zshrc"

EXPORT_LINE="export PATH=\"\$PATH:$INSTALL_DIR\""
if ! grep -qF "$INSTALL_DIR" "$SHELL_RC" 2>/dev/null; then
  echo "" >> "$SHELL_RC"
  echo "# Singularity Works Forge" >> "$SHELL_RC"
  echo "$EXPORT_LINE" >> "$SHELL_RC"
  warn "Added to $SHELL_RC — run: source $SHELL_RC"
else
  ok "PATH already configured"
fi

# ── 10. Claude Code MCP setup ─────────────────────────────────────────────────
step "Claude Code MCP configuration"
MCP_SERVER_PATH="$INSTALL_DIR/singularity_works/forge_mcp_server.py"
MCP_JSON="{
  \"mcpServers\": {
    \"singularity-works\": {
      \"command\": \"$VENV_DIR/bin/python3\",
      \"args\": [\"$MCP_SERVER_PATH\"],
      \"cwd\": \"$INSTALL_DIR\"
    }
  }
}"
CLAUDE_SETTINGS_DIR="$HOME/.claude"
mkdir -p "$CLAUDE_SETTINGS_DIR"
echo "$MCP_JSON" > "$CLAUDE_SETTINGS_DIR/mcp_singularity_works.json"
ok "MCP config → $CLAUDE_SETTINGS_DIR/mcp_singularity_works.json"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════${RESET}"
echo -e "${GREEN}${BOLD}  Singularity Works Forge installed.          ${RESET}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════${RESET}"
echo ""
echo -e "  ${CYAN}Install dir:${RESET}  $INSTALL_DIR"
echo -e "  ${CYAN}Python env:${RESET}   $VENV_DIR"
echo ""
echo -e "  ${BOLD}Quick start:${RESET}"
echo -e "    ${AMBER}# Check LM Studio models${RESET}"
echo -e "    forge-health"
echo ""
echo -e "    ${AMBER}# Scan a file → HackerOne report${RESET}"
echo -e "    forge path/to/app.py --platform HackerOne --out ./reports"
echo ""
echo -e "    ${AMBER}# Live HUD demo${RESET}"
echo -e "    forge-hud"
echo ""
echo -e "    ${AMBER}# Claude Code MCP — add to .claude/settings.json:${RESET}"
echo -e "    cat $CLAUDE_SETTINGS_DIR/mcp_singularity_works.json"
echo ""
