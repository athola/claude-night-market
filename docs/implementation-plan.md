# Stewardship Framework - Implementation Plan v0.1.0

**Author**: Claude Night Market
**Date**: 2026-03-06
**Branch**: stewardship-1.5.7
**Target Completion**: Single session, phased delivery

## Architecture

### System Overview

The stewardship framework is a cross-cutting concern that lives
primarily in leyline (foundation layer) with thin integration
points across all 16 plugins. It adds no new plugins, no new
dependencies, and no blocking gates.

```
                    STEWARDSHIP.md (repo root)
                           |
              leyline:stewardship (skill)
              /            |            \
     Per-plugin READMEs   Hookify Rule   Health Dimensions
     (16 plugins)         (campsite)     (pulse script)
                              |               |
                        Action Tracker    /stewardship-health
                        (JSONL file)      (command)
                              |
                    Integration Points
                    (abstract, sanctum, imbue)
```

### Components

#### Component: STEWARDSHIP.md (Manifesto)

**Responsibility**: Define the five principles with research
origins and concrete examples. Single source of truth for
stewardship philosophy.

**Technology**: Markdown
**Interfaces**: Read by humans, linked from plugin READMEs
**Dependencies**: None (root artifact, no dependencies)

#### Component: leyline:stewardship (Skill)

**Responsibility**: Cross-cutting skill that presents stewardship
principles with layer-specific guidance and decision heuristics.
Referenced by other skills and invoked during plugin work.

**Technology**: SKILL.md with YAML frontmatter
**Interfaces**: `Skill(leyline:stewardship)` invocation
**Dependencies**: None (foundation layer)
**Location**: `plugins/leyline/skills/stewardship/SKILL.md`

#### Component: Per-Plugin Stewardship Sections

**Responsibility**: Plugin-specific stewardship guidance appended
to each plugin's README.md. 3-5 improvement opportunities per
plugin, link to root manifesto.

**Technology**: Markdown sections in existing README.md files
**Interfaces**: Human-readable, discoverable via README
**Dependencies**: STEWARDSHIP.md must exist for linking

#### Component: Campsite Check (Hookify Rule)

**Responsibility**: Non-blocking prompt that surfaces 1-2 specific
improvement suggestions when a contributor finishes work in a
plugin.

**Technology**: Hookify rule (YAML frontmatter + markdown body)
**Interfaces**: UserPromptSubmit event, stdout message
**Dependencies**: Git diff/status for detecting modified files
**Location**: `plugins/hookify/skills/rule-catalog/rules/
stewardship/campsite-check.md`

#### Component: Stewardship Action Tracker

**Responsibility**: Append-only JSONL file recording stewardship
actions per session. Lightweight, zero-latency writes.

**Technology**: Python 3.9 script, JSONL format
**Interfaces**: Called by campsite check, read by health command
**Dependencies**: `.claude/stewardship/` directory
**Location**: `plugins/leyline/scripts/stewardship_tracker.py`

#### Component: Plugin Health Dimensions

**Responsibility**: Measure 5 health dimensions per plugin:
documentation freshness, test coverage, code quality, contributor
friendliness, improvement velocity.

**Technology**: Python 3.9 script reading filesystem + JSONL data
**Interfaces**: Called by health command, returns dimension data
**Dependencies**: Stewardship action tracker (for velocity)
**Location**: `plugins/leyline/scripts/plugin_health.py`

#### Component: /stewardship-health Command

**Responsibility**: Display stewardship health for one or all
plugins in descriptive (non-numeric) format.

**Technology**: Command markdown definition
**Interfaces**: `/stewardship-health [plugin]`
**Dependencies**: Plugin health dimensions script
**Location**: `plugins/imbue/commands/stewardship-health.md`

### Data Flow

```
1. Contributor works on plugin files
       |
2. Contributor signals completion ("commit", "PR", "done")
       |
3. Campsite Check fires (UserPromptSubmit hookify rule)
   - Reads git diff to identify modified plugin
   - Checks README age, TODO count, test presence
   - Surfaces 1-2 suggestions (non-blocking)
       |
4. Contributor optionally takes stewardship action
       |
5. Action Tracker records to .claude/stewardship/actions.jsonl
       |
6. /stewardship-health reads tracker + filesystem metrics
   - Displays per-plugin health dimensions
```

