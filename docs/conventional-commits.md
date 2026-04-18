# Conventional Commits Reference

All commits in a repository managed by `git-orchestrator` must conform to
the [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
specification as interpreted here.

## Anatomy of a commit message

```
<type>[optional scope]: <subject>

[optional body]

[optional footer(s)]
```

### Subject line rules

| Rule | Detail |
|------|--------|
| Max length | 72 characters (including type and scope) |
| Case | Lowercase first letter of the description |
| Mood | Imperative ("add feature", not "added feature" or "adds feature") |
| Trailing period | Forbidden |
| Language | English always |

### Allowed types

| Type | When to use |
|------|-------------|
| `feat` | New feature visible to the user |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, whitespace — no logic change |
| `refactor` | Code restructuring — no behavior change, no bug fix |
| `perf` | Performance improvement |
| `test` | Adding or correcting tests |
| `build` | Build system, dependencies, tooling |
| `ci` | CI/CD configuration |
| `chore` | Maintenance tasks that don't fit above |
| `revert` | Reverts a previous commit |

### Scope

Optional. Identifies the subsystem affected. Lowercase, single word or
hyphenated. Examples: `auth`, `api`, `payment`, `ui`, `db`.

```
feat(auth): add refresh token rotation
fix(payment): handle stripe webhook timeout
```

### Body

Optional. Explains **why**, not what (the diff shows what). Wrap at 72
characters. Separate from the subject with one blank line.

### Footer

Optional. Two standard uses:

**Issue references:**
```
Refs #42
Closes #17
Fixes #88
```

**Breaking changes:**
```
BREAKING CHANGE: the `login` endpoint now requires an `Authorization` header
```

## Complete examples

Minimal:
```
feat: add CSV export to the reports page
```

With scope:
```
fix(auth): prevent session fixation after password reset
```

With body and footer:
```
refactor(db): replace raw SQL with query builder

The previous approach concatenated strings directly into queries, which
made parameterization inconsistent and hard to audit. The query builder
enforces parameterized queries by construction.

Refs #301
```

Breaking change:
```
feat(api)!: require API version header on all requests

All requests to the REST API must now include `X-Api-Version: 2` header.
Clients omitting this header receive 400.

BREAKING CHANGE: requests without X-Api-Version are rejected
```

## Absolutely forbidden

- AI model names anywhere in the commit message.
- "Co-authored-by: Claude" or any AI attribution in any footer.
- Emoji anywhere in the message unless `commits.gitmoji: true` is set in
  `.claude/git-workflow.yml`.
- Sentences in past tense ("fixed", "added") or present-continuous ("fixing").
- Subject lines over 72 characters.
- Trailing period at the end of the subject.

## Validation checklist

Before finalizing a commit, verify:

- [ ] Type is in the allowed list.
- [ ] Subject is imperative mood, lowercase start, no trailing period.
- [ ] Subject is 72 characters or fewer.
- [ ] Body (if present) is wrapped at 72 characters.
- [ ] Footer (if present) uses correct format.
- [ ] No forbidden strings present.
