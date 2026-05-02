#!/usr/bin/env bash
# Batch-publish skills to ClawHub from the export directory.
#
# Reads manifest.json to find all exported skills, publishes them
# in batches (default: 5 per batch), and tracks progress in
# .egregore/clawhub-progress.json so the egregore can resume.
#
# Usage:
#   ./scripts/clawhub-batch-publish.sh                  # publish next batch
#   ./scripts/clawhub-batch-publish.sh --batch-size 10  # custom batch size
#   ./scripts/clawhub-batch-publish.sh --retry-failed   # retry failed skills
#   ./scripts/clawhub-batch-publish.sh --status         # show progress

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
SKILLS_DIR="$REPO_ROOT/clawhub"
PROGRESS_FILE="$REPO_ROOT/.egregore/clawhub-progress.json"

# ---------- defaults ----------

BATCH_SIZE=5
RETRY_FAILED=false
STATUS_ONLY=false
DRY_RUN=false
VERSION=""

# ---------- parse args ----------

while [ $# -gt 0 ]; do
  case "$1" in
    --batch-size=*) BATCH_SIZE="${1#*=}"; shift ;;
    --batch-size)
      if [ $# -lt 2 ]; then
        echo "Error: --batch-size requires a value"; exit 1
      fi
      BATCH_SIZE="$2"; shift 2
      ;;
    --retry-failed) RETRY_FAILED=true; shift ;;
    --status) STATUS_ONLY=true; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    v*) VERSION="$1"; shift ;;
    [0-9]*) VERSION="v$1"; shift ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

if [ -z "$VERSION" ]; then
  VERSION="v$(REPO_ROOT="$REPO_ROOT" python3 -c "
import json, os
print(json.load(open(os.path.join(os.environ['REPO_ROOT'], 'plugins/abstract/.claude-plugin/plugin.json')))['version'])
")"
fi

SEMVER="${VERSION#v}"

# ---------- preflight ----------

if ! command -v npx &>/dev/null; then
  echo "Error: npx required"
  exit 1
fi

if [ ! -f "$SKILLS_DIR/manifest.json" ]; then
  echo "Building clawhub export..."
  cd "$REPO_ROOT"
  python3 scripts/clawhub_export.py --output "$SKILLS_DIR"
fi

# ---------- init progress file if missing ----------

if [ ! -f "$PROGRESS_FILE" ]; then
  SKILLS_DIR="$SKILLS_DIR" SEMVER="$SEMVER" PROGRESS_FILE="$PROGRESS_FILE" python3 -c "
import json, os
from pathlib import Path

manifest = json.loads(Path(os.path.join(os.environ['SKILLS_DIR'], 'manifest.json')).read_text())
skills = manifest.get('skills', [])
progress = {
    'version': os.environ['SEMVER'],
    'total': len(skills),
    'published': [],
    'failed': [],
    'pending': [s['slug'] for s in skills],
    'batches_completed': 0,
    'started_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
}
Path(os.environ['PROGRESS_FILE']).write_text(json.dumps(progress, indent=2))
print(f'Initialized progress: {len(skills)} skills to publish')
"
fi

# ---------- status command ----------

if [ "$STATUS_ONLY" = true ]; then
  PROGRESS_FILE="$PROGRESS_FILE" BATCH_SIZE="$BATCH_SIZE" python3 -c "
import json, os
from pathlib import Path

p = json.loads(Path(os.environ['PROGRESS_FILE']).read_text())
batch_size = int(os.environ['BATCH_SIZE'])
print(f'Version:    {p[\"version\"]}')
print(f'Total:      {p[\"total\"]}')
print(f'Published:  {len(p[\"published\"])}')
print(f'Failed:     {len(p[\"failed\"])}')
print(f'Pending:    {len(p[\"pending\"])}')
print(f'Batches:    {p[\"batches_completed\"]}')
pct = (len(p['published']) / p['total'] * 100) if p['total'] else 0
print(f'Progress:   {pct:.1f}%')
if p['pending']:
    print(f'Next batch: {p[\"pending\"][:batch_size]}')
"
  exit 0
fi

# ---------- dry-run preview ----------

