# Complete Command Mapping

Full cross-platform command equivalents for forge operations.

## Issue Operations

| Operation | GitHub (`gh`) | GitLab (`glab`) | Bitbucket (REST API) |
|-----------|---------------|-----------------|----------------------|
| View | `gh issue view N --json title,body,labels,assignees,comments` | `glab issue view N` | `curl -s "https://api.bitbucket.org/2.0/repositories/OWNER/REPO/issues/N"` |
| List | `gh issue list --json number,title` | `glab issue list` | `curl -s "https://api.bitbucket.org/2.0/repositories/OWNER/REPO/issues"` |
| Create | `gh issue create --title "T" --body "B"` | `glab issue create --title "T" --description "B"` | `curl -X POST -d '{"title":"T","content":{"raw":"B"}}' "https://api.bitbucket.org/2.0/repositories/OWNER/REPO/issues"` |
| Close | `gh issue close N --comment "reason"` | `glab issue close N` | `curl -X PUT -d '{"state":"resolved"}' ".../issues/N"` |
| Comment | `gh issue comment N --body "msg"` | `glab issue note N --message "msg"` | `curl -X POST -d '{"content":{"raw":"msg"}}' ".../issues/N/comments"` |
| Search | `gh issue list --search "query"` | `glab issue list --search "query"` | N/A (filter client-side) |

## PR/MR Operations

| Operation | GitHub (`gh`) | GitLab (`glab`) |
|-----------|---------------|-----------------|
| Create | `gh pr create --title "T" --body "B"` | `glab mr create --title "T" --description "B"` |
| View | `gh pr view N --json number,title,body,state` | `glab mr view N` |
| List | `gh pr list` | `glab mr list` |
| Diff | `gh pr diff N` | `glab mr diff N` |
| Merge | `gh pr merge N` | `glab mr merge N` |
| Close | `gh pr close N` | `glab mr close N` |
| Review | `gh pr review N --approve` | `glab mr approve N` |
| Comments | `gh api repos/O/R/pulls/N/comments` | `glab api projects/ID/merge_requests/N/notes` |
| Current | `gh pr view --json number,url -q '.number'` | `glab mr view --json iid -q '.iid'` |

## GraphQL Operations

### GitHub
```bash
gh api graphql -f query='
query {
  repository(owner: "OWNER", name: "REPO") {
    pullRequest(number: N) {
      reviewThreads(first: 100) {
        nodes { id isResolved path }
      }
    }
  }
}'
```

### GitLab
```bash
glab api graphql -f query='
query {
  project(fullPath: "OWNER/REPO") {
    mergeRequest(iid: "N") {
      discussions { nodes { id resolved notes { nodes { body } } } }
    }
  }
}'
```

## CI/CD Configuration

| Feature | GitHub Actions | GitLab CI | Bitbucket Pipelines |
|---------|---------------|-----------|---------------------|
| Config file | `.github/workflows/*.yml` | `.gitlab-ci.yml` | `bitbucket-pipelines.yml` |
| Trigger syntax | `on: push` | `rules: - if:` | `pipelines: branches:` |
| Secret access | `${{ secrets.NAME }}` | `$NAME` (CI variable) | `$NAME` (repository variable) |
| Artifact upload | `actions/upload-artifact` | `artifacts: paths:` | `artifacts:` |

## Repo Metadata

| Operation | GitHub | GitLab |
|-----------|--------|--------|
| Owner/name | `gh repo view --json owner,name -q '"\(.owner.login)/\(.name)"'` | `glab repo view --json path_with_namespace -q '.path_with_namespace'` |
| Default branch | `gh repo view --json defaultBranchRef -q '.defaultBranchRef.name'` | `glab repo view --json default_branch -q '.default_branch'` |
| Labels | `gh label list` | `glab label list` |
