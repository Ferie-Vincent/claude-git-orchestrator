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
2. Select PR template from `docs/pr-templates.md` based on workflow.
3. Create PR/MR via platform (see Platform Detection below).
4. Set draft status per config `pull_request.draft_by_default`.
5. Link related issues per `pull_request.require_issue_ref`.

### TRIGGER-4: Review Requested

**Cues:** "review my changes", "check the diff", "is this ready?",
"what should I change?", "look over this".

**Actions:**
1. Run `git diff main..HEAD --stat` to surface scope.
2. Check commit history: `git log main..HEAD --oneline`.
3. Verify all commits follow Conventional Commits format.
4. Flag commits that are out of spec — offer to amend or add a fixup.
5. Summarize PR readiness: branch clean, commits conformant, tests noted.

### TRIGGER-5: Merge / Release

**Cues:** "merge to main", "merge this", "ship it", "cut a release",
"release", "tag this release", "merge request approved".

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
4. Write `.claude/git-workflow.yml` using the detected values.
5. Offer to copy the matching starter config from `examples/`.

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
