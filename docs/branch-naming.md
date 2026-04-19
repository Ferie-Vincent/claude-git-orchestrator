# Branch Naming Reference

## Default convention

```
<type>/<description>
```

`type` must be one of the values in the table below. `description` is
kebab-case, lowercase, English only, no special characters except hyphens.

| Type | Use when |
|------|----------|
| `feature` | Adding new functionality |
| `fix` | Correcting a defect |
| `docs` | Documentation-only changes |
| `chore` | Maintenance, dependency updates, tooling |
| `refactor` | Code restructuring without behavior change |
| `test` | Adding or updating tests |
| `perf` | Performance improvements |
| `ci` | CI/CD pipeline changes |
| `build` | Build system or compilation changes |

### Examples

```
feature/user-authentication
fix/login-redirect-loop
docs/api-reference-update
chore/upgrade-dependencies
refactor/extract-payment-service
test/add-cart-unit-tests
perf/reduce-image-load-time
ci/add-coverage-report
build/migrate-to-vite
```

## Issue linking convention

When a branch relates to a tracked issue, embed the issue number in the
description. The skill auto-detects it and injects `Closes #N` in the PR body.

```
<type>/<number>-<description>
```

| Example branch | Detected issue | PR footer injected |
|----------------|---------------|-------------------|
| `fix/42-login-redirect` | #42 | `Closes #42` |
| `feature/123-user-dashboard` | #123 | `Closes #123` |
| `chore/8-upgrade-deps` | #8 | `Closes #8` |

The number must appear at the **start** of the description segment (regex: `^(\d+)-`).
Numbers embedded mid-description (e.g. `fix/login-42-redirect`) are not detected.
If no match is found, linking is silently skipped (unless `require_issue_ref: true` in config).

## Trunk-based convention

When `trunk_based.username_prefix: true` is set:

```
<username>/<description>
```

No type prefix. Description is still kebab-case, lowercase, English.

### Examples

```
vferie/user-auth
vferie/fix-login-redirect
vferie/update-api-docs
```

## Git Flow special branches

These branch names are fixed and must not be renamed:

| Branch | Purpose |
|--------|---------|
| `main` | Production releases |
| `develop` | Integration branch |
| `release/<version>` | Release preparation |
| `hotfix/<description>` | Emergency production fixes |
| `support/<version>` | Long-term support maintenance |

## Absolute rules

- Always lowercase.
- Always kebab-case (`-` separators, not `_` or spaces).
- Always English.
- Issue numbers are optional. When used, place them at the start of the
  description: `<type>/<number>-<description>`. See Issue linking convention above.
- Max recommended length: 50 characters total (excluding the type prefix).
- Never reuse a branch name for unrelated work.