## Task Breakdown

### Phase 1: Philosophy — TASK-001 through TASK-005

#### TASK-001: Create STEWARDSHIP.md Manifesto

**Description**: Write the root manifesto with five principles,
research origins, and concrete examples.

**Type**: Documentation
**Priority**: P0 (Critical)
**Estimate**: 3 points
**Dependencies**: None
**Linked Requirements**: FR-001

**Acceptance Criteria**:

- [ ] File exists at repo root as `STEWARDSHIP.md`
- [ ] Contains all five principles with definitions
- [ ] Each principle has research origin cited
- [ ] Each principle has 2-3 concrete plugin examples
- [ ] Zero ambiguous language
- [ ] Readable in under 5 minutes
- [ ] Passes slop detection scan

---

#### TASK-002: Create leyline:stewardship Skill

**Description**: Create the cross-cutting stewardship skill in
the leyline plugin with principles, layer-specific guidance,
and decision heuristics.

**Type**: Implementation
**Priority**: P0 (Critical)
**Estimate**: 3 points
**Dependencies**: TASK-001
**Linked Requirements**: FR-005

**Acceptance Criteria**:

- [ ] Skill exists at `plugins/leyline/skills/stewardship/SKILL.md`
- [ ] Valid YAML frontmatter passes validation
- [ ] Under 2000 tokens estimated
- [ ] Contains decision heuristic for stewardship moments
- [ ] Contains layer-specific guidance (meta/foundation/utility/domain)
- [ ] Registered in leyline plugin.json

---

#### TASK-003: Add Stewardship Sections to Plugin READMEs

**Description**: Add a "## Stewardship" section to all 16 plugin
README.md files with plugin-specific guidance.

**Type**: Documentation
**Priority**: P1 (High)
**Estimate**: 5 points
**Dependencies**: TASK-001
**Linked Requirements**: FR-002

**Acceptance Criteria**:

- [ ] All 16 READMEs have "## Stewardship" section
- [ ] Each section has 3-5 plugin-specific opportunities
- [ ] Each section links to root STEWARDSHIP.md
- [ ] Each section is at most 20 lines
- [ ] Layer-appropriate guidance per plugin
- [ ] Passes slop detection scan

---

#### TASK-004: Update plugin.json Files

**Description**: Add stewardship skill reference to leyline
plugin.json and update any `provides` or `dependencies` fields
as needed across plugins.

**Type**: Infrastructure
**Priority**: P2 (Medium)
**Estimate**: 2 points
**Dependencies**: TASK-002
**Linked Requirements**: FR-008 (partial)

**Acceptance Criteria**:

- [ ] Leyline plugin.json lists stewardship skill
- [ ] All plugin.json files pass validation
- [ ] No circular dependencies introduced

---

#### TASK-005: Phase 1 Verification

**Description**: Verify all Phase 1 deliverables meet acceptance
criteria from FR-001, FR-002, FR-005.

**Type**: Testing
**Priority**: P0 (Critical)
**Estimate**: 2 points
**Dependencies**: TASK-001, TASK-002, TASK-003, TASK-004

**Acceptance Criteria**:

- [ ] STEWARDSHIP.md exists and contains all 5 principles
- [ ] All 16 READMEs have stewardship sections
- [ ] Leyline skill passes frontmatter validation
- [ ] Leyline skill under 2000 tokens
- [ ] Slop scan passes on all new markdown
- [ ] Manual readability check passes

### Phase 2: Practice — TASK-006 through TASK-010

#### TASK-006: Create Campsite Check Hookify Rule

**Description**: Create the hookify rule that fires on
UserPromptSubmit when completion-related keywords are detected,
surfacing 1-2 specific improvement suggestions.

**Type**: Implementation
**Priority**: P0 (Critical)
**Estimate**: 5 points
**Dependencies**: TASK-001
**Linked Requirements**: FR-003

**Acceptance Criteria**:

- [ ] Rule file at `plugins/hookify/skills/rule-catalog/rules/
  stewardship/campsite-check.md`
- [ ] YAML frontmatter with correct event/conditions
- [ ] Fires on "commit", "done", "PR", "complete" keywords
- [ ] Does not fire when no plugin files were modified
- [ ] Suggestions are specific (file ages, TODO counts)
- [ ] Completes under 2 seconds
- [ ] Follows hookify rule-catalog structure

---

#### TASK-007: Create Stewardship Action Tracker

**Description**: Create the JSONL-based action tracking script
that records stewardship actions with timestamp, plugin, type,
file, and description.

**Type**: Implementation
**Priority**: P1 (High)
**Estimate**: 3 points
**Dependencies**: TASK-006
**Linked Requirements**: FR-004

**Acceptance Criteria**:

- [ ] Script at `plugins/leyline/scripts/stewardship_tracker.py`
- [ ] Python 3.9 compatible (no 3.10+ syntax)
- [ ] Writes to `.claude/stewardship/actions.jsonl`
- [ ] Each line is valid JSON with required schema fields
- [ ] Append-only (no file locking, no rewrites)
- [ ] Creates directory if missing
- [ ] Zero-latency from contributor perspective

---

#### TASK-008: Create Stewardship Tracker Tests

**Description**: Write pytest tests for the stewardship action
tracker covering write, read, and edge cases.

**Type**: Testing
**Priority**: P1 (High)
**Estimate**: 2 points
**Dependencies**: TASK-007
**Linked Requirements**: FR-004, NFR-002

**Acceptance Criteria**:

- [ ] Tests at `plugins/leyline/tests/test_stewardship_tracker.py`
- [ ] Test: valid action writes correct JSONL
- [ ] Test: missing directory is created
- [ ] Test: corrupt file handles gracefully
- [ ] Test: Python 3.9 compatibility verified
- [ ] All tests pass with `pytest`

---

#### TASK-009: Install Campsite Check Rule

**Description**: Add the campsite-check rule to the active rules
configuration so it loads during sessions.

**Type**: Infrastructure
**Priority**: P1 (High)
**Estimate**: 1 point
**Dependencies**: TASK-006
**Linked Requirements**: FR-003

**Acceptance Criteria**:

- [ ] Rule is discoverable by hookify
- [ ] Rule loads without errors
- [ ] Rule can be enabled/disabled via hookify configuration

---

#### TASK-010: Phase 2 Verification

**Description**: Verify all Phase 2 deliverables meet acceptance
criteria from FR-003, FR-004.

**Type**: Testing
**Priority**: P0 (Critical)
**Estimate**: 2 points
**Dependencies**: TASK-006, TASK-007, TASK-008, TASK-009

**Acceptance Criteria**:

- [ ] Campsite check rule loads and fires correctly
- [ ] Action tracker writes valid JSONL
- [ ] All hooks pass Python 3.9 compatibility
- [ ] All hooks complete under 2 seconds
- [ ] No false positives (no fire when no plugin files changed)
- [ ] All tests pass

### Phase 3: Pulse — TASK-011 through TASK-015

#### TASK-011: Create Plugin Health Dimensions Script

**Description**: Create the health measurement script that
calculates 5 dimensions per plugin: documentation freshness,
test coverage, code quality, contributor friendliness, and
improvement velocity.

**Type**: Implementation
**Priority**: P1 (High)
**Estimate**: 5 points
**Dependencies**: TASK-007 (reads action tracker data)
**Linked Requirements**: FR-006

**Acceptance Criteria**:

- [ ] Script at `plugins/leyline/scripts/plugin_health.py`
- [ ] Python 3.9 compatible
- [ ] Measures all 5 dimensions
- [ ] Returns descriptive labels not numeric scores
- [ ] Handles missing data as "not measured"
- [ ] Works for all 16 plugins

---

#### TASK-012: Create Plugin Health Tests

**Description**: Write pytest tests for the plugin health
dimensions script.

**Type**: Testing
**Priority**: P1 (High)
**Estimate**: 3 points
**Dependencies**: TASK-011
**Linked Requirements**: FR-006, NFR-002