if [ "$DRY_RUN" = true ]; then
  PROGRESS_FILE="$PROGRESS_FILE" RETRY_FAILED="$RETRY_FAILED" \
    BATCH_SIZE="$BATCH_SIZE" VERSION="$VERSION" python3 -c "
import json, os
from pathlib import Path

p = json.loads(Path(os.environ['PROGRESS_FILE']).read_text())
batch_size = int(os.environ['BATCH_SIZE'])
retry_failed = os.environ.get('RETRY_FAILED', 'false')

if retry_failed == 'true' and p['failed']:
    batch, mode = p['failed'][:batch_size], 'retry'
elif p['pending']:
    batch, mode = p['pending'][:batch_size], 'publish'
else:
    print('No pending skills to publish.')
    raise SystemExit(0)

print(f'[dry-run] mode: {mode}')
print(f'[dry-run] would publish {len(batch)} skill(s) for {os.environ[\"VERSION\"]}:')
for slug in batch:
    print(f'  - {slug}')
print(f'[dry-run] no state changes, no network calls')
"
  exit 0
fi

# ---------- publish batch ----------

RESULT=$(PROGRESS_FILE="$PROGRESS_FILE" RETRY_FAILED="$RETRY_FAILED" \
  BATCH_SIZE="$BATCH_SIZE" SKILLS_DIR="$SKILLS_DIR" \
  SEMVER="$SEMVER" VERSION="$VERSION" python3 -c "
import json, os
import subprocess
import sys
from pathlib import Path

progress_file = os.environ['PROGRESS_FILE']
retry_failed = os.environ.get('RETRY_FAILED', 'false')
batch_size = int(os.environ['BATCH_SIZE'])
skills_dir = os.environ['SKILLS_DIR']
semver = os.environ['SEMVER']
version = os.environ['VERSION']

progress = json.loads(Path(progress_file).read_text())

if retry_failed == 'true' and progress['failed']:
    batch = progress['failed'][:batch_size]
    mode = 'retry'
elif progress['pending']:
    batch = progress['pending'][:batch_size]
    mode = 'publish'
else:
    print('No pending skills to publish.')
    sys.exit(0)

published = []
failed = []

for slug in batch:
    skill_dir = Path(skills_dir) / slug
    if not skill_dir.is_dir():
        print(f'  SKIP: {slug} (directory missing)')
        failed.append(slug)
        continue

    try:
        result = subprocess.run(
            ['npx', 'clawhub', 'publish', str(skill_dir),
             '--slug', slug,
             '--version', semver,
             '--tags', 'latest',
             '--changelog', f'Release {version}'],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            print(f'  OK: {slug}')
            published.append(slug)
        else:
            err = result.stderr.strip() or result.stdout.strip() or 'unknown error'
            # Truncate long errors
            if len(err) > 200:
                err = err[:200] + '...'
            print(f'  FAIL: {slug} ({err})')
            failed.append(slug)
    except subprocess.TimeoutExpired:
        print(f'  TIMEOUT: {slug}')
        failed.append(slug)
    except Exception as e:
        print(f'  ERROR: {slug} ({e})')
        failed.append(slug)

# Update progress
for slug in published:
    if slug in progress['pending']:
        progress['pending'].remove(slug)
    if slug in progress['failed']:
        progress['failed'].remove(slug)
    if slug not in progress['published']:
        progress['published'].append(slug)

for slug in failed:
    if slug in progress['pending']:
        progress['pending'].remove(slug)
    if slug not in progress['failed']:
        progress['failed'].append(slug)

progress['batches_completed'] += 1

Path(progress_file).write_text(json.dumps(progress, indent=2))

pct = (len(progress['published']) / progress['total'] * 100) if progress['total'] else 0
print(f'')
print(f'Batch {progress[\"batches_completed\"]} ({mode}): {len(published)} ok, {len(failed)} fail')
print(f'Overall: {len(progress[\"published\"])}/{progress[\"total\"]} ({pct:.1f}%)')
print(f'Remaining: {len(progress[\"pending\"])} pending, {len(progress[\"failed\"])} failed')
")

echo "$RESULT"

# Exit with failure if no skills published this batch
if echo "$RESULT" | grep -q "0 ok"; then
  echo "Warning: No skills published in this batch."
fi
