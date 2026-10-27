---
module: gauntlet-integration
description: Tier 2/3 contract via gauntlet tree-sitter and graph
parent_skill: performance-review
category: integration
tags:
- gauntlet
- tree-sitter
- graph
- optional-dependency
---

# Gauntlet Integration

Performance review is a Tier-1 skill out of the box. Tiers 2 and
3 enrich the analysis when gauntlet is installed.

## Optional-import contract

At module load time, `performance_review/__init__.py` runs
try-imports to module-level sentinels:

```python
try:
    from tree_sitter_language_pack import get_parser as _ts_get_parser
except (ImportError, ModuleNotFoundError):
    _ts_get_parser = None

try:
    from gauntlet.treesitter_parser import detect_language as _gt_detect_language
except (ImportError, ModuleNotFoundError):
    _gt_detect_language = None

try:
    from gauntlet.graph import GraphStore as _GraphStore
except (ImportError, ModuleNotFoundError):
    _GraphStore = None
```

`ModuleNotFoundError` is a subclass of `ImportError`. The tuple
therefore catches exactly what `ImportError` alone would: a missing
package, and also a transitive ImportError raised inside gauntlet.
Any other exception type propagates.
`plugins/leyline/src/leyline/tokens.py:34-42` shows the wider form,
which adds a second clause for the `ValueError` and `OSError` an
optional import can raise.

Install both with the `tiers` extra, which pulls in `gauntlet-dev`
and, through it, tree-sitter. `_tier2_findings` returns `[]` when
`_ts_get_parser` is None. `_tier3_findings` returns its input
unchanged when `_GraphStore` is None. The same pattern is in
`plugins/pensive/hooks/pr_blast_radius.py`, which consults
gauntlet's blast-radius graph only when the plugin is installed.

## Tier 2: Tree-sitter coverage

Tier 2 runs on non-Python files only. It parses the source with
`_ts_get_parser(language)` and walks the tree. Gauntlet's
`parse_file` is not used, because it returns symbols and no tree.
The language comes from gauntlet's `detect_language` when
importable and from a local extension map otherwise. `.tsx` always
uses the `tsx` grammar.

Languages and the patterns each one reports:

| Language | T1 same-iterable nested loop | T2 list scan in loop | S1 append in nested loops |
|----------|------------------------------|----------------------|---------------------------|
| JavaScript, TypeScript, TSX | `for...of` / `for...in` | `.includes(`, `.indexOf(` | `.push(` |
| Go | `for ... range` | `slices.Contains`, `slices.Index` | `append(` |
| Rust | `for ... in` | none | `.push(` |
| Java | enhanced `for` | none | none (`.add(` is ambiguous) |
| C | none (no iterable loop) | none | none |
| C++ | range-based `for` | none | `.push_back(` |

T1 is HIGH time, T2 is HIGH time, S1 is MEDIUM space, matching
Tier 1's severities. `Set.has(` and `Map.has(` never match. Loops
inside a nested function or lambda do not inherit the enclosing
loops.

Patterns that do not translate (skipped at Tier 2):

- T3 (`re.compile` in a loop): Python-specific call shape.
- T6 (list comprehension passed to a reducer): Python-specific
  syntax.
- T4 (string `+=`): many languages have language-level string
  builders that handle this, and the cost model differs.
- T5, S2, S3: no unambiguous cross-language shape.

Parse failures are reported, not swallowed. A grammar that fails to
load, or a tree with syntax errors, appends a warning to
`AnalysisResult.warnings` and yields no Tier 2 findings for that
file.

## Tier 3: Transitive call analysis

When `_GraphStore` is set and a `.gauntlet/graph.db` exists in the
scanned file's directory or any parent, `_tier3_findings` opens the
graph. It does not use `impact_radius()`, which walks callers.
Tier 3 needs callees, so it runs a forward breadth-first search
over `CALLS` edges, the same loop shape as `gauntlet.flows`.

For each finding:

1. Convert its 1-based line to a 0-based row and pick the
   innermost Function or Test node in that file whose range
   contains it. No such node, no upgrade.
2. Walk `CALLS` edges from that node with a visited set (so call
   cycles end) and a depth cap of 10. Targets without a graph node
   are skipped.
3. For each reachable function other than the seed, scan its file
   from disk (Tier 1 for `.py`, Tier 2 otherwise, cached per file)
   and check whether any finding lies inside the function's range.
4. On the first such callee, raise the finding one step and append
   the callee to its message.

| Original | Upgraded |
|----------|----------|
| LOW      | MEDIUM   |
| MEDIUM   | HIGH     |
| HIGH     | CRITICAL |

A finding is upgraded at most once. `_tier3_findings` returns the
full list with upgraded findings in place, and `analyze()` assigns
it back to `result.issues`, so nothing is duplicated. An unreadable
graph file appends a warning and leaves the findings unchanged.

Build the graph once per tree:

```bash
python3 plugins/gauntlet/scripts/graph_build.py <root>
```

## Failure modes and fallbacks

| Condition | Tier 2 | Tier 3 | User-visible effect |
|-----------|--------|--------|---------------------|
| `tiers` extra not installed | sentinel None, no-op | sentinel None, no-op | Tier 1 only; report notes the gap |
| Extra installed, no graph.db | parses non-Python files | no-op (no DB) | Multi-language coverage but no transitive upgrades |
| Extra installed, graph.db found | full detection | severity upgrades active | Maximum coverage |

In every case, Tier 1 still runs. The skill never fails because
the extra is missing. This is a deliberate choice: pensive must
not require an optional plugin to deliver core value.

## Verification

The sentinel-None contract is exercised in
`plugins/pensive/tests/skills/test_performance_review.py`
(`test_tier2_returns_empty_when_gauntlet_missing`,
`test_tier3_returns_empty_when_graphstore_missing`,
`test_full_analyze_with_gauntlet_blocked_returns_tier1_only`).
Tier 2 detection, parse warnings, and Tier 3 upgrades run against
the real parser and a real `GraphStore` in
`plugins/pensive/tests/skills/test_performance_review_tiers.py`.
The dev dependency group installs gauntlet so those tests run.

```bash
cd plugins/pensive
uv run pytest tests/skills/test_performance_review.py \
  tests/skills/test_performance_review_tiers.py -v --no-cov
```
