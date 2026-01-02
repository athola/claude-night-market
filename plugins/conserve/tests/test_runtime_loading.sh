#!/bin/bash
# Runtime module loading verification for bloat-detector

set -e

SKILL_DIR="skills/bloat-detector"
MODULES_DIR="$SKILL_DIR/modules"

echo "============================================================"
echo "Runtime Module Loading Test - bloat-detector"
echo "============================================================"

# Test 1: Verify skill file exists
echo -e "\n[Test 1] Skill File Existence"
if [ -f "$SKILL_DIR/SKILL.md" ]; then
    echo "✓ SKILL.md found"
else
    echo "✗ SKILL.md NOT found"
    exit 1
fi

# Test 2: Verify modules directory exists
echo -e "\n[Test 2] Modules Directory"
if [ -d "$MODULES_DIR" ]; then
    module_count=$(ls -1 "$MODULES_DIR"/*.md 2>/dev/null | wc -l)
    echo "✓ modules/ directory found ($module_count modules)"
else
    echo "✗ modules/ directory NOT found"
    exit 1
fi

# Test 3: Verify all modules are referenced in SKILL.md
echo -e "\n[Test 3] Module References in SKILL.md"
skill_content=$(cat "$SKILL_DIR/SKILL.md")
unreferenced=()

for module in "$MODULES_DIR"/*.md; do
    module_name=$(basename "$module" .md)
    if echo "$skill_content" | grep -q "$module_name"; then
        echo "✓ $module_name referenced"
    else
        echo "✗ $module_name NOT referenced"
        unreferenced+=("$module_name")
    fi
done

if [ ${#unreferenced[@]} -gt 0 ]; then
    echo -e "\n❌ FAILED: ${#unreferenced[@]} unreferenced module(s)"
    exit 1
fi

# Test 4: Verify modules have substantive content
echo -e "\n[Test 4] Module Content Substantiveness"
for module in "$MODULES_DIR"/*.md; do
    module_name=$(basename "$module")
    line_count=$(wc -l < "$module")

    if [ $line_count -gt 50 ]; then
        echo "✓ $module_name: $line_count lines (substantive)"
    elif [ $line_count -gt 20 ]; then
        echo "⚠ $module_name: $line_count lines (brief but okay)"
    else
        echo "✗ $module_name: $line_count lines (too brief!)"
        exit 1
    fi
done

# Test 5: Verify modules have required frontmatter
echo -e "\n[Test 5] Module Frontmatter"
for module in "$MODULES_DIR"/*.md; do
    module_name=$(basename "$module")
    content=$(cat "$module")

    if echo "$content" | grep -q "^---"; then
        if echo "$content" | grep -q "module:"; then
            if echo "$content" | grep -q "category:"; then
                echo "✓ $module_name has valid frontmatter"
            else
                echo "✗ $module_name missing 'category:'"
                exit 1
            fi
        else
            echo "✗ $module_name missing 'module:'"
            exit 1
        fi
    else
        echo "✗ $module_name missing frontmatter"
        exit 1
    fi
done

# Test 6: Verify unique module content
echo -e "\n[Test 6] Unique Module Content"

# Check for specific patterns in each module
if grep -q "God Class" "$MODULES_DIR/code-bloat-patterns.md"; then
    echo "✓ code-bloat-patterns has God Class detection"
else
    echo "⚠ code-bloat-patterns missing God Class pattern"
fi

if grep -q "staleness_score\|months_since" "$MODULES_DIR/git-history-analysis.md"; then
    echo "✓ git-history-analysis has staleness scoring"
else
    echo "⚠ git-history-analysis missing staleness logic"
fi

if grep -q "Flesch\|readability" "$MODULES_DIR/documentation-bloat.md"; then
    echo "✓ documentation-bloat has readability metrics"
else
    echo "⚠ documentation-bloat missing readability content"
fi

if grep -q "find.*-name.*\.py\|wc -l" "$MODULES_DIR/quick-scan.md"; then
    echo "✓ quick-scan has file size detection commands"
else
    echo "⚠ quick-scan missing detection commands"
fi

# Test 7: Verify no spoke-to-spoke references
echo -e "\n[Test 7] Hub-Spoke Pattern Compliance"
violations=0

for module in "$MODULES_DIR"/*.md; do
    current_module=$(basename "$module" .md)
    content=$(cat "$module")

    for other_module in "$MODULES_DIR"/*.md; do
        other_name=$(basename "$other_module" .md)

        if [ "$current_module" != "$other_name" ]; then
            # Check for module reference patterns
            if echo "$content" | grep -qE "modules/$other_name|$other_name\.md"; then
                echo "✗ $current_module references $other_name (spoke-to-spoke violation)"
                violations=$((violations + 1))
            fi
        fi
    done
done

if [ $violations -eq 0 ]; then
    echo "✓ No spoke-to-spoke references (hub-spoke pattern maintained)"
else
    echo -e "\n❌ FAILED: $violations spoke-to-spoke reference(s) found"
    exit 1
fi

# Test 8: Progressive loading marker
echo -e "\n[Test 8] Progressive Loading"
if grep -q "progressive_loading: true" "$SKILL_DIR/SKILL.md"; then
    echo "✓ Progressive loading enabled"
else
    echo "⚠ Progressive loading not enabled (optional)"
fi

# Summary
echo -e "\n============================================================"
echo "✅ ALL RUNTIME STRUCTURE TESTS PASSED"
echo "============================================================"
echo ""
echo "Next steps for full runtime verification:"
echo "1. Start Claude Code: claude"
echo "2. Test skill invocation: \"Use bloat-detector to explain God classes\""
echo "3. Verify module loading: Check for specific thresholds (>500 lines, etc.)"
echo "4. Test cross-module: \"Run Tier 2 scan with code and git analysis\""
echo ""
echo "Expected runtime behavior:"
echo "- Claude reads SKILL.md when skill invoked"
echo "- Claude reads module files when specific details needed"
echo "- Responses include exact commands/thresholds from modules"
echo "- Token usage increases progressively as modules loaded"
echo ""
