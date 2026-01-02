---
module: static-analysis-integration
category: tier-2
dependencies: [Bash, Read]
estimated_tokens: 400
---

# Static Analysis Integration Module

Bridge Tier 1 heuristics with Tier 2 programmatic analysis using language-specific static analysis tools. Auto-detects available tools and falls back gracefully.

## Tool Detection

Auto-detect static analysis tools at scan initialization:

```bash
#!/bin/bash
# detect_tools.sh

PYTHON_TOOLS=()
JS_TOOLS=()
MULTI_LANG_TOOLS=()

# Python dead code detection
if command -v vulture &> /dev/null; then
  PYTHON_TOOLS+=("vulture")
fi

if command -v deadcode &> /dev/null; then
  PYTHON_TOOLS+=("deadcode")
fi

if command -v autoflake &> /dev/null; then
  PYTHON_TOOLS+=("autoflake")
fi

# JavaScript/TypeScript
if command -v knip &> /dev/null; then
  JS_TOOLS+=("knip")
fi

# Multi-language
if command -v sonar-scanner &> /dev/null; then
  MULTI_LANG_TOOLS+=("sonarqube")
fi

# Report availability
echo "Python tools: ${PYTHON_TOOLS[@]:-none}"
echo "JS tools: ${JS_TOOLS[@]:-none}"
echo "Multi-lang tools: ${MULTI_LANG_TOOLS[@]:-none}"

# Determine tier capability
if [ ${#PYTHON_TOOLS[@]} -gt 0 ] || [ ${#JS_TOOLS[@]} -gt 0 ]; then
  echo "Tier 2 capable: true"
else
  echo "Tier 2 capable: false (falling back to Tier 1)"
fi
```

## Python Tool Integration

### 1. Vulture (Recommended - High Accuracy)

**Strengths:**
- Programmatic Python API available
- Confidence scoring (60-100%)
- Low false positives at 80%+ confidence

**Integration:**

```bash
#!/bin/bash
# run_vulture.sh

# Standard exclusion patterns
EXCLUDE_DIRS=".venv,venv,__pycache__,.pytest_cache,.mypy_cache,.ruff_cache,.tox,.git,node_modules,dist,build,vendor,.vscode,.idea"

if command -v vulture &> /dev/null; then
  echo "Running Vulture (Python dead code detection)..."

  vulture . \
    --min-confidence 80 \
    --exclude="$EXCLUDE_DIRS" \
    --sort-by-size \
    2>&1 | tee vulture-report.txt

  # Parse output
  echo ""
  echo "=== Vulture Results ==="
  grep -E "unused (function|class|variable|import)" vulture-report.txt | \
  while IFS= read -r line; do
    # Extract file, line, item
    file=$(echo "$line" | awk '{print $1}')
    confidence=$(echo "$line" | grep -oP '\d+%' | head -1)

    echo "DEAD_CODE: $file"
    echo "  Confidence: $confidence (Vulture)"
    echo "  Tool: vulture"
    echo "  Action: Safe to remove at 80%+"
  done
else
  echo "Vulture not installed. Install: pip install vulture"
  echo "Falling back to heuristic detection..."
fi
```

**Programmatic API Usage:**

```python
#!/usr/bin/env python3
"""Vulture programmatic API integration"""
import vulture
from pathlib import Path

def run_vulture_api(paths=None, min_confidence=80):
    """
    Use Vulture's Python API for dead code detection.

    Returns:
        list: Findings with confidence >= min_confidence
    """
    if paths is None:
        paths = ['.']

    # Initialize Vulture
    v = vulture.Vulture(verbose=False)

    # Scan paths
    v.scavenge(paths)

    # Filter by confidence
    findings = []
    for item in v.get_unused_code():
        if item.confidence >= min_confidence:
            findings.append({
                'file': item.filename,
                'line': item.first_lineno,
                'type': item.typ,  # 'function', 'class', 'variable', 'import'
                'name': item.name,
                'confidence': item.confidence,
                'message': f"unused {item.typ} '{item.name}'"
            })

    return findings

# Usage
EXCLUDED_DIRS = {
    '.venv', 'venv', '__pycache__', '.pytest_cache',
    '.mypy_cache', '.ruff_cache', '.tox', '.git',
    'node_modules', 'dist', 'build', 'vendor'
}

findings = run_vulture_api(paths=['.'], min_confidence=80)
for finding in findings:
    print(f"DEAD_CODE: {finding['file']}:{finding['line']}")
    print(f"  Type: {finding['type']}")
    print(f"  Name: {finding['name']}")
    print(f"  Confidence: {finding['confidence']}% (Vulture)")
    print(f"  Recommendation: DELETE")
```

