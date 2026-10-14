#!/usr/bin/env bash
# capabilities-sync-check.sh - Verify capabilities docs match plugin registrations
# Used by: make docs-sync-check
# Exit non-zero if discrepancies found
# Requires: jq
# Compatible with bash 3.2+ (no associative arrays)
#
# Usage: scripts/capabilities-sync-check.sh [-h] [-x|-t]

set -euo pipefail

# A bare name (`bash capabilities-sync-check.sh` from inside scripts/) has
# no slash for `${0%/*}` to strip, so it would come back unchanged.
case "${0}" in
  */*) MYDIR="${0%/*}" ;;
  *) MYDIR="." ;;
esac
readonly MYDIR

# shellcheck source=scripts/logging.sh
. "${MYDIR%/}/logging.sh"

REPO_ROOT="$(cd "${MYDIR%/}/.." && pwd)"
readonly REPO_ROOT
readonly CAPS_REF="${REPO_ROOT}/book/src/reference/capabilities-reference.md"
readonly PLUGINS_DIR="${REPO_ROOT}/plugins"
readonly REQUIRED_DEPENDENCIES="jq"

XTRACE=0
ERRORS=0
MISSING_ENTRIES=()
EXTRA_ENTRIES=()
# Temp files instead of associative arrays (bash 3.2 compat)
WORK_DIR=""

usage() {
  log "Usage: scripts/capabilities-sync-check.sh [-h] [-x|-t]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
}

depcheck() {
  local missing="" utility
  for utility in ${REQUIRED_DEPENDENCIES}; do
    command -v "${utility}" >/dev/null 2>&1 ||
      missing="${missing:+"${missing} "}${utility}"
  done
  case "${missing}" in
    "") return 0 ;;
  esac
  log 5 "Required utilities not found: ${missing}"
  return 1
}

# Writes "<name>\t<plugin>" lines for every skill, command and agent that a
# plugin.json registers, one file per kind under WORK_DIR.
collect_registrations() {
  local plugin_json plugin_name kind entry_path entry_name

  for kind in skills commands agents; do
    : >"${WORK_DIR}/${kind}"
  done

  for plugin_json in "${PLUGINS_DIR}"/*/.claude-plugin/plugin.json; do
    [ -f "${plugin_json}" ] || continue
    plugin_name=$(jq -r '.name' "${plugin_json}")

    # Skill entries are directories; commands and agents are .md files.
    for kind in skills commands agents; do
      while IFS= read -r entry_path; do
        [ -z "${entry_path}" ] && continue
        entry_name="${entry_path##*/}"
        printf '%s\t%s\n' "${entry_name%.md}" "${plugin_name}" >>"${WORK_DIR}/${kind}"
      done < <(jq -r --arg kind "${kind}" '.[$kind][]? // empty' "${plugin_json}")
    done
  done
}

# Prints the first-column names of the table under "### <heading>".
# awk instead of sed for BSD/GNU portability.
documented_names() {
  awk -v heading="### ${1:?documented_names needs a heading}" \
    'index($0, heading) == 1 {f=1;next} /^### /{f=0} f && /^\| `/{gsub(/^\| `|`.*$/,"",$0); print}' \
    "${CAPS_REF}"
}

# compare_kind LABEL REGISTERED_FILE DOCUMENTED_NAMES
compare_kind() {
  local label="${1}" registered="${2}" documented="${3}" name plugin

  while IFS=$'\t' read -r name plugin; do
    [ -z "${name}" ] && continue
    if ! printf '%s\n' "${documented}" | grep -Fqx "${name}"; then
      MISSING_ENTRIES+=("${label}: ${name} (${plugin}) - registered but NOT in docs")
      ERRORS=$((ERRORS + 1))
    fi
  done <"${registered}"

  while IFS= read -r name; do
    [ -z "${name}" ] && continue
    if ! grep -q "^${name}	" "${registered}"; then
      EXTRA_ENTRIES+=("${label}: ${name} - in docs but NOT registered in any plugin.json")
      ERRORS=$((ERRORS + 1))
    fi
  done <<<"${documented}"
}

# print_entries HEADER [ENTRY...]: prints nothing when no entry is given.
print_entries() {
  local header="${1}" entry
  shift
  case "${#}" in
    0) return 0 ;;
  esac
  log 4 "${header}"
  for entry in "${@}"; do
    log 4 "  - ${entry}"
  done
}

report() {
  local total_skills total_commands total_agents

  print_entries "MISSING from docs (registered in plugin.json but not documented):" \
    "${MISSING_ENTRIES[@]+"${MISSING_ENTRIES[@]}"}"
  print_entries "EXTRA in docs (documented but not registered in any plugin.json):" \
    "${EXTRA_ENTRIES[@]+"${EXTRA_ENTRIES[@]}"}"

  total_skills=$(wc -l <"${WORK_DIR}/skills" | tr -d ' ')
  total_commands=$(wc -l <"${WORK_DIR}/commands" | tr -d ' ')
  total_agents=$(wc -l <"${WORK_DIR}/agents" | tr -d ' ')
  log "Summary: ${total_skills} skills, ${total_commands} commands, ${total_agents} agents registered"

  case "${ERRORS}" in
    0) log "PASSED: All capabilities are in sync" ;;
    *)
      log 4 "FAILED: ${ERRORS} discrepancies found"
      return 1
      ;;
  esac
}

main() {
  local doc_skills doc_commands doc_agents

  while [ "${#}" -gt 0 ]; do
    case "${1}" in
      *[uU][sS][aA][gG][eE] | *[hH][eE][lL][pP] | -h)
        usage
        exit 0
        ;;
      -x | -t)
        XTRACE=1
        ;;
    esac
    shift
  done

  case "${XTRACE}" in
    1) set -x ;;
  esac

  if [ ! -f "${CAPS_REF}" ]; then
    log 4 "capabilities-reference.md not found at ${CAPS_REF}"
    exit 1
  fi
  depcheck || exit 1

  WORK_DIR=$(mktemp -d)
  trap 'rm -rf "${WORK_DIR}"' EXIT

  collect_registrations
  doc_skills=$(documented_names "All Skills")
  doc_commands=$(documented_names "All Commands" | sed 's|^/||; s|^[a-z-]*:||')
  doc_agents=$(documented_names "All Agents")

  log "=== Capabilities Sync Check ==="
  log "--- Skills ---"
  compare_kind SKILL "${WORK_DIR}/skills" "${doc_skills}"
  log "--- Commands ---"
  compare_kind COMMAND "${WORK_DIR}/commands" "${doc_commands}"
  log "--- Agents ---"
  compare_kind AGENT "${WORK_DIR}/agents" "${doc_agents}"

  report
}

main "$@"
