# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/).

## [Unreleased]

## [v1.1.0] — 2026-04-19

### Added

- `scripts/changelog-draft.sh` — parses conventional commits since last tag and
  generates a ready-to-paste `[Unreleased]` block, bucketed by type. (#22)
- Drift detection protocol — warns when feature branch is ≥1 commit behind
  `origin/main`; tiered warnings (info / warn / block) based on drift depth. (#16)

### Fixed

- Issue-linking regex tightened from `\b(\d+)\b` to `^(\d+)-` anchored at the
  start of the branch description segment. Eliminates false positives from
  mid-description numbers. Removes ambiguous Pattern B. (#20)

### Changed

- `docs/decisions.md` — 7 Architecture Decision Records covering squash merge,
  append-only history, config split, `/tmp` gate risk, skill architecture,
  issue-number anchoring, and no AI attribution. (#21)
- `docs/git-history.md` — new section on solo-dev value (retrospectives,
  abandoned-branch accounting, session recovery, burnout detection). (#23)
- `README.md` — 5-minute quickstart block at the top; docs table expanded. (#23)
- `docs/security/accepted-risks.md` — `/tmp` flag documented as accepted risk
  with CI as compensating control and upgrade path. (#19)
- `.semgrep/rules/` — replaced `--config=auto` (requires network + token) with
  10 versioned local rules: 7 secrets + 3 shell safety. (#18)
- `bootstrap.sh` + `.claude/settings.json.example` — first-clone setup script
  checks required tools, creates configs, installs pre-commit hook. (#17)

## [v1.0.0] — 2026-04-19

### Added

- Session history persistence protocol — append-only `.claude/git-history.json`
  schema with full 40-char SHAs, ISO 8601 UTC timestamps, atomic write, and
  annual rotation strategy. Gitignored HTML report generated on demand.
  (`docs/git-history.md` reference added.) (#11)
- Auto-detect issue number from branch name and inject `Closes #N` in PR body.
  Supports `fix/42-description` and `fix/description-42` patterns. (#10)
- Post-cleanup session history display after every merge: `gh pr list` merged
  view + `git log --oneline main` shown together under a Session history header. (#5)
- Post-merge local branch cleanup protocol with unpushed-commit guard,
  squash-merge divergence detection, and safe-delete confirmation flow. (#3)
- User identity collection during initialization flow — name, email, platform
  handle, and repository stored in `.claude/git-workflow.local.yml` (gitignored);
  applied immediately via `git config --local`. (#7)
- Plugin packaging — `.claude-plugin/plugin.json` manifest and
  `skills/git-orchestrator/SKILL.md` auto-synced from root `SKILL.md`
  via pre-commit hook. (#4)
- GitHub Actions CI pipeline with three independent jobs: commitlint
  (PR only), gitleaks secret detection, semgrep SAST (`--config=auto`). (#12)

### Fixed

- Split `.claude/git-workflow.yml` into team config (committed) and gitignored
  personal identity `.claude/git-workflow.local.yml` to prevent email/name
  from leaking into git history. Added `mode: solo|team` field. (#9)
- Block auto-merge after PR creation — skill now stops at PR URL and waits
  for explicit human reviewer approval before any merge action. (#6, #8)

### Changed

- Project rules and git workflow guidelines documented in `CLAUDE.md`. (#2)
- README installation verification section added with quickstart steps. (#1)
- Initial repository scaffolding with SKILL.md, docs/, and examples/. (#0)

## How to Update This File

After every merge to `main`, append entries under `[Unreleased]` grouped by:

| Section | Conventional Commit types |
|---------|--------------------------|
| **Added** | `feat` |
| **Fixed** | `fix` |
| **Changed** | `docs`, `ci`, `chore`, `refactor`, `perf`, `build` |
| **Removed** | any deletion of a previously documented feature |
| **Security** | security-relevant `fix` or `chore` |

On release: rename `[Unreleased]` to `[vX.Y.Z] — YYYY-MM-DD` and add a new
empty `[Unreleased]` section at the top.

[Unreleased]: https://github.com/Ferie-Vincent/claude-git-orchestrator/compare/v1.1.0...HEAD
[v1.1.0]: https://github.com/Ferie-Vincent/claude-git-orchestrator/compare/v1.0.0...v1.1.0
[v1.0.0]: https://github.com/Ferie-Vincent/claude-git-orchestrator/releases/tag/v1.0.0
