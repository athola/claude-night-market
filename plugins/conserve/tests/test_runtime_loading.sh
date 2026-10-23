#!/usr/bin/env bash
# Runtime module loading verification for bloat-detector.
# Usage: test_runtime_loading.sh [-h] [-x|-t]
set -euo pipefail

# A bare name has no slash, and `${0%/*}` would return the name itself.
case "${0}" in
  */*) MYDIR="${0%/*}" ;;
  *) MYDIR="." ;;
esac
readonly MYDIR

# Resolved from the script, not the working directory, so it runs from
# the repository root. SKILL_DIR overrides it to check a copy.
SKILL_DIR="${SKILL_DIR:-${MYDIR%/}/../skills/bloat-detector}"
readonly SKILL_DIR
MODULES_DIR="${SKILL_DIR}/modules"
readonly MODULES_DIR

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

# Same box as scripts/logging.sh banner().
banner() {
  _banner_line="$(printf '%*s' 60 '' | tr ' ' '=')"
  printf '\n%s\n  %s\n%s\n\n' "${_banner_line}" "${1:?banner: message required}" "${_banner_line}"
}

usage() {
  log "Usage: ${MYDIR%/}/test_runtime_loading.sh [-h] [-x|-t]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
  printf '\nEnvironment overrides:\n'
  printf '  SKILL_DIR   (default: ../skills/bloat-detector beside this script)\n'
}

heading() {
  printf '\n'
  log "${1}"
}

# Test 1: Verify skill file exists
check_skill_file() {
  heading "[Test 1] Skill File Existence"
  if [ -f "${SKILL_DIR}/SKILL.md" ]; then
    log "✓ SKILL.md found"
  else
    log 4 "✗ SKILL.md NOT found"
    exit 1
  fi
}

# Test 2: Verify modules directory exists
check_modules_dir() {
  local module_files module_count
  heading "[Test 2] Modules Directory"
  if [ -d "${MODULES_DIR}" ]; then
    module_files=("${MODULES_DIR}"/*.md)
    module_count=${#module_files[@]}
    log "✓ modules/ directory found (${module_count} modules)"
  else
    log 4 "✗ modules/ directory NOT found"
    exit 1
  fi
}

# Test 3: Verify all modules are referenced in SKILL.md
check_module_references() {
  local module module_name unreferenced=0
  heading "[Test 3] Module References in SKILL.md"
  # grep reads the files directly. Piping `echo "$content" | grep -q` under
  # pipefail returned 141 once grep -q quit early on a file larger than the
  # pipe buffer, which read a found module as missing.
  for module in "${MODULES_DIR}"/*.md; do
    module_name="${module##*/}"
    module_name="${module_name%.md}"
    if grep -q "${module_name}" "${SKILL_DIR}/SKILL.md"; then
      log "✓ ${module_name} referenced"
    else
      log 4 "✗ ${module_name} NOT referenced"
      unreferenced=$((unreferenced + 1))
    fi
  done

  case "${unreferenced}" in
    0) ;;
    *)
      log 4 "❌ FAILED: ${unreferenced} unreferenced module(s)"
      exit 1
      ;;
  esac
}

# Test 4: Verify modules have substantive content
check_module_length() {
  local module module_name line_count
  heading "[Test 4] Module Content Substantiveness"
  for module in "${MODULES_DIR}"/*.md; do
    module_name="${module##*/}"
    line_count=$(wc -l <"${module}")

    if [ "${line_count}" -gt 50 ]; then
      log "✓ ${module_name}: ${line_count} lines (substantive)"
    elif [ "${line_count}" -gt 20 ]; then
      log 2 "⚠ ${module_name}: ${line_count} lines (brief but okay)"
    else
      log 4 "✗ ${module_name}: ${line_count} lines (too brief!)"
      exit 1
    fi
  done
}

# Test 5: Verify modules have required frontmatter
check_module_frontmatter() {
  local module module_name
  heading "[Test 5] Module Frontmatter"
  for module in "${MODULES_DIR}"/*.md; do
    module_name="${module##*/}"

    if grep -q "^---" "${module}"; then
      if grep -q "module:" "${module}"; then
        if grep -q "category:" "${module}"; then
          log "✓ ${module_name} has valid frontmatter"
        else
          log 4 "✗ ${module_name} missing 'category:'"
          exit 1
        fi
      else
        log 4 "✗ ${module_name} missing 'module:'"
        exit 1
      fi
    else
      log 4 "✗ ${module_name} missing frontmatter"
      exit 1
    fi
  done
}

