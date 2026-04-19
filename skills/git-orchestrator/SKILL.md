---
name: git-orchestrator
description: >
  Manages the complete Git lifecycle for every coding session. TRIGGER THIS
  SKILL immediately whenever the user says or implies ANY of the following —
  even when Git is not explicitly mentioned: "let's add X", "I want to
  implement", "let's build", "start on X", "work on X", "this is done",
  "this feature is done", "push this", "push it", "open a PR", "create a
  pull request", "make a PR", "merge to main", "merge this", "ship it",
  "ship this", "release", "cut a release", "hotfix", "branch off", "create
  a branch", "commit this", "stage these changes", "squash commits",
  "rebase", "what branch am I on?", "check the diff", "review my changes",
  "is this ready to merge?", "tag this release", "I finished X", "X is
  working now", "all tests pass". Also trigger when the assistant writes
  code, modifies files, or completes any implementation task — even if the
  user says nothing about Git. This skill covers: branch creation,
  Conventional Commits authoring, PR/MR creation with templates, merge
  strategy enforcement, protected-branch guardrails, and platform
  integration for GitHub and GitLab.
---

## Core Philosophy

Git hygiene is not optional. Every code change belongs to a named branch,
every commit tells a story, every PR provides context. This skill enforces
those invariants automatically so the team never has to ask "what does this
commit do?" or "why was this merged?"

Operate in the user's configured language. Default to English. Follow the
workflow configured in `.claude/git-workflow.yml`. When no config exists,
run the initialization flow before any Git action.

Never take irreversible Git actions (force-push, branch deletion, merge to
a protected branch) without explicit user confirmation. All other actions
— branch creation, commits, draft PRs — may proceed after a single
confirmation step.

## Language Handling

Read `language` from `.claude/git-workflow.yml`. Supported values:
- `en` — English (default)
- `fr` — French
- `es` — Spanish
- `de` — German
- `pt` — Portuguese

All commit messages, PR titles, PR bodies, and branch names are always in
English regardless of language setting. Language setting controls only the
conversational interface (confirmations, explanations, suggestions).

## Lifecycle Triggers

### TRIGGER-1: New Work Starts

**Cues:** "let's add", "I want to implement", "start on", "work on",
"let's build", "create a branch", "branch off".

**Actions:**
1. Check current branch — never work directly on `main`, `master`,
   `develop`, or any protected branch.
2. Propose branch name following `docs/branch-naming.md`.
3. Confirm with user before creating.
4. Create branch: `git checkout -b <branch-name>`.
5. Run the Drift Detection Protocol (see below) immediately after branch
   creation so the user starts on a non-drifted base.

### TRIGGER-2: Implementation Complete

**Cues:** "this is done", "commit this", "stage these changes", "I finished
X", "X is working now", "all tests pass", after the assistant writes or
modifies any file.

**Actions:**
1. Run `git status` and `git diff --stat` — show the user what changed.
2. Propose a Conventional Commit message following `docs/conventional-commits.md`.
3. Confirm with user — user may edit the message.
4. Stage and commit: `git add <files>` then `git commit -m "..."`.
5. Never use `git add .` without listing what will be staged.

### TRIGGER-3: Feature Complete — PR/MR Creation

**Cues:** "open a PR", "make a PR", "create a pull request", "push this",
"push it", "ship it", "this feature is done", "ready to review".

**Actions:**
1. Push branch: `git push -u origin <branch>`.
2. **Detect issue reference from branch name** — run this extraction before
   building the PR body:
   - Only supported pattern: `<type>/<number>-<description>` → e.g. `fix/42-login-redirect`
   - Regex (applied to the segment after the last `/`): `^(\d+)-`
   - The number must be at the **start** of the description segment.
   - If the pattern matches, store the captured group as `ISSUE_NUMBER`.
   - If no match, `ISSUE_NUMBER` is empty — skip issue linking silently.
3. Select PR template from `docs/pr-templates.md` based on workflow.
4. Build the PR body — append issue footer when `ISSUE_NUMBER` is set:
   ```
   Closes #<ISSUE_NUMBER>
   ```
   If `pull_request.require_issue_ref: true` and no issue number was detected,
   ask the user: "No issue number found in branch name. Enter issue number or
   skip? [number/skip]"
5. Create PR/MR via platform (see Platform Detection below).
6. Set draft status per config `pull_request.draft_by_default`.
7. **STOP. Display the PR URL and wait.** Do not merge. Do not suggest
   merging. The PR must be reviewed and approved by a human reviewer
   (a teammate, a tech lead, or the project owner) before any merge
   can happen. Claude never triggers a merge on its own after PR creation.

### TRIGGER-4: Review Requested

**Cues:** "review my changes", "check the diff", "is this ready?",
"what should I change?", "look over this".

