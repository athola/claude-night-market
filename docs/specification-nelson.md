# Nelson Integration -- Specification

**Date**: 2026-03-26
**Status**: Draft
**Brief**: docs/project-brief-nelson.md

## Functional Requirements

### FR-001: Sailing Orders Template

**Priority**: High
**Plugin**: attune
**Component**: mission-orchestrator

The system shall provide a structured Sailing Orders template
for mission definition.

**Template Fields**:

```yaml
sailing_orders:
  outcome: string          # What success looks like
  success_metric: string   # Measurable completion criteria
  deadline: string         # Time boundary (session, date, or duration)
  constraints:
    token_budget: int?     # Maximum tokens to spend
    time_budget: string?   # Maximum time (e.g., "2 hours")
    forbidden: list?       # Actions that must NOT be taken
  scope:
    in_scope: list         # Areas to work on
    out_of_scope: list     # Areas to avoid
  stop_criteria: list      # Conditions that halt the mission
```

**Acceptance Criteria**:

- AC-001.1: Template exists at
  `plugins/attune/skills/mission-orchestrator/references/sailing-orders.md`
- AC-001.2: Template includes all fields above with examples
- AC-001.3: mission-orchestrator SKILL.md references the template
- AC-001.4: Template loads on demand (progressive loading)

### FR-002: Action Stations (4-Tier Risk System)

**Priority**: High
**Plugin**: leyline
**Component**: risk-classification

The system shall provide a 4-tier risk classification system
with required controls per tier.

**Tier Definitions**:

| Station | Name | When | Required Controls |
|---------|------|------|-------------------|
| 0 | Patrol | Low blast radius, easy rollback | Basic validation, rollback step |
| 1 | Caution | User-visible changes, moderate impact | Independent review, negative test, rollback note |
| 2 | Action | Security/compliance/data integrity | Red-cell review, failure-mode checklist, go/no-go checkpoint |
| 3 | Trafalgar | Irreversible, regulated, safety-sensitive | Minimal scope, human confirmation, two-step verification, contingency plan |

**Acceptance Criteria**:

- AC-002.1: Action Stations defined in
  `plugins/leyline/skills/risk-classification/modules/action-stations.md`
- AC-002.2: Each tier has clear "when" criteria
- AC-002.3: Each tier has specific required controls
- AC-002.4: risk-classification SKILL.md references the module
- AC-002.5: Integration with attune:war-room-checkpoint for tier 2+

### FR-003: Squadron Composition Rules

**Priority**: Medium
**Plugin**: conjure
**Component**: agent-teams

The system shall provide team composition rules for agent
squadrons.

**Role Definitions**:

| Role | Count | Responsibility |
|------|-------|----------------|
| Admiral | 1 (always) | Coordinates mission, delegates tasks, resolves blockers, produces synthesis |
| Captain | 2-7 | Own individual tasks and deliverables |
| Red-cell Navigator | 0-1 | Challenges assumptions, validates outputs, checks rollback readiness (for medium/high risk) |

**Team Sizing Rules**:

```yaml
team_sizing:
  simple_mission:
    mode: single-session
    team_size: 1
  moderate_mission:
    mode: subagents
    team_size: 2-4
    includes_red_cell: false
  complex_mission:
    mode: subagents
    team_size: 5-7
    includes_red_cell: true
  critical_mission:
    mode: agent-team
    team_size: 5-10
    includes_red_cell: true
```

**Maximum team size**: 10 agents (coordination overhead limit)

**Acceptance Criteria**:

- AC-003.1: Squadron Composition defined in
  `plugins/conjure/skills/agent-teams/references/squadron-composition.md`
- AC-003.2: Role definitions with responsibilities
- AC-003.3: Team sizing rules by mission complexity
- AC-003.4: agent-teams SKILL.md references the module

### FR-004: Quarterdeck Rhythm (Checkpoint Pattern)

**Priority**: Medium
**Plugin**: attune
**Component**: mission-orchestrator

The system shall provide a checkpoint rhythm pattern for
tracking mission progress.

**Checkpoint Fields**:

```yaml
quarterdeck_report:
  timestamp: datetime
  phase: string              # Current phase name
  progress:
    tasks_complete: int
    tasks_total: int
    tasks_blocked: int
  blockers: list             # Items blocking progress
  budget:
    tokens_used: int
    tokens_budget: int?
    time_elapsed: string
    time_budget: string?
  risks:
    new_risks: list
    resolved_risks: list
    current_action_station: int  # 0-3
  next_actions: list         # Immediate next steps
```

