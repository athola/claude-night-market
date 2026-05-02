# Performance Review Command

Static-analysis hot-spot review for time and space complexity.

## Usage

```bash
/performance-review                  # scan changed files
/performance-review path/to/file.py  # scan one file
/performance-review --tier 1         # force Tier 1 only (skip gauntlet)
```

## What It Does

1. **Context**: Identify target files (changed or argument-named).
2. **Tier 1: AST scan**: Detect Python time/space hotspots
   (nested loops, list `in` lookups, string concat, regex
   recompile, list-vs-generator, copy-in-loop).
3. **Tier 2: gauntlet tree-sitter** (if installed): Extend
   detection to JS/TS, Go, Rust, Java, C/C++.
4. **Tier 3: gauntlet graph** (if `.gauntlet/graph.db` exists):
   Upgrade severity for hotspots whose call chain reaches other
   hotspots transitively.
5. **Report**: Group findings by severity. Each finding cites
   `file:line`, severity, category (`time`/`space`), the pattern
   detected, and a concrete suggestion.

## Detection Categories

| Tier | ID | Pattern |
|---|---|---|
| 1 | T1 | Nested `for` over the same iterable (HIGH) |
| 1 | T2 | `x in <list>` inside a loop (HIGH) |
| 1 | T3 | `re.compile()` inside a loop (MEDIUM) |
| 1 | T4 | String `+=` accumulator in a loop (MEDIUM) |
| 1 | T5 | Recursive function without `@cache` (LOW) |
| 1 | T6 | List comprehension passed to a reducer (LOW) |
| 1 | S1 | `.append()` inside nested loops (MEDIUM) |
| 1 | S2 | `list(...)` wrapping a generator in a reducer (LOW) |
| 1 | S3 | `.copy()` / `dict()` / `list()` in a loop (MEDIUM) |
| 2 | * | Same patterns adapted to non-Python via tree-sitter |
| 3 | * | Severity upgrades from transitive call analysis |

## When to Skip

- Code is hot-path-irrelevant (config readers, one-shot scripts).
- The "hotspot" is intentional (e.g., a data-prep step where
  clarity beats micro-optimization).
- The reviewed function has runtime profiling already published.

For runtime profiling rather than static analysis, see
`Skill(parseltongue:python-performance)`.

## Output

A grouped findings list with file:line citations, severity, and
fix suggestions. No findings means no detected patterns: not a
guarantee of optimal performance.

## Fallback Behavior

When gauntlet is not installed or its graph DB does not exist
for the working tree:

- Tier 1 still runs (Python AST is stdlib).
- Tier 2 returns empty (sentinel-guarded import).
- Tier 3 returns empty (sentinel-guarded import).

Reviews of non-Python source without gauntlet produce zero
findings: that is correct behavior, not an error. Install
gauntlet to enable Tier 2/3 coverage.

## Related Skills

- `Skill(pensive:performance-review)`: methodology this command
  invokes.
- `Skill(pensive:code-refinement)`: broader refactoring guidance
  including the existing `algorithm-efficiency` module.
- `Skill(parseltongue:python-performance)`: runtime profiling.