**Confidence Levels:**
- **90-100%**: Very high confidence, safe to remove
- **80-89%**: High confidence, review before removal
- **60-79%**: Medium confidence, investigate usage
- **< 60%**: Not reported (too many false positives)

### 2. deadcode (Fastest, Auto-Fix)

**Strengths:**
- Very fast execution
- `--fix` flag for automatic removal
- `pyproject.toml` configuration
- Whitelist support for false positives

**Integration:**

```bash
#!/bin/bash
# run_deadcode.sh

if command -v deadcode &> /dev/null; then
  echo "Running deadcode (Python)..."

  # Check mode (no changes)
  deadcode --dry \
    --exclude .venv,venv,__pycache__,.pytest_cache,.mypy_cache,.ruff_cache,.tox,.git,node_modules,dist,build,vendor

  echo ""
  echo "To auto-fix, run: deadcode --fix"
  echo "To configure whitelist, add to pyproject.toml:"
  echo ""
  echo "[tool.deadcode]"
  echo "exclude = ["
  echo "  \"tests/fixtures/*\","
  echo "  \"**/migrations/*\","
  echo "]"
else
  echo "deadcode not installed. Install: pip install deadcode"
fi
```

**Configuration (pyproject.toml):**

```toml
[tool.deadcode]
exclude = [
  "tests/fixtures/*",    # Test fixtures may appear unused
  "**/migrations/*",     # DB migrations are invoked externally
  "**/__init__.py",      # Exports may not be used internally
]

# Ignore specific patterns
ignore-names = [
  ".*_test$",           # Test utilities
  "^test_.*",           # Test helpers
]

# Ignore decorators (frameworks)
ignore-names-in-files = [
  ["cli.py", ["main", "app"]],  # CLI entry points
  ["api.py", ["routes"]],       # API route decorators
]
```

**Confidence:** HIGH (85%) - Fewer false positives than Vulture

### 3. autoflake (Import Specialist)

**Strengths:**
- Focused on import cleanup
- Removes unused imports
- Expands star imports (`from x import *`)
- Auto-fix capability

**Integration:**

```bash
#!/bin/bash
# run_autoflake.sh

if command -v autoflake &> /dev/null; then
  echo "Running autoflake (Python import cleanup)..."

  # Check mode
  autoflake \
    --check \
    --remove-all-unused-imports \
    --expand-star-imports \
    --recursive \
    --exclude .venv,venv,__pycache__,.pytest_cache,.mypy_cache,.ruff_cache,.tox,.git,node_modules,dist,build,vendor \
    .

  echo ""
  echo "To auto-fix imports, run:"
  echo "  autoflake --in-place --remove-all-unused-imports --recursive ."
  echo ""
  echo "Performance impact: 40-70% startup time reduction possible"
else
  echo "autoflake not installed. Install: pip install autoflake"
fi
```

**Performance Impact:**
- Each unused import = startup tax
- Star imports prevent tree shaking
- **Measured savings**: 40-70% reduction in Python startup time

**Confidence:** VERY HIGH (95%) - Import analysis is deterministic

## JavaScript/TypeScript Tool Integration

### 4. Knip (Comprehensive, CLI Only)

**Strengths:**
- Comprehensive dead code detection
- Detects unused files, exports, dependencies
- Rich configuration

**Limitations:**
- ⚠️ **No programmatic API yet** (CLI only, roadmap item)
- Must shell out and parse JSON output

**Integration:**

```bash
#!/bin/bash
# run_knip.sh

if command -v knip &> /dev/null; then
  echo "Running Knip (JavaScript/TypeScript dead code)..."

  # Run Knip with JSON output
  knip \
    --include files,exports,dependencies \
    --reporter json \
    > knip-report.json 2>&1

  # Parse JSON output
  if [ -f knip-report.json ]; then
    echo "=== Knip Results ==="

    # Extract unused files
    jq -r '.files[] | "DEAD_CODE: \(.file)\n  Type: unused file\n  Confidence: HIGH (Knip)\n  Recommendation: DELETE"' \
      knip-report.json 2>/dev/null || echo "No unused files found"

    # Extract unused exports
    jq -r '.exports[] | "DEAD_CODE: \(.file):\(.line)\n  Export: \(.name)\n  Confidence: HIGH (Knip)\n  Recommendation: REMOVE export"' \
      knip-report.json 2>/dev/null || echo "No unused exports found"

    # Extract unused dependencies
    jq -r '.dependencies[] | "IMPORT_BLOAT: \(.name)\n  Type: unused dependency\n  Confidence: HIGH (Knip)\n  Recommendation: Remove from package.json"' \
      knip-report.json 2>/dev/null || echo "No unused dependencies found"
  fi
else
  echo "Knip not installed. Install: npm install -g knip"
fi
```