**Acceptance Criteria**:

- [ ] Tests at `plugins/leyline/tests/test_plugin_health.py`
- [ ] Test: each dimension returns valid data
- [ ] Test: missing data returns "not measured"
- [ ] Test: all 16 plugins can be measured
- [ ] Test: Python 3.9 compatibility
- [ ] All tests pass with `pytest`

---

#### TASK-013: Create /stewardship-health Command

**Description**: Create the command definition that displays
stewardship health for one or all plugins.

**Type**: Implementation
**Priority**: P2 (Medium)
**Estimate**: 3 points
**Dependencies**: TASK-011
**Linked Requirements**: FR-007

**Acceptance Criteria**:

- [ ] Command at `plugins/imbue/commands/stewardship-health.md`
- [ ] Works with no args (all plugins summary)
- [ ] Works with plugin name arg (detailed view)
- [ ] Uses descriptive language, no letter grades
- [ ] Displays "not measured" for missing data
- [ ] Registered in imbue plugin.json

---

#### TASK-014: Integration Touchpoints

**Description**: Add stewardship context to existing systems:
sanctum Stop hook checklist, proof-of-work evidence, homeostatic
monitor context.

**Type**: Implementation
**Priority**: P2 (Medium)
**Estimate**: 3 points
**Dependencies**: TASK-007, TASK-011
**Linked Requirements**: FR-008

**Acceptance Criteria**:

- [ ] Sanctum verify_workflow_complete.py includes stewardship item
- [ ] Homeostatic monitor reads stewardship velocity context
- [ ] Integration points are lightweight (< 10 lines each)
- [ ] No circular dependencies introduced
- [ ] Existing tests still pass after changes

---

#### TASK-015: Phase 3 Verification and Self-Check

**Description**: Verify all Phase 3 deliverables and run the
stewardship framework against itself (NFR-004).

**Type**: Testing
**Priority**: P0 (Critical)
**Estimate**: 2 points
**Dependencies**: TASK-011, TASK-012, TASK-013, TASK-014

**Acceptance Criteria**:

- [ ] Health dimensions report for all 16 plugins
- [ ] /stewardship-health command produces valid output
- [ ] Missing data displays correctly
- [ ] Integration points work without breaking existing systems
- [ ] Leyline plugin passes its own stewardship health check
- [ ] All new markdown passes slop detection
- [ ] Zero blame-oriented language in user-facing messages

## Dependency Graph

```
TASK-001 (STEWARDSHIP.md)
    ├──▶ TASK-002 (leyline skill)
    │       └──▶ TASK-004 (plugin.json updates)
    ├──▶ TASK-003 (16 README sections)
    ├──▶ TASK-006 (campsite check rule)
    │       ├──▶ TASK-009 (install rule)
    │       └──▶ TASK-007 (action tracker)
    │               ├──▶ TASK-008 (tracker tests)
    │               └──▶ TASK-011 (health dimensions)
    │                       ├──▶ TASK-012 (health tests)
    │                       ├──▶ TASK-013 (health command)
    │                       └──▶ TASK-014 (integrations)
    │
    ├──▶ TASK-005 (Phase 1 verify)
    │       [depends on: 001, 002, 003, 004]
    ├──▶ TASK-010 (Phase 2 verify)
    │       [depends on: 006, 007, 008, 009]
    └──▶ TASK-015 (Phase 3 verify)
            [depends on: 011, 012, 013, 014]
```

### Critical Path

```
TASK-001 → TASK-006 → TASK-007 → TASK-011 → TASK-013
  (3pt)      (5pt)      (3pt)      (5pt)      (3pt)
                                                = 19 points
```

### Parallelization Opportunities

After TASK-001 completes, three independent tracks can run:

- **Track A**: TASK-002, TASK-004 (leyline skill + plugin.json)
- **Track B**: TASK-003 (16 README sections)
- **Track C**: TASK-006, TASK-007, TASK-009 (campsite + tracker)

After TASK-011 completes:

- **Track D**: TASK-012 (health tests)
- **Track E**: TASK-013 (health command)
- **Track F**: TASK-014 (integration touchpoints)