**Actions:**
1. Run the Drift Detection Protocol (see below) first — surface any drift
   before the readiness summary so the user can resolve it.
2. Run `git diff main..HEAD --stat` to surface scope.
3. Check commit history: `git log main..HEAD --oneline`.
4. Verify all commits follow Conventional Commits format.
5. Flag commits that are out of spec — offer to amend or add a fixup.
6. Summarize PR readiness: branch clean, commits conformant, drift resolved.

### TRIGGER-5: Merge / Release

**Cues:** "merge to main", "merge this", "the PR was approved", "merge
request approved", "cut a release", "release", "tag this release".

**Prerequisite — human approval required:**
TRIGGER-5 must only fire when the user explicitly states that the PR/MR
has been reviewed and approved by a human. Never infer approval from
silence, from a thumbs-up emoji, or from the absence of objections.
If the user says "merge this" without mentioning approval, ask:
"Has this PR been reviewed and approved by a teammate or reviewer?"

**Actions:**
1. Confirm target branch — refuse to merge to protected branch without
   explicit approval step (see Confirmation Protocol).
2. Apply merge strategy from config `merge.strategy`.
3. If `merge.delete_branch_on_merge: true`, delete remote branch after merge.
4. For releases: tag with `git tag -a vX.Y.Z -m "release: vX.Y.Z"`.
5. Surface post-merge checklist: deploy pipeline, changelog, issue closure.
6. Run the Local Branch Cleanup Protocol (see below).

### Local Branch Cleanup Protocol

Execute after every successful merge, whether triggered by TRIGGER-5 or
detected via `gh pr view --json state` returning `MERGED`.

**Step 1 — Check for unpushed commits:**

```bash
git log <branch> --not origin/<branch> --oneline
```

- If output is **non-empty**: commits exist locally that were never pushed.
  Show the list to the user. Ask whether to push or discard before deleting.
  Never delete the branch until the user explicitly resolves this.

- If output is **empty**: all commits reached the remote. Proceed to Step 2.

**Step 2 — Handle squash-merge divergence:**

Squash merges rewrite history — `git log --not origin/<branch>` may show
commits even though the content is fully merged. Run an additional check:

```bash
git merge-base --is-ancestor <branch> origin/main
```

- Exit 0 → branch is an ancestor of main, fully merged. Safe to delete.
- Exit 1 → branch is NOT an ancestor. Combined with non-empty log from
  Step 1, treat as unpushed work and surface to the user.

**Step 3 — Propose local branch deletion:**

Present the confirmation block before executing. Use `git branch -d`
(safe delete) — never `git branch -D` unless the user types `yes` after
a force-delete warning.

```
Proposed action:
  Delete local branch: feature/add-user-auth
  Remote branch:       already deleted (or still exists)
  Unpushed commits:    none

Proceed? [y/n]
```

**Step 4 — Execute and confirm:**

```bash
git branch -d <branch>
```

Report result. If `git branch -d` fails (branch not fully merged per Git's
own check), surface the error verbatim — do not retry with `-D`.

**Step 5 — Display session history:**

Always show the action trail after cleanup so the user keeps a mental map
of what was done during the session.

```bash
# Merged PR history (branches + titles + dates, survives branch deletion)
gh pr list --state merged --json number,title,headRefName,mergedAt \
  --template '{{range .}}PR #{{.number}} | {{.mergedAt | timeago}} | {{.headRefName}}
  → {{.title}}
{{end}}'

# Commit log on main (squash commits with PR numbers)
git log --oneline main
```

Present both outputs together under a **Session history** header.
This gives two complementary views:
- `gh pr list` → branch names + PR context (survives deletion)
- `git log` → squash commits on main with PR numbers for traceability

**Step 6 — Append to session history:**

Run the Session History Protocol (see below) to record this merge.

### Session History Protocol

Execute after every successful merge and Local Branch Cleanup. Appends an
entry to `.claude/git-history.json` and regenerates `.claude/git-report.html`.

**Schema** — `.claude/git-history.json`:

```json
{
  "project": "owner/repo",
  "created_at": "2026-01-01T00:00:00Z",
  "sessions": [
    {
      "session_id": "2026-04-19T10:00:00Z",
      "branches": [
        {
          "name": "feature/add-pr-template",
          "type": "feature",
          "created_at": "2026-04-19T10:00:00Z",
          "merged_at": "2026-04-19T12:00:00Z",
          "status": "merged",
          "pr_number": 42,
          "pr_title": "feat(skill): add pr template selection",
          "commits": [
            {
              "sha": "<full 40-char SHA — never abbreviated>",
              "message": "feat(skill): add pr template selection",
              "timestamp": "2026-04-19T11:00:00Z"
            }
          ]
        }
      ]
    }
  ]
}
```

**Rules:**

