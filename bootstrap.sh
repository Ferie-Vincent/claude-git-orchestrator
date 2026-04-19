#!/usr/bin/env bash
# bootstrap.sh — local dev setup after cloning
# Run once: bash bootstrap.sh
#
# Non-interactive mode (CI / Docker / scripts):
#   GIT_NAME="Your Name" GIT_EMAIL="you@example.com" \
#   GIT_HANDLE="yourhandle" GIT_REPO="owner/repo" \
#   bash bootstrap.sh --non-interactive
#
# Or: bash bootstrap.sh --non-interactive   (skips identity prompts, prints instructions)

set -euo pipefail

RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'; NC='\033[0m'

# Detect interactive mode
INTERACTIVE=true
for arg in "$@"; do
  [[ "$arg" == "--non-interactive" ]] && INTERACTIVE=false
done
# Also detect non-TTY automatically
[[ ! -t 0 ]] && INTERACTIVE=false

echo "=== git-orchestrator bootstrap ==="
[[ "$INTERACTIVE" == "false" ]] && echo "(non-interactive mode)"
echo ""

# ── 1. Required tools ─────────────────────────────────────────────────────────
echo "Checking required tools..."
MISSING=()
for tool in gitleaks semgrep grype hadolint gh git; do
  command -v "$tool" >/dev/null 2>&1 && echo "  ✓ $tool" || { echo "  ✗ $tool"; MISSING+=("$tool"); }
done

if [ ${#MISSING[@]} -gt 0 ]; then
  echo ""
  echo -e "${YELLOW}Missing tools: ${MISSING[*]}${NC}"
  echo "Install on macOS: brew install ${MISSING[*]}"
  echo "The Opsera pre-commit gate requires all tools to be present."
  echo ""
  if [[ "$INTERACTIVE" == "false" ]]; then
    echo "Non-interactive mode: continuing with missing tools. Install them before committing."
  else
    read -r -p "Continue anyway? [y/n] " ans
    [[ "$ans" != "y" ]] && exit 1
  fi
fi

echo ""

# ── 2. .claude/settings.json ──────────────────────────────────────────────────
SETTINGS=".claude/settings.json"
SETTINGS_EXAMPLE=".claude/settings.json.example"

if [ -f "$SETTINGS" ]; then
  echo -e "${GREEN}✓ $SETTINGS already exists — skipping${NC}"
else
  cp "$SETTINGS_EXAMPLE" "$SETTINGS"
  echo -e "${GREEN}✓ Created $SETTINGS from example${NC}"
fi

# ── 3. .claude/git-workflow.local.yml ─────────────────────────────────────────
LOCAL_YML=".claude/git-workflow.local.yml"
LOCAL_EXAMPLE=".claude/git-workflow.local.yml.example"

if [ -f "$LOCAL_YML" ]; then
  echo -e "${GREEN}✓ $LOCAL_YML already exists — skipping${NC}"
else
  cp "$LOCAL_EXAMPLE" "$LOCAL_YML"
  echo ""
  echo -e "${YELLOW}Action required: fill in your identity in $LOCAL_YML${NC}"
  echo ""

  if [[ "$INTERACTIVE" == "false" ]]; then
    # Use environment variables if provided, otherwise leave placeholders
    GIT_NAME="${GIT_NAME:-}"
    GIT_EMAIL="${GIT_EMAIL:-}"
    GIT_HANDLE="${GIT_HANDLE:-}"
    GIT_REPO="${GIT_REPO:-}"

    if [[ -z "$GIT_NAME" || -z "$GIT_EMAIL" ]]; then
      echo "Non-interactive mode: set GIT_NAME, GIT_EMAIL, GIT_HANDLE, GIT_REPO env vars"
      echo "then re-run bootstrap.sh, or edit $LOCAL_YML manually."
      echo -e "${YELLOW}⚠ Identity not configured — git commits will use global git config${NC}"
    else
      cat > "$LOCAL_YML" <<EOF
user:
  name: "${GIT_NAME}"
  email: "${GIT_EMAIL}"
  github_handle: "${GIT_HANDLE}"
  repository: "${GIT_REPO}"
EOF
      git config --local user.name "$GIT_NAME"
      git config --local user.email "$GIT_EMAIL"
      echo -e "${GREEN}✓ Identity applied from environment variables${NC}"
    fi
  else
    cat "$LOCAL_EXAMPLE"
    echo ""
    read -r -p "Enter your full name: " GIT_NAME
    read -r -p "Enter your email: " GIT_EMAIL
    read -r -p "Enter your GitHub handle (without @): " GIT_HANDLE
    read -r -p "Enter the repository (e.g. owner/repo): " GIT_REPO

    cat > "$LOCAL_YML" <<EOF
user:
  name: "${GIT_NAME}"
  email: "${GIT_EMAIL}"
  github_handle: "${GIT_HANDLE}"
  repository: "${GIT_REPO}"
EOF

    git config --local user.name "$GIT_NAME"
    git config --local user.email "$GIT_EMAIL"
    echo -e "${GREEN}✓ Applied identity to local git config${NC}"
  fi

  echo -e "${GREEN}✓ Created $LOCAL_YML${NC}"
fi

# ── 4. Pre-commit hook (SKILL.md sync) ────────────────────────────────────────
HOOK=".git/hooks/pre-commit"
if [ -f "$HOOK" ] && grep -q "Synced.*SKILL.md" "$HOOK" 2>/dev/null; then
  echo -e "${GREEN}✓ Pre-commit hook already installed${NC}"
else
  cat > "$HOOK" <<'HOOKEOF'
#!/usr/bin/env bash
ROOT_SKILL="SKILL.md"
PLUGIN_SKILL="skills/git-orchestrator/SKILL.md"
if [ ! -f "$ROOT_SKILL" ]; then exit 0; fi
if ! diff -q "$ROOT_SKILL" "$PLUGIN_SKILL" > /dev/null 2>&1; then
  cp "$ROOT_SKILL" "$PLUGIN_SKILL"
  git add "$PLUGIN_SKILL"
  echo "[pre-commit] Synced $PLUGIN_SKILL from $ROOT_SKILL"
fi
HOOKEOF
  chmod +x "$HOOK"
  echo -e "${GREEN}✓ Pre-commit hook installed${NC}"
fi

echo ""
echo -e "${GREEN}=== Bootstrap complete ===${NC}"
echo ""
echo "Next steps:"
echo "  1. Open Claude Code in this directory"
echo "  2. Enable the Opsera plugin if not already active"
echo "  3. Start working — git-orchestrator handles the rest"
