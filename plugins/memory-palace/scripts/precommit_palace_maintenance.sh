#!/usr/bin/env bash
# Pre-commit maintenance for memory-palace self-curating state.
# Usage: precommit_palace_maintenance.sh [-h] [-x|-t]
#
# Runs the idempotent / burst-tolerant maintenance cycles and re-stages
# any artifact that actually changed, so the commit reflects curated
# state. All cycles are safe to run on every commit:
#
#   1. Capture-index drain  (promote + prune-orphans + retitle):
#      idempotent; converges to a fixed point, so quiet commits are a
#      no-op. Retitle repairs entries whose stored title is not a title
#      (#624); a repaired title is proposed no further, so it settles.
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
readonly PLUGIN_DIR INDEX VITALITY QUEUE

REQUIRED_DEPENDENCIES="git uv"
readonly REQUIRED_DEPENDENCIES

XTRACE=0

# The plugin is installed on its own, so the repository's
# scripts/logging.sh is not on disk beside it. This is the same
# interface at level 1: informational output on stdout, errors on
# stderr, and no bare echo anywhere.
log() {
  _log_level=1
  case "${1:-}" in
    [0-9])
      _log_level="${1}"
      shift
      ;;
  esac
  case "${_log_level}" in
    4 | 5) printf '[ERROR] %s\n' "${*}" >&2 ;;
    2 | 3) printf '[WARN]  %s\n' "${*}" >&2 ;;
    *) printf '[INFO]  %s\n' "${*}" ;;
  esac
}

usage() {
  log "Usage: precommit_palace_maintenance.sh [-h] [-x|-t]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
  printf '\nRun from the repository root, as the pre-commit hook does.\n'
}

depcheck() {
  _dc_missing=""
  for _dc_util in ${REQUIRED_DEPENDENCIES}; do
    command -v "${_dc_util}" >/dev/null 2>&1 ||
      _dc_missing="${_dc_missing:+"${_dc_missing} "}${_dc_util}"
  done
  case "${_dc_missing}" in
    "") return 0 ;;
  esac
  log 5 "Required utilities not found: ${_dc_missing}"
  return 1
}

# git hash-object, not md5sum: a commit hook always has git, and md5sum
# is missing on macOS before 14 and on BSD.
hash_of() {
  if [ -f "${1}" ]; then git hash-object "${1}"; else printf 'absent\n'; fi
}

run_maintenance() {
  (
    cd "${PLUGIN_DIR}"
    if [ -f "hooks/memory-palace-index.yaml" ]; then
      uv run --quiet python scripts/memory_palace_cli.py index promote --apply --top 0 \
        >/dev/null
      uv run --quiet python scripts/memory_palace_cli.py index prune-orphans --apply --top 0 \
        >/dev/null
      uv run --quiet python scripts/memory_palace_cli.py index retitle --apply --top 0 \
        >/dev/null
    fi
    uv run --quiet python scripts/update_vitality_scores.py >/dev/null
  )
}

restage_if_changed() {
  local path="${1}" before="${2}"
  case "$(hash_of "${path}")" in
    "${before}") ;;
    *)
      git add "${path}"
      restaged=1
      ;;
  esac
}

main() {
  while [ "${#}" -gt 0 ]; do
    case "${1}" in
      *[uU][sS][aA][gG][eE] | *[hH][eE][lL][pP] | -h)
        usage
        exit 0
        ;;
      -x | -t) XTRACE=1 ;;
    esac
    shift
  done

  case "${XTRACE}" in
    1) set -x ;;
  esac

  depcheck || exit 1

  index_before=$(hash_of "${INDEX}")
  vitality_before=$(hash_of "${VITALITY}")
  queue_before=$(hash_of "${QUEUE}")

  run_maintenance

  restaged=0
  restage_if_changed "${INDEX}" "${index_before}"
  restage_if_changed "${VITALITY}" "${vitality_before}"
  restage_if_changed "${QUEUE}" "${queue_before}"

  case "${restaged}" in
    1) log "[memory-palace] maintenance applied; curated artifacts re-staged." ;;
  esac

  # The index is tracked so the drain has something to converge on, which
  # only means anything if what lands is drained. The drain above resolves
  # everything it can; this asserts the result and blocks the commit on
  # whatever it held back. Exits nonzero under `set -e`, which is the
  # block.
  (
    cd "${PLUGIN_DIR}"
    uv run --quiet python scripts/check_capture_index_drained.py
  )
}

main "$@"
