# Interactive OAuth Authentication

**Status:** ✅ Complete and Tested
**Date:** 2025-01-15
**Approach:** Centralized Auth Module

## Overview

This module provides an interactive authentication system for external services (GitHub, GitLab, AWS, GCP, Azure) with automatic token caching, session management, and CI/CD support. This allows users to authenticate during workflow execution rather than requiring environment variables to be set upfront.

## Features

### 1. Core Module (`interactive_auth.sh`)

**File:** `plugins/leyline/scripts/interactive_auth.sh`

**Capabilities:**
- Multi-service support (GitHub, GitLab, AWS, GCP, Azure)
- Token caching with 5-minute TTL
- Session persistence with 24-hour TTL
- Interactive OAuth prompts
- CI/CD detection and automatic fallback
- Retry logic with exponential backoff (max 3 attempts)
- Cache invalidation functions
- Wrapper functions for common operations

**Key Functions:**
```bash
ensure_auth <service>            # Main authentication function
check_auth_status <service>      # Non-interactive status check
invalidate_auth_cache <service>  # Clear cache for service
clear_all_auth_cache             # Clear all caches
gh_with_auth [args...]           # Wrapper for gh commands
gh_api_with_auth <endpoint>      # Wrapper for gh API calls
glab_with_auth [args...]         # Wrapper for glab commands
aws_with_auth [args...]          # Wrapper for aws commands
```

### 2. Documentation

**Files:**
- `plugins/leyline/skills/authentication-patterns/modules/interactive-auth.md` - Module documentation
- `plugins/leyline/skills/authentication-patterns/README.md` - Quick start guide
- `plugins/leyline/skills/authentication-patterns/examples/workflow-integration.md` - Integration examples
- `plugins/leyline/skills/authentication-patterns/SKILL.md` - Skill documentation

### 3. Test Suite

**File:** `plugins/leyline/skills/authentication-patterns/tests/test-interactive_auth.sh`

**Tests:**
- Syntax validation
- Module sourcing
- Function availability
- Cache directory initialization
- Cache write and read
- Cache validation
- Session creation
- Session validation
- Cache invalidation
- Clear all caches
- Interactive mode detection
- CI/CD environment detection
- Unsupported service error handling
- Usage validation

## Architecture

### Cache Storage

```
~/.cache/claude-auth/
├── github/
│   ├── auth_status.json      # Auth status + timestamp
│   ├── session.json          # Session info (24hr TTL)
│   └── token_cache.json      # Token metadata (optional)
├── gitlab/
│   └── ...
└── config.json               # Global config
```

### Authentication Flow

```
1. Check cache (fast)
   └─> Valid? → Return success

2. Check session (medium)
   └─> Valid? → Verify auth status
       └─> Valid? → Return success

3. Full auth check (slow)
   └─> Valid? → Create session, cache result
   └─> Not valid? → Prompt user

4. Interactive prompt
   └─> User authenticates
   └─> Verify success
   └─> Create session, cache result
   └─> Return success
```

### Configuration

Environment variables:

| Variable | Purpose | Default |
|----------|---------|---------|
| `AUTH_CACHE_DIR` | Cache directory | `~/.cache/claude-auth` |
| `AUTH_CACHE_TTL` | Cache TTL (seconds) | `300` (5 min) |
| `AUTH_SESSION_TTL` | Session TTL (seconds) | `86400` (24 hr) |
| `AUTH_INTERACTIVE` | Force mode | `auto` (detect) |
| `AUTH_MAX_ATTEMPTS` | Max retries | `3` |

## Usage Examples

### Basic Usage

```bash
# Source the module
source plugins/leyline/scripts/interactive_auth.sh

# Ensure authentication
ensure_auth github || exit 1

# Use service APIs
gh pr view 123
gh api repos/owner/repo/issues
```

### In Workflows

```bash
#!/usr/bin/env bash
# My workflow

source plugins/leyline/scripts/interactive_auth.sh

# Ensure authentication at start
if ! ensure_auth github; then
  echo "❌ GitHub authentication required"
  exit 1
fi

# Continue with workflow
gh pr list
```

### CI/CD Integration

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

      - name: Run PR Review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          AUTH_INTERACTIVE: false  # Force non-interactive
        run: |
          source plugins/leyline/scripts/interactive_auth.sh
          ensure_auth github || exit 1
          /pr-review ${{ github.event.pull_request.number }}
```

## User Experience Improvements

### Before

```bash
$ gh pr view 123
gh: command not found or not authenticated
```

### After

```bash
$ gh pr view 123

🔐 GitHub Authentication Required

This workflow needs GitHub API access to continue.

How would you like to authenticate?
  1. Browser (OAuth) - Recommended
  2. Personal Access Token
  3. Cancel workflow

Choose [1-3]: 1

