---
name: war-room
description: Convene a multi-LLM War Room for strategic decision making through expert deliberation
---

# War Room Command

Orchestrate multi-expert deliberation for complex strategic decisions.

## Usage

```bash
# Basic invocation with problem statement
/attune:war-room "What architecture should we use for the payment system?"

# With context files
/attune:war-room "Best API versioning strategy" --files src/api/**/*.py

# Force full council (all experts)
/attune:war-room "Migration approach" --full-council

# High-stakes Delphi mode (iterative until consensus)
/attune:war-room "Platform decision" --delphi

# Resume interrupted session
/attune:war-room --resume war-room-20260120-153022

# Escalate from brainstorm
/attune:war-room --from-brainstorm
```

## What This Command Does

1. **Convenes expert panel** based on mode (lightweight or full council)
2. **Gathers intelligence** via Scout and Intelligence Officer
3. **Develops courses of action** from multiple perspectives
4. **Pressure tests** via Red Team adversarial review
5. **Synthesizes decision** via Supreme Commander
6. **Persists session** to Strategeion (Memory Palace)

## Arguments

| Argument | Description |
|----------|-------------|
| `<problem>` | The decision/problem to deliberate (required unless --resume) |
| `--files <globs>` | Context files to analyze |
| `--full-council` | Use all experts (skip lightweight mode) |
| `--delphi` | Iterate until expert consensus |
| `--resume <id>` | Resume interrupted session |
| `--from-brainstorm` | Import context from recent brainstorm |
| `--archive <name>` | Custom name for campaign archive |

## Expert Panel

### Lightweight Mode (Default)

| Expert | Model | Role |
|--------|-------|------|
| Supreme Commander | Claude Opus | Final synthesis |
| Chief Strategist | Claude Sonnet | Approach generation |
| Red Team | Gemini Flash | Adversarial challenge |

### Full Council (--full-council)

| Expert | Model | Role |
|--------|-------|------|
| Supreme Commander | Claude Opus | Final synthesis |
| Chief Strategist | Claude Sonnet | Approach generation |
| Intelligence Officer | Gemini 2.5 Pro | Deep context analysis |
| Field Tactician | GLM-4.7 | Implementation feasibility |
| Scout | Qwen Turbo | Rapid reconnaissance |
| Red Team Commander | Gemini Flash | Adversarial challenge |
| Logistics Officer | Qwen Max | Resource estimation |

## Workflow

```bash
# 1. Invoke war-room skill
Skill(attune:war-room)

# 2. Execute deliberation phases:
#    - Phase 1: Intelligence Gathering (parallel)
#    - Phase 2: Situation Assessment
#    - Phase 3: COA Development (parallel, anonymized)
#    - Escalation Check (Commander decides)
#    - Phase 4: Red Team Review
#    - Phase 5: Voting + Narrowing
#    - Phase 6: Premortem Analysis
#    - Phase 7: Supreme Commander Synthesis

# 3. Persist to Strategeion
#    ~/.claude/memory-palace/strategeion/war-table/{session-id}/

# 4. Output decision document
```

## Output

### Decision Document

```markdown
## SUPREME COMMANDER DECISION: war-room-20260120-153022

### Decision
**Selected Approach**: Microservices with Event Sourcing

### Rationale
[2-3 paragraphs explaining why]

### Implementation Orders
1. [ ] Set up event bus infrastructure
2. [ ] Define bounded contexts
3. [ ] Create service templates

### Watch Points
- Event bus latency exceeding 100ms
- Service discovery failures

### Dissenting Views
Field Tactician advocated for modular monolith due to team size.
```

### Session Artifacts

Saved to Strategeion:
```
~/.claude/memory-palace/strategeion/war-table/{session-id}/
  session.json           # Full session state
  intelligence/          # Scout and Intel Officer reports
  battle-plans/          # All COAs
  wargames/              # Red Team challenges + Premortem
  orders/                # Final decision
```

## Integration

### From Brainstorm

When brainstorm produces multiple strong approaches:

```bash
# Brainstorm first
/attune:brainstorm "New payment system"

# Then escalate to War Room
/attune:war-room --from-brainstorm
```

### With Memory Palace

```bash
# Review past War Room sessions
/memory-palace:strategeion list

# Archive completed campaign
/memory-palace:strategeion archive {session-id} --project payments

# Extract patterns to doctrine
/memory-palace:strategeion doctrine --extract {session-id}
```

## Escalation

The Supreme Commander may escalate from lightweight to full council when:
- Multiple architectural trade-offs detected
- Significant disagreement between initial experts
- Novel problem domain
- High stakes (irreversible decisions)

Escalation includes written justification.

## Examples

### Example 1: Architecture Decision

```bash
/attune:war-room "Should we use microservices or monolith for order management?"
```

**Outcome**: Full deliberation with 3 COAs, Red Team challenge, and final decision with implementation orders.

### Example 2: With Codebase Context

```bash
/attune:war-room "Best approach for database migration" --files src/models/**/*.py --full-council
```

**Outcome**: Intelligence Officer analyzes full codebase, Tactician assesses implementation complexity.

### Example 3: High-Stakes Platform Decision

```bash
/attune:war-room "Long-term cloud provider strategy" --delphi --full-council
```

**Outcome**: Iterative Delphi rounds until 85% expert consensus.

## Related Commands

- `/attune:brainstorm` - Pre-War Room ideation
- `/attune:specify` - Post-War Room specification
- `/memory-palace:strategeion` - War Room history
- `/imbue:feature-review` - Feature worthiness check

## Related Skills

- `Skill(attune:war-room)` - Core War Room skill
- `Skill(attune:project-brainstorming)` - Ideation
- `Skill(conjure:delegation-core)` - Expert dispatch
- `Skill(imbue:rigorous-reasoning)` - Reasoning methodology