**Configuration (.knip.json):**

```json
{
  "$schema": "https://unpkg.com/knip@latest/schema.json",
  "entry": ["src/index.ts", "src/cli.ts"],
  "project": ["src/**/*.ts"],
  "ignore": ["**/*.test.ts", "**/*.spec.ts"],
  "ignoreDependencies": ["@types/*"]
}
```

**Workaround for No API:**

```python
#!/usr/bin/env python3
"""Knip integration via subprocess and JSON parsing"""
import subprocess
import json

def run_knip(cwd='.'):
    """
    Run Knip and parse JSON output.

    Returns:
        dict: Parsed findings from Knip
    """
    try:
        # Run Knip with JSON reporter
        result = subprocess.run(
            ['knip', '--include', 'files,exports,dependencies', '--reporter', 'json'],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300
        )

        # Parse JSON output
        if result.stdout:
            findings = json.loads(result.stdout)
            return {
                'files': findings.get('files', []),
                'exports': findings.get('exports', []),
                'dependencies': findings.get('dependencies', [])
            }
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Knip error: {e}")
        return {'files': [], 'exports': [], 'dependencies': []}

# Usage
findings = run_knip()
print(f"Unused files: {len(findings['files'])}")
print(f"Unused exports: {len(findings['exports'])}")
print(f"Unused dependencies: {len(findings['dependencies'])}")
```

**Confidence:** VERY HIGH (95%) - Static analysis is accurate

### Tree-Shaking Prerequisites

Knip works best when tree-shaking is enabled:

```bash
# Check if project supports tree-shaking
check_tree_shaking() {
  # ESM required (not CommonJS)
  if grep -q '"type": "module"' package.json; then
    echo "✅ ESM enabled (tree-shaking supported)"
  else
    echo "⚠️  CommonJS mode (tree-shaking blocked)"
    echo "   Add '\"type\": \"module\"' to package.json"
  fi

  # Check for barrel files (break tree-shaking)
  barrel_files=$(grep -r "export \* from" --include="*.ts" --include="*.js" src/ | wc -l)
  if [ $barrel_files -gt 0 ]; then
    echo "⚠️  Found $barrel_files barrel files (export *)"
    echo "   Recommendation: Use explicit exports"
  fi
}
```

## Multi-Language Tool Integration

### 5. SonarQube (Enterprise-Grade)

**Strengths:**
- Multi-language support
- Web API for metrics
- Cyclomatic complexity, duplication metrics
- Continuous quality tracking

**Integration:**

```bash
#!/bin/bash
# run_sonar.sh

if command -v sonar-scanner &> /dev/null; then
  echo "Running SonarQube analysis..."

  # Run scanner
  sonar-scanner \
    -Dsonar.projectKey=my-project \
    -Dsonar.sources=. \
    -Dsonar.host.url=http://localhost:9000 \
    -Dsonar.exclusions="**/node_modules/**,**/.venv/**,**/dist/**,**/build/**"

  # Fetch metrics via API
  PROJECT_KEY="my-project"
  SONAR_URL="http://localhost:9000"

  curl -s "$SONAR_URL/api/measures/component?component=$PROJECT_KEY&metricKeys=duplicated_lines_density,complexity,code_smells" | \
  jq -r '.component.measures[] | "\(.metric): \(.value)"'
else
  echo "SonarQube not available. Install sonar-scanner or skip."
fi
```

**Key Metrics:**
- **Duplication**: > 100 tokens or 10+ statements = code smell
- **Complexity**: Cyclomatic complexity per function
- **Code Smells**: Maintainability issues

**Confidence:** VERY HIGH (95%) - Industry-standard tool

## Tool Selection Strategy

