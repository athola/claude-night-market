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
  vulture . --min-confidence 80 \
    --exclude=.venv,venv,__pycache__,.pytest_cache,.mypy_cache,.ruff_cache,.tox,.git,node_modules,dist,build,vendor
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

#### A. Duplicate Function Names (Cross-File)

**Simple Duplicate Detection:**
```bash
# Find duplicate functions by name across files
find . -name "*.py" -o -name "*.js" -o -name "*.ts" | \
xargs grep -h "^def \|^function " | \
sort | uniq -d
```

**Confidence:** LOW (60%) - only detects name duplication, not logic

#### B. Duplicate Code Blocks (Intra-File)

**Detect repeated code within the same file:**
```python
#!/usr/bin/env python3
"""Detect duplicate code blocks within files"""
import hashlib
from collections import defaultdict
from pathlib import Path

def find_intra_file_duplication(file_path, min_lines=5):
    """Find duplicate code blocks of min_lines or more within a file."""
    with open(file_path) as f:
        lines = f.readlines()

    # Track blocks by hash
    block_hashes = defaultdict(list)

    # Sliding window to find duplicate blocks
    for i in range(len(lines) - min_lines + 1):
        block = ''.join(lines[i:i+min_lines])
        # Normalize: strip whitespace for hash
        normalized = ''.join(line.strip() for line in block.splitlines())

        if len(normalized) < 20:  # Skip trivial blocks
            continue

        block_hash = hashlib.md5(normalized.encode()).hexdigest()
        block_hashes[block_hash].append((i+1, block))

    # Report duplicates
    duplicates = []
    for hash_val, occurrences in block_hashes.items():
        if len(occurrences) > 1:
            duplicates.append({
                'lines': [occ[0] for occ in occurrences],
                'count': len(occurrences),
                'sample': occurrences[0][1][:100]
            })

    return duplicates

# Usage
EXCLUDED_DIRS = {
    '.venv', 'venv', '__pycache__', '.pytest_cache',
    '.mypy_cache', '.ruff_cache', '.tox', '.git',
    'node_modules', 'dist', 'build', 'vendor'
}

for file_path in Path('.').rglob('*.py'):
    if any(ex in file_path.parts for ex in EXCLUDED_DIRS):
        continue

    dups = find_intra_file_duplication(file_path, min_lines=5)
    if dups:
        print(f"\nDUPLICATION_INTRAFILE: {file_path}")
        for dup in dups:
            lines_str = ', '.join(map(str, dup['lines']))
            print(f"  {dup['count']}x at lines {lines_str}")
            print(f"  Sample: {dup['sample']!r}")
        print(f"  Recommendation: Extract to helper function")
```

**Confidence:** HIGH (85%) - exact block matches

#### C. Duplicate Functions (Cross-File)

**Detect similar functions across different files:**
```bash
#!/bin/bash
# find_duplicate_functions.sh

# Create temp file to store function signatures
tmpfile=$(mktemp)

# Extract all function definitions with file info
find . -name "*.py" -not -path '*/\.*' | while read file; do
    grep -n "^def " "$file" | while IFS=: read line_num func_def; do
        # Extract function signature (name + params)
        func_sig=$(echo "$func_def" | sed 's/def //' | cut -d':' -f1)
        # Remove whitespace for comparison
        normalized=$(echo "$func_sig" | tr -d ' ')
        echo "$normalized|$file:$line_num|$func_def" >> "$tmpfile"
    done
done

# Find duplicates by signature
cat "$tmpfile" | cut -d'|' -f1 | sort | uniq -d | while read dup_sig; do
    echo "DUPLICATION_CROSSFILE: Function signature '$dup_sig' found in multiple files:"
    grep "^$dup_sig|" "$tmpfile" | cut -d'|' -f2-
    echo "  Recommendation: Consolidate into shared utility module"
    echo
done

rm "$tmpfile"
```

**For JavaScript/TypeScript:**
```bash
# Similar approach for JS/TS
find . -name "*.js" -o -name "*.ts" | while read file; do
    grep -n "^\s*function\s\|^\s*const\s.*=\s.*=>" "$file"
done | awk -F: '{...}' # Similar logic
```

**Confidence:** MEDIUM (75%) - signature match, may have different implementations

#### D. Semantic Code Clones (Advanced)

