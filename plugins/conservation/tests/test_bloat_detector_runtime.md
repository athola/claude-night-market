# Runtime Module Loading Test

Test that modules are actually loaded and used when the bloat-detector skill is invoked.

## Test Methodology

### Phase 1: Baseline (Skill Only)

**Test:** Ask Claude about bloat detection WITHOUT referencing modules

```
Prompt: "What bloat detection patterns do you know about?"
Expected: Generic knowledge, no specific tool/technique details
```

### Phase 2: Skill Invocation

**Test:** Ask Claude to use the bloat-detector skill

```
Prompt: "Use the bloat-detector skill to explain how to detect God classes"
Expected:
- Claude reads SKILL.md
- Sees reference to modules/code-bloat-patterns.md
- Explicitly reads the module
- Provides specific detection patterns from the module
```

**Evidence of Module Loading:**
Look for responses that include:
- ✅ Specific thresholds (> 500 lines, > 10 methods)
- ✅ Detection commands from the module
- ✅ Confidence scoring from module (85%, etc.)
- ✅ Language-specific patterns (Python, JS/TS)

### Phase 3: Module Detail Verification

**Test:** Ask for specific module content

```
Prompt: "What's the exact bash command for detecting large files in the quick-scan module?"
Expected:
- Claude reads modules/quick-scan.md
- Returns the specific find command with thresholds
- Includes the 500-line threshold
```

**Success Criteria:**
```bash
# Expected output should match modules/quick-scan.md (with cache exclusions):
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" \) \
  -not -path "*/.venv/*" \
  -not -path "*/venv/*" \
  -not -path "*/__pycache__/*" \
  -not -path "*/.pytest_cache/*" \
  -not -path "*/node_modules/*" \
  -not -path "*/.git/*" \
  -not -path "*/dist/*" \
  -not -path "*/build/*" \
  -not -path "*/.tox/*" \
  -not -path "*/.mypy_cache/*" \
  -not -path "*/.ruff_cache/*" | \
while read f; do
  lines=$(wc -l < "$f")
  if [ $lines -gt 500 ]; then
    echo "$lines $f"
  fi
done | sort -rn
```

### Phase 4: Cross-Module Orchestration

**Test:** Ask for multi-module workflow

```
Prompt: "Walk me through running a Tier 2 bloat scan with focus on code patterns"
Expected:
- References SKILL.md for tier definitions
- Reads modules/code-bloat-patterns.md for detection methods
- Reads modules/git-history-analysis.md for validation
- Synthesizes workflow across modules
```

### Phase 5: Cache Directory Exclusion Test

**Test:** Verify that cache directories are excluded from scans

```
Prompt: "Run a bloat scan on the conservation plugin. How many markdown files did you find?"
Expected:
- Should NOT count files in .venv/, node_modules/, .pytest_cache/, etc.
- Should report count excluding cache directories
- File list should not include paths with excluded directories
```

**Manual Verification:**
```bash
# Count all markdown files (including cache dirs)
find plugins/conservation -name "*.md" | wc -l
# Example output: 45 files

# Count markdown files (excluding cache dirs) - should match bloat scan
find plugins/conservation -type f -name "*.md" \
  -not -path "*/.venv/*" \
  -not -path "*/.pytest_cache/*" \
  -not -path "*/node_modules/*" | wc -l
# Example output: 12 files

# The bloat scan count should match the second number, NOT the first
```

**Success Criteria:**
- ✅ Bloat scan excludes cache directories automatically
- ✅ File counts match manual count with exclusions
- ✅ No .venv, node_modules, or .pytest_cache files in scan results

## Automated Test Script

