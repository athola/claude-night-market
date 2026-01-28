#!/usr/bin/env bash
#
# Test script for interactive authentication module
# Demonstrates basic functionality without requiring actual authentication
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "Interactive Auth Module Test Suite"
echo "========================================"
echo ""

# Source the module
# Get the repository root by going up from tests directory
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Find leyline plugin root (contains scripts/ directory)
LEYLINE_ROOT="$(cd "$TEST_DIR/../../.." && pwd)"
MODULE_PATH="$LEYLINE_ROOT/scripts/interactive_auth.sh"

if [[ ! -f "$MODULE_PATH" ]]; then
  echo -e "${RED}✗ Module not found: $MODULE_PATH${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Module file exists${NC}"

# Test 1: Syntax check
echo ""
echo "Test 1: Syntax validation"
if bash -n "$MODULE_PATH"; then
  echo -e "${GREEN}✓ Syntax is valid${NC}"
else
  echo -e "${RED}✗ Syntax errors found${NC}"
  exit 1
fi

# Test 2: Source module
echo ""
echo "Test 2: Source module"
if source "$MODULE_PATH"; then
  echo -e "${GREEN}✓ Module sourced successfully${NC}"
else
  echo -e "${RED}✗ Failed to source module${NC}"
  exit 1
fi

# Test 3: Check function availability
echo ""
echo "Test 3: Function availability"

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
  if declare -f "$func" > /dev/null; then
    echo -e "  ${GREEN}✓${NC} $func"
  else
    echo -e "  ${RED}✗${NC} $func (not found)"
    all_found=false
  fi
done

if [[ "$all_found" == "true" ]]; then
  echo -e "${GREEN}✓ All functions available${NC}"
else
  echo -e "${RED}✗ Some functions missing${NC}"
  exit 1
fi

# Test 4: Check cache directory creation
echo ""
echo "Test 4: Cache directory initialization"

TEST_CACHE_DIR="/tmp/test-auth-cache-$$"
export AUTH_CACHE_DIR="$TEST_CACHE_DIR"

init_cache_dir "github"

if [[ -d "$TEST_CACHE_DIR/github" ]]; then
  echo -e "${GREEN}✓ Cache directory created${NC}"
else
  echo -e "${RED}✗ Failed to create cache directory${NC}"
  exit 1
fi

# Test 5: Cache write and read
echo ""
echo "Test 5: Cache write and read"

write_cache "github" "true"

if [[ -f "$TEST_CACHE_DIR/github/auth_status.json" ]]; then
  echo -e "${GREEN}✓ Cache file created${NC}"
else
  echo -e "${RED}✗ Failed to create cache file${NC}"
  exit 1
fi

# Test 6: Cache validation
echo ""
echo "Test 6: Cache validation"

if check_cache "github"; then
  echo -e "${GREEN}✓ Cache validation works${NC}"
else
  echo -e "${RED}✗ Cache validation failed${NC}"
  exit 1
fi

# Test 7: Session creation
echo ""
echo "Test 7: Session creation"

create_session "github"

if [[ -f "$TEST_CACHE_DIR/github/session.json" ]]; then
  echo -e "${GREEN}✓ Session file created${NC}"
else
  echo -e "${RED}✗ Failed to create session file${NC}"
  exit 1
fi

# Test 8: Session validation
echo ""
echo "Test 8: Session validation"

if load_session "github"; then
  echo -e "${GREEN}✓ Session validation works${NC}"
else
  echo -e "${RED}✗ Session validation failed${NC}"
  exit 1
fi

# Test 9: Cache invalidation
echo ""
echo "Test 9: Cache invalidation"

invalidate_auth_cache "github" > /dev/null 2>&1

if [[ ! -f "$TEST_CACHE_DIR/github/auth_status.json" ]]; then
  echo -e "${GREEN}✓ Cache invalidated${NC}"
else
  echo -e "${RED}✗ Cache invalidation failed${NC}"
  exit 1
fi

# Test 10: Clear all caches
echo ""
echo "Test 10: Clear all caches"

clear_all_auth_cache > /dev/null 2>&1

if [[ ! -d "$TEST_CACHE_DIR" ]]; then
  echo -e "${GREEN}✓ All caches cleared${NC}"
else
  echo -e "${RED}✗ Failed to clear all caches${NC}"
  exit 1
fi

# Test 11: Interactive detection
echo ""
echo "Test 11: Interactive mode detection"

export AUTH_INTERACTIVE=true
if is_interactive; then
  echo -e "${GREEN}✓ Interactive mode detected (forced)${NC}"
else
  echo -e "${YELLOW}⚠ May not be a TTY${NC}"
fi

export AUTH_INTERACTIVE=false
if ! is_interactive; then
  echo -e "${GREEN}✓ Non-interactive mode detected (forced)${NC}"
else
  echo -e "${RED}✗ Interactive mode should be false${NC}"
  exit 1
fi

# Test 12: CI/CD detection
echo ""
echo "Test 12: CI/CD environment detection"

unset CI GITHUB_ACTIONS GITLAB_CI AWS_EXECUTION_ENV
if ! is_ci; then
  echo -e "${GREEN}✓ Correctly detected non-CI environment${NC}"
else
  echo -e "${YELLOW}⚠ Running in CI environment${NC}"
fi

export CI=true
if is_ci; then
  echo -e "${GREEN}✓ CI environment detected${NC}"
else
  echo -e "${RED}✗ Failed to detect CI environment${NC}"
  exit 1
fi

unset CI

# Test 13: Unsupported service error handling
echo ""
echo "Test 13: Unsupported service error handling"

if ensure_auth "unsupported_service" 2>/dev/null; then
  echo -e "${RED}✗ Should have failed for unsupported service${NC}"
  exit 1
else
  echo -e "${GREEN}✓ Correctly rejected unsupported service${NC}"
fi

# Test 14: Usage validation
echo ""
echo "Test 14: Usage validation"

if ensure_auth 2>/dev/null; then
  echo -e "${RED}✗ Should have failed with no arguments${NC}"
  exit 1
else
  echo -e "${GREEN}✓ Correctly rejected missing service argument${NC}"
fi

# Cleanup
echo ""
echo "Cleanup"
rm -rf "$TEST_CACHE_DIR" 2>/dev/null || true
echo -e "${GREEN}✓ Test artifacts cleaned up${NC}"

# Summary
echo ""
echo "========================================"
echo -e "${GREEN}All tests passed!${NC}"
echo "========================================"
echo ""
echo "Module is ready for use in workflows."
echo ""
echo "Quick start:"
echo "  source plugins/leyline/scripts/interactive_auth.sh"
echo "  ensure_auth github || exit 1"
echo "  gh pr view 123"
echo ""
