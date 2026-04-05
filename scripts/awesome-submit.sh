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

  # Ensure fork exists
  gh repo fork "$TARGET" --clone=false 2>&1 || true

  if ! gh repo view "${FORK_OWNER}/${REPO_NAME}" --json name -q .name > /dev/null 2>&1; then
    echo "Warning: Cannot access fork ${FORK_OWNER}/${REPO_NAME}, skipping"
    continue
  fi

  # Sync fork
  gh repo sync "${FORK_OWNER}/${REPO_NAME}" --branch main 2>&1 || true

  WORKDIR=$(mktemp -d)

  gh repo clone "${FORK_OWNER}/${REPO_NAME}" "$WORKDIR/repo" -- --depth=10
  cd "$WORKDIR/repo"

  git config user.name "$FORK_OWNER"
  git config user.email "${FORK_OWNER}@users.noreply.github.com"

  # Clean up stale branch
  if git ls-remote --heads origin "$BRANCH" | grep -q "$BRANCH"; then
    git push origin --delete "$BRANCH" 2>/dev/null || true
  fi

  git checkout -b "$BRANCH"

  # Add entry if not already present
  if grep -q "night-market" README.md; then
    echo "Already listed in $TARGET, skipping"
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
    rm -rf "$WORKDIR"
    continue
  fi

  git add README.md
  git commit -m "Add night-market: ${SKILLS} skills for code review, testing, architecture"

  echo "Changes:"
  git diff HEAD~1 --stat

  if [ "$DRY_RUN" = true ]; then
    echo "Dry run -- skipping push/PR for $TARGET"
    rm -rf "$WORKDIR"
    continue
  fi

  git push origin "$BRANCH"

  EXISTING=$(gh pr list \
    --repo "$TARGET" \
    --head "${FORK_OWNER}:${BRANCH}" \
    --json number -q '.[0].number' 2>/dev/null || true)

  if [ -n "$EXISTING" ]; then
    echo "PR #${EXISTING} updated"
  else
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
  fi

  rm -rf "$WORKDIR"
done

echo ""
echo "=== Done ==="
