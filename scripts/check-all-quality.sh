#!/usr/bin/env bash
# Run comprehensive quality checks on entire codebase
#
# Usage:
#   ./scripts/check-all-quality.sh [-h] [-x|-t] [--fix] [--report]
#
# Options:
#   --fix     Auto-fix linting issues where possible
#   --report  Generate detailed report file

set -euo pipefail

# A bare name (`bash check-all-quality.sh` from inside scripts/) has no
# slash for `${0%/*}` to strip, so it would come back unchanged.
case "${0}" in
  */*) MYDIR="${0%/*}" ;;
  *) MYDIR="." ;;
esac
readonly MYDIR

# shellcheck source=scripts/logging.sh
. "${MYDIR%/}/logging.sh"

PROJECT_ROOT="$(cd "${MYDIR%/}/.." && pwd)"
readonly PROJECT_ROOT
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
readonly TIMESTAMP
# Relative on purpose: every phase runs from PROJECT_ROOT.
readonly REPORT_FILE="audit/quality-report-${TIMESTAMP}.md"

AUTO_FIX=false
GENERATE_REPORT=false
XTRACE=0
TOTAL_FAILED=0
# Output captures, one per phase, removed on exit.
PHASE_OUTPUTS=()
# Set by run_phase: PASS or FAIL.
PHASE_STATUS=""

usage() {
  log "Usage: scripts/check-all-quality.sh [-h] [-x|-t] [--fix] [--report]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
  printf '  --fix       Auto-fix linting issues where possible\n'
  printf '  --report    Write a report to audit/quality-report-<timestamp>.md\n'
}

cleanup() {
  rm -f "${PHASE_OUTPUTS[@]+"${PHASE_OUTPUTS[@]}"}"
}

# run_phase NAME COMMAND [ARGS...]
# Runs one sub-runner, shows its output, sets PHASE_STATUS, and appends its
# tail to the report when one was asked for.
run_phase() {
  local name="${1:?run_phase needs a name}" output exit_code
  shift

  output=$(mktemp)
  PHASE_OUTPUTS+=("${output}")

  # The exit code is read from PIPESTATUS so tee cannot mask it.
  if
    "$@" 2>&1 | tee "${output}"
    exit_code=${PIPESTATUS[0]}
    [ "${exit_code}" -eq 0 ]
  then
    PHASE_STATUS="PASS"
  else
    PHASE_STATUS="FAIL"
    TOTAL_FAILED=$((TOTAL_FAILED + 1))
  fi

  case "${GENERATE_REPORT}" in
    true)
      {
        printf '### %s: %s\n' "${name}" "${PHASE_STATUS}"
        printf '```\n'
        tail -20 "${output}"
        printf '```\n'
        printf '\n'
      } >>"${REPORT_FILE}"
      ;;
  esac
}

# log_result STATUS PASS_MESSAGE FAIL_MESSAGE
log_result() {
  case "${1}" in
    PASS) log "${2}" ;;
    *) log 4 "${3}" ;;
  esac
}

run_quality_checks() {
  local lint_status typecheck_status test_status final_status
  local lint_args=(--all)

  cd "${PROJECT_ROOT}"
  trap cleanup EXIT

  banner "Comprehensive Code Quality Check: All Plugins, Full Codebase Audit" 72

  # Initialize report
  case "${GENERATE_REPORT}" in
    true)
      mkdir -p audit
      cat >"${REPORT_FILE}" <<EOF
# Code Quality Report

**Date**: $(date)
**Branch**: $(git branch --show-current)
**Commit**: $(git rev-parse --short HEAD)

## Summary

EOF
      ;;
  esac

  # 1. Linting
  log "==== Phase 1: Linting All Plugins ===="
  case "${AUTO_FIX}" in
    true)
      log "Running with auto-fix enabled..."
      lint_args+=(--fix)
      ;;
  esac
  run_phase "Linting" ./scripts/run-plugin-lint.sh "${lint_args[@]}"
  lint_status="${PHASE_STATUS}"
  log_result "${lint_status}" \
    "All plugins passed linting" "Some plugins failed linting"

  # 2. Type Checking
  log "==== Phase 2: Type Checking All Plugins ===="
  run_phase "Type Checking" ./scripts/run-plugin-typecheck.sh --all
  typecheck_status="${PHASE_STATUS}"
  log_result "${typecheck_status}" \
    "All plugins passed type checking" "Some plugins failed type checking"

  # 3. Testing
  log "==== Phase 3: Testing All Plugins ===="
  run_phase "Testing" ./scripts/run-plugin-tests.sh --all
  test_status="${PHASE_STATUS}"
  log_result "${test_status}" \
    "All plugins passed tests" "Some plugins failed tests"

  # Final Summary
  log "==== Final Summary ===="
  log_result "${lint_status}" "Linting: PASSED" "Linting: FAILED"
  log_result "${typecheck_status}" \
    "Type Checking: PASSED" "Type Checking: FAILED"
  log_result "${test_status}" "Testing: PASSED" "Testing: FAILED"

  case "${TOTAL_FAILED}" in
    0)
      banner "ALL CHECKS PASSED: codebase meets all quality standards" 72
      final_status="PASS"
      ;;
    *)
      banner "CHECKS FAILED: ${TOTAL_FAILED} check(s) failed, see details above" 72
      final_status="FAIL"
      ;;
  esac

  case "${GENERATE_REPORT}" in
    true)
      {
        printf '\n'
        printf '## Final Status: %s\n' "${final_status}"
        printf '\n'
        printf -- '- Linting: %s\n' "${lint_status}"
        printf -- '- Type Checking: %s\n' "${typecheck_status}"
        printf -- '- Testing: %s\n' "${test_status}"
        printf '\n'
        printf '**Total Failed**: %s / 3\n' "${TOTAL_FAILED}"
      } >>"${REPORT_FILE}"
      log "Report saved to: ${REPORT_FILE}"
      ;;
  esac

  log "Next steps:"
  case "${TOTAL_FAILED}" in
    0)
      log "1. Commit your changes"
      log "2. Pre-commit hooks will enforce quality on future commits"
      log "3. Re-run monthly: ./scripts/check-all-quality.sh --report"
      ;;
    *)
      log "1. Review failures above"
      log "2. Fix issues in failing plugins"
      log "3. Run individual checks: ./scripts/run-plugin-{lint|typecheck|test}.sh <plugin>"
      log "4. Re-run this script to verify fixes"
      case "${AUTO_FIX}" in
        false) log "5. Try with --fix flag for automatic linting fixes" ;;
      esac
      return 1
      ;;
  esac
}

main() {
  local arg
  for arg in "$@"; do
    case "${arg}" in
      *[uU][sS][aA][gG][eE] | *[hH][eE][lL][pP] | -h)
        usage
        exit 0
        ;;
      -x | -t) XTRACE=1 ;;
      --fix) AUTO_FIX=true ;;
      --report) GENERATE_REPORT=true ;;
    esac
  done

  case "${XTRACE}" in
    1) set -x ;;
  esac

  # The subshell keeps the cd into PROJECT_ROOT, and the cleanup trap,
  # to the checks themselves.
  (run_quality_checks)
}

main "$@"
