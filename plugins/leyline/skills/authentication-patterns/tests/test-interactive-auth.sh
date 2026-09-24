#!/usr/bin/env bash
#
# Test script for interactive authentication module
# Demonstrates basic functionality without requiring actual authentication
#

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

main() {
  case "${1:-}" in
    -x | -t) set -x ;;
  esac

  printf '%s\n' "========================================"
  printf '%s\n' "Interactive Auth Module Test Suite"
  printf '%s\n' "========================================"
  printf '\n'

  # Source the module
  # Get the repository root by going up from tests directory
  # Parameter expansion in place of dirname; a bare name means the cwd.
  case "${BASH_SOURCE[0]}" in
    */*) src_dir="${BASH_SOURCE[0]%/*}" ;;
    *) src_dir="." ;;
  esac
  TEST_DIR="$(cd "${src_dir:-/}" && pwd)"
  # Find leyline plugin root (contains scripts/ directory)
  LEYLINE_ROOT="$(cd "${TEST_DIR}/../../.." && pwd)"
  MODULE_PATH="${LEYLINE_ROOT}/scripts/interactive_auth.sh"

  if [[ ! -f "${MODULE_PATH}" ]]; then
    printf '%b\n' "${RED}✗ Module not found: ${MODULE_PATH}${NC}"
    exit 1
  fi

  printf '%b\n' "${GREEN}✓ Module file exists${NC}"

  # Test 1: Syntax check
  printf '\n'
  printf '%s\n' "Test 1: Syntax validation"
  if bash -n "${MODULE_PATH}"; then
    printf '%b\n' "${GREEN}✓ Syntax is valid${NC}"
  else
    printf '%b\n' "${RED}✗ Syntax errors found${NC}"
    exit 1
  fi

  # Test 2: Source module
  printf '\n'
  printf '%s\n' "Test 2: Source module"
  # shellcheck source=plugins/leyline/scripts/interactive_auth.sh
  if source "${MODULE_PATH}"; then
    printf '%b\n' "${GREEN}✓ Module sourced successfully${NC}"
  else
    printf '%b\n' "${RED}✗ Failed to source module${NC}"
    exit 1
  fi

  # Test 3: Check function availability
  printf '\n'
  printf '%s\n' "Test 3: Function availability"

  functions=(
    "ensure_auth"
    "check_auth_status"
    "invalidate_auth_cache"
    "clear_all_auth_cache"
    "is_interactive"
    "is_ci"
  )

  all_found=true
  for func in "${functions[@]}"; do
    if declare -f "${func}" >/dev/null; then
      printf '%b\n' "  ${GREEN}✓${NC} ${func}"
    else
      printf '%b\n' "  ${RED}✗${NC} ${func} (not found)"
      all_found=false
    fi
  done

  if [[ "${all_found}" == "true" ]]; then
    printf '%b\n' "${GREEN}✓ All functions available${NC}"
  else
    printf '%b\n' "${RED}✗ Some functions missing${NC}"
    exit 1
  fi

  # Test 4: Check cache directory creation
  printf '\n'
  printf '%s\n' "Test 4: Cache directory initialization"

  TEST_CACHE_DIR="/tmp/test-auth-cache-${$}"
  export AUTH_CACHE_DIR="${TEST_CACHE_DIR}"

  init_cache_dir "github"

  if [[ -d "${TEST_CACHE_DIR}/github" ]]; then
    printf '%b\n' "${GREEN}✓ Cache directory created${NC}"
  else
    printf '%b\n' "${RED}✗ Failed to create cache directory${NC}"
    exit 1
  fi

  # Test 5: Cache write and read
  printf '\n'
  printf '%s\n' "Test 5: Cache write and read"

  write_cache "github" "true"

  if [[ -f "${TEST_CACHE_DIR}/github/auth_status.json" ]]; then
    printf '%b\n' "${GREEN}✓ Cache file created${NC}"
  else
    printf '%b\n' "${RED}✗ Failed to create cache file${NC}"
    exit 1
  fi

  # Test 6: Cache validation
  printf '\n'
  printf '%s\n' "Test 6: Cache validation"

  if check_cache "github"; then
    printf '%b\n' "${GREEN}✓ Cache validation works${NC}"
  else
    printf '%b\n' "${RED}✗ Cache validation failed${NC}"
    exit 1
  fi

  # Test 7: Session creation
  printf '\n'
  printf '%s\n' "Test 7: Session creation"

  create_session "github"

  if [[ -f "${TEST_CACHE_DIR}/github/session.json" ]]; then
    printf '%b\n' "${GREEN}✓ Session file created${NC}"
  else
    printf '%b\n' "${RED}✗ Failed to create session file${NC}"
    exit 1
  fi

  # Test 8: Session validation
  printf '\n'
  printf '%s\n' "Test 8: Session validation"

  if load_session "github"; then
    printf '%b\n' "${GREEN}✓ Session validation works${NC}"
  else
    printf '%b\n' "${RED}✗ Session validation failed${NC}"
    exit 1
  fi

  # Test 9: Cache invalidation
  printf '\n'
  printf '%s\n' "Test 9: Cache invalidation"

  invalidate_auth_cache "github" >/dev/null 2>&1

  if [[ ! -f "${TEST_CACHE_DIR}/github/auth_status.json" ]]; then
    printf '%b\n' "${GREEN}✓ Cache invalidated${NC}"
  else
    printf '%b\n' "${RED}✗ Cache invalidation failed${NC}"
    exit 1
  fi

  # Test 10: Clear all caches
  printf '\n'
  printf '%s\n' "Test 10: Clear all caches"

  clear_all_auth_cache >/dev/null 2>&1

  if [[ ! -d "${TEST_CACHE_DIR}" ]]; then
    printf '%b\n' "${GREEN}✓ All caches cleared${NC}"
  else
    printf '%b\n' "${RED}✗ Failed to clear all caches${NC}"
    exit 1
  fi

  # Test 11: Interactive detection
  printf '\n'
  printf '%s\n' "Test 11: Interactive mode detection"

  export AUTH_INTERACTIVE=true
  if is_interactive; then
    printf '%b\n' "${GREEN}✓ Interactive mode detected (forced)${NC}"
  else
    printf '%b\n' "${YELLOW}⚠ May not be a TTY${NC}"
  fi

  export AUTH_INTERACTIVE=false
  if ! is_interactive; then
    printf '%b\n' "${GREEN}✓ Non-interactive mode detected (forced)${NC}"
  else
    printf '%b\n' "${RED}✗ Interactive mode should be false${NC}"
    exit 1
  fi

  # Test 12: CI/CD detection
  printf '\n'
  printf '%s\n' "Test 12: CI/CD environment detection"

  unset CI GITHUB_ACTIONS GITLAB_CI AWS_EXECUTION_ENV
  if ! is_ci; then
    printf '%b\n' "${GREEN}✓ Correctly detected non-CI environment${NC}"
  else
    printf '%b\n' "${YELLOW}⚠ Running in CI environment${NC}"
  fi

  export CI=true
  if is_ci; then
    printf '%b\n' "${GREEN}✓ CI environment detected${NC}"
  else
    printf '%b\n' "${RED}✗ Failed to detect CI environment${NC}"
    exit 1
  fi

  unset CI

  # Test 13: Unsupported service error handling
  printf '\n'
  printf '%s\n' "Test 13: Unsupported service error handling"

  if ensure_auth "unsupported_service" 2>/dev/null; then
    printf '%b\n' "${RED}✗ Should have failed for unsupported service${NC}"
    exit 1
  else
    printf '%b\n' "${GREEN}✓ Correctly rejected unsupported service${NC}"
  fi

  # Test 14: Usage validation
  printf '\n'
  printf '%s\n' "Test 14: Usage validation"

  if ensure_auth 2>/dev/null; then
    printf '%b\n' "${RED}✗ Should have failed with no arguments${NC}"
    exit 1
  else
    printf '%b\n' "${GREEN}✓ Correctly rejected missing service argument${NC}"
  fi

  # Cleanup
  printf '\n'
  printf '%s\n' "Cleanup"
  rm -rf "${TEST_CACHE_DIR}" 2>/dev/null || true
  printf '%b\n' "${GREEN}✓ Test artifacts cleaned up${NC}"

  # Summary
  printf '\n'
  printf '%s\n' "========================================"
  printf '%b\n' "${GREEN}All tests passed!${NC}"
  printf '%s\n' "========================================"
  printf '\n'
  printf '%s\n' "Module is ready for use in workflows."
  printf '\n'
  printf '%s\n' "Quick start:"
  printf '%s\n' "  source plugins/leyline/scripts/interactive_auth.sh"
  printf '%s\n' "  ensure_auth github || exit 1"
  printf '%s\n' "  gh pr view 123"
  printf '\n'
}

main "$@"
