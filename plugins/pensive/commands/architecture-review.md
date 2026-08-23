---
name: architecture-review
description: Principal-level architecture assessment against ADRs and design patterns.
---

# Architecture Review Command

Principal-level architecture assessment against ADRs and design patterns.

## Usage

```bash
/architecture-review
```

## What It Does

Invoke `Skill(pensive:architecture-review)`, which carries the assessment
workflow, the ADR checks and the output format.

## War Room Checkpoint (Automatic)

**Purpose**: Assess whether architecture findings warrant expert deliberation before recommendation.

**Auto-triggers when** (moderate approach):
- ADR violations without clear remediation path, OR
- High coupling score (>0.7), OR
- Multiple module boundary violations (>2), OR
- Conflicting design principles detected

**Checkpoint invocation** (automatic, after Risk Assessment):

```markdown
Skill(attune:war-room-checkpoint) with context:
  source_command: "architecture-review"
  decision_needed: "Architecture recommendation for [component/PR]"
  blocking_items: [
    {type: "adr", description: "Violates ADR-003 without justification"},
    {type: "coupling", description: "High coupling between auth and payment"}
  ]
  files_affected: [modules under review]
  profile: [from user settings, default: "default"]
```

**War Room Questions** (when escalated):
- "Should we recommend blocking or propose remediation?"
- "Does this coupling warrant refactoring or is it acceptable?"
- "Should a new ADR be created to document this deviation?"

**Response handling**:

| RS Score | Mode | Action |
|----------|------|--------|
| RS <= 0.40 | Express | Quick recommendation, continue |
| RS 0.41-0.60 | Lightweight | Panel reviews trade-offs |
| RS > 0.60 | Full Council | Full deliberation on architecture decision |

**Skip conditions**:
- All ADRs compliant
- Coupling within acceptable thresholds
- No boundary violations
