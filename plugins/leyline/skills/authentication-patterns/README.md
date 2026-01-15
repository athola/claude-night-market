# Authentication Patterns - Interactive OAuth

Interactive authentication for external services with automatic token caching, session management, and CI/CD support.

## Quick Start

```bash
# Source the interactive auth script
source plugins/leyline/scripts/interactive-auth.sh

# Ensure authentication (prompts if needed)
ensure_auth github || exit 1

# Use service APIs
gh pr view 123
gh api repos/owner/repo/issues
```

## Features

✅ **Interactive OAuth** - Browser-based authentication flow for GitHub, GitLab, AWS, and more
✅ **Token Caching** - 5-minute cache reduces redundant auth checks
✅ **Session Management** - 24-hour session persistence across workflow runs
✅ **Multi-Service Support** - Unified interface for GitHub, GitLab, AWS, GCP, Azure
✅ **CI/CD Compatible** - Auto-detects non-interactive environments
✅ **Retry Logic** - Exponential backoff for transient failures
✅ **Secure** - Tokens stored by service CLIs, never logged

## Supported Services

| Service | CLI Tool | Auth Command |
|---------|----------|--------------|
| GitHub | `gh` | `gh auth login` |
| GitLab | `glab` | `glab auth login` |
| AWS | `aws` | `aws configure` |
| Google Cloud | `gcloud` | `gcloud auth login` |
| Azure | `az` | `az login` |

## Installation

No installation required - the module is part of the `leyline` plugin.

## Usage

### Basic Authentication

```bash
source plugins/leyline/skills/authentication-patterns/modules/interactive-auth.sh

# Check and prompt if needed
ensure_auth github || exit 1
ensure_auth gitlab || exit 1
ensure_auth aws || exit 1
```

### In Workflows

```bash
#!/usr/bin/env bash
# My workflow that uses GitHub API

source plugins/leyline/skills/authentication-patterns/modules/interactive-auth.sh

# Ensure authentication at start
if ! ensure_auth github; then
  echo "❌ GitHub authentication required"
  exit 1
fi

# Continue with workflow
gh pr list
gh issue create --title "My Issue"
```

### Wrapper Functions

```bash
# Use wrapper functions for cleaner code
gh_with_auth pr view 123
gh_api_with_auth repos/owner/repo/pulls
glab_with_auth issue list
aws_with_auth s3 ls
```

## Configuration

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `AUTH_CACHE_DIR` | Cache directory | `~/.cache/claude-auth` |
| `AUTH_CACHE_TTL` | Cache TTL (seconds) | `300` (5 min) |
| `AUTH_SESSION_TTL` | Session TTL (seconds) | `86400` (24 hr) |
| `AUTH_INTERACTIVE` | Force mode | `auto` (detect) |
| `AUTH_MAX_ATTEMPTS` | Max retries | `3` |

### Service-Specific Variables

```bash
# GitHub (fallback for CI/CD)
export GITHUB_TOKEN="ghp_..."

# GitLab
export GITLAB_TOKEN="glpat-..."

# AWS
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."  # For temp credentials
```

## How It Works

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

## Interactive Prompt Example

When authentication is needed, users see:

```
🔐 GitHub Authentication Required

This workflow needs GitHub API access to continue.

How would you like to authenticate?
  1. Browser (OAuth) - Recommended
  2. Personal Access Token
  3. Cancel workflow

Choose [1-3]:
```

**Option 1 (OAuth):** Opens browser for GitHub authorization
**Option 2 (Token):** Paste personal access token directly
**Option 3:** Cancel the workflow

## CI/CD Integration

### GitHub Actions Example

```yaml
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
          source plugins/leyline/skills/authentication-patterns/modules/interactive-auth.sh
          ensure_auth github || exit 1
          /pr-review ${{ github.event.pull_request.number }}
```

### GitLab CI Example

```yaml
review:
  script:
    - export GITLAB_TOKEN="$CI_JOB_TOKEN"
    - export AUTH_INTERACTIVE=false
    - source plugins/leyline/skills/authentication-patterns/modules/interactive-auth.sh
    - ensure_auth gitlab || exit 1
    - ./run-review.sh
```

## API Reference

### Main Functions

#### `ensure_auth <service>`

Ensure authentication for a service, prompting if necessary.

**Parameters:**
- `service` - Service name (github, gitlab, aws, gcloud, azure)

**Returns:**
- `0` - Authentication successful
- `1` - Authentication failed

**Example:**
```bash
if ensure_auth github; then
  echo "Authenticated!"
  gh pr view 123
else
  echo "Authentication failed"
  exit 1
fi
```

#### `check_auth_status <service>`

Check if service is authenticated (non-interactive).

