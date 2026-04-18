# Configuration Reference

All configuration lives in `.claude/git-workflow.yml` at the repository root.
Run the initialization flow (invoke the `git-orchestrator` skill with no config
present) to generate this file interactively.

## Schema

### Top-level fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `version` | integer | yes | — | Schema version. Currently `1`. |
| `language` | string | yes | `en` | UI language for confirmations and explanations. Commit messages are always English. Supported: `en`, `fr`, `es`, `de`, `pt`. |
| `platform` | string | yes | auto-detected | Hosting platform. One of: `github`, `gitlab`, `bitbucket`, `azure-devops`. |
| `workflow` | string | yes | `github-flow` | Git branching workflow. One of: `github-flow`, `git-flow`, `trunk-based`, `custom`. |
| `branches` | object | yes | — | Branch naming and structure configuration. |
| `commits` | object | yes | — | Commit message rules. |
| `merge` | object | yes | — | Merge strategy settings. |
| `pull_request` | object | yes (GitHub/Bitbucket) | — | PR configuration. Use `merge_request` for GitLab. |
| `merge_request` | object | yes (GitLab only) | — | MR configuration. Alias of `pull_request` for GitLab. |
| `protected_branches` | array | yes | `[main]` | Branch patterns that cannot receive direct commits. |
| `git_flow` | object | no | — | Git Flow-specific settings. Only read when `workflow: git-flow`. |
| `trunk_based` | object | no | — | Trunk-based-specific settings. Only read when `workflow: trunk-based`. |

---

### `branches`

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `main` | string | yes | `main` | Name of the main/production branch. |
| `develop` | string | no | `develop` | Name of the integration branch (Git Flow only). |
| `prefix` | object | no | see below | Maps branch type to its prefix string. |

**Default `prefix` values:**

| Type | Default prefix |
|------|---------------|
| `feature` | `feature/` |
| `fix` | `fix/` |
| `docs` | `docs/` |
| `chore` | `chore/` |
| `refactor` | `refactor/` |
| `test` | `test/` |
| `perf` | `perf/` |
| `ci` | `ci/` |
| `build` | `build/` |

For trunk-based workflows, branches use `<username>/<description>` format.
Set `prefix` to an empty object `{}` and configure `trunk_based.username_prefix: true`.

---

### `commits`

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `max_subject_length` | integer | no | `72` | Maximum characters in the commit subject line. |
| `gitmoji` | boolean | no | `false` | Allow emoji at the start of commit subjects. Enables gitmoji convention. |
| `types` | array | no | see below | Allowed commit type tokens. |

**Default `types`:**
`feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

---

### `merge`

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `strategy` | string | yes | `merge` | How PRs/MRs are merged. One of: `merge`, `squash`, `rebase`. |
| `delete_branch_on_merge` | boolean | no | `true` | Delete the source branch after a successful merge. |

---

### `pull_request` / `merge_request`

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `template` | string | no | `default` | Template variant. One of: `default`, `release`, `hotfix`, `minimal`. |
| `draft_by_default` | boolean | no | `false` | Open new PRs/MRs as drafts. |
| `require_issue_ref` | boolean | no | `false` | Require a `Closes #N` or `Refs #N` footer in the PR body. |

---

### `protected_branches`

Array of exact branch names or glob patterns. Any branch matching a pattern
in this list cannot receive direct commits — changes must go through a PR/MR.

```yaml
protected_branches:
  - main
  - develop
  - release/*
```

---

### `git_flow`

Only read when `workflow: git-flow`.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `release_prefix` | string | no | `release/` | Prefix for release branches. |
| `hotfix_prefix` | string | no | `hotfix/` | Prefix for hotfix branches. |
| `support_prefix` | string | no | `support/` | Prefix for long-term support branches. |
| `version_tag_prefix` | string | no | `v` | Prefix added before version numbers in tags. |

---

### `trunk_based`

Only read when `workflow: trunk-based`.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `username_prefix` | boolean | no | `false` | Use `<username>/<description>` branch naming instead of type-based prefixes. |
| `max_branch_age_days` | integer | no | `2` | Warn when a feature branch is older than this many days. |
| `feature_flags_required` | boolean | no | `false` | Remind the user to wrap new features in a feature flag. |

---

## Complete example

```yaml
version: 1
language: en
platform: github
workflow: git-flow

branches:
  main: main
  develop: develop
  prefix:
    feature: feature/
    fix: fix/
    docs: docs/
    chore: chore/
    refactor: refactor/
    test: test/
    perf: perf/
    ci: ci/
    build: build/

commits:
  max_subject_length: 72
  gitmoji: false
  types:
    - feat
    - fix
    - docs
    - style
    - refactor
    - perf
    - test
    - build
    - ci
    - chore
    - revert

merge:
  strategy: squash
  delete_branch_on_merge: true

pull_request:
  template: default
  draft_by_default: false
  require_issue_ref: true

protected_branches:
  - main
  - develop
  - release/*

git_flow:
  release_prefix: release/
  hotfix_prefix: hotfix/
  support_prefix: support/
  version_tag_prefix: v
```
