# Session History Reference

## Overview

Every merge appends a record to `.claude/git-history.json`. The file is an
append-only audit trail of branches, PRs, and commits across all sessions.
`.claude/git-report.html` is a generated human-readable view — it is
gitignored and never committed.

## File Locations

| File | Committed | Purpose |
|------|-----------|---------|
| `.claude/git-history.json` | Yes | Append-only audit log |
| `.claude/git-report.html` | No (gitignored) | Generated human-readable report |
| `.claude/git-history-<YEAR>.json` | Yes | Annual archive when sessions > 500 |

## JSON Schema

### Top-level

| Field | Type | Description |
|-------|------|-------------|
| `project` | string | Repository identifier (`owner/repo`) |
| `created_at` | string | ISO 8601 UTC — when this file was first created |
| `sessions` | array | Ordered list of session records (append-only) |

### Session object

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | ISO 8601 UTC timestamp of first Git action in the session |
| `branches` | array | Branches touched during this session |

### Branch object

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Full branch name (e.g. `feature/add-pr-template`) |
| `type` | string | Branch type prefix: `feature`, `fix`, `docs`, `chore`, `refactor`, `test`, `perf`, `ci`, `build`, `hotfix` |
| `created_at` | string | ISO 8601 UTC — when branch was created |
| `merged_at` | string \| null | ISO 8601 UTC — when merged; `null` if not yet merged |
| `status` | string | `merged` \| `abandoned` \| `open` |
| `pr_number` | integer \| null | GitHub/GitLab PR or MR number |
| `pr_title` | string \| null | PR title as it appears on the platform |
| `commits` | array | Commits made on this branch (excluding merge commit) |

### Commit object

| Field | Type | Description |
|-------|------|-------------|
| `sha` | string | Full 40-character commit hash — never abbreviated |
| `message` | string | Commit subject line |
| `timestamp` | string | ISO 8601 UTC author timestamp |

## Complete Example

```json
{
  "project": "Ferie-Vincent/claude-git-orchestrator",
  "created_at": "2026-04-19T10:00:00Z",
  "sessions": [
    {
      "session_id": "2026-04-19T10:00:00Z",
      "branches": [
        {
          "name": "feature/add-pr-template",
          "type": "feature",
          "created_at": "2026-04-19T10:05:00Z",
          "merged_at": "2026-04-19T12:30:00Z",
          "status": "merged",
          "pr_number": 42,
          "pr_title": "feat(skill): add pr template selection",
          "commits": [
            {
              "sha": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
              "message": "feat(skill): add pr template selection",
              "timestamp": "2026-04-19T11:45:00Z"
            }
          ]
        }
      ]
    }
  ]
}
```

## Write Rules

1. **Append only** — never modify or delete existing entries.
2. **Atomic write** — write to `.claude/git-history.json.tmp`, then rename
   to `.claude/git-history.json`. Prevents partial-write corruption.
3. **Initialize if missing** — if no file exists, create it with `project`,
   `created_at` (now), and `sessions: []`, then append the first entry.
4. **Session grouping** — use the same `session_id` for all branches opened
   in a single working session. A new session starts when the conversation
   is fresh (no prior Git actions recorded this session).

## Shell Commands for Field Population

```bash
# Full 40-char SHA of HEAD
git log --format="%H" -1

# Full 40-char SHA of a specific ref
git log --format="%H" -1 <ref>

# ISO 8601 UTC author timestamp
git log --format="%aI" -1 <ref>

# PR number, title, and mergedAt from GitHub CLI
gh pr view <branch> --json number,title,mergedAt
```

## Annual Rotation

When `sessions` array length exceeds **500 entries**:

1. Copy `.claude/git-history.json` to `.claude/git-history-<YEAR>.json`
   where `<YEAR>` is the year of the oldest session in the file.
2. Reset `.claude/git-history.json` to a fresh file with `project`,
   `created_at` (now), and `sessions: []`.
3. Commit both files: the archive and the fresh file.
4. Never delete archived files — they are permanent audit records.

## HTML Report

`.claude/git-report.html` is generated on demand or after each merge. It
renders the full `git-history.json` as a navigable HTML page:

- Session timeline with branch cards
- PR links (clickable if `repository` is set in config)
- Commit log per branch with full SHA and timestamp
- Status badges: merged / open / abandoned

Regenerate with the command: "show me the git history report" or "regenerate git report".
