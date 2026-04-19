# Architecture Decision Records

Key design decisions for git-orchestrator — the WHY behind each choice.

---

## ADR-001: Squash merge as the only merge strategy

**Decision:** All PRs merge via squash. Rebase and merge-commit are not offered.

**Why:**
The skill targets solo and small-team workflows where the feature branch is a personal
scratchpad. Individual commits on a branch often have messages like "wip", "fix typo",
or "try again" — noise that pollutes `git log --oneline main`. Squash collapses those
into one well-formed Conventional Commit that represents the intent of the change, not
the steps taken to get there.

Rebase would preserve noisy commits. Merge commit would add a synthetic "Merge PR" node
on top of them, making `git bisect` harder without meaningfully improving history quality.

**Trade-off:** Squash loses fine-grained authorship detail per commit. Acceptable for
this context; teams needing commit-level attribution can override `merge.strategy` in
`git-workflow.yml`.

---

## ADR-002: Append-only git-history.json

**Decision:** Session history is written to `.claude/git-history.json` as an append-only
array of objects. Entries are never deleted or rewritten. The file rotates annually.

**Why:**
An append-only log cannot corrupt itself on partial writes — the worst case is a
truncated final entry, which is detectable. A mutable database or overwrite-on-save
approach risks leaving the file in an invalid state if Claude is interrupted mid-write.

The `.tmp` → `rename` atomic write pattern means readers always see either the old file
or the complete new file, never a partial update.

JSON was chosen over SQLite or a flat log because it is human-readable, diff-friendly
in PRs, and requires no dependencies. The schema is simple enough that JSON never becomes
a bottleneck at the scale of a single developer's session history.

Annual rotation caps file size without discarding history: the previous year's file is
kept intact alongside the current one.

**Trade-off:** JSON is slow to query at large scale. At the anticipated volume
(~hundreds of entries per year per developer), this is irrelevant.

---

## ADR-003: Two-file config split (team vs personal identity)

**Decision:** `git-workflow.yml` is committed and holds team-wide rules. Personal
identity (name, email, platform handle) lives exclusively in `git-workflow.local.yml`,
which is gitignored.

**Why:**
Early versions stored everything in one file. This meant every developer had to
remember to un-fill their name and email before committing, or they would expose their
identity in a public repository's git history. This is not a theoretical risk — it
happened in testing.

The split makes the safe path the default path: `git-workflow.local.yml` cannot be
committed even accidentally because `.gitignore` blocks it. The `.example` template
gives new contributors a clear starting point without any sensitive data.

**Trade-off:** Two files to manage instead of one. Mitigated by `bootstrap.sh`, which
creates the local file interactively on first clone.

---

## ADR-004: /tmp flag file for Opsera pre-commit gate

**Decision:** The Opsera security gate uses a flag file at `/tmp/.opsera-pre-commit-scan-passed`
to signal that a scan has passed for the current commit attempt.

**Why this is an accepted risk:**
A flag file in `/tmp` can be set by any process on the machine, including the developer
themselves. This means the gate is bypassable locally. We accept this because:

1. The pre-commit hook is a developer-experience guard, not a security boundary.
2. The real security gate is the CI pipeline (semgrep + gitleaks on GitHub Actions),
   which cannot be bypassed by local flag manipulation.
3. The alternative — a cryptographically signed token from the Opsera MCP server —
   would require network access on every commit, making offline development painful.

**Upgrade path:** If a stronger local gate is required, the hook can be changed to
verify a signed token written by the MCP server instead of a plain flag file. This
would require the Opsera plugin to expose a signing endpoint.

**Compensating control:** CI blocks merges to `main` on any scan failure, regardless
of what happened locally.

---

## ADR-005: SKILL.md auto-trigger (skill-based, not CLI-based)

**Decision:** The orchestrator is implemented as a Claude Code skill (SKILL.md) that
auto-triggers on natural language cues, not as a standalone CLI tool or git hook.

**Why:**
A CLI tool would require installation, PATH configuration, and explicit invocation.
A git hook would run silently and couldn't ask clarifying questions or adapt to context.

The skill approach means the orchestrator can:
- Ask the developer what they meant before acting
- Adapt its behavior based on config (`mode: solo` vs `mode: team`)
- Surface warnings inline in the conversation rather than in a separate terminal pane
- Require zero installation beyond the Claude Code CLI the developer already uses

**Trade-off:** Behavior depends on Claude correctly recognizing trigger phrases. A
deterministic CLI would always fire when called. Mitigated by broad trigger matching
(TRIGGER-1 through TRIGGER-5 cover all common workflow entry points) and a fallback
`/git` command the user can invoke explicitly.

---

## ADR-006: Issue number at the start of the branch description

**Decision:** The only supported issue-linking pattern is `<type>/<number>-<description>`
(e.g. `fix/42-login-redirect`). The number-last pattern (`fix/login-redirect-42`) is
not supported.

**Why:**
`\b(\d+)\b` applied to the full branch segment matches any digit sequence, including
version numbers, dates, or incidental numbers in the description
(`fix/refactor-v2-42-items` would match both `2` and `42`). The "first match wins"
rule is arbitrary and produces surprising behavior.

Anchoring with `^(\d+)-` requires the number to be the very first thing after the
slash. This makes the intent unambiguous: if you put a number first, you mean an issue
reference. Numbers elsewhere in the description are treated as description text.

**Trade-off:** Developers who name branches `fix/description-42` must rename their
habit. The convention is documented in `docs/branch-naming.md` and enforced
consistently — there is no ambiguous middle state.

---

## ADR-007: No AI attribution in commits or PR titles

**Decision:** The skill does not add "Co-authored-by: Claude" or any AI attribution
to commit messages, PR titles, or branch names.

**Why:**
Attribution in commits is a permanent, public record. Adding AI attribution:
- Conflates the tool with the author (the developer owns the decision, Claude executes it)
- May trigger AI-content policies in some organizations
- Pollutes `git log` with noise unrelated to the change itself

The developer chose to use this tool the same way they chose to use their IDE or
linter — the IDE is not credited in commits.

**Trade-off:** Loss of transparency about AI involvement in a commit. Teams that want
this can add it via a custom commit template or a `footer` field in `git-workflow.yml`.