- `session_id` = ISO 8601 UTC timestamp of the first Git action this session.
  Group all branches touched in one working session under the same id.
- `sha` must be the full 40-character commit hash — never abbreviated.
- All timestamps are ISO 8601 UTC (`Z` suffix, no offset).
- `status` values: `merged` | `abandoned` | `open`.
- **Append only** — never overwrite or reorder existing entries.
- **Atomic write** — write to `.claude/git-history.json.tmp`, then rename.
  Prevents corruption if the process is interrupted mid-write.
- If the file does not exist, initialize it with `project`, `created_at`,
  and an empty `sessions` array, then append the first entry.

**Annual rotation:**

When `sessions` exceeds 500 entries, archive to
`.claude/git-history-<YEAR>.json` and start a fresh file. Never delete
archived files — they are permanent audit records.

**Populate fields using:**

```bash
# Full 40-char SHA
git log --format="%H" -1 <ref>

# ISO 8601 UTC author timestamp
git log --format="%aI" -1 <ref>

# PR number, title, mergedAt (after merge)
gh pr view <branch> --json number,title,mergedAt
```

**HTML report** — `.claude/git-report.html`:

Generated after every append to `git-history.json`. Gitignored — never
committed. Contains a human-readable summary: session timeline, branch
list, PR links, commit log. Regenerate from `git-history.json` on demand
when the user asks for a history report.

Consult `docs/git-history.md` for the full schema reference and field
descriptions.

### Drift Detection Protocol

Execute at TRIGGER-1 (after branch creation) and TRIGGER-4 (before readiness
summary). Detects how far a feature branch has fallen behind `main`.

**Step 1 — Fetch and count:**

```bash
git fetch origin main --quiet
git rev-list --count HEAD..origin/main
```

- **0** → branch is up to date. No action, no message.
- **1–5** → minor drift. Surface a non-blocking warning.
- **6+** → significant drift. Surface a prominent warning and recommend
  rebasing before opening the PR to reduce merge conflict risk.

**Warning format (minor drift):**

```
⚠ Drift detected: your branch is 3 commit(s) behind main.
  Consider rebasing: git rebase origin/main
  Proceed anyway? [y/n]
```

**Warning format (significant drift — 6+ commits):**

```
⚠ Drift detected: your branch is 12 commit(s) behind main.
  High risk of merge conflicts. Strongly recommend rebasing first.
  git fetch origin main && git rebase origin/main
  Proceed anyway? [y/n]
```

**Rules:**

- Never block work automatically — drift is a warning, not a gate.
- Never rebase without explicit user confirmation.
- If `workflow: trunk-based` and `max_branch_age_days` is set, also warn
  when the branch age exceeds the configured threshold.
- Re-run after a rebase to confirm drift is resolved before continuing.

### TRIGGER-6: Hotfix / Emergency

**Cues:** "hotfix", "urgent fix", "production is broken", "patch this now",
"emergency".

**Actions:**
1. Branch off the production branch (not `develop`): `git checkout -b hotfix/<description> main`.
2. Use commit type `fix:` with a clear scope.
3. After fix: open a PR against main AND (for Git Flow) against `develop`.
4. Use the hotfix PR template from `docs/pr-templates.md`.
5. Flag the expedited nature in the PR body — do not skip the Testing checklist.

## Confirmation Protocol

Present a single confirmation block before any Git action. Format:

```
Proposed action:
  Branch: feature/add-user-auth
  Commit: feat(auth): add JWT-based authentication
  Target: main ← feature/add-user-auth

Proceed? [y/n]
```

For IRREVERSIBLE actions (force-push, branch deletion, merge to protected
branch, tag deletion), add a warning header and require explicit `yes`
(not just `y`).

Never chain confirmations. One action = one confirmation.

## Initialization Flow

When `.claude/git-workflow.yml` is absent, execute the initialization
sequence before any Git action:

1. Detect platform (see Platform Detection).
2. Detect workflow (see Workflow Detection).
3. Ask language preference.
4. Ask the work mode:
   ```
   Work mode:
     1) solo  — personal project or single developer
     2) team  — multiple contributors, shared conventions, PR reviews
   ```
   Stored as `mode: solo | team` in `.claude/git-workflow.yml`.
5. Collect user identity — ask the following in order:
   - **Full name** (e.g. `Jane Doe`)
   - **Email address** (e.g. `jane@example.com`)
   - **Platform handle** (GitHub or GitLab username)
   - **Repository name** (e.g. `org/my-app`)
6. Apply identity to local git config immediately:
   ```bash
   git config --local user.name "<name>"
   git config --local user.email "<email>"
   ```
7. Write **two** config files:
   - `.claude/git-workflow.yml` — team config (commit this): platform,
     workflow, mode, branches, commits, merge, protected_branches.
   - `.claude/git-workflow.local.yml` — personal config (gitignored, never
     commit): user identity only. Copy from
     `.claude/git-workflow.local.yml.example` if the example exists.
