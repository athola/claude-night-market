# MECW Optimization Plan: Module Bloat Consolidation

**Issues**: #28 (Consolidate module bloat in skill directories), #29 (Optimize oversized agent/module files)
**Priority**: Performance - Token Optimization
**Status**: IN PROGRESS

## Current State Analysis

### Module Size Breakdown (Lines)

| Skill Directory | Total Size | Largest Module | Lines |
|-----------------|------------|----------------|-------|
| `skills-eval/modules/` | 112K | performance-benchmarking.md | 543 |
| `skill-authoring/modules/` | 104K | progressive-disclosure.md | 593 |
| `hook-authoring/modules/` | 80K | testing-hooks.md | 627 |
| `methodology-curator/modules/` | 52K | - | - |
| `makefile-dogfooder/modules/` | 52K | testing.md | 567 |
| `modular-skills/modules/` | 44K | - | - |
| `subagent-testing/modules/` | 20K | testing-patterns.md | 569 |

### Files Exceeding 500 Lines (MECW Critical)

| File | Lines | Recommendation |
|------|-------|----------------|
| `hook-authoring/modules/testing-hooks.md` | 627 | Archive examples to docs/examples/ |
| `hook-authoring/modules/performance-guidelines.md` | 608 | Extract benchmarks to examples |
| `hook-authoring/modules/sdk-callbacks.md` | 597 | Keep core, archive advanced patterns |
| `skill-authoring/modules/progressive-disclosure.md` | 593 | Keep - core methodology |
| `hook-authoring/modules/scope-selection.md` | 577 | Keep - essential guidance |
| `skill-authoring/modules/graphviz-conventions.md` | 570 | Archive examples to examples/ |
| `subagent-testing/modules/testing-patterns.md` | 569 | Extract to standalone skill |
| `makefile-dogfooder/modules/testing.md` | 567 | Archive test examples |
| `skill-authoring/modules/anti-rationalization.md` | 563 | Keep - core methodology |

## Optimization Strategy

### Phase 1: Extract to Standalone Skills (High Impact)

**Target**: `subagent-testing/modules/testing-patterns.md` (569 lines)

Per issue #29, this module should be a standalone skill:
- Allows independent loading when testing focus is needed
- Referenced from skill-authoring instead of embedded
- Reduces skill-authoring token load by ~570 lines

**Action**: Already exists as `abstract/skills/subagent-testing/` - verify it's properly referenced.

### Phase 2: Archive Examples (Medium Impact)

Move large example blocks to `docs/examples/`:

1. `hook-authoring/modules/testing-hooks.md`
   - Keep: Testing philosophy, basic patterns (first 200 lines)
   - Archive: Detailed examples, advanced scenarios

2. `skill-authoring/modules/graphviz-conventions.md`
   - Keep: Core conventions, basic syntax
   - Archive: Complex diagram examples

3. `makefile-dogfooder/modules/testing.md`
   - Keep: Testing methodology
   - Archive: Full test file examples

### Phase 3: Link Replacement Pattern

Replace archived content with links:

```markdown
## Advanced Examples

For detailed examples, see:
- [Hook Testing Examples](../../../docs/examples/hook-testing/)
- [Complex Scenarios](../../../docs/examples/hook-testing/advanced-scenarios.md)
```

## Implementation Checklist

- [x] Analyze module sizes (completed)
- [x] Identify optimization candidates (completed)
- [x] Phase 1: Verify subagent-testing skill structure (verified as standalone)
- [x] Phase 2: Archive hook-authoring examples (testing-hooks.md: 627 -> 118 lines)
- [ ] Phase 2: Archive graphviz-conventions examples (deferred)
- [ ] Phase 2: Archive testing.md examples (deferred)
- [x] Phase 3: Update modules with links (testing-hooks.md done)
- [x] Validate token reduction achieved (81% reduction on first module)

## Expected Impact

| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| hook-authoring total | 80K | ~50K | ~37% |
| skill-authoring total | 104K | ~80K | ~23% |
| Total abstract tokens | Critical | Warning | ~25% |

## MECW Compliance Target

Move abstract plugin from **Critical (>70K tokens)** to **Warning (<70K tokens)**.
