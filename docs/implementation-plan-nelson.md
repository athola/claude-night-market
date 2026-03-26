# Nelson Integration -- Implementation Plan

**Date**: 2026-03-26
**Status**: Ready for execution
**Specification**: docs/specification-nelson.md
**Estimated effort**: 7 tasks across 3 phases

## Phase 1: Foundation (Core Patterns)

### T001: Create Sailing Orders Template (FR-001)

**File**: `plugins/attune/skills/mission-orchestrator/references/sailing-orders.md`
**Action**: Create new reference module with structured template.

**Content**:
- Template overview and purpose
- Field definitions with types
- Example sailing orders (2-3 scenarios)
- Integration guidance for mission-orchestrator

**Depends on**: Nothing
**Effort**: S
**Verification**: File exists, all AC-001 criteria met

### T002: Create Action Stations Module (FR-002)

**File**: `plugins/leyline/skills/risk-classification/modules/action-stations.md`
**Action**: Create new module with 4-tier risk system.

**Content**:
- Station 0 (Patrol): criteria and controls
- Station 1 (Caution): criteria and controls
- Station 2 (Action): criteria and controls
- Station 3 (Trafalgar): criteria and controls
- Station selection decision tree
- Integration with war-room-checkpoint

**Depends on**: Nothing
**Effort**: M
**Verification**: File exists, all AC-002 criteria met

## Phase 2: Team Composition

### T003: Create Squadron Composition Module (FR-003)

**File**: `plugins/conjure/skills/agent-teams/references/squadron-composition.md`
**Action**: Create new reference module with team rules.

**Content**:
- Role definitions (Admiral, Captain, Red-cell Navigator)
- Team sizing rules by mission complexity
- Execution mode selection guidance
- Maximum team size rationale (10 agents)
- Example squadron compositions

**Depends on**: Nothing
**Effort**: S
**Verification**: File exists, all AC-003 criteria met

### T004: Create Execution Modes Module (FR-007)

**File**: `plugins/conjure/skills/delegation-core/references/execution-modes.md`
**Action**: Create new reference module with mode selection criteria.

**Content**:
- single-session mode: when to use, how it works
- subagents mode: when to use, how it works
- agent-team mode: when to use, how it works
- Decision matrix for mode selection
- Compatibility notes (agent-team experimental)

**Depends on**: T003
**Effort**: S
**Verification**: File exists, all AC-007 criteria met

## Phase 3: Reporting & Checklists

### T005: Create Quarterdeck Report Template (FR-004)

**File**: `plugins/attune/skills/mission-orchestrator/references/quarterdeck-report.md`
**Action**: Create new reference module with checkpoint template.

**Content**:
- Template overview and purpose
- Field definitions (progress, blockers, budget, risks)
- Example quarterdeck reports
- Checkpoint rhythm guidance (when to checkpoint)

**Depends on**: T001
**Effort**: S
**Verification**: File exists, all AC-004 criteria met

### T006: Create Captain's Log Template (FR-005)

**File**: `plugins/attune/skills/project-execution/references/captains-log.md`
**Action**: Create new reference module with final report template.

**Content**:
- Template overview and purpose
- Field definitions (artifacts, decisions, evidence, follow-ups)
- Example captain's logs (success, partial, failed)
- Integration with project-execution workflow

**Depends on**: T005
**Effort**: S
**Verification**: File exists, all AC-005 criteria met

### T007: Create Failure-mode Checklist (FR-006)

**File**: `plugins/leyline/skills/damage-control/modules/failure-mode-checklist.md`
**Action**: Create new module with checklist questions.

**Content**:
- 5 checklist questions with explanations
- When to apply (Station 1+ tasks)
- How to document answers
- Integration with quality-gate verification

**Depends on**: T002
**Effort**: S
**Verification**: File exists, all AC-006 criteria met

## Phase 4: Integration (SKILL.md Updates)

### T008: Update mission-orchestrator SKILL.md

**File**: `plugins/attune/skills/mission-orchestrator/SKILL.md`
**Action**: Add references to new modules.

**Updates**:
- Add "Sailing Orders" section referencing sailing-orders.md
- Add "Quarterdeck Rhythm" section referencing quarterdeck-report.md
- Update "Related Skills" to include risk-classification for action stations

**Depends on**: T001, T005
**Effort**: S
**Verification**: SKILL.md contains references, links work

### T009: Update risk-classification SKILL.md

**File**: `plugins/leyline/skills/risk-classification/SKILL.md`
**Action**: Add reference to action-stations module.

**Updates**:
- Add "Action Stations" section referencing action-stations.md
- Update classification guidance to use 4-tier system
- Add cross-reference to damage-control for failure-mode checklist

**Depends on**: T002, T007
**Effort**: S
**Verification**: SKILL.md contains references, links work

### T010: Update agent-teams SKILL.md

**File**: `plugins/conjure/skills/agent-teams/SKILL.md`
**Action**: Add reference to squadron-composition module.

**Updates**:
- Add "Squadron Composition" section referencing squadron-composition.md
- Update team sizing guidance
- Add role definitions (Admiral, Captain, Red-cell Navigator)

**Depends on**: T003
**Effort**: S
**Verification**: SKILL.md contains references, links work

### T011: Update delegation-core SKILL.md

**File**: `plugins/conjure/skills/delegation-core/SKILL.md`
**Action**: Add reference to execution-modes module.

**Updates**:
- Add "Execution Modes" section referencing execution-modes.md
- Add mode selection decision guidance
- Note experimental status of agent-team mode

**Depends on**: T004
**Effort**: S
**Verification**: SKILL.md contains references, links work

### T012: Update project-execution SKILL.md

**File**: `plugins/attune/skills/project-execution/SKILL.md`
**Action**: Add reference to captains-log module.

**Updates**:
- Add "Captain's Log" section referencing captains-log.md
- Add final report structure guidance
- Link to mission-orchestrator for full workflow

**Depends on**: T006
**Effort**: S
**Verification**: SKILL.md contains references, links work

### T013: Update damage-control SKILL.md

**File**: `plugins/leyline/skills/damage-control/SKILL.md`
**Action**: Add reference to failure-mode-checklist module.

**Updates**:
- Add "Failure-mode Checklist" section referencing failure-mode-checklist.md
- Add requirement for Station 1+ tasks
- Link to risk-classification for station determination

**Depends on**: T007
**Effort**: S
**Verification**: SKILL.md contains references, links work

## Dependency Graph

```
Phase 1:
  T001 ─────────────────────────────────┐
  T002 ────────────────────────┐        │
                                │        │
Phase 2:                        │        │
  T003                          │        │
    └─→ T004                    │        │
                                │        │
Phase 3:                        │        │
  T001 ─→ T005                  │        │
           └─→ T006             │        │
  T002 ─→ T007                  │        │
                                │        │
Phase 4:                        │        │
  T001 ─→ T008 ←────────────────┼────────┘
  T002 ─→ T009 ←────────────────┘
  T007 ─→ T009
  T003 ─→ T010
  T004 ─→ T011
  T006 ─→ T012
  T007 ─→ T013
```

## Risk Summary

| Task | Action Station | Rationale |
|------|----------------|-----------|
| T001-T007 | 0 (Patrol) | Adding new reference files, no existing code changes |
| T008-T013 | 1 (Caution) | Modifying existing SKILL.md files, user-visible documentation |

## Verification Checklist

- [ ] All 7 reference/module files created
- [ ] All 6 SKILL.md files updated with references
- [ ] All acceptance criteria from specification met
- [ ] Markdown formatting validated (80-char wrap)
- [ ] No broken internal links
- [ ] Progressive loading pattern followed
