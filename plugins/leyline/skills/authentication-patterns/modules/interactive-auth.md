---
name: interactive-auth
description: Interactive authentication with token caching and multi-service support
estimated_tokens: 800
---

# Interactive Authentication

## Overview

Provides interactive authentication flows for external
services with automatic token caching, session management,
and multi-service support.

**Authenticate Once, Use Everywhere**: Tokens are cached
locally and validated efficiently, minimizing interactive
prompts while maintaining security.

**CI/CD Compatible**: Automatically detects non-interactive
environments and falls back to environment variables.

## Quick Start

```bash
source plugins/leyline/scripts/interactive_auth.sh

ensure_auth github || exit 1
gh pr view 123
```

## Configuration

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `AUTH_CACHE_DIR` | Token cache directory | `~/.cache/claude-auth` |
| `AUTH_CACHE_TTL` | Cache TTL in seconds | `300` (5 min) |
| `AUTH_SESSION_TTL` | Session persistence TTL | `86400` (24 hr) |
| `AUTH_INTERACTIVE` | Force interactive mode | `auto` (detect) |
| `AUTH_MAX_ATTEMPTS` | Max authentication attempts | `3` |

### Service-Specific Variables

```bash
export GITHUB_TOKEN="..."               # GitHub fallback
export GITLAB_TOKEN="..."               # GitLab
export AWS_ACCESS_KEY_ID="..."          # AWS
export AWS_SECRET_ACCESS_KEY="..."
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
```

## Core Functions

### `ensure_auth <service>`

Ensure authentication for a service, prompting if
necessary. Returns 0 on success, 1 on failure.

```bash
ensure_auth github || exit 1
ensure_auth gitlab || exit 1
ensure_auth aws || exit 1
```

**Supported services:** `github` (gh), `gitlab` (glab),
`aws`, `gcloud`, `azure`

### `check_auth_status <service>`

Non-interactive check. Returns 0 if authenticated, 1
otherwise.

```bash
if check_auth_status github; then
  echo "GitHub is authenticated"
fi
```

### `invalidate_auth_cache <service>`

Force re-authentication next time.

```bash
invalidate_auth_cache github
ensure_auth github  # Will prompt again
```

### `clear_all_auth_cache`

Clear all cached authentication data across all services.

## Token Caching

Cache structure:

```
~/.cache/claude-auth/
├── github/
│   ├── auth_status.json
│   ├── last_verified.txt
│   └── token_cache.json
├── gitlab/
└── config.json
```

Cache validation uses three mechanisms:

1. **Time-based expiration** (default: 5 minutes)
2. **Session persistence** (default: 24 hours)
3. **Manual invalidation** (via `invalidate_auth_cache`)

Within the cache TTL, `ensure_auth` returns immediately
without contacting the service. After TTL expiry, it
re-validates with the service. After session TTL expiry,
full re-authentication is required.

## Authentication Flows

### GitHub

`ensure_auth github` checks `gh auth status` first,
then cache, then prompts:

1. Browser OAuth (recommended)
2. Personal Access Token
3. Cancel workflow

### AWS

`ensure_auth aws` checks `aws sts get-caller-identity`
first, then prompts:

1. AWS Access Keys
2. SSO Session
3. Web Identity (OIDC)
4. Cancel workflow

### Other Services

GitLab uses `glab auth login`, GCP uses
`gcloud auth login`, Azure uses `az login`. All follow
the same check-cache-prompt pattern.

## CI/CD Compatibility

The module auto-detects non-interactive environments
(`$CI`, `$GITHUB_ACTIONS`, or non-terminal stdin) and
falls back to environment variables.

```yaml
# .github/workflows/pr-review.yml
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run PR review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          AUTH_INTERACTIVE: false
        run: |
          source plugins/leyline/scripts/interactive_auth.sh
          ensure_auth github || exit 1
          /pr-review ${{ github.event.pull_request.number }}
```

## Error Handling

Failed authentications retry with exponential backoff
(2, 4, 8 seconds) up to `AUTH_MAX_ATTEMPTS`.

| Error | Cause | Solution |
|-------|-------|----------|
| `gh: command not found` | CLI not installed | Install via package manager |
| `gh auth status: failed` | Not authenticated | Run `gh auth login` or set `GITHUB_TOKEN` |
| `Token expired` | Cached token expired | Re-authenticate via `ensure_auth` |
| `Invalid credentials` | Wrong token/keys | Verify in service dashboard |

## Troubleshooting

**Auth not working after changing credentials:**
```bash
clear_all_auth_cache
ensure_auth github
```

**Keeps asking for authentication:**
```bash
export AUTH_SESSION_TTL=604800  # Extend to 7 days
ensure_auth github
```

**Fails in CI with "not a terminal":**
```bash
export AUTH_INTERACTIVE=false
export GITHUB_TOKEN="..."
ensure_auth github
```

## Security Considerations

1. **Token storage**: Managed by service CLIs, not this
   module (e.g., `~/.config/gh/hosts.yml`)
2. **Cache permissions**: Directory restricted to `0700`
3. **No token logging**: Tokens are never logged or echoed
4. **Session expiration**: Limits credential lifetime
5. **CI/CD best practice**: Use short-lived tokens

## Exit Criteria

- Service is authenticated (via CLI or token)
- Session is cached for future use
- Workflow can proceed with API access
- CI/CD environments use environment variables