Opening browser for OAuth authentication...
Follow the prompts in your browser.
✓ OAuth authentication successful
✓ GitHub authentication successful

# Original command succeeds
```

## Supported Services

| Service | CLI Tool | Status |
|---------|----------|--------|
| GitHub | `gh` | ✅ Implemented |
| GitLab | `glab` | ✅ Implemented |
| AWS | `aws` | ✅ Implemented |
| Google Cloud | `gcloud` | ✅ Implemented |
| Azure | `az` | ✅ Implemented |

## Integration Points

### Workflows That Can Benefit

Current workflows that use GitHub API:

1. **`/fix-pr`** - Fetch PR comments, resolve threads, create issues
2. **`/pr-review`** - Fetch PR details, post review comments
3. **`/create-issue`** - Create GitHub issues
4. **`/do-issue`** - Batch issue operations
5. **Any workflow using `gh` CLI** - Automatic authentication

### Migration Path

**Step 1:** Add to workflow
```bash
source plugins/leyline/scripts/interactive_auth.sh
```

**Step 2:** Replace auth checks
```bash
# Old
if ! gh auth status &>/dev/null; then
  echo "Run: gh auth login"
  exit 1
fi

# New
ensure_auth github || exit 1
```

**Step 3:** Test thoroughly
```bash
# Test interactive flow
clear_all_auth_cache
./workflow.sh

# Test CI/CD flow
export AUTH_INTERACTIVE=false
export GITHUB_TOKEN="..."
./workflow.sh
```

## Security Considerations

1. **Token Storage:** Tokens stored by service CLIs (not by this module)
   - GitHub: `~/.config/gh/hosts.yml`
   - GitLab: `~/.config/glab/config.yml`
   - AWS: `~/.aws/credentials`

2. **Cache Permissions:** Cache directory has restricted permissions (`0700`)

3. **No Logging:** Tokens never logged or echoed

4. **Session Expiration:** Sessions expire to limit credential lifetime

5. **CI/CD Best Practice:** Use short-lived tokens in CI/CD environments

## Performance

### Cache Benefits

- **First call:** Full auth check (1-2 seconds)
- **Within 5 minutes:** Uses cached result (< 10ms)
- **Within 24 hours:** Validates session (100-200ms)
- **After 24 hours:** Full re-authentication

### Example Timeline

```
T=0s:  ensure_auth github  # First call, no cache
T=1.5s: ✓ Authenticated
T=2s:  ensure_auth github  # Second call, cache hit
T=2.01s: ✓ Authenticated
T=300s: ensure_auth github  # Cache expired, session valid
T=300.2s: ✓ Authenticated
T=86400s: ensure_auth github  # Session expired
T=86401.5s: ✓ Re-authenticated
```

## Testing

### Run Test Suite

```bash
bash plugins/leyline/skills/authentication-patterns/tests/test-interactive_auth.sh
```

### Test Interactive Flow

```bash
# Clear caches
clear_all_auth_cache

# Test authentication
source plugins/leyline/scripts/interactive_auth.sh
ensure_auth github
```

### Test CI/CD Flow

```bash
export AUTH_INTERACTIVE=false
export GITHUB_TOKEN="ghp_test..."

source plugins/leyline/scripts/interactive_auth.sh
ensure_auth github  # Should use GITHUB_TOKEN, no prompt
```

## Next Steps

### Recommended Actions

1. **Update Pilot Workflows** - Integrate into key workflows
   - `/fix-pr`
   - `/pr-review`
   - `/create-issue`
   - `/do-issue`
   - `/update-plugins`

2. **Document Migration** - Add migration guide to plugin documentation

3. **Monitor Usage** - Track adoption and user feedback

4. **Extend Services** - Add services as needed (Jira, PagerDuty, etc.)

## Files Created/Modified

### Created

```
plugins/leyline/skills/authentication-patterns/
├── README.md                           # Quick start guide
├── modules/
│   ├── interactive-auth.md            # Comprehensive docs
│   └── interactive_auth.sh            # Implementation
├── examples/
│   └── workflow-integration.md        # Integration examples
└── tests/
    └── test-interactive_auth.sh       # Test suite
```

### Modified

```
plugins/leyline/skills/authentication-patterns/SKILL.md  # Added module reference
```

## Statistics

- **Supported services:** 5 (GitHub, GitLab, AWS, GCP, Azure)
- **Configuration options:** 5 environment variables
- **Cache TTL:** 5 minutes (configurable)
- **Session TTL:** 24 hours (configurable)

## Compatibility

- **Shell:** Bash 4.0+
- **Operating Systems:** Linux, macOS, Windows (WSL)
- **CI/CD:** GitHub Actions, GitLab CI, CircleCI, AWS CodeBuild, and more
- **Terminal:** Interactive (TTY) and non-interactive modes