8. Offer to copy the matching starter config from `examples/`.

### Config file contract

| File | Committed | Contains | Who owns it |
|------|-----------|----------|-------------|
| `.claude/git-workflow.yml` | Yes | Workflow rules, mode, branch config | The team |
| `.claude/git-workflow.local.yml` | **Never** | name, email, handles, repo | Each developer |
| `.claude/git-workflow.local.yml.example` | Yes | Empty template | The team |

Never store credentials, tokens, or personal identity in
`.claude/git-workflow.yml`. If found, alert the user and offer to migrate
the data to the `.local.yml` file.

### Re-initialization / Identity Change

When `.claude/git-workflow.yml` already exists, read identity from
`.claude/git-workflow.local.yml` on every session start.
Display the active identity before the first Git action:

```
Active identity for this project:
  Name:       Jane Doe
  Email:      jane@example.com
  Handle:     @janedoe
  Repository: org/my-app

Change identity? [y/n]
```

If `.claude/git-workflow.local.yml` is absent, copy from the example and
prompt for values before proceeding. If the user confirms a change,
re-run steps 5–6 above and overwrite `.local.yml`.
This allows switching between multiple GitHub/GitLab accounts per project
without touching the global git config.

Full field reference: `docs/configuration.md`.

## Platform Detection

Check in this order:

1. **GitHub MCP** — if `mcp__github__*` tools are available, use them.
   Fallback: `gh` CLI (`gh pr create`, `gh pr view`).
   Final fallback: generate `https://github.com/<owner>/<repo>/compare/<branch>` URL.

2. **GitLab MCP** — if `mcp__gitlab__*` tools are available, use them.
   Fallback: `glab` CLI (`glab mr create`).
   Final fallback: generate `https://gitlab.com/<owner>/<repo>/-/merge_requests/new` URL.

3. **Unknown** — use `git` CLI only; do not assume a platform.

Never prompt for tokens, credentials, or passwords. Assume pre-authenticated.
Surface auth/rate-limit errors with the exact error message — no silent retry.

Read `platform` from config if already set; skip detection.

## Workflow Detection

Detect from git remote and branch structure if not configured:

| Signal | Detected workflow |
|--------|------------------|
| Branch `develop` exists | `git-flow` |
| `.github/` present, no `develop` | `github-flow` |
| Feature flags mentioned, short-lived branches | `trunk-based` |
| No remote, single branch | `github-flow` (default) |

Confirm detected workflow with user before writing config.

## Reference Files

Consult these files for detail — do not guess or recall from training data:

| File | When to consult |
|------|----------------|
| `docs/branch-naming.md` | Constructing any branch name |
| `docs/conventional-commits.md` | Authoring any commit message |
| `docs/pr-templates.md` | Filling any PR or MR body |
| `docs/mcp-integration.md` | Interacting with GitHub/GitLab APIs |
| `docs/configuration.md` | Reading or writing `.claude/git-workflow.yml` |
| `examples/github-flow.yml` | Initializing a GitHub Flow project |
| `examples/git-flow.yml` | Initializing a Git Flow project |
| `examples/trunk-based.yml` | Initializing a Trunk-based project |
| `docs/git-history.md` | Session History Protocol schema and field reference |

## Absolute Rules

1. **Never commit to a protected branch directly.** Protected branches
   (`main`, `master`, `develop`, or any listed in `protected_branches`)
   accept changes only via merged PR/MR.

2. **Every commit must follow Conventional Commits.** No exceptions.
   Squash or amend non-conformant commits before pushing.

3. **No AI attribution in any Git artifact.** Commits, PR titles, PR
   bodies, branch names, and tags must not contain "Claude", "AI-generated",
   "Co-authored-by: Claude", or any AI model reference.

4. **No emoji in commits unless gitmoji is explicitly configured.**
   Check `commits.gitmoji: true` in config before using any emoji.

5. **No force-push to shared branches.** `git push --force` is forbidden
   on any branch that other contributors may have pulled. Use
   `--force-with-lease` only on personal feature branches, only when
   rebasing, and only with explicit user confirmation.

6. **No silent actions.** Every Git action (branch create, commit, push,
   merge) must be shown to the user before execution.

7. **Branch names are always kebab-case, always in English.** No spaces,
   no uppercase, no special characters except `/` and `-`.

8. **Commit subject max 72 characters, imperative mood, no trailing
   period, lowercase first letter.** Validate before committing.

9. **Never use `git add .` or `git add -A` without first showing the
   user what will be staged.** Stage explicitly by file or directory.

10. **Initialization is mandatory.** If `.claude/git-workflow.yml` does
    not exist, run the initialization flow. Never assume defaults silently.
