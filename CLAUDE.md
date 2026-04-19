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

Without running this script, the Opsera security gate and branch guard will not be active.

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

A pre-commit security scan (Opsera) runs before every commit.
Scan must pass before the commit is allowed through.

Tools in use: `gitleaks`, `semgrep`, `grype`, `hadolint`

## Skill

The git-orchestrator skill lives at `.claude/skills/SKILL.md` (per-project)
or `~/.claude/skills/git-orchestrator.md` (global personal install).

Config: `.claude/git-workflow.yml`
