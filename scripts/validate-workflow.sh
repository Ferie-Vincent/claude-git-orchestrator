#!/usr/bin/env bash
# Validates .claude/git-workflow.yml against required fields and allowed values.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo .)"
CONFIG="$REPO_ROOT/.claude/git-workflow.yml"

errors=0
warn() { echo "⚠️  WARN: $*" >&2; }
fail() { echo "❌ ERROR: $*" >&2; errors=$((errors + 1)); }

# Check file exists
if [ ! -f "$CONFIG" ]; then
  fail "git-workflow.yml not found at $CONFIG"
  exit 1
fi

# Helper: extract a YAML value (simple key: value — no nested)
yaml_get() {
  grep -E "^[[:space:]]*$1:" "$CONFIG" 2>/dev/null \
    | head -1 | sed 's/.*:[[:space:]]*//' | tr -d '"' | tr -d "'"
}

# Required top-level fields
for field in project mode merge_strategy default_branch; do
  val=$(yaml_get "$field")
  if [ -z "$val" ]; then
    fail "missing required field: $field"
  fi
done

# mode must be solo or team
mode=$(yaml_get "mode")
if [ -n "$mode" ] && [[ "$mode" != "solo" && "$mode" != "team" ]]; then
  fail "mode must be 'solo' or 'team', got: '$mode'"
fi

# merge_strategy must be squash, rebase, or merge
ms=$(yaml_get "merge_strategy")
if [ -n "$ms" ] && [[ "$ms" != "squash" && "$ms" != "rebase" && "$ms" != "merge" ]]; then
  fail "merge_strategy must be squash|rebase|merge, got: '$ms'"
fi

# default_branch must be non-empty string
db=$(yaml_get "default_branch")
if [ -n "$db" ] && echo "$db" | grep -qE '[[:space:]]'; then
  fail "default_branch must not contain spaces"
fi

# Warn if local identity fields are present (ADR-003 violation)
for field in name email handle; do
  val=$(yaml_get "$field")
  if [ -n "$val" ]; then
    warn "field '$field' belongs in git-workflow.local.yml (ADR-003), not in committed config"
  fi
done

if [ "$errors" -gt 0 ]; then
  echo ""
  echo "❌ $errors validation error(s) in $CONFIG"
  echo "   See docs/configuration.md for the expected schema."
  exit 1
fi

echo "✅ git-workflow.yml valid"
exit 0