**Parameters:**
- `service` - Service name

**Returns:**
- `0` - Authenticated
- `1` - Not authenticated

**Example:**
```bash
if check_auth_status github; then
  echo "GitHub is authenticated"
else
  echo "Need to authenticate"
fi
```

#### `invalidate_auth_cache <service>`

Invalidate cached authentication status.

**Parameters:**
- `service` - Service name

**Example:**
```bash
invalidate_auth_cache github
ensure_auth github  # Will re-check
```

#### `clear_all_auth_cache`

Clear all cached authentication data.

**Example:**
```bash
clear_all_auth_cache
```

### Wrapper Functions

#### `gh_with_auth [args...]`

Run `gh` command with automatic authentication.

**Example:**
```bash
gh_with_auth pr view 123
gh_with_auth issue list
```

#### `gh_api_with_auth <endpoint>`

Run `gh api` with automatic authentication.

**Example:**
```bash
gh_api_with_auth "repos/owner/repo/issues"
gh_api_with_auth "repos/owner/repo/pulls/123"
```

## Advanced Usage

### Custom Cache Configuration

```bash
# Extend cache to 1 hour
export AUTH_CACHE_TTL=3600
ensure_auth github

# Disable caching
export AUTH_CACHE_TTL=0
ensure_auth github
```

### Force Interactive Mode

```bash
# Force prompts even if terminal detection fails
export AUTH_INTERACTIVE=true
ensure_auth github
```

### Force Non-Interactive Mode

```bash
# Disable prompts (fail if not authenticated)
export AUTH_INTERACTIVE=false
ensure_auth github || exit 1
```

### Multi-Service Workflows

```bash
# Authenticate multiple services
ensure_auth github || exit 1
ensure_auth gitlab || exit 1
ensure_auth aws || exit 1

# Use all services
gh pr list
glab issue list
aws s3 ls
```

## Troubleshooting

### "gh: command not found"

**Problem:** GitHub CLI is not installed.

**Solution:**
```bash
# macOS
brew install gh

# Linux
sudo apt install gh  # Ubuntu/Debian
sudo yum install gh  # RHEL/CentOS

# Verify installation
gh --version
```

### "Authentication failed"

**Problem:** OAuth flow or token authentication failed.

**Solution:**
```bash
# Clear cache and retry
clear_all_auth_cache
ensure_auth github

# Or use token manually
echo "your_token" | gh auth login --with-token
```

### "Keeps asking for authentication"

**Problem:** Session not persisting.

**Solution:**
```bash
# Check session file
cat ~/.cache/claude-auth/github/session.json

# Extend session TTL
export AUTH_SESSION_TTL=604800  # 7 days
ensure_auth github
```

### "Not working in CI/CD"

**Problem:** CI/CD environment requires non-interactive mode.

**Solution:**
```bash
# Set environment variable
export AUTH_INTERACTIVE=false
export GITHUB_TOKEN="..."  # Your token
ensure_auth github
```

## Security Considerations

1. **Token Storage** - Tokens stored by service CLIs, not this module
   - GitHub: `~/.config/gh/hosts.yml`
   - GitLab: `~/.config/glab/config.yml`
   - AWS: `~/.aws/credentials`

2. **Cache Permissions** - Cache directory has restricted permissions (`0700`)

3. **No Logging** - Tokens never logged or echoed

4. **Session Expiration** - Sessions expire to limit credential lifetime

5. **CI/CD Best Practice** - Use short-lived tokens in CI/CD environments

## Examples

See `examples/workflow-integration.md` for comprehensive examples:
- PR Review command integration
- Create Issue command integration
- Multi-service workflows
- CI/CD pipelines
- Error handling patterns

## Contributing

To add support for a new service:

1. Add to `AUTH_CHECK_COMMANDS` array in `interactive-auth.sh`
2. Add to `AUTH_LOGIN_COMMANDS` array
3. Create prompt function if needed (e.g., `prompt_newservice_auth`)
4. Add documentation to this README

Example:
```bash
# In interactive-auth.sh
declare -A AUTH_CHECK_COMMANDS=(
  ...
  [myservice]="myservice auth status"
)

declare -A AUTH_LOGIN_COMMANDS=(
  ...
  [myservice]="myservice auth login"
)
```

## License

Part of the claude-night-market ecosystem.

## See Also

- [Authentication Patterns Skill](SKILL.md) - Main skill documentation
- [Interactive Auth Module](modules/interactive-auth.md) - Detailed module docs
- [Workflow Integration Examples](examples/workflow-integration.md) - Integration patterns
- [Auth Methods](modules/auth-methods.md) - Authentication method details
- [Verification Patterns](modules/verification-patterns.md) - Testing patterns
