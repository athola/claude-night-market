---
module: snapshot-management
category: voice-learning
dependencies: [Bash, Write, Read]
estimated_tokens: 400
---

# Snapshot Management Module

Capture and organize text snapshots for the learning loop.

## Snapshot Stages

| Stage | When Captured | Purpose |
|-------|--------------|---------|
| pre-review | After generation, before review agents | Baseline output |
| post-review | After user accepts/rejects advisories | Review impact |
| post-edit | When user runs /voice-learn | Manual edit patterns |

## File Naming

```
{piece-name}-{YYYYMMDD-HHMMSS}-{stage}.md
```

Example:
```
blog-api-design-20260410-143022-pre-review.md
blog-api-design-20260410-143022-post-review.md
blog-api-design-20260410-145511-post-edit.md
```

## Capture Commands

### Pre-review (automatic)

Called by voice-generate after producing text:
```bash
SNAP_DIR="$HOME/.claude/voice-profiles/$PROFILE/learning/snapshots"
PIECE_NAME="$1"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
cp "$OUTPUT_FILE" "$SNAP_DIR/${PIECE_NAME}-${TIMESTAMP}-pre-review.md"
```

### Post-review (automatic)

Called by voice-review after user completes advisory decisions:
```bash
cp "$REVIEWED_FILE" "$SNAP_DIR/${PIECE_NAME}-${TIMESTAMP}-post-review.md"
```

### Post-edit (user-triggered)

User runs `/voice-learn` after making manual edits:
```bash
cp "$EDITED_FILE" "$SNAP_DIR/${PIECE_NAME}-${TIMESTAMP}-post-edit.md"
```

## Snapshot Sets

A complete set has all three stages with matching piece-name
and timestamp prefix. Incomplete sets (missing post-edit) are
ignored by the learning agent until completed.

## Manifest Tracking

Update `manifest.json` learning section:
```json
{
  "learning": {
    "snapshot_count": 12,
    "complete_sets": 4,
    "last_capture": "2026-04-10",
    "last_learning_pass": "2026-04-09"
  }
}
```

## Cleanup

Snapshots older than 90 days with completed learning passes
can be archived or deleted. The accumulator retains the
pattern evidence independent of raw snapshots.
