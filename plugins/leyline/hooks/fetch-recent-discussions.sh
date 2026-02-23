#!/usr/bin/env bash
# SessionStart hook for leyline - Fetch recent Discussions
# Queries the 5 most recent "Decisions" discussions from GitHub Discussions
# and injects a brief summary into the session context for cross-session learning.
#
# Requirements:
#   - GitHub platform (self-detected via git remote URL)
#   - gh CLI authenticated
#   - Repository has Discussions enabled with a "Decisions" category
#
# Performance: Must complete within 3 seconds (single bounded GraphQL query)
# Token budget: < 600 tokens injected into session context

set -euo pipefail

# --- Helper: emit empty SessionStart JSON and exit ---

_emit_empty() {
    local reason="${1:-}"
    if [ -n "$reason" ]; then
        echo "[fetch-recent-discussions] $reason" >&2
    fi
    cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": ""
  }
}
EOF
    exit 0
}

# --- Guard: GitHub platform only ---

# Check if gh CLI is available
if ! command -v gh >/dev/null 2>&1; then
    _emit_empty
fi

# Check if gh is authenticated (suppress output)
if ! gh auth status >/dev/null 2>&1; then
    _emit_empty
fi

# Check if we're in a git repo with a GitHub remote
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    _emit_empty
fi

remote_url=$(git remote get-url origin 2>/dev/null || echo "")
case "$remote_url" in
    *github.com*) ;;  # GitHub.com — continue
    *)
        # Not GitHub.com — skip silently
        _emit_empty
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
    _emit_empty "could not parse owner/repo from remote URL"
fi

# --- Resolve "Decisions" category ID ---

category_err=$(mktemp)
category_response=$(gh api graphql -f query='
query($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    hasDiscussionsEnabled
    discussionCategories(first: 25) {
      nodes { id slug }
    }
  }
}' -f owner="$owner" -f repo="$repo" 2>"$category_err" || echo "")

if [ -z "$category_response" ]; then
    err_msg=$(cat "$category_err" 2>/dev/null || true)
    rm -f "$category_err"
    _emit_empty "GraphQL category query failed: ${err_msg:-unknown error}"
fi
rm -f "$category_err"

# Check for GraphQL errors and whether discussions are enabled
has_discussions=$(echo "$category_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('errors'):
        msgs = '; '.join(e.get('message', '?') for e in data['errors'])
        print('Error: ' + msgs, file=sys.stderr)
        print('False')
    else:
        print(data.get('data', {}).get('repository', {}).get('hasDiscussionsEnabled', False))
except Exception as exc:
    print(f'JSON parse error: {exc}', file=sys.stderr)
    print('False')
" || echo "False")

if [ "$has_discussions" != "True" ]; then
    _emit_empty
fi

# Find the "decisions" category ID
category_id=$(echo "$category_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('errors'):
        sys.exit(0)
    cats = data.get('data', {}).get('repository', {}).get('discussionCategories', {}).get('nodes', [])
    for c in cats:
        if c.get('slug', '').lower() == 'decisions':
            print(c['id'])
            break
except Exception as exc:
    print(f'JSON parse error: {exc}', file=sys.stderr)
" || echo "")

if [ -z "$category_id" ]; then
    _emit_empty
fi

# --- Fetch 5 most recent Decisions discussions ---

discussions_err=$(mktemp)
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
}' -f owner="$owner" -f repo="$repo" -f categoryId="$category_id" 2>"$discussions_err" || echo "")

if [ -z "$discussions_response" ]; then
    err_msg=$(cat "$discussions_err" 2>/dev/null || true)
    rm -f "$discussions_err"
    _emit_empty "GraphQL discussions query failed: ${err_msg:-unknown error}"
fi
rm -f "$discussions_err"

# --- Format summary ---

summary=$(echo "$discussions_response" | python3 -c "
import sys, json

try:
    data = json.load(sys.stdin)
    if data.get('errors'):
        msgs = '; '.join(e.get('message', '?') for e in data['errors'])
        print(f'GraphQL errors: {msgs}', file=sys.stderr)
        sys.exit(0)
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
except Exception as exc:
    print(f'Format error: {exc}', file=sys.stderr)
" || echo "")

if [ -z "$summary" ]; then
    _emit_empty
fi

# --- Inject into session context ---
# Escape for JSON: replace newlines, quotes, backslashes
escaped_summary=$(echo "$summary" | python3 -c "
import sys, json
text = sys.stdin.read()
print(json.dumps(text)[1:-1])
" || echo "")

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "${escaped_summary}"
  }
}
EOF

exit 0
