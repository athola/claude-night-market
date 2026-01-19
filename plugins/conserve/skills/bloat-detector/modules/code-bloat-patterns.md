---
module: code-bloat-patterns
category: tier-2
dependencies: [Bash, Grep, Read]
estimated_tokens: 150
---

# Code Bloat Patterns Module

Detect anti-patterns using pattern recognition and heuristics. Works without external tools.

## Anti-Patterns

### 1. God Class
**Definition:** Single class with > 500 lines, > 10 methods, multiple responsibilities.

```bash
# Quick detection
find . -name "*.py" -exec sh -c 'lines=$(wc -l < "$1"); [ $lines -gt 500 ] && echo "GOD_CLASS: $1 - $lines lines"' _ {} \;
```
**Confidence:** HIGH (85%) | **Action:** REFACTOR into focused modules

### 2. Lava Flow
**Definition:** Ancient untouched code - commented blocks, old TODOs.

```bash
# Find files with >20% commented code
grep -rn "^#\|^//" --include="*.py" . | cut -d: -f1 | sort | uniq -c | sort -rn | head -10
```
**Confidence:** HIGH (90%) | **Action:** DELETE commented code

### 3. Dead Code
**Detection:** Use static analysis (Vulture/Knip) or fallback heuristic:
```bash
# Heuristic: find functions with 0 calls
grep -rn "^def " --include="*.py" . | while read line; do
  func=$(echo $line | awk '{print $2}' | cut -d'(' -f1)
  [ $(git grep -c "$func(" 2>/dev/null || echo 0) -eq 1 ] && echo "DEAD: $func"
done
```
**Confidence:** MEDIUM (70%) heuristic, HIGH (90%) with tools | **Action:** DELETE

### 4. Import Bloat
```bash
# Star imports (block tree-shaking)
grep -rn "^from .* import \*" --include="*.py" .

# Unused imports (requires autoflake)
autoflake --check --remove-all-unused-imports -r .
```
**Confidence:** HIGH (95%) | **Action:** Fix imports

### 5. Duplication
**Intra-file:** Hash-based block detection (5+ line matches)
**Cross-file:** Function signature matching
**Semantic:** AST comparison (80%+ similarity)

**Confidence:** HIGH (85%) | **Action:** EXTRACT to shared utility

## Language-Specific

### Python
- Circular imports: Files with 20+ imports
- Deep nesting: > 4 indentation levels

### JavaScript/TypeScript
- Barrel files: `export * from` breaks tree-shaking
- CommonJS in ESM: `module.exports`/`require()` blocks bundler optimization

## Scoring

```python
PATTERN_SCORES = {
    'god_class': 30, 'lava_flow': 25, 'dead_code': 35,
    'import_bloat': 15, 'duplication': 20
}
score = min(100, sum(PATTERN_SCORES[p] for p in detected))
```

## Output Format

```yaml
file: src/legacy/manager.py
patterns: [god_class, lava_flow, import_bloat]
bloat_score: 85/100
confidence: HIGH
token_estimate: ~3,400
action: REFACTOR
```

All actions require user approval.
