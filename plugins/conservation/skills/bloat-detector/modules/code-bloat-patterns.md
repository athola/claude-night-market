---
module: code-bloat-patterns
category: tier-2
dependencies: [Bash, Grep, Read]
estimated_tokens: 300
---

# Code Bloat Patterns Module

Detect anti-patterns and code bloat using pattern recognition and heuristics. Language-specific detection for Python, JavaScript/TypeScript.

## Anti-Pattern Detection

### 1. God Class Pattern

**Definition:** Single class handling multiple non-cohesive responsibilities (> 500 lines, > 10 methods).

**Python Detection:**
```bash
# Find large classes with many methods
grep -rn "^class " --include="*.py" . | \
while read line; do
  file=$(echo $line | cut -d: -f1)
  class_line=$(echo $line | cut -d: -f2)
  class_name=$(echo $line | awk '{print $2}' | cut -d'(' -f1)

  # Count methods in class
  methods=$(awk "/^class $class_name/,/^class / {/def /}" $file | wc -l)

  # Count lines in file (proxy for class size)
  lines=$(wc -l < $file)

  if [ $lines -gt 500 ] && [ $methods -gt 10 ]; then
    echo "GOD_CLASS: $file - $lines lines, $methods methods"
  fi
done
```

**JavaScript/TypeScript Detection:**
```bash
# Find large classes
grep -rn "^class \|^export class " --include="*.js" --include="*.ts" . | \
while read line; do
  file=$(echo $line | cut -d: -f1)
  methods=$(grep -c "  [a-zA-Z_]*(" $file)
  lines=$(wc -l < $file)

  if [ $lines -gt 400 ] && [ $methods -gt 10 ]; then
    echo "GOD_CLASS: $file - $lines lines, $methods methods"
  fi
done
```

**Confidence:** HIGH (85%) when combined with low cohesion signals

**Recommendation:** REFACTOR - Extract responsibilities into focused classes

### 2. Lava Flow Pattern

**Definition:** Ancient, untouched code preserved out of fear (commented code, old TODOs, no recent changes).

**Detection:**
```bash
# Find files with large commented code blocks
find . -name "*.py" -o -name "*.js" -o -name "*.ts" | \
while read file; do
  commented=$(grep -c "^#\|^//" $file)
  total=$(wc -l < $file)
  if [ $commented -gt 50 ] && [ $total -gt 100 ]; then
    ratio=$((commented * 100 / total))
    echo "LAVA_FLOW: $file - ${ratio}% commented code"
  fi
done

# Find files with ancient TODOs
grep -rn "TODO.*[0-9]\{4\}" --include="*.py" --include="*.js" --include="*.ts" . | \
awk -F: '{
  # Extract year from TODO comment
  match($0, /[0-9]{4}/, year)
  current_year = 2025
  if (year[0] < current_year - 1) {
    print "LAVA_FLOW: Old TODO in " $1 " from " year[0]
  }
}'
```

**Confidence:** HIGH (90%) - Commented code is rarely needed

**Recommendation:** DELETE commented code, convert old TODOs to issues or remove

### 3. Dead Code Pattern

**Detection requires static analysis (Tier 2 tools):**

**Python (Vulture):**
```bash
if command -v vulture &> /dev/null; then
  vulture . --min-confidence 80 --exclude=tests,venv
fi
```

**JavaScript/TypeScript (Knip):**
```bash
if command -v knip &> /dev/null; then
  knip --include files,exports,dependencies
fi
```

**Fallback Heuristic (no tools):**
```bash
# Find Python functions never called
grep -rn "^def " --include="*.py" . | \
while read line; do
  func_name=$(echo $line | awk '{print $2}' | cut -d'(' -f1)
  # Search for calls to this function
  calls=$(grep -r "$func_name(" --include="*.py" . | grep -v "^def $func_name" | wc -l)
  if [ $calls -eq 0 ]; then
    echo "DEAD_CODE: Unused function $func_name in $line"
  fi
done
```

**Confidence:** MEDIUM (70%) with heuristics, HIGH (90%) with static analysis

### 4. Import Bloat (Python-Specific)

**Star Imports:**
```bash
# Find star imports (prevents tree shaking)
grep -rn "^from .* import \*" --include="*.py" . | \
while read line; do
  file=$(echo $line | cut -d: -f1)
  echo "IMPORT_BLOAT: Star import in $file"
  echo "  Recommendation: Convert to explicit imports"
done
```

**Unused Imports (requires autoflake):**
```bash
if command -v autoflake &> /dev/null; then
  autoflake --check --remove-all-unused-imports -r .
else
  # Fallback: Find imports never used in file
  grep -rn "^import \|^from .* import " --include="*.py" . | \
  while read line; do
    file=$(echo $line | cut -d: -f1)
    import_name=$(echo $line | awk '{print $2}')
    # Check if import is used in file
    usage=$(grep -c "$import_name" $file)
    if [ $usage -eq 1 ]; then  # Only the import line itself
      echo "IMPORT_BLOAT: Unused import $import_name in $file"
    fi
  done
fi
```

**Performance Impact:** Each unused import = startup tax (40-70% reduction possible with lazy loading)

### 5. Duplication Pattern

**Simple Duplicate Detection:**
```bash
# Find duplicate functions by name
find . -name "*.py" -o -name "*.js" -o -name "*.ts" | \
xargs grep -h "^def \|^function " | \
sort | uniq -d
```

