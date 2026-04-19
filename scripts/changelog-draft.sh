#!/usr/bin/env bash
# Generates a CHANGELOG [Unreleased] draft from conventional commits since the last tag.
# Usage: bash scripts/changelog-draft.sh
# Output: prints draft to stdout, ready to paste into CHANGELOG.md

set -euo pipefail

CHANGELOG="CHANGELOG.md"

# Find the base ref: last tag, or first commit if no tags exist
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)

# Collect commits since that ref
COMMITS=$(git log "${LAST_TAG}..HEAD" --pretty=format:"%s" --no-merges 2>/dev/null)

if [[ -z "$COMMITS" ]]; then
  echo "No commits since ${LAST_TAG}. Nothing to draft." >&2
  exit 0
fi

# Buckets
BREAKING=()
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
SECURITY=()
UNKNOWN=()

while IFS= read -r msg; do
  [[ -z "$msg" ]] && continue
  type="${msg%%(*}"      # everything before first '(' or ':'
  type="${type%%:*}"
  type="${type// /}"
  body="${msg#*: }"      # everything after ': '

  # Detect breaking changes: trailing ! or BREAKING CHANGE in footer
  if [[ "$msg" =~ ^[a-z]+(\([^)]+\))?!: ]] || [[ "$msg" =~ BREAKING[[:space:]]CHANGE ]]; then
    BREAKING+=("$body")
  fi

  case "$type" in
    feat)                ADDED+=("$body") ;;
    fix)                 FIXED+=("$body") ;;
    docs|ci|chore|refactor|perf|build|style|test) CHANGED+=("$body") ;;
    revert)              REMOVED+=("$body") ;;
    security)            SECURITY+=("$body") ;;
    *)                   UNKNOWN+=("$body") ;;
  esac
done <<< "$COMMITS"

# Render
TODAY=$(date +%Y-%m-%d)
echo "## [Unreleased]"
echo ""
echo "<!--"
echo "  Auto-drafted by scripts/changelog-draft.sh on ${TODAY}"
echo "  Based on commits since ${LAST_TAG}"
echo "  Review, edit, and paste into CHANGELOG.md under [Unreleased]"
echo "-->"
echo ""

print_section() {
  local header="$1"; shift
  local -a items=("$@")
  if [[ ${#items[@]} -gt 0 ]]; then
    echo "### ${header}"
    echo ""
    for item in "${items[@]}"; do
      echo "- ${item}"
    done
    echo ""
  fi
}

print_section "Breaking Changes" "${BREAKING[@]+"${BREAKING[@]}"}"
print_section "Added"    "${ADDED[@]+"${ADDED[@]}"}"
print_section "Fixed"    "${FIXED[@]+"${FIXED[@]}"}"
print_section "Changed"  "${CHANGED[@]+"${CHANGED[@]}"}"
print_section "Removed"  "${REMOVED[@]+"${REMOVED[@]}"}"
print_section "Security" "${SECURITY[@]+"${SECURITY[@]}"}"

if [[ ${#UNKNOWN[@]} -gt 0 ]]; then
  echo "### Uncategorized (review manually)"
  echo ""
  for item in "${UNKNOWN[@]}"; do
    echo "- ${item}"
  done
  echo ""
fi
