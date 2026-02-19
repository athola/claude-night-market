#!/usr/bin/env bash
# SessionStart hook for leyline - Fetch recent Discussions
# Queries the 5 most recent "Decisions" discussions from GitHub Discussions
# and injects a brief summary into the session context for cross-session learning.
#
# Requirements:
#   - GitHub platform (detected by detect-git-platform.sh)
#   - gh CLI authenticated
#   - Repository has Discussions enabled with a "Decisions" category
#
# Performance: Must complete within 3 seconds (single bounded GraphQL query)
# Token budget: < 600 tokens injected into session context

set -euo pipefail

# --- Guard: GitHub platform only ---

# Check if gh CLI is available
if ! command -v gh >/dev/null 2>&1; then
    cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": ""
  }
}
EOF
    exit 0
fi

# Check if gh is authenticated (suppress output)
if ! gh auth status >/dev/null 2>&1; then
    cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": ""
  }
}
EOF
    exit 0
fi

# Check if we're in a git repo with a GitHub remote
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": ""
  }
}
EOF
    exit 0
fi

remote_url=$(git remote get-url origin 2>/dev/null || echo "")
case "$remote_url" in
    *github.com*|*github.*) ;;  # GitHub — continue
    *)
        # Not GitHub — skip silently
        cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": ""
  }
}
EOF
        exit 0
        ;;
esac

# --- Resolve owner/repo from remote URL ---

parse_github_remote() {
    local url="$1"
    # Handle SSH: git@github.com:owner/repo.git
    # Handle HTTPS: https://github.com/owner/repo.git
    echo "$url" | sed -E 's#.*github\.com[:/]([^/]+)/([^/.]+)(\.git)?$#\1/\2#'
}

owner_repo=$(parse_github_remote "$remote_url")
owner="${owner_repo%%/*}"
repo="${owner_repo##*/}"

if [ -z "$owner" ] || [ -z "$repo" ]; then
    cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": ""
  }
}
EOF
    exit 0
fi

# --- Resolve "Decisions" category ID ---

category_response=$(gh api graphql -f query='
query($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    hasDiscussionsEnabled
    discussionCategories(first: 25) {
      nodes { id slug }
    }
  }
}' -f owner="$owner" -f repo="$repo" 2>/dev/null || echo "")

if [ -z "$category_response" ]; then
    cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": ""
  }
}
EOF
    exit 0
fi

# Check if discussions are enabled
has_discussions=$(echo "$category_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('data', {}).get('repository', {}).get('hasDiscussionsEnabled', False))
except Exception:
    print('False')
" 2>/dev/null || echo "False")

if [ "$has_discussions" != "True" ]; then
    cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": ""
  }
}
EOF
    exit 0
fi

# Find the "decisions" category ID
category_id=$(echo "$category_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    cats = data.get('data', {}).get('repository', {}).get('discussionCategories', {}).get('nodes', [])
    for c in cats:
        if c.get('slug', '').lower() == 'decisions':
            print(c['id'])
            break
except Exception:
    pass
" 2>/dev/null || echo "")

if [ -z "$category_id" ]; then
    # No "Decisions" category — skip silently
    cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": ""
  }
}
EOF
    exit 0
fi

# --- Fetch 5 most recent Decisions discussions ---

discussions_response=$(gh api graphql -f query='
query($owner: String!, $repo: String!, $categoryId: ID!) {
  repository(owner: $owner, name: $repo) {
    discussions(first: 5, categoryId: $categoryId, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        number
        title
        createdAt
        body
      }
    }
  }
}' -f owner="$owner" -f repo="$repo" -f categoryId="$category_id" 2>/dev/null || echo "")

if [ -z "$discussions_response" ]; then
    cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": ""
  }
}
EOF
    exit 0
fi

# --- Format summary ---

summary=$(echo "$discussions_response" | python3 -c "
from __future__ import annotations
import sys, json

try:
    data = json.load(sys.stdin)
    nodes = data.get('data', {}).get('repository', {}).get('discussions', {}).get('nodes', [])
    if not nodes:
        sys.exit(0)

    lines = ['Recent Decisions (from GitHub Discussions):']
    for d in nodes:
        num = d.get('number', '?')
        title = d.get('title', 'Untitled')
        date = d.get('createdAt', '')[:10]
        body = d.get('body', '')
        # First 100 chars of body, single line
        snippet = body.replace('\n', ' ').replace('\r', '')[:100].strip()
        if len(body) > 100:
            snippet += '...'
        lines.append(f'  #{num} {title} ({date}) -- {snippet}')

    print('\n'.join(lines))
except Exception:
    pass
" 2>/dev/null || echo "")

if [ -z "$summary" ]; then
    cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": ""
  }
}
EOF
    exit 0
fi

# --- Inject into session context ---
# Escape for JSON: replace newlines, quotes, backslashes
escaped_summary=$(echo "$summary" | python3 -c "
import sys, json
text = sys.stdin.read()
print(json.dumps(text)[1:-1])
" 2>/dev/null || echo "")

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "${escaped_summary}"
  }
}
EOF

exit 0
