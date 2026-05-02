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

At module load time, `performance_review.py` runs two
try-imports to module-level sentinels:

```python
try:
    from gauntlet.treesitter_parser import parse_file as _gt_parse
except (ImportError, ModuleNotFoundError):
    _gt_parse = None

try:
    from gauntlet.graph import GraphStore as _GraphStore
except (ImportError, ModuleNotFoundError):
    _GraphStore = None
```

The dual-exception catch matches the precedent in
`plugins/leyline/src/leyline/tokens.py:25-32`. It survives the
case where the import fails for a reason other than the module
being absent (e.g., a transitive ImportError deep inside
gauntlet's own stack).

Each tier helper checks its sentinel and early-returns:

```python
def _tier2_findings(self, context, file_path):
    if _gt_parse is None:
        return []
    ...

def _tier3_findings(self, context, existing, file_path):
    if _GraphStore is None:
        return []
    ...
```

This is the same pattern proven in
`plugins/pensive/hooks/pr_blast_radius.py:52-56`, where
gauntlet's blast-radius graph is consulted only when the
plugin is installed.

## Tier 2: Tree-sitter coverage

When `_gt_parse` is set, `_tier2_findings` invokes
`parse_file(path)` and receives `(nodes, edges)` describing the
target file's AST in gauntlet's neutral graph format.

Languages currently parsed: Python, JavaScript, TypeScript, Go,
Rust, Java, C, C++, C#, Ruby, PHP, Kotlin, Swift, Scala (per
gauntlet's `_EXT_TO_LANG` map).

The patterns translated to Tier 2 are the language-agnostic
ones:

- T1 (nested loop over same iterable): present in every
  imperative language.
- T2 (membership in list): adapts to language idioms (e.g.,
  `Array.includes` in JS, `slices.Contains` in Go).
- S1 (append in nested loops): `arr.push(...)` in JS,
  `append(slice, ...)` in Go.

Patterns that do NOT translate (skipped at Tier 2):

- T3 (`re.compile` in a loop): Python-specific call shape.
- T6 (list comprehension passed to a reducer): Python-specific
  syntax.
- T4 (string `+=`): many languages have language-level string
  builders that handle this; the cost model differs.

## Tier 3: Transitive call analysis

When both `_GraphStore` is set AND a `.gauntlet/graph.db` file
exists in the working tree, `_tier3_findings` opens the graph
and queries `impact_radius()` for each existing finding's
function.

If a function reachable from a Tier-1/2 hotspot is itself a
hotspot, the original finding's severity is upgraded one step:

| Original | Upgraded |
|----------|----------|
| LOW      | MEDIUM   |
| MEDIUM   | HIGH     |
| HIGH     | CRITICAL |

This catches cases where the surface code looks fine but the
helper it calls is the actual bottleneck.

The graph file is built by gauntlet's own command:

```bash
/gauntlet-graph build .
```

When the graph does not exist, Tier 3 returns []. Building the
graph is a one-time cost; it speeds up every subsequent review.

## Failure modes and fallbacks

| Condition | Tier 2 | Tier 3 | User-visible effect |
|-----------|--------|--------|---------------------|
| gauntlet not installed | sentinel None, no-op | sentinel None, no-op | Tier 1 only; report notes the gap |
| gauntlet installed, no graph.db | parses non-Python files | no-op (no DB) | Multi-language coverage but no transitive upgrades |
| Both installed | full enrichment | severity upgrades active | Maximum coverage |

In every case, Tier 1 still runs. The skill never fails because
gauntlet is missing. This is a deliberate choice: pensive must
not require an optional plugin to deliver core value.

## Verification

The fallback contract is exercised by three tests in
`plugins/pensive/tests/skills/test_performance_review.py`:

- `test_tier2_returns_empty_when_gauntlet_missing`: stubs
  `_gt_parse` to None and asserts `_tier2_findings` returns `[]`.
- `test_tier3_returns_empty_when_graphstore_missing`: same for
  `_tier3_findings`.
- `test_full_analyze_with_gauntlet_blocked_returns_tier1_only`:
  stubs both sentinels and asserts the full `analyze()` still
  produces Tier-1 findings (T1 fires on a nested-loop snippet).

Run them with:

```bash
cd plugins/pensive
uv run pytest tests/skills/test_performance_review.py -v --no-cov
```
