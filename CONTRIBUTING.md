# Contributing to git-orchestrator

Contributions are welcome. Read this document before opening a PR.

---

## Ground rules

1. **No AI attribution anywhere.** No "Co-authored-by: Claude", no
   "AI-generated", no model names in commits, PR descriptions, code
   comments, or documentation. This is rule #1 and is non-negotiable.
2. Follow the project's own conventions — this repo uses `git-orchestrator`
   and `.claude/git-workflow.yml`.
3. Keep SKILL.md under 500 lines. Refactor rather than append.
4. Every change to behavior must be reflected in the relevant reference doc
   under `docs/`.

---

## What we welcome

### High priority

| Contribution | Notes |
|-------------|-------|
| New language support | Add the language code and translation notes to SKILL.md and docs |
| New platform support | Bitbucket, Azure DevOps — follow the MCP → CLI → URL pattern in `docs/mcp-integration.md` |
| New workflow variants | Document in `docs/configuration.md`, add an example config |
| Bug fixes | Incorrect behavior, edge cases, broken fallback chains |

### Lower priority

| Contribution | Notes |
|-------------|-------|
| Cosmetic rewording | Minor prose improvements accepted if they improve clarity |
| Additional examples | More starter configs for common setups |

### Not accepted

- Removing the confirmation requirement from any lifecycle trigger.
- Adding AI attribution in any form.
- Making force-push the default for any scenario.
- Reducing the scope of protected-branch enforcement.
- Changes that make SKILL.md exceed 500 lines without removing equivalent content.

---

## Development workflow

1. **Fork** the repository on GitHub.
2. **Create a branch** following the project's convention:
   ```
   feature/<description>
   fix/<description>
   docs/<description>
   ```
3. **Make your changes.** See Testing below.
4. **Open a PR** against `main` using the default PR template.

---

## Testing

`git-orchestrator` is a markdown-based skill — there is no compiled
artifact to test. Testing is manual scenario walkthrough.

For each change, verify the following scenarios:

### Scenario 1 — New work

Open Claude Code in a repo with `.claude/git-workflow.yml` present. Say:
"let's add a login page." Verify:
- Skill triggers without being named.
- Branch name follows `docs/branch-naming.md`.
- Confirmation is shown before branch creation.
- Branch is created only after confirmation.

### Scenario 2 — Commit

After modifying a file, say "commit this." Verify:
- `git status` and `git diff --stat` are shown.
- Proposed commit message is Conventional Commits-conformant.
- User can edit the message before confirming.
- Staged files are listed explicitly (no silent `git add .`).

### Scenario 3 — PR creation

After committing, say "open a PR." Verify:
- Branch is pushed before PR creation.
- PR body matches the configured template.
- Platform priority chain is followed (MCP → CLI → URL).

### Scenario 4 — Protected branch enforcement

Attempt to commit directly to `main`. Verify the skill refuses and
redirects to a PR flow.

### Scenario 5 — Initialization

Delete `.claude/git-workflow.yml`. Open Claude Code and say anything
about Git. Verify initialization flow runs and produces a valid config
file.

---

## PR guidelines

- Title must follow Conventional Commits format.
- Fill every section of the default PR template.
- Reference an issue or discussion if one exists.
- Keep PRs focused — one concern per PR.
- Squash your commits to a clean history before requesting review.
