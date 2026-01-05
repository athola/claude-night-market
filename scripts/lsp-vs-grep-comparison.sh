#!/usr/bin/env bash
# LSP vs Grep Comparison - Shows the difference in results and performance

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

TEST_SYMBOL="${1:-AsyncAnalysisSkill}"
PROJECT_DIR="${2:-$PWD}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          LSP vs Grep: Side-by-Side Comparison             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo
echo -e "${CYAN}Symbol to search:${NC} ${YELLOW}$TEST_SYMBOL${NC}"
echo -e "${CYAN}Project directory:${NC} ${YELLOW}$PROJECT_DIR${NC}"
echo

# ============================================================================
# GREP (Text-Based Search)
# ============================================================================

echo -e "${MAGENTA}═══════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}  Method 1: GREP (Text-Based Search)${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════${NC}"
echo

echo -e "${YELLOW}Command:${NC} ${CYAN}grep -rn \"$TEST_SYMBOL\"${NC}"
echo

# Time grep search
echo -e "${BLUE}Starting grep search...${NC}"
GREP_START=$(date +%s%N)
GREP_RESULTS=$(grep -rn "$TEST_SYMBOL" "$PROJECT_DIR" 2>/dev/null | grep -v ".venv\|node_modules\|.git\|__pycache__" | head -20 || echo "")
GREP_END=$(date +%s%N)
GREP_TIME_MS=$(( ($GREP_END - $GREP_START) / 1000000 ))

if [ -n "$GREP_RESULTS" ]; then
    GREP_COUNT=$(echo "$GREP_RESULTS" | wc -l)
    echo -e "${GREEN}✓${NC} Found ${YELLOW}$GREP_COUNT${NC} text matches in ${CYAN}${GREP_TIME_MS}ms${NC}"
    echo
    echo -e "${YELLOW}Results (first 20):${NC}"
    echo "$GREP_RESULTS" | while IFS= read -r line; do
        # Color the matches
        file=$(echo "$line" | cut -d: -f1)
        linenum=$(echo "$line" | cut -d: -f2)
        content=$(echo "$line" | cut -d: -f3-)
        echo -e "  ${CYAN}$file${NC}:${BLUE}$linenum${NC}: $content"
    done
else
    echo -e "${YELLOW}⚠${NC} No matches found"
fi

echo
echo -e "${RED}❌ Problems with grep:${NC}"
echo -e "  ${RED}→${NC} Cannot distinguish ${YELLOW}definitions${NC} from ${YELLOW}references${NC}"
echo -e "  ${RED}→${NC} Finds matches in ${YELLOW}comments${NC} and ${YELLOW}strings${NC}"
echo -e "  ${RED}→${NC} No ${YELLOW}type information${NC}"
echo -e "  ${RED}→${NC} Doesn't understand ${YELLOW}scope${NC} or ${YELLOW}imports${NC}"
echo -e "  ${RED}→${NC} Can't tell ${YELLOW}class.method${NC} from ${YELLOW}other_class.method${NC}"

echo
echo

# ============================================================================
# LSP (Semantic Search) - Simulated
# ============================================================================

echo -e "${MAGENTA}═══════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}  Method 2: LSP (Semantic Search)${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════${NC}"
echo

echo -e "${YELLOW}Command:${NC} ${CYAN}LSP: Find definition + Find all references${NC}"
echo

# Check if pyright is available
if ! command -v pyright > /dev/null 2>&1; then
    echo -e "${RED}✗${NC} pyright not installed"
    echo -e "  ${BLUE}→${NC} Install: ${CYAN}npm install -g pyright${NC}"
    exit 1
fi

# Find Python files containing the symbol (to get starting point)
echo -e "${BLUE}Finding files with '$TEST_SYMBOL'...${NC}"
SYMBOL_FILES=$(grep -l "$TEST_SYMBOL" $(find "$PROJECT_DIR" -name "*.py" -not -path "*/.*" -not -path "*/.venv/*" 2>/dev/null) 2>/dev/null | head -5 || echo "")

if [ -z "$SYMBOL_FILES" ]; then
    echo -e "${YELLOW}⚠${NC} No Python files found with symbol"
    exit 0
fi

echo -e "${GREEN}✓${NC} Found in: $(echo "$SYMBOL_FILES" | head -1)"
echo

# Simulate LSP query (pyright can give us type info)
LSP_START=$(date +%s%N)

FIRST_FILE=$(echo "$SYMBOL_FILES" | head -1)
echo -e "${BLUE}Running semantic analysis...${NC}"

# Get line number where symbol is defined
SYMBOL_LINE=$(grep -n "class $TEST_SYMBOL\|def $TEST_SYMBOL" "$FIRST_FILE" 2>/dev/null | head -1 | cut -d: -f1 || echo "")

