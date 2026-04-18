# MCP Integration Reference

`git-orchestrator` uses a priority chain to interact with GitHub and GitLab.
Try each level in order; stop at the first that works.

## GitHub

### Level 1 — GitHub MCP

Check for available tools matching the pattern `mcp__github__*`.

If present, use:
- `mcp__github__create_pull_request` — create PR
- `mcp__github__get_pull_request` — fetch PR status
- `mcp__github__list_pull_requests` — list open PRs
- `mcp__github__merge_pull_request` — merge PR
- `mcp__github__create_issue` — create issue
- `mcp__github__add_pull_request_review_comment` — add review comment

### Level 2 — `gh` CLI

If GitHub MCP is unavailable, check for `gh` in `$PATH`:

```bash
gh pr create \
  --title "feat(auth): add JWT authentication" \
  --body "$(cat pr-body.md)" \
  --base main \
  --head feature/user-auth \
  --draft
```

Useful commands:

```bash
gh pr view                     # view current branch PR
gh pr list --state open        # list open PRs
gh pr merge --squash --delete-branch
gh pr review --approve
gh pr checks                   # CI status
```

### Level 3 — URL generation

If neither MCP nor CLI is available, generate the PR creation URL and
display it to the user:

```
https://github.com/<owner>/<repo>/compare/main...<branch>?expand=1
```

---

## GitLab

### Level 1 — GitLab MCP

Check for available tools matching `mcp__gitlab__*`.

If present, use:
- `mcp__gitlab__create_merge_request` — create MR
- `mcp__gitlab__get_merge_request` — fetch MR status
- `mcp__gitlab__list_merge_requests` — list open MRs
- `mcp__gitlab__merge_merge_request` — merge MR

### Level 2 — `glab` CLI

```bash
glab mr create \
  --title "feat(auth): add JWT authentication" \
  --description "$(cat mr-body.md)" \
  --target-branch main \
  --source-branch feature/user-auth \
  --draft
```

Useful commands:

```bash
glab mr view                   # view current branch MR
glab mr list --state opened    # list open MRs
glab mr merge --squash --remove-source-branch
glab pipeline status           # CI status
```

### Level 3 — URL generation

```
https://gitlab.com/<owner>/<repo>/-/merge_requests/new?merge_request[source_branch]=<branch>&merge_request[target_branch]=main
```

---

## Error handling

| Error | Behavior |
|-------|----------|
| Auth failure (401/403) | Surface the exact error message. Do not retry. Instruct user to run `gh auth login` or `glab auth login`. |
| Rate limit (429) | Surface the error and the `X-RateLimit-Reset` timestamp if available. Do not retry automatically. |
| Network timeout | Surface the error. Do not retry. |
| PR already exists | Surface the existing PR URL. Do not attempt to create a duplicate. |
| Branch not pushed | Run `git push -u origin <branch>` first, then retry the PR/MR creation. |

## Authentication assumptions

- For `gh`: `gh auth status` returns exit code 0.
- For `glab`: `glab auth status` returns exit code 0.
- For MCPs: the MCP server is pre-authenticated via its own config.

Never ask the user for tokens, passwords, or API keys.