**Acceptance Criteria**:

- AC-004.1: Quarterdeck Report template exists at
  `plugins/attune/skills/mission-orchestrator/references/quarterdeck-report.md`
- AC-004.2: Template includes all fields above
- AC-004.3: mission-orchestrator SKILL.md references checkpoint rhythm

### FR-005: Captain's Log (Final Report)

**Priority**: Medium
**Plugin**: attune
**Component**: project-execution

The system shall provide a Captain's Log template for final
mission reports.

**Report Fields**:

```yaml
captains_log:
  mission: string            # Mission name/brief
  duration: string           # Total time spent
  outcome: enum              # success | partial | failed
  delivered_artifacts: list  # Files created/modified
  decisions: list            # Key decisions made with rationale
  validation_evidence:
    - description: string
      evidence_type: enum    # test | review | demo
      status: enum           # pass | fail | blocked
      reference: string?     # Link to evidence
  follow_ups: list           # Recommended next steps
  lessons_learned: list?     # Optional retrospectives
```

**Acceptance Criteria**:

- AC-005.1: Captain's Log template exists at
  `plugins/attune/skills/project-execution/references/captains-log.md`
- AC-005.2: Template includes all fields above with examples
- AC-005.3: project-execution SKILL.md references the template

### FR-006: Failure-mode Checklist

**Priority**: Medium
**Plugin**: leyline
**Component**: damage-control

The system shall provide a failure-mode checklist for Station 1+
tasks.

**Checklist Questions**:

1. What could fail in production?
2. How would we detect it quickly?
3. What is the fastest safe rollback?
4. What dependency could invalidate this plan?
5. What assumption is least certain?

**Acceptance Criteria**:

- AC-006.1: Failure-mode Checklist exists at
  `plugins/leyline/skills/damage-control/modules/failure-mode-checklist.md`
- AC-006.2: Checklist includes all 5 questions
- AC-006.3: damage-control SKILL.md references the checklist
- AC-006.4: Required for Station 1+ tasks before marking complete

### FR-007: Execution Mode Selection

**Priority**: Low
**Plugin**: conjure
**Component**: delegation-core

The system shall clarify execution mode selection criteria.

**Mode Definitions**:

| Mode | When to Use | How It Works |
|------|-------------|--------------|
| single-session | Sequential tasks, low complexity, heavy same-file editing | Claude works through tasks in order within one session |
| subagents | Parallel tasks where workers only report back to coordinator | Claude spawns subagents that work independently and return results |
| agent-team | Parallel tasks where workers need to coordinate with each other | Claude creates an agent team with direct teammate-to-teammate communication |

**Acceptance Criteria**:

- AC-007.1: Execution mode guidance added to
  `plugins/conjure/skills/delegation-core/references/execution-modes.md`
- AC-007.2: Selection criteria clearly defined
- AC-007.3: delegation-core SKILL.md references the module

## Non-Functional Requirements

### NFR-001: Progressive Loading

All new reference modules shall follow the progressive loading
pattern:
- Main SKILL.md contains overview and references
- Detailed content in `references/` or `modules/` directories
- Content loads on demand, not at skill invocation

### NFR-002: Backward Compatibility

No existing skill interfaces shall be broken:
- Existing commands continue to work unchanged
- New templates are additive, not replacements
- No required parameter changes

### NFR-003: Documentation Quality

All new modules shall follow markdown formatting rules:
- 80-character line wrapping for prose
- ATX headings only
- Blank lines before/after headings and lists

## Dependencies

- No external dependencies
- Internal dependencies on existing skill architecture

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Terminology confusion | Medium | Low | Clear mapping document from existing terms to Nelson terms |
| Template bloat | Low | Medium | Keep templates minimal, load on demand |
| Integration gaps | Medium | Medium | Comprehensive acceptance criteria per FR |

## Testing Strategy

1. **Unit tests**: Python analyzer tests for any new code
2. **Integration tests**: Verify SKILL.md references load correctly
3. **Manual tests**: Walk through each template with example data

## Timeline

| Phase | Tasks | Estimated Effort |
|-------|-------|------------------|
| Phase 1: Foundation | FR-001, FR-002 | 2 tasks |
| Phase 2: Composition | FR-003, FR-007 | 2 tasks |
| Phase 3: Reporting | FR-004, FR-005, FR-006 | 3 tasks |
