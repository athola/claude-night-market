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

# ---------- publish each skill independently ----------

# Rationale (issue #570): `clawhub sync --all` is a single bulk call
# that aborts on the first hard error. During the v1.9.11 release a
# `Version already exists` collision on one skill halted the run after
# 68/188 skills, leaving ~120 unpublished, and re-running made no
# progress because the same skill kept colliding first.
#
# We instead publish each skill in its own `clawhub publish` call so
# one skill's failure never blocks the rest. A version-collision
# ("already exists") is treated as an idempotent skip, not a failure,
# so re-runs converge. Real failures are collected and reported but do
# not abort the run.
#
# Out of scope (clawhub CLI): the version string clawhub derives per
# skill (the v1.9.11 collision was on "1.0.3", which matches neither
# the release tag nor the manifest version). Fixing that derivation
# belongs in the clawhub CLI, tracked as a follow-up. This script only
# makes the publish loop resilient to it.

SEMVER="${VERSION#v}"

echo ""
echo "Publishing $EXPORTED skill(s) individually for $VERSION..."
echo ""

SUMMARY=$(
  SKILLS_DIR="$REPO_ROOT/$SKILLS_DIR" \
  SEMVER="$SEMVER" VERSION="$VERSION" \
  DRY_RUN="$DRY_RUN" CLAWHUB="$CLAWHUB" python3 -c '
import json, os, shlex, subprocess, sys
from pathlib import Path

skills_dir = Path(os.environ["SKILLS_DIR"])
semver = os.environ["SEMVER"]
version = os.environ["VERSION"]
dry_run = os.environ["DRY_RUN"] == "true"
clawhub = shlex.split(os.environ["CLAWHUB"])

manifest = json.loads((skills_dir / "manifest.json").read_text())
skills = manifest.get("skills", [])

published, skipped, failed = [], [], []

for skill in skills:
    slug = skill["slug"]
    skill_dir = skills_dir / slug
    if not skill_dir.is_dir():
        print(f"  FAIL: {slug} (directory missing)")
        failed.append((slug, "directory missing"))
        continue

    if dry_run:
        print(f"  [dry-run] would publish: {slug}")
        published.append(slug)
        continue

    cmd = clawhub + [
        "publish", str(skill_dir),
        "--slug", slug,
        "--version", semver,
        "--tags", "latest",
        "--changelog", f"Release {version}",
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        print(f"  FAIL: {slug} (timeout)")
        failed.append((slug, "timeout"))
        continue
    except Exception as e:  # noqa: BLE001 - keep the loop alive
        print(f"  FAIL: {slug} ({e})")
        failed.append((slug, str(e)))
        continue

    out = ((r.stderr or "") + (r.stdout or "")).strip()
    low = out.lower()
    if r.returncode == 0:
        print(f"  OK: {slug}")
        published.append(slug)
    elif "already exists" in low:
        # Idempotent: this version is already on ClawHub. Skip, do
        # not fail, so the run completes and re-runs converge.
        print(f"  SKIP: {slug} (version already exists)")
        skipped.append(slug)
    else:
        msg = out or "unknown error"
        if len(msg) > 200:
            msg = msg[:200] + "..."
        print(f"  FAIL: {slug} ({msg})")
        failed.append((slug, msg))

print("")
print("=== ClawHub Publish Summary ===")
print(f"Version:   {version}")
print(f"Total:     {len(skills)}")
print(f"Published: {len(published)}")
print(f"Skipped:   {len(skipped)} (already exists)")
print(f"Failed:    {len(failed)}")
if dry_run:
    print("Mode:      dry-run")
if failed:
    print("")
    print("Failed skills:")
    for slug, why in failed:
        print(f"  - {slug}: {why}")

# Exit non-zero only on genuine failures. Collisions/skips are fine.
sys.exit(1 if failed else 0)
'
) && PUBLISH_EXIT=0 || PUBLISH_EXIT=$?

echo "$SUMMARY"

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

# ---------- final status ----------

echo ""
if [ "$PUBLISH_EXIT" -ne 0 ]; then
  echo "Status:  completed with failures (see list above)"
  echo "Re-run this script to retry; already-published skills are skipped."
  exit 1
else
  echo "Status:  complete"
fi
