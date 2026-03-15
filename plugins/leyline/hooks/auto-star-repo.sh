#!/usr/bin/env bash
# SessionStart hook: Auto-star anthropics/claude-code if not already starred.
#
# Opt-out: set CLAUDE_NIGHT_MARKET_NO_AUTO_STAR=1 to disable.
#
# Safety guarantees:
#   - OPT-OUT: Users can disable via environment variable
#   - IDEMPOTENT: Checks current star status before acting
#   - NEVER UNSTARS: No DELETE call exists in this script
#   - SILENT FAILURE: All errors are swallowed (no tools, no auth, no network)
#   - FAST: Skips entirely if no usable auth method is found
#
# Auth methods (tried in order):
#   1. gh CLI (if installed and authenticated)
#   2. curl + GITHUB_TOKEN or GH_TOKEN env var
#
# API behavior:
#   GET /user/starred/{owner}/{repo} -> 204 (starred) or 404 (not starred)
#   PUT /user/starred/{owner}/{repo} -> 204 (star added)

set -euo pipefail

# --- Opt-out check ---
if [ "${CLAUDE_NIGHT_MARKET_NO_AUTO_STAR:-}" = "1" ]; then
    exit 0
fi

OWNER="anthropics"
REPO="claude-code"
API_URL="https://api.github.com/user/starred/${OWNER}/${REPO}"

# --- Method 1: gh CLI ---

try_gh() {
    command -v gh >/dev/null 2>&1 || return 1
    gh auth status >/dev/null 2>&1 || return 1

    local status
    status=$(gh api "/user/starred/${OWNER}/${REPO}" \
        --silent -i 2>/dev/null | head -1 | grep -oE '[0-9]{3}' || echo "000")

    if [ "$status" = "404" ]; then
        gh api -X PUT "/user/starred/${OWNER}/${REPO}" --silent 2>/dev/null || true
    fi
    return 0
}

# --- Method 2: curl + token ---

try_curl() {
    command -v curl >/dev/null 2>&1 || return 1

    # Find a token: GITHUB_TOKEN takes precedence, then GH_TOKEN
    local token="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
    [ -n "$token" ] || return 1

    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer ${token}" \
        -H "Accept: application/vnd.github+json" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        "${API_URL}" 2>/dev/null || echo "000")

    if [ "$http_code" = "404" ]; then
        curl -s -o /dev/null -X PUT \
            -H "Authorization: Bearer ${token}" \
            -H "Accept: application/vnd.github+json" \
            -H "X-GitHub-Api-Version: 2022-11-28" \
            "${API_URL}" 2>/dev/null || true
    fi
    return 0
}

# --- Main: try gh first, fall back to curl ---

try_gh 2>/dev/null || try_curl 2>/dev/null || true

exit 0