# Test 6: Verify unique module content
check_module_patterns() {
  heading "[Test 6] Unique Module Content"

  # Check for specific patterns in each module
  if grep -q "God Class" "${MODULES_DIR}/code-bloat-patterns.md"; then
    log "✓ code-bloat-patterns has God Class detection"
  else
    log 2 "⚠ code-bloat-patterns missing God Class pattern"
  fi

  if grep -q "staleness_score\|months_since" "${MODULES_DIR}/git-history-analysis.md"; then
    log "✓ git-history-analysis has staleness scoring"
  else
    log 2 "⚠ git-history-analysis missing staleness logic"
  fi

  if grep -q "Flesch\|readability" "${MODULES_DIR}/documentation-bloat.md"; then
    log "✓ documentation-bloat has readability metrics"
  else
    log 2 "⚠ documentation-bloat missing readability content"
  fi

  if grep -q "find.*-name.*\.py\|wc -l" "${MODULES_DIR}/quick-scan.md"; then
    log "✓ quick-scan has file size detection commands"
  else
    log 2 "⚠ quick-scan missing detection commands"
  fi
}

# Test 7: Verify no spoke-to-spoke references
check_hub_spoke() {
  local module current_module other_module other_name violations=0
  heading "[Test 7] Hub-Spoke Pattern Compliance"

  for module in "${MODULES_DIR}"/*.md; do
    current_module="${module##*/}"
    current_module="${current_module%.md}"

    for other_module in "${MODULES_DIR}"/*.md; do
      other_name="${other_module##*/}"
      other_name="${other_name%.md}"

      case "${other_name}" in
        "${current_module}") continue ;;
      esac
      # Check for module reference patterns
      if grep -qE "modules/${other_name}|${other_name}\.md" "${module}"; then
        log 4 "✗ ${current_module} references ${other_name} (spoke-to-spoke violation)"
        violations=$((violations + 1))
      fi
    done
  done

  case "${violations}" in
    0) log "✓ No spoke-to-spoke references (hub-spoke pattern maintained)" ;;
    *)
      log 4 "❌ FAILED: ${violations} spoke-to-spoke reference(s) found"
      exit 1
      ;;
  esac
}

# Test 8: Progressive loading marker
check_progressive_loading() {
  heading "[Test 8] Progressive Loading"
  if grep -q "progressive_loading: true" "${SKILL_DIR}/SKILL.md"; then
    log "✓ Progressive loading enabled"
  else
    log 2 "⚠ Progressive loading not enabled (optional)"
  fi
}

summary() {
  banner "✅ ALL RUNTIME STRUCTURE TESTS PASSED"
  log "Next steps for full runtime verification:"
  log "1. Start Claude Code: claude"
  log "2. Test skill invocation: \"Use bloat-detector to explain God classes\""
  log "3. Verify module loading: Check for specific thresholds (>500 lines, etc.)"
  log "4. Test cross-module: \"Run Tier 2 scan with code and git analysis\""
  printf '\n'
  log "Expected runtime behavior:"
  log "- Claude reads SKILL.md when skill invoked"
  log "- Claude reads module files when specific details needed"
  log "- Responses include exact commands/thresholds from modules"
  log "- Token usage increases progressively as modules loaded"
}

main() {
  while [ "${#}" -gt 0 ]; do
    case "${1}" in
      *[uU][sS][aA][gG][eE] | *[hH][eE][lL][pP] | -h)
        usage
        exit 0
        ;;
      -x | -t)
        XTRACE=1
        ;;
      *)
        log 4 "Unknown option: ${1}"
        usage
        exit 1
        ;;
    esac
    shift
  done

  case "${XTRACE}" in
    1) set -x ;;
  esac

  banner "Runtime Module Loading Test - bloat-detector"
  check_skill_file
  check_modules_dir
  check_module_references
  check_module_length
  check_module_frontmatter
  check_module_patterns
  check_hub_spoke
  check_progressive_loading
  summary
}

main "$@"
