# Workflow Integration Examples

Examples of integrating the interactive authentication module into existing workflows.

## Pattern: Pre-Flight Authentication Check

Add authentication check at the start of any workflow requiring external service access.

### Before: Manual Auth Check

```bash
# Old way - manual check, unclear error handling
if ! gh auth status &>/dev/null; then
  echo "Error: Not authenticated"
  echo "Run: gh auth login"
  exit 1
fi

gh pr view 123
```

### After: Interactive Auth with Caching

```bash
# New way - interactive auth with caching
source plugins/leyline/scripts/interactive_auth.sh

ensure_auth github || exit 1

gh pr view 123
```

## Example 1: PR Review Command

```bash
#!/usr/bin/env bash
# /pr-review command

# Source interactive auth
source plugins/leyline/skills/authentication-patterns/modules/interactive_auth.sh

# Ensure GitHub authentication
if ! ensure_auth github; then
  echo "❌ GitHub authentication required for PR review"
  exit 1
fi

# Get PR number
PR_NUMBER="${1:-$(gh pr view --json number -q .number)}"

# Continue with workflow
echo "Reviewing PR #$PR_NUMBER..."
gh pr view "$PR_NUMBER"
gh api "repos/owner/repo/pulls/$PR_NUMBER/comments"
```

**Benefits:**
- ✅ User is prompted to authenticate if needed
- ✅ Auth status cached for 5 minutes
- ✅ Session persists for 24 hours
- ✅ Works in CI/CD with `GITHUB_TOKEN`

## Example 2: Create Issue Command

```bash
#!/usr/bin/env bash
# /create-issue command

source plugins/leyline/skills/authentication-patterns/modules/interactive_auth.sh

# Ensure authentication
if ! ensure_auth github; then
  echo "❌ GitHub authentication required to create issues"
  exit 1
fi

# Parse arguments
TITLE="$1"
shift

# Create issue
gh issue create --title "$TITLE" "$@"
```

## Example 3: Multi-Service Workflow

```bash
#!/usr/bin/env bash
# Sync issues from GitHub to GitLab

source plugins/leyline/skills/authentication-patterns/modules/interactive_auth.sh

# Authenticate both services
ensure_auth github || exit 1
ensure_auth gitlab || exit 1

# Sync issues
gh issue list --json number,title | \
  jq -r '.[] | "\(.number)|\(.title)"' | \
  while IFS='|' read -r num title; do
    glab issue create --title "gh-$num: $title"
  done
```

## Example 4: Batch Operations with Wrapper Functions

```bash
#!/usr/bin/env bash
# Batch PR operations

source plugins/leyline/skills/authentication-patterns/modules/interactive_auth.sh

# Use wrapper functions for cleaner code
gh_api_with_auth "repos/owner/repo/pulls" | \
  jq -r '.[].number' | \
  while read -r pr_num; do
    gh_with_auth pr view "$pr_num"
  done
```

## Example 5: CI/CD Pipeline Integration

```yaml
# .github/workflows/pr-review.yml
name: PR Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Claude Code plugins
        run: |
          # Plugin setup here
          :

      - name: Run PR Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          AUTH_INTERACTIVE: false  # Force non-interactive mode
        run: |
          source plugins/leyline/skills/authentication-patterns/modules/interactive_auth.sh

          # Will use GITHUB_TOKEN from environment
          if ! ensure_auth github; then
            echo "GitHub authentication failed"
            exit 1
          fi

          # Run review
          /pr-review ${{ github.event.pull_request.number }}
```

**Key Points:**
- `AUTH_INTERACTIVE=false` forces non-interactive mode
- `GITHUB_TOKEN` is used automatically (GitHub Actions provides it)
- No browser prompts in CI/CD environment

## Example 6: Fix PR Command Integration

```bash
#!/usr/bin/env bash
# /fix-pr command

source plugins/leyline/skills/authentication-patterns/modules/interactive_auth.sh

# Ensure authentication before starting workflow
if ! ensure_auth github; then
  cat << 'EOF'
❌ GitHub Authentication Required

This workflow requires GitHub API access to:
- Fetch PR details and review comments
- Post replies to review threads
- Resolve review threads
- Create issues for deferred items

Please authenticate to continue.
EOF
  exit 1
fi

# Continue with workflow
PR_NUMBER="${1:-$(gh pr view --json number -q .number)}"

echo "Processing PR #$PR_NUMBER..."
# ... rest of workflow
```

## Migration Checklist

When updating existing workflows to use interactive auth:

- [ ] Add `source` line at the top of the script
- [ ] Replace `gh auth status` checks with `ensure_auth github`
- [ ] Add informative error messages if auth fails
- [ ] Test interactive authentication flow
- [ ] Test CI/CD compatibility with `AUTH_INTERACTIVE=false`
- [ ] Update workflow documentation

## Advanced: Custom Cache Configuration

```bash
#!/usr/bin/env bash
# Long-running workflow with extended cache

source plugins/leyline/skills/authentication-patterns/modules/interactive_auth.sh

# Extend cache to 1 hour for long-running workflow
export AUTH_CACHE_TTL=3600

# Initial authentication
ensure_auth github || exit 1

# ... operations that take a long time ...

# Later in workflow - uses cached auth (fast)
ensure_auth github  # Skips check if within 1 hour
```

## Error Handling Pattern

```bash
#!/usr/bin/env bash
source plugins/leyline/skills/authentication-patterns/modules/interactive_auth.sh

# Wrapper for error handling
run_authenticated_command() {
  local service="$1"
  shift

  if ! ensure_auth "$service"; then
    return 1
  fi

  "$@"
}

# Usage
if ! run_authenticated_command github gh pr view 123; then
  echo "Failed to fetch PR details"
  exit 1
fi
```

## Testing the Integration

### Test Interactive Flow

```bash
# 1. Ensure not authenticated
gh auth logout || true
clear_all_auth_cache

# 2. Run workflow - should prompt for auth
/test-workflow.sh

# 3. Verify session created
cat ~/.cache/claude-auth/github/session.json

# 4. Run again - should use session (no prompt)
/test-workflow.sh
```

### Test CI/CD Flow

```bash
# Test non-interactive mode
export AUTH_INTERACTIVE=false
export GITHUB_TOKEN="ghp_..."

source plugins/leyline/skills/authentication-patterns/modules/interactive_auth.sh

ensure_auth github  # Should use GITHUB_TOKEN, no prompt
```

### Test Cache Expiration

```bash
# Set short TTL for testing
export AUTH_CACHE_TTL=10

ensure_auth github  # Initial auth
ensure_auth github  # Uses cache (fast)

sleep 11

ensure_auth github  # Cache expired, re-validates
```

## Benefits Summary

| Aspect | Before | After |
|--------|--------|-------|
| **User Experience** | Silent failure or manual instructions | Interactive OAuth prompt |
| **Caching** | No caching | 5-minute auth cache |
| **Sessions** | No persistence | 24-hour session |
| **CI/CD Support** | Manual env var setup | Auto-detects and uses env vars |
| **Multi-Service** | Separate checks for each | Unified interface |
| **Error Messages** | Generic errors | Clear, actionable messages |
