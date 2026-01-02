# Test Plan: Project Init 1.2.0 + Knowledge Corpus Integration

**Branch**: `project-init-1.2.0`
**Date**: 2026-01-02
**Scope**: Attune plugin, conserve plugin enhancements, memory-palace queue integration

## Overview

This PR includes:
1. **Attune Plugin** - New plugin for project initialization and workflow setup
2. **Conserve Plugin Enhancement** - Static analysis integration module for bloat detection
3. **Memory Palace** - Knowledge corpus queue processing and integration
4. **Conservation → Conserve Rename** - Plugin rename with all references updated

## Test Categories

### 1. Attune Plugin Testing

#### 1.1 Plugin Structure Validation
```bash
# Verify plugin structure
python3 plugins/attune/tests/test_plugin_structure.py

# Expected: All plugin structure tests pass
# - Metadata files exist
# - Required directories present
# - Plugin.json valid
```

#### 1.2 Project Detection
```bash
# Test project type detection
python3 -m pytest plugins/attune/tests/test_project_detector.py -v

# Expected: Detect Python, Rust, TypeScript projects correctly
```

#### 1.3 Template Engine
```bash
# Test template rendering
python3 -m pytest plugins/attune/tests/test_template_engine.py -v

# Expected: Templates render with correct context
# - Variables substituted
# - Conditional blocks work
# - No template syntax errors
```

#### 1.4 Version Fetching
```bash
# Test version fetcher
python3 -m pytest plugins/attune/tests/test_version_fetcher.py -v

# Expected: Fetch latest versions from registries
# - PyPI for Python packages
# - crates.io for Rust
# - npm for JavaScript/TypeScript
```

#### 1.5 Project Validation
```bash
# Test project validation
python3 -m pytest plugins/attune/tests/test_validate_project.py -v

# Expected: Validate project structure
# - Required files present
# - Configuration valid
# - Dependencies resolvable
```

#### 1.6 Integration Tests
```bash
# Full workflow integration
python3 -m pytest plugins/attune/tests/test_integration.py -v

# Expected: End-to-end workflows work
# - init → detect → template → validate
# - Multiple project types
# - Error handling
```

#### 1.7 Attune Init Script
```bash
# Test attune_init.py
python3 -m pytest plugins/attune/tests/test_attune_init.py -v

# Expected: Initialize projects correctly
# - Create required files
# - Set up git hooks
# - Configure tooling
```

### 2. Conserve Plugin Testing

#### 2.1 Bloat Detector Module Structure ✅
```bash
# Verify all modules properly referenced
python3 plugins/conserve/tests/test_bloat_detector_modules.py

# Status: PASSED (verified 2026-01-02)
# ✅ All 5 modules referenced in SKILL.md
# ✅ All modules have valid frontmatter
# ✅ Hub-spoke pattern maintained
```

**Modules Verified:**
- ✅ `quick-scan.md` (237 lines)
- ✅ `git-history-analysis.md` (276 lines)
- ✅ `code-bloat-patterns.md` (638 lines)
- ✅ `documentation-bloat.md` (634 lines)
- ✅ `static-analysis-integration.md` (638 lines) **← NEW**

#### 2.2 Static Analysis Integration Testing

**Test Suite for New Module:**

```bash
# Create test scenarios for static-analysis-integration module
cat > /tmp/test_static_analysis.sh << 'EOF'
#!/bin/bash
set -e

echo "=== Testing Static Analysis Integration ==="

# Test 1: Tool Detection
echo "Test 1: Tool detection..."
which vulture && echo "✅ Vulture detected" || echo "⚠️  Vulture not installed"
which deadcode && echo "✅ deadcode detected" || echo "⚠️  deadcode not installed"
which autoflake && echo "✅ autoflake detected" || echo "⚠️  autoflake not installed"
which knip && echo "✅ Knip detected" || echo "⚠️  Knip not installed"

# Test 2: Python Dead Code Detection (if vulture available)
if command -v vulture &> /dev/null; then
    echo "Test 2: Running Vulture on sample code..."
    mkdir -p /tmp/bloat-test
    cat > /tmp/bloat-test/sample.py << 'PYTHON'
def used_function():
    return "I'm used!"

def unused_function():
    return "I'm never called!"

result = used_function()
PYTHON

    vulture /tmp/bloat-test/sample.py --min-confidence 80
    echo "✅ Vulture executed successfully"
else
    echo "⚠️  Skipping Vulture test (not installed)"
fi

# Test 3: Import Bloat Detection (if autoflake available)
if command -v autoflake &> /dev/null; then
    echo "Test 3: Running autoflake on sample code..."
    cat > /tmp/bloat-test/imports.py << 'PYTHON'
import os
import sys
import json  # unused
from pathlib import Path
from typing import Dict, List  # List unused

def main():
    print(os.path.exists('.'))
    return Path('.')
PYTHON

    autoflake --check --remove-all-unused-imports /tmp/bloat-test/imports.py
    echo "✅ autoflake executed successfully"
else
    echo "⚠️  Skipping autoflake test (not installed)"
fi

# Test 4: Module Integration
echo "Test 4: Verify static-analysis-integration module exists..."
MODULE_PATH="plugins/conserve/skills/bloat-detector/modules/static-analysis-integration.md"
if [ -f "$MODULE_PATH" ]; then
    echo "✅ Module file exists"

    # Check key sections
    grep -q "Vulture" "$MODULE_PATH" && echo "  ✅ Vulture integration documented"
    grep -q "deadcode" "$MODULE_PATH" && echo "  ✅ deadcode integration documented"
    grep -q "autoflake" "$MODULE_PATH" && echo "  ✅ autoflake integration documented"
    grep -q "Knip" "$MODULE_PATH" && echo "  ✅ Knip integration documented"
    grep -q "SonarQube" "$MODULE_PATH" && echo "  ✅ SonarQube integration documented"
else
    echo "❌ Module file not found: $MODULE_PATH"
    exit 1
fi

echo ""
echo "=== Static Analysis Integration Tests Complete ==="
EOF

chmod +x /tmp/test_static_analysis.sh
/tmp/test_static_analysis.sh
```

