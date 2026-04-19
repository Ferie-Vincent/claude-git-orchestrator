# Team Onboarding Guide

For teams adopting git-orchestrator across multiple developers.

## Prerequisites

Each developer must complete the per-developer setup independently:

1. Clone the repository
2. Run `bash bootstrap.sh` — this creates local identity config and installs hooks
3. Verify with `cat .claude/git-workflow.local.yml` — should show your name and email

## Shared configuration

The file `.claude/git-workflow.yml` is committed and team-wide. It contains:
- `project`: GitHub owner/repo
- `mode: team` (set this when onboarding a team — enables stricter checks)
- `merge_strategy: squash`
- `default_branch: main`

Each developer's identity goes in their own `.claude/git-workflow.local.yml`
(gitignored). Identity is never committed.

## Per-developer checklist

- [ ] `bash bootstrap.sh` completed without errors
- [ ] `git config --local user.name` returns your name
- [ ] `git config --local user.email` returns your email
- [ ] `git log --oneline -1` shows a commit (repo not empty)
- [ ] Claude Code installed and `claude` command available

## Mode: solo vs team

| Setting | `solo` | `team` |
|---------|--------|--------|
| Drift warning | 1 commit | 1 commit |
| Drift block | 5 commits | 3 commits |
| PR review required | optional | enforced |

Set `mode: team` in `git-workflow.yml` and commit it when multiple developers use the skill.

## Common issues

**Identity not applied:** Run `bash bootstrap.sh` again — it is idempotent.

**Pre-commit hook missing:** `bootstrap.sh` installs it. Check with `cat .git/hooks/pre-commit`.

**Different merge strategies per developer:** Not supported — `merge_strategy` is team-wide.
