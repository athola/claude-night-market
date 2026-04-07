#!/usr/bin/env bash
# Submit night-market to awesome-openclaw lists via fork PRs.
# Uses your existing `gh auth` session. No PAT or secrets needed.
#
# Usage:
#   ./scripts/awesome-submit.sh v1.8.1
#   ./scripts/awesome-submit.sh v1.8.1 --dry-run

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

TARGETS=(
  "vincentkoc/awesome-openclaw"
  "SamurAIGPT/awesome-openclaw"
)

# ---------- parse args ----------

DRY_RUN=false
VERSION=""

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    v*) VERSION="$arg" ;;
    [0-9]*) VERSION="v$arg" ;;
    *) echo "Unknown argument: $arg"; exit 1 ;;
  esac
done

if [ -z "$VERSION" ]; then
  VERSION="v$(python3 -c "
import json
print(json.load(open('$REPO_ROOT/plugins/abstract/.claude-plugin/plugin.json'))['version'])
")"
  echo "Auto-detected version: $VERSION"
fi

# ---------- preflight ----------

if ! command -v gh &> /dev/null; then
  echo "Error: gh CLI is required. Install from https://cli.github.com"
  exit 1
fi

if ! gh auth status &> /dev/null; then
  echo "Error: Not authenticated. Run: gh auth login"
  exit 1
fi

FORK_OWNER=$(gh api user --jq .login)
echo "Authenticated as: $FORK_OWNER"

# Count skills from export manifest or plugin.json
if [ -f "$REPO_ROOT/clawhub/manifest.json" ]; then
  SKILLS=$(python3 -c "
import json
print(json.load(open('$REPO_ROOT/clawhub/manifest.json'))['total_exported'])
")
else
  SKILLS="100+"
fi

ENTRY="- [night-market](https://github.com/athola/claude-night-market) - ${SKILLS} curated skills for code review, testing, docs, and architecture."

# ---------- submit to each target ----------

for TARGET in "${TARGETS[@]}"; do
  echo ""
  echo "=== $TARGET ==="

  REPO_NAME=$(echo "$TARGET" | cut -d/ -f2)
  BRANCH="add-night-market-${VERSION}"

  # Check for existing open PR from us before doing any work
  EXISTING=$(gh pr list \
    --repo "$TARGET" \
    --author "$FORK_OWNER" \
    --search "night-market" \
    --state open \
    --json number,url -q '.[0]' 2>/dev/null || true)

  if [ -n "$EXISTING" ] && [ "$EXISTING" != "null" ]; then
    EXISTING_NUM=$(echo "$EXISTING" | python3 -c "import sys,json; print(json.load(sys.stdin)['number'])")
    EXISTING_URL=$(echo "$EXISTING" | python3 -c "import sys,json; print(json.load(sys.stdin)['url'])")
    echo "Open PR #${EXISTING_NUM} already exists: ${EXISTING_URL}"
    echo "Skipping $TARGET"
    continue
  fi

  # Ensure fork exists
  gh repo fork "$TARGET" --clone=false 2>&1 || true

  if ! gh repo view "${FORK_OWNER}/${REPO_NAME}" --json name -q .name > /dev/null 2>&1; then
    echo "Warning: Cannot access fork ${FORK_OWNER}/${REPO_NAME}, skipping"
    continue
  fi

  # Sync fork
  gh repo sync "${FORK_OWNER}/${REPO_NAME}" --branch main 2>&1 || true

  WORKDIR=$(mktemp -d)
  trap 'rm -rf "$WORKDIR"' EXIT

  gh repo clone "${FORK_OWNER}/${REPO_NAME}" "$WORKDIR/repo" -- --depth=10
  cd "$WORKDIR/repo"

  git config user.name "$FORK_OWNER"
  git config user.email "${FORK_OWNER}@users.noreply.github.com"

  git checkout -b "$BRANCH"

  # Add entry if not already present in upstream
  if grep -q "night-market" README.md; then
    echo "Already listed in $TARGET, skipping"
    cd "$REPO_ROOT"
    rm -rf "$WORKDIR"
    continue
  fi

  # Insert after ## Skills header, or append
  if grep -q "## Skills" README.md; then
    python3 -c "
import re
content = open('README.md').read()
m = re.search(r'(## Skills[^\n]*\n(?:.*?\n)*?)(\n## |\Z)', content, re.DOTALL)
if m:
    before = m.group(1).rstrip()
    after = m.group(2)
    content = content[:m.start()] + before + '\n$ENTRY\n' + after + content[m.end():]
else:
    content += '\n$ENTRY\n'
open('README.md', 'w').write(content)
"
  else
    echo "" >> README.md
    echo "$ENTRY" >> README.md
  fi

  if git diff --quiet; then
    echo "No changes needed"
    cd "$REPO_ROOT"
    rm -rf "$WORKDIR"
    continue
  fi

  git add README.md
  git commit -m "Add night-market: ${SKILLS} skills for code review, testing, architecture"

  echo "Changes:"
  git diff HEAD~1 --stat

  if [ "$DRY_RUN" = true ]; then
    echo "Dry run -- skipping push/PR for $TARGET"
    cd "$REPO_ROOT"
    rm -rf "$WORKDIR"
    continue
  fi

  git push --force-with-lease origin "$BRANCH"

  # Check if a PR already exists for this branch (e.g. from a prior failed run)
  EXISTING_PR=$(gh pr list \
    --repo "$TARGET" \
    --head "${FORK_OWNER}:${BRANCH}" \
    --state open \
    --json number -q '.[0].number' 2>/dev/null || true)

  if [ -n "$EXISTING_PR" ]; then
    echo "PR #${EXISTING_PR} updated on $TARGET"
    cd "$REPO_ROOT"
    rm -rf "$WORKDIR"
    continue
  fi

  gh pr create \
    --repo "$TARGET" \
    --head "${FORK_OWNER}:${BRANCH}" \
    --title "Add night-market skills" \
    --body "$(cat <<'PRBODYEOF'
Adds [Claude Night Market](https://github.com/athola/claude-night-market)
-- curated skills for code review, testing, documentation, architecture,
and git workflows. MIT licensed, published on ClawHub.
PRBODYEOF
    )"
  echo "PR created on $TARGET"

  cd "$REPO_ROOT"
  rm -rf "$WORKDIR"
done

echo ""
echo "=== Done ==="
