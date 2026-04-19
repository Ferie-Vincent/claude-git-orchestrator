# Claude Code — Project Rules

## Getting started (first clone)

Run once after cloning:

```bash
bash bootstrap.sh
```

The script:
1. Checks required tools (`gitleaks`, `semgrep`, `grype`, `hadolint`, `gh`)
2. Creates `.claude/settings.json` from `.claude/settings.json.example` (branch guard + Opsera plugin)
3. Creates `.claude/git-workflow.local.yml` from the example template and prompts for your identity
4. Applies your identity to local git config (`git config --local`)
5. Installs the pre-commit hook that auto-syncs `SKILL.md` → plugin copy

Without running this script, `.claude/settings.json` (branch guard + Opsera plugin) and the SKILL.md sync hook will not be in place. Note: `bootstrap.sh` installs the SKILL.md auto-sync pre-commit hook (step 5), not the Opsera security gate — the gate is a Claude Code PreToolUse hook configured in `settings.json` (step 2).

## Git workflow

This project uses **git-orchestrator** to enforce the full Git lifecycle.
The skill auto-triggers on any implementation or Git-related request.

### Protected branches

`main` is the only long-lived branch. Direct commits are forbidden.
Every change goes through a feature branch and a pull request.

### Branch naming (kebab-case, English, always)

| Type | Prefix | Example |
|------|--------|---------|
| Feature | `feature/` | `feature/add-pr-template` |
| Bug fix | `fix/` | `fix/branch-detection-edge-case` |
| Documentation | `docs/` | `docs/update-configuration-guide` |
| Chore | `chore/` | `chore/update-dependencies` |
| Refactor | `refactor/` | `refactor/simplify-workflow-detection` |
| CI | `ci/` | `ci/add-semgrep-scan` |

### Commit format (Conventional Commits, always)

```
<type>(<scope>): <subject>

type    = feat | fix | docs | style | refactor | perf | test | build | ci | chore | revert
scope   = optional, lowercase (e.g. readme, skill, config, hooks)
subject = imperative mood, max 72 chars, no trailing period, lowercase first letter
```

### Pull request rules

- Every PR targets `main`
- Merge strategy: **squash**
- Branch deleted after merge
- No AI attribution in commits, PR titles, or branch names

## Security

An Opsera security gate (Claude Code PreToolUse hook) runs before git commands executed via Claude Code. Commits made directly via terminal bypass this gate — GitHub Actions CI provides the authoritative security boundary.

Tools in use: `gitleaks`, `semgrep`, `grype`, `hadolint`

### Known limitation — gate flag

The pre-commit gate uses a flag file at `/tmp/.opsera-pre-commit-scan-passed`.
This is trivially bypassable with `touch /tmp/.opsera-pre-commit-scan-passed`.

**Accepted risk (solo project):** the gate is a developer habit enforcer, not
a cryptographic guarantee. The CI pipeline (GitHub Actions) provides the
authoritative security gate — branch protection rules require all CI checks
to pass before any PR can merge, regardless of local gate state.

If this project moves to a multi-contributor team, replace the flag with a
hash-based approach: write `sha256(git write-tree)` into the flag so it is
tied to the exact staged content being committed.

## Skill

The git-orchestrator skill lives at `.claude/skills/SKILL.md` (per-project)
or `~/.claude/skills/git-orchestrator.md` (global personal install).

Config: `.claude/git-workflow.yml`