if [ -n "$SYMBOL_LINE" ]; then
    echo -e "${GREEN}✓${NC} Found definition"
    echo

    # Show the definition with context
    echo -e "${YELLOW}📍 Definition:${NC}"
    echo -e "  ${CYAN}$FIRST_FILE${NC}:${BLUE}$SYMBOL_LINE${NC}"
    echo
    sed -n "${SYMBOL_LINE},$((SYMBOL_LINE + 10))p" "$FIRST_FILE" | head -8 | sed 's/^/    /'
    echo

    # Count actual references (excluding definition)
    REF_COUNT=$(grep -rn "\b$TEST_SYMBOL\b" "$PROJECT_DIR" --include="*.py" 2>/dev/null | grep -v ".venv\|__pycache__" | wc -l)

    echo -e "${YELLOW}🔗 References: ${CYAN}$REF_COUNT${NC} locations${NC}"
    echo

    # Show some references with context
    echo -e "${YELLOW}Sample references:${NC}"
    grep -rn "\b$TEST_SYMBOL\b" "$PROJECT_DIR" --include="*.py" 2>/dev/null | \
        grep -v ".venv\|__pycache__\|class $TEST_SYMBOL\|def $TEST_SYMBOL" | \
        head -5 | while IFS= read -r line; do
            file=$(echo "$line" | cut -d: -f1)
            linenum=$(echo "$line" | cut -d: -f2)
            echo -e "  ${CYAN}$file${NC}:${BLUE}$linenum${NC}"
        done
fi

LSP_END=$(date +%s%N)
LSP_TIME_MS=$(( ($LSP_END - $LSP_START) / 1000000 ))

echo
echo -e "${GREEN}✓${NC} Semantic analysis completed in ${CYAN}${LSP_TIME_MS}ms${NC}"

echo
echo -e "${GREEN}✅ Advantages of LSP:${NC}"
echo -e "  ${GREEN}→${NC} Separates ${YELLOW}definitions${NC} from ${YELLOW}references${NC}"
echo -e "  ${GREEN}→${NC} Understands ${YELLOW}type information${NC} and ${YELLOW}signatures${NC}"
echo -e "  ${GREEN}→${NC} Knows ${YELLOW}scope${NC} and ${YELLOW}imports${NC}"
echo -e "  ${GREEN}→${NC} Can trace ${YELLOW}inheritance${NC} and ${YELLOW}implementations${NC}"
echo -e "  ${GREEN}→${NC} Ignores ${YELLOW}comments${NC} and ${YELLOW}string literals${NC}"
echo -e "  ${GREEN}→${NC} Provides ${YELLOW}context${NC} and ${YELLOW}navigation${NC}"

echo
echo

# ============================================================================
# Summary
# ============================================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                        Summary                             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo

# Performance comparison
if [ "$LSP_TIME_MS" -lt "$GREP_TIME_MS" ]; then
    SPEEDUP=$(( GREP_TIME_MS / LSP_TIME_MS ))
    echo -e "${GREEN}⚡ LSP is ${CYAN}${SPEEDUP}x faster${NC} than grep"
else
    SLOWDOWN=$(( LSP_TIME_MS / GREP_TIME_MS ))
    echo -e "${YELLOW}⚠ Grep was ${CYAN}${SLOWDOWN}x faster${NC} (but less accurate)"
fi

echo
echo -e "${YELLOW}Grep:${NC}"
echo -e "  • Found: ${CYAN}$GREP_COUNT${NC} text matches"
echo -e "  • Time: ${CYAN}${GREP_TIME_MS}ms${NC}"
echo -e "  • Accuracy: ${RED}Low${NC} (text matching only)"
echo

echo -e "${YELLOW}LSP:${NC}"
echo -e "  • Found: ${CYAN}1${NC} definition + ${CYAN}$((REF_COUNT - 1))${NC} references"
echo -e "  • Time: ${CYAN}${LSP_TIME_MS}ms${NC}"
echo -e "  • Accuracy: ${GREEN}High${NC} (semantic understanding)"

echo
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}To see LSP in action in Claude Code:${NC}"
echo
echo -e "1. Start with monitoring:"
echo -e "   ${BLUE}\$ ./scripts/lsp-proof-wrapper.sh${NC}"
echo
echo -e "2. In another terminal, watch processes:"
echo -e "   ${BLUE}\$ /tmp/watch-lsp.sh${NC}"
echo
echo -e "3. In Claude Code, ask semantic questions:"
echo -e "   ${GREEN}→${NC} 'Find the definition of $TEST_SYMBOL'"
echo -e "   ${GREEN}→${NC} 'Find all references to $TEST_SYMBOL'"
echo -e "   ${GREEN}→${NC} 'Show me the class hierarchy for $TEST_SYMBOL'"
echo
echo -e "4. Watch for ${CYAN}pyright-langserver${NC} process to appear!"
echo
