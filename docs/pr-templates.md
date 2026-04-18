# PR / MR Templates Reference

Templates are filled by `git-orchestrator` when creating pull requests or
merge requests. Select the template based on `pull_request.template` in
`.claude/git-workflow.yml` or override per-PR.

---

## Default template

Use for: feature branches, fix branches, any standard PR.

```markdown
## Context

<!-- Why does this PR exist? What problem does it solve? Link to the
issue, spec, or discussion that motivated this work. -->

## Changes

<!-- High-level summary of what changed — not a diff rehash. Group
related changes. -->

-
-
-

## Testing

- [ ] Unit tests added or updated
- [ ] Integration tests added or updated
- [ ] Manually tested in local environment
- [ ] Edge cases considered and covered

## Screenshots

<!-- If this PR affects UI: before/after screenshots or a screen
recording. Delete this section if not applicable. -->

## Related issues

<!-- Closes #N / Refs #N -->
```

---

## Release PR template (Git Flow)

Use for: `release/*` branches being merged into `main` and back into
`develop`.

```markdown
## Release: vX.Y.Z

**Release branch:** `release/X.Y.Z`
**Merging into:** `main` and `develop`

## What's in this release

<!-- Summarize the notable changes included since the last release.
Reference the relevant feature and fix PRs. -->

-
-
-

## Pre-release checklist

- [ ] Version bumped in `package.json` / `pyproject.toml` / equivalent
- [ ] Changelog updated
- [ ] All CI checks passing
- [ ] Release notes drafted
- [ ] QA sign-off obtained

## Post-merge actions

- [ ] Tag created: `git tag -a vX.Y.Z -m "release: vX.Y.Z"`
- [ ] Tag pushed: `git push origin vX.Y.Z`
- [ ] Deployment triggered
- [ ] Stakeholders notified

## Related issues

<!-- Closes #N -->
```

---

## Hotfix PR template (Git Flow)

Use for: `hotfix/*` branches branched from `main`.

```markdown
## Hotfix: <description>

**Severity:** <!-- P0 / P1 / P2 -->
**Affected version(s):** <!-- vX.Y.Z -->
**Hotfix branch:** `hotfix/<description>`

## Problem

<!-- Describe the production issue. Include symptoms, error messages,
and impact scope. -->

## Root cause

<!-- What caused the issue? -->

## Fix

<!-- What change was made and why it resolves the root cause. -->

## Testing

- [ ] Fix verified locally
- [ ] Regression test added to prevent recurrence
- [ ] Tested against production data snapshot (if applicable)

## Deployment notes

<!-- Any migration steps, cache invalidations, feature flag changes, or
manual actions required after deploy. -->

## Related issues

<!-- Closes #N -->
```

---

## Minimal template (Trunk-based)

Use for: short-lived branches in trunk-based development.

```markdown
## Summary

<!-- One paragraph: what changed and why. -->

## Testing

- [ ] Tests pass locally
- [ ] Manually verified

## Related issues

<!-- Closes #N / Refs #N -->
```

---

## Usage rules

- Always fill every section. Delete optional sections explicitly marked
  for deletion rather than leaving them empty.
- The Testing checklist is mandatory in all templates — never remove it.
- Screenshots section: include for any UI change; delete for backend-only
  changes.
- No AI attribution anywhere in the PR body.
- PR titles follow the same Conventional Commits format as commit subjects.
