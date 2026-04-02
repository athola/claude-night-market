# Tome-Enriched Feature Review -- Implementation Plan

**Date**: 2026-04-01
**Status**: Ready for execution
**Estimated effort**: 6 tasks across 3 phases

## Phase 1: Foundation (Module + Config)

### T001: Create research-enrichment module

**File**: `plugins/imbue/skills/feature-review/modules/research-enrichment.md`
**Action**: Create new module defining the research enrichment logic.

Contents:
- Channel-to-factor mapping table
- Score delta calculation formula
- Fibonacci clamping logic
- Evidence weight thresholds
- Graceful degradation protocol
- Integration with tome skill interfaces

**Depends on**: Nothing

### T002: Update configuration module

**File**: `plugins/imbue/skills/feature-review/modules/configuration.md`
**Action**: Add `research:` section to the configuration schema.

New section to add after the `tradeoffs:` section:

```yaml
research:
  enabled: true
  channels:
    code_search: true
    discourse: true
    papers: false
    triz: false
  evidence_threshold: 0.3
  max_delta: 2
  timeout_seconds: 120
```

Also update `.feature-review.yaml` with the same section.

**Depends on**: Nothing

### T003: Update plugin.json dependencies

**File**: `plugins/imbue/.claude-plugin/plugin.json`
**Action**: Add `tome` as an optional dependency.

Change:
```json
"dependencies": ["leyline"]
```
To:
```json
"dependencies": ["leyline"],
"optional_dependencies": ["tome"]
```

Note: The `optional_dependencies` field indicates the plugin
works without tome but gains capabilities with it installed.

**Depends on**: Nothing

## Phase 2: Skill Integration

### T004: Update SKILL.md with Phase 4.5

**File**: `plugins/imbue/skills/feature-review/SKILL.md`
**Action**: Add research enrichment phase between Phase 4
and Phase 5.

Changes:
1. Add `--research` flag to Quick Start section
2. Add Phase 4.5 workflow description after Phase 4
3. Add `feature-review:research-enriched` TodoWrite item
4. Update output format to include Adjusted and Evidence columns
5. Add `tome:research` to Integration Points section
6. Update dependencies in frontmatter to include `tome:research`
   (optional)
7. Update usage_patterns to include `research-enrichment`

**Depends on**: T001 (module must exist to reference)

### T005: Update .feature-review.yaml

**File**: `.feature-review.yaml`
**Action**: Add research configuration section.

Add after the `tradeoffs:` block:

```yaml
research:
  enabled: true
  channels:
    code_search: true
    discourse: true
    papers: false
    triz: false
  evidence_threshold: 0.3
  max_delta: 2
  timeout_seconds: 120
```

Also update:
- `output.sections` to include `research_evidence`
- `plugins.categories` to include `tome` under `specialized`

**Depends on**: T002 (config schema must be defined first)

## Phase 3: Tests

### T006: Add research enrichment tests

**File**: `plugins/imbue/tests/unit/skills/test_feature_review.py`
**Action**: Add a new test class `TestResearchEnrichment` covering:

1. `test_delta_calculation` - Research delta is applied correctly
2. `test_fibonacci_clamping` - Adjusted scores clamp to nearest
   Fibonacci number
3. `test_max_delta_constraint` - Delta capped at max_delta
4. `test_evidence_threshold_discard` - Low-evidence deltas
   discarded
5. `test_graceful_degradation` - Scores unchanged when research
   unavailable
6. `test_channel_factor_mapping` - Correct mapping between
   channels and scoring factors

**Depends on**: T001, T004 (logic and skill must be defined)

## Execution Order

```
T001 ──┐
T002 ──┤── T004 ──┐
T003 ──┘    T005 ──┤── T006
                   │
              (all complete)
```

T001, T002, T003 can run in parallel.
T004 and T005 depend on T001/T002 respectively.
T006 depends on T001 and T004.
