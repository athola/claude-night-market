#!/usr/bin/env bash
# Publish night-market skills to ClawHub via the clawhub CLI.
#
# Uses `clawhub sync` for bulk publishing: scans the export
# directory, detects new/updated skills, and uploads them.
#
# Usage:
#   ./scripts/clawhub-submit.sh v1.8.3
#   ./scripts/clawhub-submit.sh v1.8.3 --dry-run
#   ./scripts/clawhub-submit.sh              # uses version from plugin.json
#
# Note: ClawHub enforces a rate limit of 5 new skills/hour.
# For initial publish of 100+ skills, the sync will partially
# complete and can be re-run to continue where it left off.

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

# ---------- preflight ----------

# Find clawhub binary
CLAWHUB=""
if command -v clawhub &>/dev/null; then
  CLAWHUB="clawhub"
elif command -v npx &>/dev/null && npx clawhub --help &>/dev/null 2>&1; then
  CLAWHUB="npx clawhub"
else
  echo "Error: clawhub CLI not found."
  echo "Install: npm install -g clawhub"
  echo "    or: curl -fsSL https://clawhub.dev/install.sh | sh"
  exit 1
fi

# Verify authentication
if ! $CLAWHUB whoami &>/dev/null 2>&1; then
  echo "Error: Not authenticated with ClawHub."
  echo "Run: $CLAWHUB login"
  exit 1
fi

CLAWHUB_USER=$($CLAWHUB whoami 2>/dev/null | grep -oP '(?<=✔ )\S+' || $CLAWHUB whoami 2>/dev/null)
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

# ---------- sync (bulk publish) ----------

SYNC_ARGS=(
  --workdir "$REPO_ROOT/$SKILLS_DIR"
  --dir .
  --all
  --tags latest
  --changelog "Release $VERSION"
  --concurrency 1
)

if [ "$DRY_RUN" = true ]; then
  SYNC_ARGS+=(--dry-run)
fi

echo ""
echo "Running: $CLAWHUB sync ${SYNC_ARGS[*]}"
echo ""

# Capture exit code without tripping `set -e`.
# Plain `$CLAWHUB sync ...; SYNC_EXIT=$?` is unreachable when sync
# fails because errexit terminates the script first. The `|| ...`
# tested-context exempts the command from errexit so we can fall
# through to the partial-sync messaging below.
SYNC_EXIT=0
$CLAWHUB sync "${SYNC_ARGS[@]}" || SYNC_EXIT=$?

# ---------- publish package ----------

echo ""
if [ "$DRY_RUN" = true ]; then
  echo "[dry-run] Would publish package: athola/claude-night-market@$VERSION"
else
  echo "Publishing package..."
  if $CLAWHUB package publish "athola/claude-night-market@$VERSION" 2>/dev/null; then
    echo "Package published: athola/claude-night-market@$VERSION"
  else
    echo "Warning: Package publish failed (may require manual setup)"
  fi
fi

# ---------- summary ----------

echo ""
echo "=== ClawHub Publish Summary ==="
echo "Version: $VERSION"
echo "Skills:  $EXPORTED"

if [ "$DRY_RUN" = true ]; then
  echo "Mode:    dry-run"
fi

if [ "$SYNC_EXIT" -ne 0 ]; then
  echo "Status:  partial (rate limit or error)"
  echo ""
  echo "Re-run this script to continue publishing."
  echo "clawhub sync only uploads new/updated skills."
  exit 1
else
  echo "Status:  complete"
fi
