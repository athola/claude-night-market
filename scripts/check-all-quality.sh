#!/bin/bash
# Run comprehensive quality checks on entire codebase
#
# Usage:
#   ./scripts/check-all-quality.sh [--fix] [--report]
#
# Options:
#   --fix     Auto-fix linting issues where possible
#   --report  Generate detailed report file

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

AUTO_FIX=false
GENERATE_REPORT=false
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_FILE="audit/quality-report-${TIMESTAMP}.md"

# Parse arguments
for arg in "$@"; do
    case $arg in
        --fix)
            AUTO_FIX=true
            ;;
        --report)
            GENERATE_REPORT=true
            mkdir -p audit
            ;;
    esac
done

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          Comprehensive Code Quality Check                    ║${NC}"
echo -e "${BLUE}║          All Plugins - Full Codebase Audit                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo

# Initialize report
if [ "$GENERATE_REPORT" = true ]; then
    cat > "$REPORT_FILE" <<EOF
# Code Quality Report

**Date**: $(date)
**Branch**: $(git branch --show-current)
**Commit**: $(git rev-parse --short HEAD)

## Summary

EOF
fi

LINT_FAILED=false
TYPECHECK_FAILED=false
TEST_FAILED=false

# ============================================================
# 1. Linting
# ============================================================

echo -e "${BLUE}════ Phase 1: Linting All Plugins ════${NC}"
echo

LINT_OUTPUT=$(mktemp)
if [ "$AUTO_FIX" = true ]; then
    echo -e "${YELLOW}Running with auto-fix enabled...${NC}"
fi

if ./scripts/run-plugin-lint.sh --all 2>&1 | tee "$LINT_OUTPUT"; then
    echo -e "${GREEN}✓ All plugins passed linting${NC}"
    LINT_STATUS="PASS"
else
    echo -e "${RED}✗ Some plugins failed linting${NC}"
    LINT_STATUS="FAIL"
    LINT_FAILED=true
fi

if [ "$GENERATE_REPORT" = true ]; then
    echo "### Linting: $LINT_STATUS" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    tail -20 "$LINT_OUTPUT" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    echo >> "$REPORT_FILE"
fi

echo
echo "─────────────────────────────────────────────────────────────"
echo

# ============================================================
# 2. Type Checking
# ============================================================

echo -e "${BLUE}════ Phase 2: Type Checking All Plugins ════${NC}"
echo

TYPECHECK_OUTPUT=$(mktemp)
if ./scripts/run-plugin-typecheck.sh --all 2>&1 | tee "$TYPECHECK_OUTPUT"; then
    echo -e "${GREEN}✓ All plugins passed type checking${NC}"
    TYPECHECK_STATUS="PASS"
else
    echo -e "${RED}✗ Some plugins failed type checking${NC}"
    TYPECHECK_STATUS="FAIL"
    TYPECHECK_FAILED=true
fi

if [ "$GENERATE_REPORT" = true ]; then
    echo "### Type Checking: $TYPECHECK_STATUS" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    tail -20 "$TYPECHECK_OUTPUT" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    echo >> "$REPORT_FILE"
fi

echo
echo "─────────────────────────────────────────────────────────────"
echo

# ============================================================
# 3. Testing
# ============================================================

echo -e "${BLUE}════ Phase 3: Testing All Plugins ════${NC}"
echo

TEST_OUTPUT=$(mktemp)
if ./scripts/run-plugin-tests.sh --all 2>&1 | tee "$TEST_OUTPUT"; then
    echo -e "${GREEN}✓ All plugins passed tests${NC}"
    TEST_STATUS="PASS"
else
    echo -e "${RED}✗ Some plugins failed tests${NC}"
    TEST_STATUS="FAIL"
    TEST_FAILED=true
fi

if [ "$GENERATE_REPORT" = true ]; then
    echo "### Testing: $TEST_STATUS" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    tail -20 "$TEST_OUTPUT" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    echo >> "$REPORT_FILE"
fi

echo
echo "─────────────────────────────────────────────────────────────"
echo

# ============================================================
# Final Summary
# ============================================================

echo -e "${BLUE}════ Final Summary ════${NC}"
echo

TOTAL_FAILED=0
if [ "$LINT_FAILED" = true ]; then
    echo -e "${RED}✗ Linting: FAILED${NC}"
    TOTAL_FAILED=$((TOTAL_FAILED + 1))
else
    echo -e "${GREEN}✓ Linting: PASSED${NC}"
fi

if [ "$TYPECHECK_FAILED" = true ]; then
    echo -e "${RED}✗ Type Checking: FAILED${NC}"
    TOTAL_FAILED=$((TOTAL_FAILED + 1))
else
    echo -e "${GREEN}✓ Type Checking: PASSED${NC}"
fi

if [ "$TEST_FAILED" = true ]; then
    echo -e "${RED}✗ Testing: FAILED${NC}"
    TOTAL_FAILED=$((TOTAL_FAILED + 1))
else
    echo -e "${GREEN}✓ Testing: PASSED${NC}"
fi

echo

if [ $TOTAL_FAILED -eq 0 ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                  🎉 ALL CHECKS PASSED 🎉                      ║${NC}"
    echo -e "${GREEN}║          Codebase meets all quality standards!               ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    FINAL_STATUS="PASS"
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                   ⚠️  CHECKS FAILED ⚠️                        ║${NC}"
    echo -e "${RED}║          $TOTAL_FAILED check(s) failed - see details above              ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
    FINAL_STATUS="FAIL"
fi

if [ "$GENERATE_REPORT" = true ]; then
    echo >> "$REPORT_FILE"
    echo "## Final Status: $FINAL_STATUS" >> "$REPORT_FILE"
    echo >> "$REPORT_FILE"
    echo "- Linting: $LINT_STATUS" >> "$REPORT_FILE"
    echo "- Type Checking: $TYPECHECK_STATUS" >> "$REPORT_FILE"
    echo "- Testing: $TEST_STATUS" >> "$REPORT_FILE"
    echo >> "$REPORT_FILE"
    echo "**Total Failed**: $TOTAL_FAILED / 3" >> "$REPORT_FILE"

    echo
    echo -e "${BLUE}Report saved to: $REPORT_FILE${NC}"
fi

echo
echo "Next steps:"
if [ $TOTAL_FAILED -gt 0 ]; then
    echo "1. Review failures above"
    echo "2. Fix issues in failing plugins"
    echo "3. Run individual checks: ./scripts/run-plugin-{lint|typecheck|test}.sh <plugin>"
    echo "4. Re-run this script to verify fixes"
    if [ "$AUTO_FIX" = false ]; then
        echo "5. Try with --fix flag for automatic linting fixes"
    fi
else
    echo "1. Commit your changes"
    echo "2. Pre-commit hooks will enforce quality on future commits"
    echo "3. Re-run monthly: ./scripts/check-all-quality.sh --report"
fi

# Cleanup
rm -f "$LINT_OUTPUT" "$TYPECHECK_OUTPUT" "$TEST_OUTPUT"

# Exit with appropriate code
if [ $TOTAL_FAILED -gt 0 ]; then
    exit 1
fi

exit 0
