#!/usr/bin/env bash
# Pre-commit maintenance for memory-palace self-curating state.
#
# Runs the idempotent / burst-tolerant maintenance cycles and re-stages
# any artifact that actually changed, so the commit reflects curated
# state. All cycles are safe to run on every commit:
#
#   1. Capture-index drain  (promote + prune-orphans): idempotent;
#      converges to a fixed point, so quiet commits are a no-op.
#   2. Vitality refresh     (time-based decay): decays by elapsed days
#      since last recompute, so a burst of same-day commits adds ~0
#      decay while a post-gap commit decays proportionally.
#
# Every mutating step writes a timestamped backup (drain) or only
# persists on real change (vitality), so this hook is recoverable and
# sub-second when there is nothing to do.
#
# The drain then has to have worked, so the hook ends on a gate: zero
# pending entries in the index the commit carries, or the commit is
# blocked. Fresh captures reach that drain because the capture write
# stages the index (`shared/deduplication._stage_index`); without that,
# pre-commit reverts the unstaged write before this hook runs and the
# drain converges on a tree the capture is missing from.

set -euo pipefail

PLUGIN_DIR="plugins/memory-palace"
INDEX="${PLUGIN_DIR}/hooks/memory-palace-index.yaml"
VITALITY="${PLUGIN_DIR}/data/indexes/vitality-scores.yaml"
QUEUE="${PLUGIN_DIR}/data/indexes/vitality-tending-queue.json"

hash_of() {
  if [ -f "$1" ]; then md5sum "$1" | awk '{print $1}'; else echo "absent"; fi
}

index_before=$(hash_of "${INDEX}")
vitality_before=$(hash_of "${VITALITY}")
queue_before=$(hash_of "${QUEUE}")

(
  cd "${PLUGIN_DIR}"
  if [ -f "hooks/memory-palace-index.yaml" ]; then
    uv run --quiet python scripts/memory_palace_cli.py index promote --apply --top 0 \
      >/dev/null
    uv run --quiet python scripts/memory_palace_cli.py index prune-orphans --apply --top 0 \
      >/dev/null
  fi
  uv run --quiet python scripts/update_vitality_scores.py >/dev/null
)

restaged=0
restage_if_changed() {
  local path="$1" before="$2"
  if [ "${before}" != "$(hash_of "${path}")" ]; then
    git add "${path}"
    restaged=1
  fi
}

restage_if_changed "${INDEX}" "${index_before}"
restage_if_changed "${VITALITY}" "${vitality_before}"
restage_if_changed "${QUEUE}" "${queue_before}"

if [ "${restaged}" = 1 ]; then
  echo "[memory-palace] maintenance applied; curated artifacts re-staged."
fi

# The index is tracked so the drain has something to converge on, which
# only means anything if what lands is drained. The drain above resolves
# everything it can; this asserts the result and blocks the commit on
# whatever it held back. Exits nonzero under `set -e`, which is the
# block.
(
  cd "${PLUGIN_DIR}"
  uv run --quiet python scripts/check_capture_index_drained.py
)
