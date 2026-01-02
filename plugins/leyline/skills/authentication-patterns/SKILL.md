---
name: authentication-patterns
description: |
  Authentication patterns for external services: API keys, OAuth, token management, verification.

  Triggers: authentication, API keys, OAuth, token management, credentials
  Use when: integrating external services or implementing authentication flows
category: infrastructure
tags: [authentication, api-keys, oauth, tokens, security]
dependencies: [error-patterns]
provides:
  infrastructure: [authentication, credential-management, auth-verification]
  patterns: [api-key-auth, oauth-flow, token-refresh]
usage_patterns:
  - service-authentication
  - credential-verification
  - token-management
complexity: beginner
estimated_tokens: 400
progressive_loading: true
modules:
  - modules/auth-methods.md
  - modules/verification-patterns.md
---

# Authentication Patterns

## Overview

Common authentication patterns for integrating with external services. Provides consistent approaches to credential management, verification, and error handling.

## When to Use

- Integrating with external APIs
- Need credential verification
- Managing multiple auth methods
- Handling auth failures gracefully

## Authentication Methods

| Method | Best For | Environment Variable |
|--------|----------|---------------------|
| API Key | Simple integrations | `{SERVICE}_API_KEY` |
| OAuth | User-authenticated | Browser-based flow |
| Token | Session-based | `{SERVICE}_TOKEN` |
| None | Public APIs | N/A |

## Quick Start

### Verify Authentication
```python
from leyline.auth import verify_auth, AuthMethod

# API Key verification
status = verify_auth(
    service="gemini",
    method=AuthMethod.API_KEY,
    env_var="GEMINI_API_KEY"
)

if not status.authenticated:
    print(f"Auth failed: {status.message}")
    print(f"Action: {status.suggested_action}")
```

### Smoke Test
```python
def verify_with_smoke_test(service: str) -> bool:
    """Verify auth with simple request."""
    result = execute_simple_request(service, "ping")
    return result.success
```

## Standard Flow

### Step 1: Check Environment
```python
def check_credentials(service: str, env_var: str) -> bool:
    value = os.getenv(env_var)
    if not value:
        print(f"Missing {env_var}")
        return False
    return True
```

### Step 2: Verify with Service
```python
def verify_with_service(service: str) -> AuthStatus:
    result = subprocess.run(
        [service, "auth", "status"],
        capture_output=True
    )
    return AuthStatus(
        authenticated=(result.returncode == 0),
        message=result.stdout.decode()
    )
```

### Step 3: Handle Failures
```python
def handle_auth_failure(service: str, method: AuthMethod) -> str:
    actions = {
        AuthMethod.API_KEY: f"Set {service.upper()}_API_KEY environment variable",
        AuthMethod.OAUTH: f"Run '{service} auth login' for browser auth",
        AuthMethod.TOKEN: f"Refresh token with '{service} token refresh'"
    }
    return actions[method]
```

## Integration Pattern

```yaml
# In your skill's frontmatter
dependencies: [leyline:authentication-patterns]
```

## Detailed Resources

- **Auth Methods**: See `modules/auth-methods.md` for method details
- **Verification**: See `modules/verification-patterns.md` for testing patterns

## Exit Criteria

- Credentials verified or clear failure message
- Suggested action for auth failures
- Smoke test confirms working auth
