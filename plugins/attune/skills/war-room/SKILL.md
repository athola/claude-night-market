---
name: war-room
description: Multi-LLM deliberation framework for strategic decisions through pressure-based expert consultation
triggers: war room, strategic decision, multi-expert, deliberation, council, convene experts, expert panel
use_when: complex decisions requiring multiple perspectives, architectural trade-offs, high-stakes choices
do_not_use_when: simple questions, routine tasks, single-path implementations
model_preference: claude-opus-4
category: strategic-planning
tags: [deliberation, multi-llm, strategy, decision-making, council]
dependencies:
  - conjure:delegation-core
  - memory-palace:strategeion
tools: [Bash, Read, Write]
complexity: advanced
estimated_tokens: 2500
progressive_loading: true
modules:
  - modules/expert-roles.md
  - modules/deliberation-protocol.md
  - modules/merkle-dag.md
---

# War Room Skill

Orchestrate multi-LLM deliberation for complex strategic decisions.

## Overview

The War Room convenes multiple AI experts to analyze problems from diverse perspectives, challenge assumptions through adversarial review, and synthesize optimal approaches under the guidance of a Supreme Commander.

### Philosophy

> "The trick is that there is no trick. The power of intelligence stems from our vast diversity, not from any single, perfect principle."
> - Marvin Minsky, Society of Mind

## When to Use

- Architectural decisions with major trade-offs
- Multi-stakeholder problems requiring diverse perspectives
- High-stakes choices with significant consequences
- Novel problems without clear precedent
- When brainstorming produces multiple strong competing approaches

## When NOT to Use

- Simple questions with obvious answers
- Routine implementation tasks
- Well-documented patterns with clear solutions
- Time-critical decisions requiring immediate action

## Expert Panel

### Default (Lightweight Mode)

| Role | Model | Purpose |
|------|-------|---------|
| Supreme Commander | Claude Opus | Final synthesis, escalation decisions |
| Chief Strategist | Claude Sonnet | Approach generation, trade-off analysis |
| Red Team | Gemini Flash | Adversarial challenge, failure modes |

### Full Council (Escalated)

| Role | Model | Purpose |
|------|-------|---------|
| Supreme Commander | Claude Opus | Final synthesis |
| Chief Strategist | Claude Sonnet | Approach generation |
| Intelligence Officer | Gemini 2.5 Pro | Large context analysis (1M+) |
| Field Tactician | GLM-4.7 | Implementation feasibility |
| Scout | Qwen Turbo | Quick data gathering |
| Red Team Commander | Gemini Flash | Adversarial challenge |
| Logistics Officer | Qwen Max | Resource estimation |

## Deliberation Protocol

### Two-Round Default

```
Round 1: Generation
  - Phase 1: Intelligence Gathering (Scout, Intel Officer)
  - Phase 2: Situation Assessment (Chief Strategist)
  - Phase 3: COA Development (Multiple experts, parallel)
  - Commander Escalation Check

Round 2: Pressure Testing
  - Phase 4: Red Team Review (all COAs)
  - Phase 5: Voting + Narrowing (top 2-3)
  - Phase 6: Premortem Analysis (selected COA)
  - Phase 7: Supreme Commander Synthesis
```

### Delphi Extension (High-Stakes)

For high-stakes decisions, extend to iterative Delphi convergence:
- Multiple rounds until expert consensus
- Convergence threshold: 0.85

## Integration

### With Brainstorm

War Room can be invoked from `/attune:brainstorm` when:
- Multiple strong approaches emerge with no clear winner
- User explicitly requests expert council
- Problem complexity exceeds threshold

```bash
# From brainstorm, escalate to War Room
/attune:war-room --from-brainstorm

# Direct invocation
/attune:war-room "Should we use microservices or monolith for this system?"
```

### With Memory Palace

Sessions persist to the **Strategeion** (War Palace):

```
~/.claude/memory-palace/strategeion/
  - war-table/      # Active sessions
  - campaign-archive/  # Historical decisions
  - doctrine/       # Learned patterns
  - armory/         # Expert configurations
```

### With Conjure

Experts are invoked via conjure delegation:
- `conjure:gemini-delegation` for Gemini models
- `conjure:qwen-delegation` for Qwen models
- Direct CLI for GLM-4.7 (`ccgd` or `claude-glm --dangerously-skip-permissions`)

## Usage

### Basic Invocation

```bash
/attune:war-room "What architecture should we use for the new payment system?"
```

### With Context

```bash
/attune:war-room "Best approach for API versioning" --files src/api/**/*.py
```

### Force Full Council

```bash
/attune:war-room "Migration strategy" --full-council
```

### Delphi Mode

```bash
/attune:war-room "Long-term platform decision" --delphi
```

### Resume Session

```bash
/attune:war-room --resume war-room-20260120-153022
```

## Output

### Decision Document

The War Room produces a Supreme Commander Decision document:

```markdown
## SUPREME COMMANDER DECISION: {session_id}

### Decision
**Selected Approach**: [Name]

### Rationale
[Why this approach was selected]

### Implementation Orders
1. [ ] Immediate actions
2. [ ] Short-term actions

### Watch Points
[From Premortem - what to monitor]

### Dissenting Views
[For the record]
```

### Session Artifacts

Saved to Strategeion:
- Intelligence reports
- Situation assessment
- All COAs (with full attribution after unsealing)
- Red Team challenges
- Premortem analysis
- Final decision

## Anonymization

Expert contributions are anonymized during deliberation using Merkle-DAG:
- Responses labeled as "Response A, B, C..." during review
- Attribution revealed only after decision is made
- Hash verification ensures integrity

See `modules/merkle-dag.md` for details.

## Escalation

The Supreme Commander may escalate from lightweight to full council when:
- High complexity detected (multiple architectural trade-offs)
- Significant disagreement between initial experts
- Novel problem domain requiring specialized analysis
- Stakes are high (irreversible decisions)

Escalation requires written justification.

## Configuration

### User Settings

```json
{
  "war_room": {
    "default_mode": "lightweight",
    "auto_escalate": true,
    "delphi_threshold": 0.85,
    "max_delphi_rounds": 5
  }
}
```

### Hook Auto-Trigger

War Room can be auto-suggested via hook when:
- Keywords detected ("strategic decision", "trade-off", etc.)
- Complexity score exceeds threshold (0.7)
- User has opted in via settings

## Related Skills

- `Skill(attune:project-brainstorming)` - Pre-War Room ideation
- `Skill(imbue:scope-guard)` - Scope management
- `Skill(imbue:rigorous-reasoning)` - Reasoning methodology
- `Skill(conjure:delegation-core)` - Expert dispatch

## Related Commands

- `/attune:war-room` - Invoke this skill
- `/attune:brainstorm` - Pre-War Room ideation
- `/memory-palace:strategeion` - Access War Room history

## References

- Sun Tzu - Art of War (intelligence gathering)
- Clausewitz - On War (friction and fog)
- Robert Greene - 33 Strategies of War (unity of command)
- MDMP - U.S. Army (structured decision process)
- Gary Klein - Premortem (failure mode analysis)
- Karpathy - LLM Council (anonymized peer review)