```bash
#!/bin/bash
# Test runtime module loading

echo "=== Testing bloat-detector runtime module loading ==="

# Test 1: Verify SKILL.md references modules
echo "\n[Test 1] Checking SKILL.md module references..."
grep -q "modules/quick-scan" skills/bloat-detector/SKILL.md && \
  echo "✓ quick-scan referenced" || echo "✗ quick-scan NOT referenced"

grep -q "modules/code-bloat-patterns" skills/bloat-detector/SKILL.md && \
  echo "✓ code-bloat-patterns referenced" || echo "✗ NOT referenced"

# Test 2: Verify modules are readable
echo "\n[Test 2] Checking modules are readable..."
for module in skills/bloat-detector/modules/*.md; do
  if [ -r "$module" ]; then
    echo "✓ $(basename $module) is readable"
  else
    echo "✗ $(basename $module) NOT readable"
  fi
done

# Test 3: Verify module content is substantive
echo "\n[Test 3] Checking modules have substantive content..."
for module in skills/bloat-detector/modules/*.md; do
  lines=$(wc -l < "$module")
  if [ $lines -gt 50 ]; then
    echo "✓ $(basename $module): $lines lines (substantive)"
  else
    echo "⚠ $(basename $module): $lines lines (may be too brief)"
  fi
done

# Test 4: Check for unique content in modules
echo "\n[Test 4] Verifying modules have unique content..."
if grep -q "God Class" skills/bloat-detector/modules/code-bloat-patterns.md; then
  echo "✓ code-bloat-patterns has unique God Class content"
fi

if grep -q "Flesch" skills/bloat-detector/modules/documentation-bloat.md; then
  echo "✓ documentation-bloat has unique readability metrics"
fi

if grep -q "staleness_score" skills/bloat-detector/modules/git-history-analysis.md; then
  echo "✓ git-history-analysis has unique scoring logic"
fi

echo "\n=== Test Complete ==="
```

## Interactive Test

Run in Claude Code:

```bash
# 1. Start Claude with the skill loaded
claude

# 2. Test skill awareness
> "List all modules in the bloat-detector skill"
# Claude should list: quick-scan, git-history-analysis, code-bloat-patterns, documentation-bloat

# 3. Test module reading
> "Show me the exact staleness scoring algorithm from git-history-analysis"
# Claude should read the module and show lines 34-48 from git-history-analysis.md

# 4. Test cross-module synthesis
> "How do I run a detailed bloat scan combining quick-scan and code-bloat-patterns?"
# Claude should read both modules and synthesize a workflow
```

## Evidence Collection

**Positive Indicators (module WAS loaded):**
- Response includes specific line numbers/code blocks from module
- Uses exact terminology from module frontmatter
- References module-specific thresholds (500 lines, 85% confidence, etc.)
- Provides bash commands verbatim from module

**Negative Indicators (module NOT loaded):**
- Generic/vague responses
- No specific thresholds or commands
- Doesn't mention module names explicitly
- Can't answer detailed questions about module content

## Token Usage Verification

**With Progressive Loading:**
```bash
# Initial load (SKILL.md only): ~800 tokens
# After requesting quick-scan details: +200 tokens
# After requesting code-bloat-patterns: +300 tokens
# Total: ~1,300 tokens (progressive)
```

**Without Progressive Loading (all-at-once):**
```bash
# Initial load (SKILL.md + all modules): ~1,550 tokens
# No additional loads needed
# Total: ~1,550 tokens (upfront)
```

Progressive loading saves ~250 tokens when not all modules are needed.

## Troubleshooting

### Module Not Loading

**Symptom:** Claude gives generic answer, doesn't reference module

**Debug:**
```bash
# 1. Check module reference exists
grep "modules/quick-scan" skills/bloat-detector/SKILL.md

# 2. Check module file exists and is readable
ls -la skills/bloat-detector/modules/quick-scan.md

# 3. Verify frontmatter
head -10 skills/bloat-detector/modules/quick-scan.md
```

### Module Loaded But Not Used

**Symptom:** Claude reads module but doesn't apply its patterns

**Cause:** Module content may not be directive enough

**Fix:** Add explicit instructions in module:
```markdown
## Usage

When detecting large files, use this command EXACTLY:
[command here]
```

## Conclusion

**Runtime verification requires:**
1. ✅ Static validation (modules referenced)
2. ✅ Interactive testing (Claude reads modules when asked)
3. ✅ Content verification (responses match module content)
4. ✅ Token tracking (progressive loading working)

**Without interactive testing, you can't confirm runtime behavior!**