**Expected Results:**
- ✅ Module file exists and contains all tool integrations
- ✅ Tool detection works (with graceful degradation)
- ✅ Sample code detection works (if tools installed)
- ⚠️  Tools may not be installed (acceptable - module documents fallback)

#### 2.3 Bloat Detector Functional Tests

**Manual Test Scenarios:**

```bash
# Scenario 1: Quick Scan (Tier 1 - Heuristics Only)
# Test bloat detection without external tools
# Expected: Heuristic-based detection works
# - Large files detected
# - Stale files detected
# - Commented code blocks found

# Scenario 2: Targeted Analysis (Tier 2 - With Tools)
# Requires: vulture, deadcode, or knip installed
# Expected: Tool-based detection enhances heuristics
# - Dead code detected with high confidence
# - Import bloat identified
# - Unused exports found (JS/TS)

# Scenario 3: Tool Fallback
# Uninstall/disable tools, run Tier 2 scan
# Expected: Graceful degradation to Tier 1
# - Warning message shown
# - Heuristic detection continues
# - No crashes or errors

# Scenario 4: Confidence Boosting
# Run scan with both heuristics and tools
# Expected: Findings with both signals have higher confidence
# - Heuristic alone: 70-80% confidence
# - Tool alone: 85-95% confidence
# - Both agree: 95%+ confidence
```

#### 2.4 Integration with Existing Skills

```bash
# Test integration with context-optimization
# Expected: Bloat metrics feed into MECW assessment

# Test integration with unbloat-remediator
# Expected: Bloat findings can be remediated safely

# Test integration with performance-monitoring
# Expected: Bloat correlates with performance issues
```

### 3. Memory Palace Testing

#### 3.1 Queue Processing ✅
```bash
# Verify queue entry was processed
ls -la plugins/memory-palace/docs/knowledge-corpus/queue/archive/

# Expected:
# ✅ 2025-12-31_codebase-bloat-detection-research.md archived
# ✅ Status updated to 'processed'
```

#### 3.2 Knowledge Corpus Entry ✅
```bash
# Verify knowledge corpus entry created
ls -la plugins/memory-palace/docs/knowledge-corpus/codebase-bloat-detection.md

# Expected:
# ✅ File exists
# ✅ Proper memory palace format
# ✅ All research findings included
# ✅ Cross-references to conserve plugin
```

#### 3.3 Knowledge Corpus Index ✅
```bash
# Verify index updated
grep "codebase-bloat-detection" plugins/memory-palace/docs/knowledge-corpus/README.md

# Expected:
# ✅ Entry listed under "Code Quality & Maintenance"
# ✅ Link is valid
```

### 4. Plugin Rename Testing (conservation → conserve)

#### 4.1 File Structure ✅
```bash
# Verify old plugin removed, new plugin exists
ls -d plugins/conservation 2>/dev/null && echo "❌ Old plugin still exists" || echo "✅ Old plugin removed"
ls -d plugins/conserve && echo "✅ New plugin exists"

# Expected:
# ✅ plugins/conserve/ exists
# ❌ plugins/conservation/ does not exist
```

#### 4.2 References Updated ✅
```bash
# Check for lingering "conservation" references
grep -r "conservation" --include="*.md" --include="*.json" plugins/conserve/ | \
  grep -v "conservation:" | \
  grep -v "category: conservation" | \
  grep -v "# Conservation"

# Expected: No incorrect references (category and headers are OK)
```

#### 4.3 Plugin.json Versions ✅
```bash
# Verify all plugins at 1.1.2
find plugins/*/. claude-plugin/plugin.json -exec jq -r '.name + ": " + .version' {} \;

# Expected: All plugins show consistent version
```

### 5. Cross-Plugin Integration

#### 5.1 Attune → Conserve
```bash
# Test that attune can set up conserve integration
# Expected: Attune creates .pre-commit-config.yaml with conserve hooks
```

