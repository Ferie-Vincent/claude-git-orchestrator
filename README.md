# git-orchestrator

A Claude Code skill that manages the full Git lifecycle — branching, commits,
PRs, and merges — with enforced conventions, so your team never debates
commit format or PR hygiene again.

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

### Option 1 — Per-project (recommended, shared with team)

```bash
mkdir -p .claude/skills
curl -o .claude/skills/SKILL.md \
  https://raw.githubusercontent.com/Ferie-Vincent/claude-git-orchestrator/main/SKILL.md
```

Commit `SKILL.md` to your repository so the whole team benefits.

### Option 2 — Personal (applies to all your projects)

```bash
mkdir -p ~/.claude/skills
curl -o ~/.claude/skills/git-orchestrator.md \
  https://raw.githubusercontent.com/Ferie-Vincent/claude-git-orchestrator/main/SKILL.md
```

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