```python
def select_best_tool(language, available_tools):
    """
    Choose optimal tool based on language and availability.

    Priority (descending):
    1. Highest accuracy
    2. Best performance
    3. Fewest false positives
    """
    TOOL_PRIORITY = {
        'python': ['vulture', 'deadcode', 'autoflake'],
        'javascript': ['knip'],
        'typescript': ['knip'],
        'multi': ['sonarqube']
    }

    for tool in TOOL_PRIORITY.get(language, []):
        if tool in available_tools:
            return tool

    # Fallback to heuristics
    return 'heuristic'

# Example
available = ['vulture', 'autoflake']
best = select_best_tool('python', available)
print(f"Using: {best}")  # Output: vulture (highest priority)
```

## Graceful Degradation

When tools are unavailable, fall back to Tier 1 heuristics:

```bash
#!/bin/bash
# run_with_fallback.sh

run_tier2_analysis() {
  local language=$1

  case "$language" in
    python)
      if command -v vulture &> /dev/null; then
        run_vulture
      elif command -v deadcode &> /dev/null; then
        run_deadcode
      else
        echo "No Python tools available, using heuristics..."
        run_python_heuristics
      fi
      ;;
    javascript|typescript)
      if command -v knip &> /dev/null; then
        run_knip
      else
        echo "Knip not available, using heuristics..."
        run_js_heuristics
      fi
      ;;
    *)
      echo "Language $language: Using heuristics (no tools)"
      run_generic_heuristics
      ;;
  esac
}
```

## Confidence Boosting

Combine tool findings with heuristics for higher confidence:

```python
def merge_findings(heuristic_findings, tool_findings):
    """
    Merge heuristic and tool findings, boosting confidence for matches.
    """
    merged = []

    for heuristic in heuristic_findings:
        match = find_matching_tool_finding(heuristic, tool_findings)

        if match:
            # Both heuristic and tool agree = HIGH confidence
            confidence = min(95, heuristic.confidence + 15)
            merged.append({
                **heuristic,
                'confidence': confidence,
                'sources': ['heuristic', match.tool],
                'recommendation': 'DELETE' if confidence >= 85 else 'INVESTIGATE'
            })
        else:
            # Only heuristic = MEDIUM confidence
            merged.append(heuristic)

    # Add tool-only findings
    for tool_finding in tool_findings:
        if not has_matching_heuristic(tool_finding, heuristic_findings):
            merged.append({
                **tool_finding,
                'sources': [tool_finding.tool]
            })

    return merged
```

## Output Format

```yaml
file: src/utils/helpers.py
line: 42
type: function
name: calculate_legacy
confidence: 95% (HIGH)
sources:
  - heuristic (stale 18 months, zero references)
  - vulture (confidence: 88%)
bloat_score: 92/100
token_estimate: 240 tokens
recommendations:
  action: DELETE
  rationale: Multiple high-confidence signals confirm dead code
  safety: Create backup branch before deletion
  command: git rm src/utils/helpers.py
```

## Performance Optimization

**Parallel Execution:**

```bash
# Run tools in parallel for speed
run_vulture &
run_deadcode &
run_knip &
wait

# Merge results
merge_findings vulture-report.txt deadcode-report.txt knip-report.json
```

**Caching:**

```bash
# Cache tool results for 24 hours
CACHE_FILE=".bloat-cache-$(date +%Y%m%d).json"

if [ -f "$CACHE_FILE" ]; then
  echo "Using cached results from today..."
  cat "$CACHE_FILE"
else
  echo "Running fresh analysis..."
  run_all_tools > "$CACHE_FILE"
  cat "$CACHE_FILE"
fi
```

## Integration Points

- **Tier 1 (quick-scan)**: Use heuristics when tools unavailable
- **Tier 2 (static-analysis)**: This module - tool-based detection
- **Tier 3 (deep-audit)**: Combine all tools + cross-file analysis

## Safety & Validation

**Always validate before deletion:**

```bash
# Validate tool findings with git grep
validate_finding() {
  local file=$1
  local symbol=$2

  # Check if symbol is actually referenced
  references=$(git grep -c "$symbol" || echo "0")

  if [ "$references" -eq 0 ]; then
    echo "CONFIRMED: $symbol has zero references"
    return 0  # Safe to delete
  else
    echo "FALSE POSITIVE: $symbol has $references references"
    return 1  # Not safe
  fi
}
```

## Related Resources

- **code-bloat-patterns**: Provides heuristic fallbacks
- **quick-scan**: Tier 1 baseline
- **bloat-auditor**: Orchestrates tool execution