#### 5.2 Memory Palace → Conserve
```bash
# Test that memory palace can reference conserve concepts
# Expected: Knowledge corpus entries properly link to conserve skills
```

#### 5.3 Leyline → Conserve
```bash
# Test MECW pattern integration
# Expected: Conserve skills use leyline MECW patterns
```

## Regression Testing

### 6.1 Existing Functionality
```bash
# Verify existing features still work after changes
# - Context optimization
# - Performance monitoring
# - Token conservation
# - MCP code execution
```

### 6.2 Backward Compatibility
```bash
# Verify old skill references still resolve
# - Skills using old conservation: category
# - Commands using old paths
# - Agents using old references
```

## Performance Testing

### 7.1 Bloat Detector Performance
```bash
# Measure scan times on different codebase sizes
# Small (<1000 lines): < 30 seconds
# Medium (1000-10000 lines): < 2 minutes
# Large (10000+ lines): < 5 minutes (Tier 1)
```

### 7.2 Memory Palace Queue Performance
```bash
# Test queue processing with multiple entries
# Expected: O(n) processing time, no exponential growth
```

## Documentation Testing

### 8.1 README Accuracy
```bash
# Verify all READMEs are up-to-date
# - Attune: Commands, usage examples
# - Conserve: Updated bloat detection features
# - Memory Palace: Queue system documented
```

### 8.2 CHANGELOG Completeness
```bash
# Verify CHANGELOG entries for all changes
# - Attune plugin added
# - Conserve static analysis module
# - Conservation → Conserve rename
# - Memory palace queue integration
```

### 8.3 Book/Docs Updates
```bash
# Verify mdBook documentation updated
# - book/src/plugins/attune.md exists
# - book/src/plugins/conserve.md updated (not conservation.md)
# - SUMMARY.md includes all plugins
```

## Automated Test Execution

### Run All Tests
```bash
# Attune tests
cd plugins/attune && make test

# Conserve tests
cd plugins/conserve && make test

# Memory palace tests (if applicable)
cd plugins/memory-palace && make test

# Abstract tests (plugin validation)
cd plugins/abstract && make test

# Root-level tests
make test
```

## Manual Validation Checklist

### Pre-Merge Checklist
- [ ] All automated tests pass
- [ ] Manual test scenarios executed
- [ ] Documentation reviewed and updated
- [ ] No regressions in existing functionality
- [ ] Performance acceptable on large codebases
- [ ] Error handling graceful (missing tools, etc.)
- [ ] Git history clean (no sensitive data)
- [ ] Commit messages follow convention
- [ ] PR description comprehensive

### Post-Merge Validation
- [ ] CI/CD pipeline passes
- [ ] Integration tests pass in main
- [ ] No breaking changes for users
- [ ] Documentation deployed correctly
- [ ] Release notes prepared

## Known Limitations

### Attune Plugin
- **Language Coverage**: Python, Rust, TypeScript (can expand)
- **Version Fetching**: Requires network access to registries
- **Template Coverage**: Basic templates (can be extended)

### Conserve Static Analysis
- **Tool Dependency**: Best results require external tools (Vulture, Knip, etc.)
- **Knip API**: No programmatic API yet (CLI only with JSON parsing)
- **PyTrim**: Not integrated (too new, Oct 2024)

### Memory Palace Queue
- **Manual Processing**: Queue review requires human approval
- **No Automation**: No auto-intake (intentional, maintains quality)

## Success Criteria

✅ **Pass Criteria:**
1. All automated tests pass
2. Manual scenarios complete without errors
3. Documentation is accurate and complete
4. No performance degradation
5. Graceful degradation when tools unavailable
6. No breaking changes to existing functionality

❌ **Fail Criteria:**
1. Test failures in core functionality
2. Performance regression > 20%
3. Breaking changes without migration path
4. Missing documentation for new features
5. Security issues or sensitive data exposed

## Test Execution Log

**Date**: 2026-01-02
**Tester**: Claude (automated) + User (manual validation)

### Executed Tests

#### Conserve Plugin
- ✅ `test_bloat_detector_modules.py` - PASSED
  - All 5 modules referenced
  - Valid frontmatter
  - Hub-spoke pattern maintained

#### Static Analysis Integration
- ⏳ `test_static_analysis.sh` - PENDING (awaiting tool installation)
  - Module structure verified ✅
  - Tool integrations documented ✅
  - Functional testing pending tool availability

#### Memory Palace
- ✅ Queue processing - PASSED
  - Entry archived
  - Knowledge corpus created
  - Index updated

#### Attune Plugin
- ⏳ Integration tests - PENDING
  - Structure tests needed
  - Template tests needed
  - End-to-end workflow tests needed

### Next Steps
1. Run attune test suite
2. Execute static analysis functional tests (with tools)
3. Manual validation of bloat detection on real codebase
4. Performance benchmarking
5. Documentation review

---

**Test Plan Version**: 1.0
**Last Updated**: 2026-01-02
**Branch**: project-init-1.2.0
**Status**: In Progress