**Using Python AST for semantic similarity:**
```python
#!/usr/bin/env python3
"""Detect semantically similar functions (different names, same logic)"""
import ast
from difflib import SequenceMatcher
from pathlib import Path

def normalize_ast(node):
    """Normalize AST by removing names, keeping structure."""
    if isinstance(node, ast.Name):
        return 'VAR'
    elif isinstance(node, ast.Constant):
        return f'CONST_{type(node.value).__name__}'
    return ast.dump(node, annotate_fields=False)

def functions_similar(func1_ast, func2_ast, threshold=0.8):
    """Check if two function ASTs are structurally similar."""
    norm1 = normalize_ast(func1_ast)
    norm2 = normalize_ast(func2_ast)
    ratio = SequenceMatcher(None, norm1, norm2).ratio()
    return ratio >= threshold

def find_semantic_clones(directory='.', similarity=0.8):
    """Find functions with similar logic but different names."""
    functions = []

    EXCLUDED_DIRS = {
        '.venv', 'venv', '__pycache__', '.pytest_cache',
        '.mypy_cache', '.ruff_cache', '.tox', '.git',
        'node_modules', 'dist', 'build', 'vendor'
    }

    # Parse all functions
    for file_path in Path(directory).rglob('*.py'):
        if any(ex in file_path.parts for ex in EXCLUDED_DIRS):
            continue

        try:
            with open(file_path) as f:
                tree = ast.parse(f.read())

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append((file_path, node.name, node))
        except:
            pass

    # Compare all pairs
    clones = []
    for i, (file1, name1, ast1) in enumerate(functions):
        for file2, name2, ast2 in functions[i+1:]:
            if name1 != name2 and functions_similar(ast1, ast2, similarity):
                clones.append({
                    'function1': f"{file1}::{name1}",
                    'function2': f"{file2}::{name2}",
                    'similarity': 'HIGH'
                })

    return clones

# Usage
clones = find_semantic_clones('.', similarity=0.8)
for clone in clones:
    print(f"DUPLICATION_SEMANTIC: {clone['function1']} ≈ {clone['function2']}")
    print(f"  Confidence: {clone['similarity']}")
    print(f"  Recommendation: Consolidate or abstract common logic")
```

**Confidence:** HIGH (90%) with AST analysis

#### E. Copy-Paste Detection (Token-Based)

**Detect code blocks copied across files:**
```bash
#!/bin/bash
# Requires: ccfinder or jscpd tool

# Using jscpd (JavaScript Copy-Paste Detector - works for multiple languages)
if command -v jscpd &> /dev/null; then
    jscpd . --min-lines 5 --min-tokens 50 \
        --format "json" \
        --output "./bloat-report-duplication.json"

    # Parse output
    echo "DUPLICATION_COPYPASTE: Copy-paste detection results:"
    cat bloat-report-duplication.json
else
    echo "Install jscpd for advanced copy-paste detection: npm install -g jscpd"
fi
```

**Manual alternative (hash-based):**
```python
#!/usr/bin/env python3
"""Hash-based copy-paste detection"""
import hashlib
from collections import defaultdict
from pathlib import Path

def tokenize_code(code):
    """Simple tokenization: remove comments, normalize whitespace."""
    # Remove Python comments
    lines = [line.split('#')[0] for line in code.splitlines()]
    # Normalize whitespace
    return ' '.join(' '.join(lines).split())

def find_copy_paste(directory='.', min_tokens=50):
    """Find copied code blocks across files."""
    blocks = defaultdict(list)

    EXCLUDED_DIRS = {
        '.venv', 'venv', '__pycache__', '.pytest_cache',
        '.mypy_cache', '.ruff_cache', '.tox', '.git',
        'node_modules', 'dist', 'build', 'vendor'
    }

    for file_path in Path(directory).rglob('*.py'):
        if any(ex in file_path.parts for ex in EXCLUDED_DIRS):
            continue

        try:
            with open(file_path) as f:
                lines = f.readlines()

            # Sliding window
            for i in range(len(lines) - 10):
                block = ''.join(lines[i:i+10])
                tokens = tokenize_code(block)

                if len(tokens.split()) < min_tokens:
                    continue

                block_hash = hashlib.md5(tokens.encode()).hexdigest()
                blocks[block_hash].append((file_path, i+1, block[:100]))
        except:
            pass

    # Report duplicates
    for hash_val, occurrences in blocks.items():
        if len(occurrences) > 1:
            print(f"\nDUPLICATION_COPYPASTE: {len(occurrences)} instances found")
            for file_path, line_num, sample in occurrences:
                print(f"  {file_path}:{line_num}")
            print(f"  Sample: {sample!r}")
            print(f"  Recommendation: Extract to shared module")

find_copy_paste('.', min_tokens=50)
```

**Confidence:** HIGH (85%) for exact matches

**Summary - Duplication Detection:**
- **Intra-file blocks**: Hash-based detection (HIGH confidence)
- **Cross-file functions**: Signature matching (MEDIUM confidence)
- **Semantic clones**: AST analysis (HIGH confidence)
- **Copy-paste**: Token/hash-based (HIGH confidence)

**Recommendation:** EXTRACT duplicated code to shared utilities, DRY refactor

## Language-Specific Patterns

### Python Anti-Patterns

**1. Circular Imports:**
```bash
# Detect potential circular imports (heuristic)
python3 << 'EOF'
import ast
import os

EXCLUDED_DIRS = {
    '.venv', 'venv', '__pycache__', '.pytest_cache',
    '.mypy_cache', '.ruff_cache', '.tox', '.git',
    'node_modules', 'dist', 'build', 'vendor',
    '.vscode', '.idea'
}

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
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
