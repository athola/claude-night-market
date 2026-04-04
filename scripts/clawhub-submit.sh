#!/usr/bin/env bash
# Submit night-market skills to openclaw/clawhub via fork PR.
# Uses your existing `gh auth` session. No PAT or secrets needed.
#
# Usage:
#   ./scripts/clawhub-submit.sh v1.8.1
#   ./scripts/clawhub-submit.sh v1.8.1 --dry-run
#   ./scripts/clawhub-submit.sh              # uses version from plugin.json

set -euo pipefail

UPSTREAM="openclaw/clawhub"
SKILLS_DIR="clawhub"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

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

BRANCH="night-market-${VERSION}"

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

# ---------- build artifacts if needed ----------

if [ ! -d "$REPO_ROOT/$SKILLS_DIR" ] || [ ! -f "$REPO_ROOT/$SKILLS_DIR/manifest.json" ]; then
  echo "Building clawhub export..."
  cd "$REPO_ROOT"
  make clawhub-export
fi

EXPORTED=$(python3 -c "
import json
print(json.load(open('$REPO_ROOT/$SKILLS_DIR/manifest.json'))['total_exported'])
")
echo "Skills to submit: $EXPORTED"

if [ "$EXPORTED" -eq 0 ]; then
  echo "Error: No skills exported"
  exit 1
fi

# ---------- fork + sync ----------

echo "Ensuring fork exists..."
gh repo fork "$UPSTREAM" --clone=false 2>&1 || true

if ! gh repo view "${FORK_OWNER}/clawhub" --json name -q .name > /dev/null 2>&1; then
  echo "Error: Cannot access fork ${FORK_OWNER}/clawhub"
  exit 1
fi

echo "Syncing fork with upstream..."
gh repo sync "${FORK_OWNER}/clawhub" --branch main 2>&1 || true

# ---------- clone + branch ----------

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

echo "Cloning fork..."
gh repo clone "${FORK_OWNER}/clawhub" "$WORKDIR/clawhub" -- --depth=50
cd "$WORKDIR/clawhub"

git config user.name "$FORK_OWNER"
git config user.email "${FORK_OWNER}@users.noreply.github.com"

# Clean up stale branch from a prior run
if git ls-remote --heads origin "$BRANCH" | grep -q "$BRANCH"; then
  echo "Removing stale branch $BRANCH from fork..."
  git push origin --delete "$BRANCH" 2>/dev/null || true
fi

git checkout -b "$BRANCH"

# ---------- copy skills ----------

mkdir -p skills/athola
for skill_dir in "$REPO_ROOT/$SKILLS_DIR"/nm-*/; do
  [ -d "$skill_dir" ] || continue
  skill_name=$(basename "$skill_dir")
  cp -r "$skill_dir" "skills/athola/$skill_name/"
done

git add -A

if git diff --cached --quiet; then
  echo "No changes -- skills already match upstream."
  exit 0
fi

echo ""
echo "=== Changes ==="
git diff --cached --stat
echo ""

git commit -m "$(cat <<COMMITEOF
feat: add night-market skills (${VERSION})

Claude Night Market cross-framework export.
Source: https://github.com/athola/claude-night-market
COMMITEOF
)"

# ---------- dry run stops here ----------

if [ "$DRY_RUN" = true ]; then
  echo ""
  echo "=== Dry Run Passed ==="
  echo "Version:  $VERSION"
  echo "Skills:   $EXPORTED"
  echo "Branch:   $BRANCH"
  echo "Commit:   $(git log --oneline -1)"
  echo ""
  echo "Run without --dry-run to push and open PR."
  exit 0
fi

# ---------- push + PR ----------

echo "Pushing branch..."
git push origin "$BRANCH"

# Check for existing PR
EXISTING=$(gh pr list \
  --repo "$UPSTREAM" \
  --head "${FORK_OWNER}:${BRANCH}" \
  --json number -q '.[0].number' 2>/dev/null || true)

if [ -n "$EXISTING" ]; then
  echo "PR #${EXISTING} updated (branch force-pushed)"
  echo "https://github.com/${UPSTREAM}/pull/${EXISTING}"
else
  gh pr create \
    --repo "$UPSTREAM" \
    --head "${FORK_OWNER}:${BRANCH}" \
    --title "Add night-market skills (${VERSION})" \
    --body "$(cat <<'PRBODYEOF'
## Night Market Skills for OpenClaw

Top 20 curated skills from [Claude Night Market](https://github.com/athola/claude-night-market).

**Categories:** code review, testing, documentation, git workflow,
token conservation, architecture, skill development, project lifecycle.

**Provenance:** MIT licensed, automated export with validation.
Full plugin (agents, hooks, commands) available for Claude Code.
PRBODYEOF
    )"
  echo "PR created on ${UPSTREAM}"
fi
