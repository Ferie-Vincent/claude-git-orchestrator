# git-orchestrator

[![CI](https://github.com/Ferie-Vincent/claude-git-orchestrator/actions/workflows/ci.yml/badge.svg)](https://github.com/Ferie-Vincent/claude-git-orchestrator/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/github/v/tag/Ferie-Vincent/claude-git-orchestrator?label=version)](https://github.com/Ferie-Vincent/claude-git-orchestrator/releases)

A Claude Code skill that manages the full Git lifecycle — branching, commits,
PRs, and merges — with enforced conventions, so your team never debates
commit format or PR hygiene again.

---

## Quickstart (5 minutes)

```bash
# 1. Clone the repo
git clone https://github.com/Ferie-Vincent/claude-git-orchestrator
cd claude-git-orchestrator

# 2. Bootstrap (checks tools, creates config, installs pre-commit hook)
bash bootstrap.sh

# 3. Open Claude Code in this repo
claude .
```

Then say anything — "let's add a feature", "commit this", "open a PR" — and
the skill takes over. If it's your first run, the initialization flow collects
your identity and creates `.claude/git-workflow.yml` automatically.

> **Using it in your own project?** Install SKILL.md into your `.claude/skills/`
> folder (see [Installation](#installation) below) and say anything Git-related.

---

## What it does

| You say | Claude proposes |
|---------|----------------|
| "let's add user authentication" | Creates `feature/user-auth` branch |
| "this is done" / "commit this" | Drafts a Conventional Commit message, confirms, stages, commits |
| "push this" / "open a PR" | Pushes branch, fills PR template, creates PR via MCP or `gh` |
| "merge to main" | Applies configured merge strategy, deletes branch if configured |
| "hotfix" / "production is broken" | Branches off `main`, uses hotfix PR template, expedited flow |
| "review my changes" | Audits commits for convention compliance, summarizes PR readiness |
| "cut a release" | Tags release, opens release PR, pre-release checklist |

The skill triggers automatically when you finish implementing anything —
even when you don't mention Git.

---

## Example

```
> "this is done"

git-orchestrator proposes:

  Branch: feature/user-auth
  Commit: feat(auth): add JWT login endpoint
  Subject: 38/72 chars ✓

  Staged files:
    src/auth/login.ts
    tests/auth.test.ts

  Proceed? [y/n]
```

---

## Why this skill

- **Zero debate.** Branch names, commit messages, and PR templates are
  enforced by config, not by whoever reviewed last.
- **Works with your platform.** GitHub MCP, `gh` CLI, GitLab MCP, `glab`
  CLI — the skill tries each in order, falls back gracefully.
- **Configurable, not opinionated by force.** GitHub Flow, Git Flow, and
  Trunk-based are all first-class. Three example configs to copy-paste.
- **No AI footprint in your Git history.** Commits and PRs contain only
  your team's work. No AI attribution, ever.

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Claude Code | Any recent version |
| `git` | Must be in `$PATH` |
| `gh` | Optional — for GitHub PR creation via CLI |
| `glab` | Optional — for GitLab MR creation via CLI |
| GitHub MCP | Optional — for GitHub API access without CLI |
| GitLab MCP | Optional — for GitLab API access without CLI |

---

## Installation

Three options exist. **Pick exactly one** — do not mix them or you will get duplicate
behavior. If multiple are present, Claude Code loads them in this priority order:
**per-project > plugin > personal global**. The per-project copy always wins.

### Option 1 — Per-project (recommended for teams)

The skill lives inside your repo. Every developer who clones it gets the same version.

```bash
mkdir -p .claude/skills
curl -o .claude/skills/SKILL.md \
  https://raw.githubusercontent.com/Ferie-Vincent/claude-git-orchestrator/main/SKILL.md
```

Commit `.claude/skills/SKILL.md` so the whole team benefits automatically.

**When to use:** shared codebases, teams, or when you want the skill version pinned
to the repo (you control upgrades explicitly via `curl` + commit).

### Option 2 — Personal global (applies to all your projects)

The skill lives in your home directory. One install, every project you open.

```bash
mkdir -p ~/.claude/skills
curl -o ~/.claude/skills/git-orchestrator.md \
  https://raw.githubusercontent.com/Ferie-Vincent/claude-git-orchestrator/main/SKILL.md
```

**When to use:** solo developer, personal projects, or when you want the skill
available everywhere without committing anything to each repo.

**Note:** if a repo also has a per-project copy (Option 1), the per-project copy
takes precedence. Your global install is silently ignored for that project.

### Option 3 — Plugin (native Skill tool integration)

Add this to your `~/.claude/settings.json` under `extraKnownMarketplaces`
and `enabledPlugins`:

```json
{
  "extraKnownMarketplaces": {
    "git-orchestrator": {
      "source": {
        "source": "github",
        "repo": "Ferie-Vincent/claude-git-orchestrator"
      }
    }
  },
  "enabledPlugins": {
    "git-orchestrator@git-orchestrator": true
  }
}
```

The skill becomes available natively via the `Skill` tool and auto-triggers
without needing to read the file manually.

---

## Verify installation

After installing, open Claude Code in any repo and say anything Git-related.
If the skill is active, Claude will run the initialization flow automatically.

You should see something like this — a confirmation that the orchestrator is live:

```
     +        .           *          +           .           *        +
         .          *          +          .            *         .
              *        .           +          *           .          *
                                                       ,---------.
     +    .       *        +        .         +        /  *-,.-*   \     .
     ,--,                                             |  . /|\ .    |
    /    \    *       +        .        *     . . . . | -*-*-*-*-   |  .    +
   /      \       .       +        *       .          |  . \|/ .    |
  |         \  +       *       .       +        +     |   *-'-*     |    +
  |          )     *       .       *       .            \   ~~~    /
  |         /  +       .       +       .       .    .    '---------'  ,^\,
   \       /        *       .       +       *                        (o_o)
    `--,.-'     +       .       +       .            +                ):(
        |            *       .       *       .                       / \
       ,|,    +       .       +       .       *       +       .
       (o)        *       .       *       .       *       .       *
      _/|\_   .       +       .       +       .       +       .       +
     ( ___ )      *       .       *       .       *       .       *
     [_____]  .       +       .       +       .       +       .
```

**git-orchestrator is installed and ready.**

---

## Configuration

Copy a starter config to your project:

```bash
mkdir -p .claude
# Pick one:
curl -o .claude/git-workflow.yml \
  https://raw.githubusercontent.com/Ferie-Vincent/claude-git-orchestrator/main/examples/github-flow.yml

curl -o .claude/git-workflow.yml \
  https://raw.githubusercontent.com/Ferie-Vincent/claude-git-orchestrator/main/examples/git-flow.yml

curl -o .claude/git-workflow.yml \
  https://raw.githubusercontent.com/Ferie-Vincent/claude-git-orchestrator/main/examples/trunk-based.yml
```

Or let Claude generate it: open Claude Code in a repo without
`.claude/git-workflow.yml` and say anything about Git — the skill runs
the initialization flow automatically.

Full field reference: [`docs/configuration.md`](docs/configuration.md)

---

## Absolute rules

The skill enforces these unconditionally:

1. No direct commits to protected branches — PRs only.
2. Every commit follows Conventional Commits.
3. No AI attribution in any commit, PR, branch name, or tag.
4. No emoji in commits unless `gitmoji: true` is configured.
5. No force-push to shared branches.
6. No silent Git actions — every action is shown before execution.
7. Branch names are always kebab-case English.
8. Commit subject max 72 characters, imperative mood, no trailing period.
9. No `git add .` without showing what will be staged.
10. Config file is mandatory — initialization runs if it's missing.

---

## Documentation

| Document | Contents |
|----------|----------|
| [`docs/configuration.md`](docs/configuration.md) | Full config schema with field tables |
| [`docs/branch-naming.md`](docs/branch-naming.md) | Branch naming rules and examples |
| [`docs/conventional-commits.md`](docs/conventional-commits.md) | Commit message rules, types, examples |
| [`docs/pr-templates.md`](docs/pr-templates.md) | Default, release, hotfix, and minimal templates |
| [`docs/mcp-integration.md`](docs/mcp-integration.md) | GitHub/GitLab MCP and CLI integration details |
| [`docs/git-history.md`](docs/git-history.md) | Session history schema and solo-dev value |
| [`docs/decisions.md`](docs/decisions.md) | Architecture Decision Records (WHY behind design choices) |

---

## Uninstalling

**Per-project install:**
```bash
rm .claude/skills/SKILL.md
```

**Global install:**
```bash
rm ~/.claude/skills/git-orchestrator.md
```

**Plugin:**
Remove `git-orchestrator@git-orchestrator` from `enabledPlugins` in `~/.claude/settings.json`.

**Emergency override** (if you need to bypass guardrails for a single commit):
Temporarily remove the branch guard hook from `.claude/settings.json`, commit, then restore it.

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## License

MIT

**Author:** Vincent Ferie — [ekissivincent@gmail.com](mailto:ekissivincent@gmail.com)

---

> This skill is an independent community project and is not affiliated with
> or endorsed by Anthropic.
