---
name: performance-review
description: Detects time and space complexity hotspots via AST scan. Use when code feels slow, before performance-sensitive merges, or to find O(n²) regressions.
alwaysApply: false
category: code-quality
tags:
- performance
- complexity
- algorithms
- ast
- static-analysis
tools: []
usage_patterns:
- hotspot-detection
- complexity-review
- pre-merge-performance-check
complexity: advanced
model_hint: deep
estimated_tokens: 280
progressive_loading: true
dependencies:
- imbue:proof-of-work
- imbue:review-core
- imbue:structured-output
modules:
- modules/time-complexity.md
- modules/space-complexity.md
- modules/gauntlet-integration.md
- modules/kuva-visualization.md
- modules/memory-allocation-lenses.md
---

## Table of Contents

- [Quick Start](#quick-start)
- [When to Use](#when-to-use)
- [When NOT to Use](#when-not-to-use)
- [Required TodoWrite Items](#required-todowrite-items)
- [Workflow](#workflow)
- [Tiered Analysis](#tiered-analysis)
- [Output Format](#output-format)
- [Cross-Plugin Dependencies](#cross-plugin-dependencies)
- [Supporting Modules](#supporting-modules)

# Performance Review

Static-analysis review of time and space complexity hotspots.

The skill runs in three escalating tiers. Tier 1 uses Python's
stdlib `ast` and always runs. Tier 2 uses gauntlet's tree-sitter
parser to extend detection across languages when gauntlet is
installed. Tier 3 uses the gauntlet code graph to upgrade
severity when hotspots reach other hotspots transitively. If
gauntlet is missing, Tiers 2 and 3 no-op and Tier 1 still
produces useful findings on Python source.

## Quick Start

```bash
/performance-review                  # scan changed files
/performance-review path/to/file.py  # scan one file
/performance-review --tier 1         # force Tier 1 only
```

Programmatic use:

```python
from pensive.skills.performance_review import PerformanceReviewSkill
skill = PerformanceReviewSkill()
result = skill.analyze(context, "src/module.py")
for f in result.issues:
    print(f"[{f.severity}] {f.file}:{f.line} {f.message}")
```

## When to Use

- Pre-merge review of code that runs on user-scaled inputs.
- Triage of a function that "feels slow" before reaching for a
  profiler.
- Audit a refactor for newly introduced O(n²) patterns.
- Guardrail for AI-generated code where nested-loop hot spots
  are common.

## When NOT to Use

- The target needs **runtime** measurement (memory profile, CPU
  time on real data). Use `Skill(parseltongue:python-performance)`
  instead: that skill drives `cProfile`, `py-spy`, and benchmarks.
- General refactoring guidance not focused on hotspots: use
  `Skill(pensive:code-refinement)` whose `algorithm-efficiency`
  module covers broader optimization patterns. This skill
  detects; that skill teaches.
- Deciding whether a hand-rolled loop transform (unrolling, manual
  SIMD, strength reduction) is worth keeping: use
  `Skill(leyline:loop-optimization)` for the hand-vs-compiler rule.
  This skill flags hotspot shapes, not transformation choices.
- Architecture-level performance (sharding, caching layers,
  queue placement): use `Skill(pensive:architecture-review)`.

## Required TodoWrite Items

1. `perf-review:context-established`
2. `perf-review:scan-complete`
3. `perf-review:findings-categorized`
4. `perf-review:integration-checked`
5. `perf-review:report-generated`
6. `perf-review:findings-verified`

## Workflow

### Step 1: Context (`perf-review:context-established`)

- Identify target files. If invoked with no argument, use
  `git diff --name-only`. If invoked with a path, scope to that.
- Note language(s) involved. Tier 1 covers Python; non-Python
  files need gauntlet for Tier 2 coverage.

### Step 2: Tier 1 AST scan (`perf-review:scan-complete`)

Load `modules/time-complexity.md` for the time-side patterns and
`modules/space-complexity.md` for space-side. Each module
documents the AST shape of every detector.

Alongside the automated scan, load
`modules/memory-allocation-lenses.md` and apply its three
manual lenses (unbounded external-source collections, hot-path
recompute, serial blocking I/O) by reading the target files.

For each Python target file, call:

```python
from pensive.skills.performance_review import PerformanceReviewSkill
result = PerformanceReviewSkill().analyze(context, path)
```

The visitor walks the AST once and emits `ReviewFinding` records.

### Step 3: Categorize and rank (`perf-review:findings-categorized`)

Group findings by severity:

- **HIGH**: O(n²) or worse on input-sized iterables (T1, T2).
- **MEDIUM**: Unbounded allocation or per-iteration overhead
  (T3, T4, S1, S3).
- **LOW**: Style-level inefficiencies (T5, T6, S2).
- **CRITICAL**: Reserved for Tier-3 transitive upgrades.

Within a severity, sort by file then line. Suppress findings
the user has explicitly marked acceptable (TODO/comment
markers) at module-load time of the target.

### Step 4: Tier 2/3 enrichment (`perf-review:integration-checked`)

Load `modules/gauntlet-integration.md` for the contract.

If gauntlet is installed, run Tier 2 on non-Python files that
were skipped at Step 2. If a `.gauntlet/graph.db` exists in the
working tree, run Tier 3 to upgrade severities based on
transitive hotspot reachability.

If gauntlet is missing, this step is a no-op and the report
notes "Tier 2/3 not available: install gauntlet for
multi-language and call-chain coverage."

### Step 5: Report (`perf-review:report-generated`)

Emit a markdown report:

```
## Performance Review: <target>

### HIGH (<count>)
- src/foo.py:42: Nested loop over the same iterable 'items'.
  Suggestion: sort + two pointers, or hash-set membership.

### MEDIUM (<count>)
- ...

### LOW (<count>)
- ...

Tier coverage: 1 (always) | 2 (gauntlet ✓/✗) | 3 (graph ✓/✗)
```

The report is informational. Apply fixes via
`Skill(pensive:code-refinement)` or hand-merge.

## Tiered Analysis

| Tier | Source | When it runs | What it covers |
|------|--------|--------------|----------------|
| 1 | stdlib `ast` | Always (Python source only) | T1-T6, S1-S3 |
| 2 | `gauntlet.treesitter_parser` | When gauntlet importable | Same patterns adapted to JS/TS, Go, Rust, Java, C/C++ |
| 3 | `gauntlet.graph.GraphStore` | When `.gauntlet/graph.db` exists | Severity upgrade via transitive call chains |

## Output Format

Findings use the shared `ReviewFinding` dataclass from
`pensive.skills.base`:

```python
ReviewFinding(
    file="src/module.py",
    line=42,
    severity="HIGH",          # LOW | MEDIUM | HIGH | CRITICAL
    category="time",          # time | space
    message="Nested loop over the same iterable 'items'.",
    suggestion="Sort + two pointers, or hash-set membership.",
    anchor="verbatim source text at file:line",
    code_snippet="",
)
```

This shape matches every other pensive review skill, so the
findings can flow into `Skill(pensive:unified-review)` without
translation.

## Cross-Plugin Dependencies

| Dependency | Required? | Effect when missing |
|------------|-----------|---------------------|
| `gauntlet.treesitter_parser` | Optional | Tier 2 returns []; Python coverage unchanged |
| `gauntlet.graph.GraphStore` | Optional | Tier 3 returns []; severities are not upgraded |

The optional-import contract follows the precedent in
`plugins/leyline/src/leyline/tokens.py:25-32` and
`plugins/gauntlet/hooks/pr_blast_radius.py:52-56`: try-import
to module-level sentinels, then early-return on `None` inside
each tier helper. See `modules/gauntlet-integration.md` for the
exact code shape.

## Supporting Modules

- `modules/time-complexity.md`: T1-T6 detector patterns and AST
  shapes.
- `modules/space-complexity.md`: S1-S3 detector patterns.
- `modules/gauntlet-integration.md`: Tier 2/3 contract,
  fallback semantics, examples.
- `modules/kuva-visualization.md`: Rendering benchmark data as
  charts with kuva (criterion, pytest-benchmark, ad-hoc tables).
  Covers when chart evidence satisfies proof-of-work requirements.
- `modules/memory-allocation-lenses.md`: Manual review lenses
  (not AST detectors) for unbounded collections fed from
  external sources, hot-path recompute that should be memoized,
  and serial blocking I/O over unbounded sets. Apply by reading
  the code; the detector-test rule in Testing does not cover
  these because nothing is automated.

## Verification

A perf-review finding is only useful if the caller can confirm it
is real. Use this checklist before treating any finding as worth
fixing:

1. **Reproduce under a profiler.** Run `cProfile`, `py-spy`, or the
   language-specific equivalent on the hotspot. The findings
   pinpoint AST shapes; the profiler validates the runtime impact.
2. **Re-run the failing benchmark.** If `benches/` exists, the
   hotspot should show up in numbers, not just AST scans.
3. **Compare numbers before and after the proposed fix.** The fix
   is wrong if numbers do not move. Capture both timings as
   evidence references like `[E1]` (before) and `[E2]` (after).
   When 3+ data points exist, render a kuva chart and attach it
   to the PR (see `modules/kuva-visualization.md`).
4. **Sample two or three reported hotspots manually.** Findings can
   be true at the AST level and false at the call-graph level
   when callers short-circuit. Manual sampling catches that.

The `Skill(imbue:proof-of-work)` discipline applies: claims like
"the hotspot is fixed" require evidence, not assertion.

## Testing

A test file already lives at
`plugins/pensive/tests/skills/test_performance_review.py` covering
the AST-shape detectors. Two rules for changes here:

- **Add a new detector with a test.** Any new T-* or S-* pattern
  added to the modules ships with a test that has the smallest
  AST sample exercising it.
- **Add a regression test for any false positive removed.** When
  the skill stops firing on a shape that used to look hot, the
  reason should appear as a test case so the regression is
  discoverable later.

The Iron Law applies: a new detector without a failing test first
is a request to skip TDD on a code-analysis component, which is
exactly the place where TDD pays off most.

## Verify Findings Are Grounded (`perf-review:findings-verified`)

Every finding must cite a real location and a verbatim anchor. Write
findings to `.review/findings.json` and confirm each citation resolves:

```bash
python plugins/imbue/scripts/citation_verifier.py \
  --findings .review/findings.json --repo-root .
```

Drop or label `UNVERIFIED` any finding the verifier fails (exit `1`); only
verified findings enter the report. See `Skill(imbue:review-core)` Step 5
and `Skill(imbue:structured-output)` for the schema.

## Exit Criteria

- [ ] A perf-review report file exists for the requested target.
- [ ] Every finding carries a severity label and a concrete
      suggestion the caller can act on.
- [ ] Time-complexity (T1-T6) and space-complexity (S1-S3)
      detectors have been run; tier coverage is reported.
- [ ] Tier 2 (gauntlet treesitter) and Tier 3 (graph store)
      contracts honor the optional-import sentinel: missing
      modules return `[]` rather than raising.
- [ ] Each new detector ships with a smallest-AST test that
      fails before the detector exists; each removed false
      positive ships with a regression test.
- [ ] Findings flow into `Skill(pensive:unified-review)` without
      translation when invoked from the unified entry point.
- [ ] Every reported finding carries a `Location` + verbatim `Anchor`
      confirmed by `citation_verifier.py` (exit `0`), or unverified
      findings were dropped or labeled `UNVERIFIED`