## Sprint Schedule

### Sprint 1: Philosophy (Phase 1)

**Goal**: Establish stewardship philosophy across the ecosystem.

**Planned Tasks (15 points)**:

- TASK-001: STEWARDSHIP.md (3 pts)
- TASK-002: Leyline skill (3 pts)
- TASK-003: 16 README sections (5 pts)
- TASK-004: Plugin.json updates (2 pts)
- TASK-005: Phase 1 verification (2 pts)

**Deliverable**: Every plugin has stewardship documentation.
Contributors can find and understand the five principles.

**Risks**:

- README sections become repetitive across plugins.
  Mitigation: each section is layer-specific and plugin-specific.

### Sprint 2: Practice (Phase 2)

**Goal**: Activate stewardship at the point of work.

**Planned Tasks (13 points)**:

- TASK-006: Campsite check rule (5 pts)
- TASK-007: Action tracker (3 pts)
- TASK-008: Tracker tests (2 pts)
- TASK-009: Install rule (1 pt)
- TASK-010: Phase 2 verification (2 pts)

**Deliverable**: Contributors receive improvement suggestions
when finishing work. Actions are tracked.

**Risks**:

- Campsite check produces noise. Mitigation: max 2 suggestions,
  only when plugin files were actually modified.
- Hook latency budget exceeded. Mitigation: simple filesystem
  checks only, no expensive git operations.

### Sprint 3: Pulse (Phase 3)

**Goal**: Make stewardship health visible.

**Planned Tasks (16 points)**:

- TASK-011: Health dimensions script (5 pts)
- TASK-012: Health tests (3 pts)
- TASK-013: Health command (3 pts)
- TASK-014: Integration touchpoints (3 pts)
- TASK-015: Phase 3 verification (2 pts)

**Deliverable**: `/stewardship-health` command works. Existing
systems enriched with stewardship context.

**Risks**:

- Test coverage data unavailable for some plugins.
  Mitigation: "not measured" fallback for all dimensions.
- Integration changes break existing systems.
  Mitigation: changes are additive-only, < 10 lines each.

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| README sections become generic | Med | Med | Layer-specific templates, plugin-specific examples |
| Campsite check noise/fatigue | High | Med | Max 2 suggestions, only on modified plugins |
| Hook latency > 2 seconds | High | Low | Filesystem-only checks, no git subprocess calls |
| Python 3.9 compatibility breaks | High | Low | No 3.10+ syntax, test under 3.9.6 |
| Integration breaks existing hooks | High | Low | Additive changes only, run existing tests |
| Framework becomes shelf-ware | Med | Med | Philosophy-first ships immediately, practice activates daily |
| Blame-oriented language slips in | Med | Low | Slop scan + manual review, NFR-005 explicit |

## Success Metrics

- [ ] STEWARDSHIP.md exists with all 5 principles
- [ ] 16/16 plugin READMEs have stewardship sections
- [ ] Leyline skill passes validation, under 2000 tokens
- [ ] Campsite check fires correctly, no false positives
- [ ] Action tracker writes valid JSONL
- [ ] Health dimensions report for all 16 plugins
- [ ] /stewardship-health command works
- [ ] All hooks Python 3.9 compatible
- [ ] All hooks under 2-second timeout
- [ ] Zero blame language in user-facing messages
- [ ] Framework passes its own health check (NFR-004)

## Timeline

| Sprint | Focus | Tasks | Points | Deliverable |
|--------|-------|-------|--------|-------------|
| 1 | Philosophy | 001-005 | 15 | Stewardship docs everywhere |
| 2 | Practice | 006-010 | 13 | Campsite check + tracking |
| 3 | Pulse | 011-015 | 16 | Health command + integrations |
| **Total** | | **15 tasks** | **44 pts** | **Complete framework** |

## Next Steps

1. Proceed to execution with `Skill(attune:project-execution)`
2. Execute Sprint 1 (Philosophy) first as foundation
3. Sprint 2 (Practice) and Sprint 3 (Pulse) build on Sprint 1
4. After all sprints: final verification pass (TASK-015)
