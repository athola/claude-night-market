---
description: Create git tags from merged PRs or version arguments
usage: /create-tag [version|PR-URL]...
---

# Create Git Tags

Create annotated git tags for releases. Supports multiple modes:

- **Version only**: `/create-tag v1.2.0` - Tags the most recent merged PR with the specified version
- **PR URLs**: `/create-tag <PR-URL1> <PR-URL2>` - Creates tags for each PR, inferring versions from PR content
- **Mixed**: `/create-tag v1.0.5 <PR-URL>` - Explicit version for first, inferred for second
- **No args**: `/create-tag` - Detects version from most recently merged PR

## Workflow

### Step 1: Parse Arguments

Classify each argument:
- **Version**: Matches `v?\d+\.\d+\.\d+` pattern (e.g., `v1.2.0`, `1.2.0`)
- **PR URL**: Contains `github.com/.../pull/\d+` or `#\d+` format
- **No arguments**: Use most recent merged PR on current branch

### Step 2: Gather PR Information

For each PR (explicit or inferred):

1. **Fetch PR details** using GitHub MCP tools:
   ```
   mcp__github__pull_request_read(method="get", owner, repo, pullNumber)
   ```

2. **Extract merge commit SHA** from response:
   - `merge_commit_sha` field contains the commit to tag

3. **Infer version** (if not explicitly provided):
   - Check PR title for version pattern (e.g., "Release v1.2.0", "v1.2.0 update")
   - Check PR body for version references
   - Look for version changes in PR files (package.json, pyproject.toml, plugin.json)
   - If no version found, prompt user for version

### Step 3: Validate

Before creating tags:
- Confirm PR is merged (`merged: true`)
- Verify tag doesn't already exist: `git tag -l <version>`
- validate version follows semver format

### Step 4: Create Tags

For each version/commit pair:

```bash
# Fetch latest from remote
git fetch origin <base-branch>

# Create annotated tag
git tag -a <version> <merge_commit_sha> -m "<tag message>"

# Push tag to remote
git push origin <version>
```

Tag message format:
```
<version> - merged from PR #<number>

<PR title>
```

### Step 5: Report Results

Display summary table:
```
| Tag     | PR   | Commit  | Status |
|---------|------|---------|--------|
| v1.2.0  | #45  | abc1234 | OK     |
| v1.3.0  | #52  | def5678 | OK     |
```

Include links to created tags on GitHub.

## Examples

### Tag most recent merged PR with explicit version
```
/create-tag v1.2.0
```

### Tag multiple PRs with inferred versions
```
/create-tag https://github.com/owner/repo/pull/45 https://github.com/owner/repo/pull/52
```

### Tag single PR with explicit version
```
/create-tag v1.0.5 https://github.com/owner/repo/pull/45
```

### Auto-detect version from latest merged PR
```
/create-tag
```

## Version Inference Logic

When inferring version from a PR:

1. **PR Title** - Extract version from title patterns:
   - "Release v1.2.0"
   - "v1.2.0: Feature update"
   - "Skills update 1.2.0"

2. **PR Body** - Look for version markers:
   - "Version: 1.2.0"
   - "Bumps version to v1.2.0"

3. **Changed Files** - Check version files in PR diff:
   - `package.json`: `"version": "1.2.0"`
   - `pyproject.toml`: `version = "1.2.0"`
   - `plugin.json`: `"version": "1.2.0"`
   - `setup.py`: `version="1.2.0"`

4. **Branch Name** - Extract from branch:
   - `release/v1.2.0`
   - `v1.2.0-release`
   - `version-1.2.0`

If no version can be inferred, prompt user to provide one.

## Error Handling

- **PR not merged**: Skip and warn user
- **Tag exists**: Skip and warn user, offer `--force` to overwrite
- **No version found**: Prompt user interactively
- **Network error**: Retry once, then report failure

## Manual Execution

If GitHub MCP tools are unavailable:

```bash
# Get PR info via gh CLI
gh pr view <PR-NUMBER> --json mergeCommit,merged,title

# Create tag manually
git fetch origin
git tag -a v1.2.0 <merge-commit-sha> -m "v1.2.0 - merged from PR #<number>"
git push origin v1.2.0
```
