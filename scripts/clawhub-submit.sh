#!/usr/bin/env bash
# Publish night-market skills to ClawHub via the clawhub CLI.
#
# Usage:
#   ./scripts/clawhub-submit.sh v1.8.1
#   ./scripts/clawhub-submit.sh v1.8.1 --dry-run
#   ./scripts/clawhub-submit.sh              # uses version from plugin.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
SKILLS_DIR="clawhub"

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

# Strip leading v for semver arg
SEMVER="${VERSION#v}"

# ---------- preflight ----------

if ! command -v npx &>/dev/null; then
  echo "Error: npx is required (Node.js 20+). Install from https://nodejs.org"
  exit 1
fi

# Ensure clawhub CLI is available (npx will fetch if missing)
if ! npx clawhub --help &>/dev/null 2>&1; then
  echo "Installing clawhub CLI..."
  npm install -g clawhub
fi

# Verify authentication
if ! npx clawhub whoami &>/dev/null 2>&1; then
  echo "Error: Not authenticated with ClawHub."
  echo "Run: npx clawhub login"
  exit 1
fi

CLAWHUB_USER=$(npx clawhub whoami 2>/dev/null)
echo "Authenticated as: $CLAWHUB_USER"

# ---------- build artifacts if needed ----------

if [ ! -d "$REPO_ROOT/$SKILLS_DIR" ] || \
   [ ! -f "$REPO_ROOT/$SKILLS_DIR/manifest.json" ]; then
  echo "Building clawhub export..."
  cd "$REPO_ROOT"
  make clawhub-export
fi

EXPORTED=$(python3 -c "
import json
print(json.load(open('$REPO_ROOT/$SKILLS_DIR/manifest.json'))['total_exported'])
")
echo "Skills to publish: $EXPORTED"

if [ "$EXPORTED" -eq 0 ]; then
  echo "Error: No skills exported"
  exit 1
fi

# ---------- publish ----------

PUBLISHED=0
SKIPPED=0
FAILED=0

for skill_dir in "$REPO_ROOT/$SKILLS_DIR"/nm-*/; do
  [ -d "$skill_dir" ] || continue
  [ -f "$skill_dir/SKILL.md" ] || continue

  skill_name=$(basename "$skill_dir")

  if [ "$DRY_RUN" = true ]; then
    echo "[dry-run] Would publish: $skill_name ($SEMVER)"
    PUBLISHED=$((PUBLISHED + 1))
    continue
  fi

  if npx clawhub skill publish "$skill_dir" \
      --slug "$skill_name" \
      --version "$SEMVER" \
      --tags latest \
      --changelog "Release $VERSION" 2>/dev/null; then
    echo "  Published: $skill_name"
    PUBLISHED=$((PUBLISHED + 1))
  else
    echo "  Failed: $skill_name"
    FAILED=$((FAILED + 1))
  fi
done

# ---------- publish package (whole plugin) ----------

echo ""
if [ "$DRY_RUN" = true ]; then
  echo "[dry-run] Would publish package: athola/claude-night-market@$VERSION"
else
  echo "Publishing package..."
  if npx clawhub package publish "athola/claude-night-market@$VERSION" 2>/dev/null; then
    echo "Package published: athola/claude-night-market@$VERSION"
  else
    echo "Warning: Package publish failed (may require manual setup)"
  fi
fi

# ---------- summary ----------

echo ""
echo "=== ClawHub Publish Summary ==="
echo "Version:   $VERSION"
echo "Published: $PUBLISHED"
echo "Skipped:   $SKIPPED"
echo "Failed:    $FAILED"

if [ "$DRY_RUN" = true ]; then
  echo ""
  echo "Dry run -- nothing was published."
  echo "Run without --dry-run to publish."
fi

if [ "$FAILED" -gt 0 ]; then
  exit 1
fi