**Advanced (requires SonarQube or similar):**
- Detects code clones (> 100 tokens duplicated)
- Semantic similarity (different names, same logic)

**Confidence:** LOW (60%) with simple detection, HIGH (85%) with semantic analysis

**Recommendation:** EXTRACT to shared utility or DRY refactor

## Language-Specific Patterns

### Python Anti-Patterns

**1. Circular Imports:**
```bash
# Detect potential circular imports (heuristic)
python3 << 'EOF'
import ast
import os

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ['venv', '.venv', '__pycache__']]
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            try:
                with open(path) as f:
                    tree = ast.parse(f.read())
                imports = [node.module for node in ast.walk(tree)
                          if isinstance(node, (ast.Import, ast.ImportFrom))
                          and node.module]
                if len(imports) > 20:  # High import count = potential circular
                    print(f"IMPORT_BLOAT: {path} has {len(imports)} imports")
            except:
                pass
EOF
```

**2. Deeply Nested Code:**
```bash
# Find excessive nesting (> 4 levels)
grep -rn "^        " --include="*.py" . | \
grep -v "^        #" | \
wc -l
```

### JavaScript/TypeScript Anti-Patterns

**1. Barrel Files (Tree-Shaking Blockers):**
```bash
# Find barrel files (export * from ...)
grep -rn "export \* from" --include="*.js" --include="*.ts" . | \
while read line; do
  echo "BUNDLE_BLOAT: Barrel file pattern in $line"
  echo "  Recommendation: Use explicit exports or granular imports"
done
```

**2. CommonJS in ESM Project:**
```bash
# Find CommonJS syntax in modern project
grep -rn "module.exports\|require(" --include="*.js" --include="*.ts" . | \
while read line; do
  echo "BUNDLE_BLOAT: CommonJS syntax prevents tree-shaking: $line"
  echo "  Recommendation: Convert to ESM (import/export)"
done
```

**3. Side Effects:**
```bash
# Find potential side effects (heuristic)
grep -rn "window\.\|document\.\|global\." --include="*.js" --include="*.ts" . | \
grep -v "// @ts-" | \
wc -l
```

## Scoring Algorithm

```python
def calculate_pattern_score(file_path, patterns_detected):
    score = 0
    confidence = 'LOW'

    # God Class
    if 'god_class' in patterns_detected:
        score += 30
        confidence = max(confidence, 'HIGH')

    # Lava Flow
    if 'lava_flow' in patterns_detected:
        score += 25
        confidence = max(confidence, 'HIGH')

    # Dead Code
    if 'dead_code' in patterns_detected:
        score += 35
        confidence = max(confidence, 'MEDIUM')

    # Import Bloat
    if 'import_bloat' in patterns_detected:
        score += 15
        confidence = max(confidence, 'MEDIUM')

    # Duplication
    if 'duplication' in patterns_detected:
        score += 20
        confidence = max(confidence, 'LOW')

    return min(score, 100), confidence
```

## Output Format

```yaml
file: src/legacy/manager.py
patterns_detected:
  - god_class:
      lines: 847
      methods: 18
      responsibilities: [auth, db, logging, validation]
      confidence: HIGH
  - lava_flow:
      commented_lines: 142
      commented_ratio: 17%
      old_todos: 5 (oldest: 2023-03)
      confidence: HIGH
  - import_bloat:
      star_imports: 2
      unused_imports: 7
      confidence: MEDIUM
bloat_score: 85/100
overall_confidence: HIGH
token_estimate: ~3,400 tokens
recommendations:
  primary: REFACTOR
  rationale: God class with multiple anti-patterns
  steps:
    - Extract AuthManager (lines 100-250)
    - Extract DBHandler (lines 251-450)
    - Extract ValidationService (lines 451-600)
    - Remove commented code (lines 601-742)
    - Fix imports (remove unused, convert star imports)
  estimated_effort: 4-6 hours
  risk: MEDIUM (core component, needs comprehensive tests)
```

## Integration with Static Analysis

When static analysis tools are available:

```python
def enhanced_pattern_detection(file_path):
    # Heuristic detection
    heuristic_patterns = detect_patterns_heuristic(file_path)

    # Static analysis (if available)
    if has_vulture():
        dead_code = run_vulture(file_path)
        heuristic_patterns['dead_code'].update(dead_code)

    if has_knip():
        unused_exports = run_knip(file_path)
        heuristic_patterns['dead_code'].update(unused_exports)

    # Combine and boost confidence
    return merge_findings(heuristic_patterns, confidence_boost=15)
```

## False Positive Mitigation

**Whitelist Patterns:**
```yaml
# .bloat-patterns-ignore
patterns_to_ignore:
  - pattern: god_class
    paths:
      - tests/fixtures/mock_large_class.py  # Test fixture
      - migrations/*.py  # DB migrations are naturally large

  - pattern: lava_flow
    paths:
      - docs/archive/*  # Intentionally preserved

  - pattern: import_bloat
    files:
      - __init__.py  # Barrel files are expected here
```

## Next Steps

Based on patterns detected:
- **God Class**: Create refactoring plan, extract services
- **Lava Flow**: Delete commented code, archive if needed
- **Dead Code**: Safe to delete (with backup)
- **Import Bloat**: Run autoflake --fix or manual cleanup
- **Duplication**: Extract to shared utility

All actions require user approval before execution.
