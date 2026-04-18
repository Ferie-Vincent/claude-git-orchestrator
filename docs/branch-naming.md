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
- No ticket numbers unless required by team convention — and if used, put them
  in the commit footer, not the branch name.
- Max recommended length: 50 characters total (excluding the type prefix).
- Never reuse a branch name for unrelated work.
