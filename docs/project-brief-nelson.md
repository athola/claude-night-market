# Nelson Integration -- Project Brief

**Date**: 2026-03-26
**Status**: Draft
**Source**: https://github.com/harrymunro/nelson

## Problem Statement

**Who**: Developers using night-market plugins for complex,
coordinated agent work
**What**: Current mission orchestration lacks structured
terminology, clear risk tier classification, and formalized
checkpoint rhythms for multi-agent coordination
**Where**: attune (mission orchestration), conjure (agent teams),
leyline (risk classification), egregore (quality gates)
**When**: Complex multi-phase projects requiring coordinated agent
work, risk-aware task execution, and structured reporting
**Why**: Without a unified operational framework:
- Mission definitions vary in structure and completeness
- Risk classification uses inconsistent terminology
- Checkpoint rhythms lack budget tracking and blocker identification
- Final reports miss decision documentation and validation evidence

**Current State**:
- `attune:mission-orchestrator` has phase routing but no formal
  "sailing orders" pattern
- `conjure:agent-teams` handles teams but lacks "squadron"
  composition rules and team sizing
- `leyline:risk-classification` has risk levels but not the clear
  4-tier action station system
- `egregore:quality-gate` lacks failure-mode checklists for
  elevated-risk tasks

## Goals

1. **Adopt Sailing Orders pattern** for mission definition with
   outcome, success metric, constraints, and stop criteria
2. **Add Squadron composition rules** for team sizing and role
   assignment (Admiral, Captains, Red-cell navigator)
3. **Implement Action Stations** as a 4-tier risk classification
   system (Patrol, Caution, Action, Trafalgar) with required
   controls per tier
4. **Add Quarterdeck Rhythm** checkpoints with progress, blockers,
   budget tracking, and risk updates
5. **Create Captain's Log** pattern for final reports with
   decisions, artifacts, validation evidence, and follow-ups
6. **Add Failure-mode Checklists** for Station 1+ tasks

## Integration Points

### attune Plugin

| Component | Nelson Concept | Enhancement |
|-----------|----------------|-------------|
| mission-orchestrator | Sailing Orders | Add structured mission definition template |
| mission-orchestrator | Quarterdeck Rhythm | Add checkpoint rhythm with budget tracking |
| project-execution | Captain's Log | Add final report structure with evidence |
| war-room | Action Stations | Integrate 4-tier risk system |

### conjure Plugin

| Component | Nelson Concept | Enhancement |
|-----------|----------------|-------------|
| agent-teams | Squadron Composition | Add team sizing rules and role definitions |
| delegation-core | Execution Modes | Clarify single-session/subagents/agent-team selection |

### leyline Plugin

| Component | Nelson Concept | Enhancement |
|-----------|----------------|-------------|
| risk-classification | Action Stations | Adopt 4-tier system with controls per tier |
| damage-control | Failure-mode Checklist | Add checklist for Station 1+ tasks |

### egregore Plugin

| Component | Nelson Concept | Enhancement |
|-----------|----------------|-------------|
| quality-gate | Action Stations | Require verification per tier before marking complete |

## Constraints

### Technical

- Must follow existing skill architecture (SKILL.md + modules)
- Progressive loading compatible (references pattern)
- No breaking changes to existing skill interfaces
- Python 3.9+ compatible where code is involved

### Scope

- Focus on structural patterns, not full reimplementation
- Add templates as reference modules (load on demand)
- Maintain backward compatibility with existing commands

### Out of Scope

- OpenAI agent interface (Nelson's openai.yaml)
- Visual/branding elements
- Installation documentation changes

## Success Metrics

1. Sailing Orders template available in attune references
2. Action Stations defined in leyline with 4 tiers and controls
3. Squadron Composition rules in conjure references
4. Captain's Log template in attune references
5. Failure-mode Checklist in leylandamage-control
6. All existing tests pass
7. New module tests cover added functionality

## References

- Nelson Repository: https://github.com/harrymunro/nelson
- Nelson SKILL.md: Six-step operational framework
- Nelson references/action-stations.md: Risk tier definitions
- Nelson references/admiralty-templates.md: Reusable templates
- Nelson references/squadron-composition.md: Team sizing rules
