---
description: Create git release tags from merged PRs or version args. Pushes a v-prefixed tag to trigger the release pipeline, then confirms the run started.
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

### Step 3: Validate and Normalize

Before creating tags:

- Confirm PR is merged (`merged: true`)
- Validate version follows semver format
- **Normalize to a `v` prefix**: the release pipeline
  (`.github/workflows/cross-framework-publish.yml`) only fires on
  tags matching `v*`. A bare `1.2.0` tag will push successfully but
  silently never trigger a release. Always tag as `v<version>`:
  ```bash
  # Strip any leading v, then re-add it, so 1.2.0 and v1.2.0
  # both become v1.2.0
  TAG="v${VERSION#v}"
  ```
- Verify the normalized tag doesn't already exist: `git tag -l "$TAG"`

### Step 4: Create Tags

For each version/commit pair, using the normalized `$TAG` from
Step 3:

```bash
# Fetch latest from remote
git fetch origin <base-branch>

# Create annotated tag (TAG is v-prefixed, e.g. v1.2.0)
git tag -a "$TAG" <merge_commit_sha> -m "<tag message>"

# Push tag to remote (this is what triggers the release pipeline)
git push origin "$TAG"
```

Tag message format:
```
<version> - merged from PR #<number>

<PR title>
```

### Step 5: Verify Release Pipeline Triggered

Pushing a `v*` tag should start the `cross-framework-publish`
release run. Confirm it actually appeared, then hand the operator a
link to watch it. This is a non-blocking check: report and move on,
do not wait for the run to finish.

```bash
# GitHub reports the tag name as the run's headBranch, so filter
# the workflow runs by the tag we just pushed.
sleep 8  # give GitHub a moment to register the run
RUN_URL=$(gh run list \
  --workflow cross-framework-publish.yml \
  --branch "$TAG" \
  --limit 1 \
  --json url,status \
  -q '.[0].url')

if [ -n "$RUN_URL" ]; then
  echo "Release pipeline triggered: $RUN_URL"
else
  echo "::warning::No release run found for $TAG. Confirm the tag" \
    "matches the v* trigger and that Actions is enabled, then check" \
    "the Actions tab manually."
fi
```

If no run is found, the most likely cause is a tag that does not
match `v*` (see Step 3 normalization) or Actions being disabled for
the repo. Capture `$RUN_URL` for the summary in Step 7.

### Step 6: Run Post-Tag Submissions (Config-Driven)

After the tag is pushed, check for a `tag-submissions.json`
file in the repository root. This file defines which external
repos or scripts to run after tagging. If the file does not
exist, skip this step entirely.

```bash
# Check for config
if [ -f tag-submissions.json ]; then
  # Parse and run each submission script
  for script in $(python3 -c "
import json
for s in json.load(open('tag-submissions.json'))['submissions']:
    print(s['script'])
"); do
    if [ -x "$script" ]; then
      echo "Running: $script <version>"
      ./"$script" <version>
    else
      echo "Warning: $script not found or not executable, skipping"
    fi
  done
else
  echo "No tag-submissions.json found, skipping post-tag submissions"
fi
```

**Config format** (`tag-submissions.json` in repo root):
```json
{
  "submissions": [
    {
      "name": "ClawHub",
      "script": "scripts/clawhub-submit.sh",
      "description": "Submit skills to openclaw/clawhub"
    }
  ]
}
```

Each entry's `script` path is relative to the repo root.
Scripts receive the version tag as their first argument and
use the user's existing `gh auth` session.

### Step 7: Report Results

Display summary table, including the release run from Step 5:

```
| Tag     | PR   | Commit  | Release run | Status |
|---------|------|---------|-------------|--------|
| v1.2.0  | #45  | abc1234 | triggered   | OK     |
| v1.3.0  | #52  | def5678 | triggered   | OK     |
```

Include links to created tags on GitHub, the release run URL
(`$RUN_URL`) so the operator can watch the build-and-release job,
and the ClawHub PR.

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

# Create tag manually (keep the v prefix so the release pipeline fires)
git fetch origin
git tag -a v1.2.0 <merge-commit-sha> -m "v1.2.0 - merged from PR #<number>"
git push origin v1.2.0

# Confirm the release run started
gh run list --workflow cross-framework-publish.yml \
  --branch v1.2.0 --limit 1 --json url -q '.[0].url'
```
