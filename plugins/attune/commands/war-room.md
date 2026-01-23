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

# Reversibility assessment only (no deliberation)
/attune:war-room "Database migration to MongoDB" --assess-only

# Force express mode (Type 2 decisions)
/attune:war-room "Which logging library?" --express

# Use startup threshold profile (more aggressive)
/attune:war-room "New feature architecture" --thresholds startup

# Use regulated profile (more conservative)
/attune:war-room "Data retention policy" --thresholds regulated

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

1. **Assesses reversibility** (Phase 0) to determine appropriate deliberation intensity
2. **Routes to correct mode** based on Reversibility Score (RS):
   - RS ≤ 0.40: Express (1 expert, < 2 min)
   - RS 0.41-0.60: Lightweight (3 experts, 5-10 min)
   - RS 0.61-0.80: Full Council (7 experts, 15-30 min)
   - RS > 0.80: Full Council + Delphi (iterative, 30-60 min)
3. **Gathers intelligence** via Scout and Intelligence Officer
4. **Develops courses of action** from multiple perspectives
5. **Pressure tests** via Red Team adversarial review
6. **Synthesizes decision** via Supreme Commander
7. **Persists session** to Strategeion (Memory Palace)

## Reversibility Score (RS)

The War Room automatically assesses decision reversibility using five dimensions (1-5 each):

| Dimension | 1 (Reversible) | 5 (Irreversible) |
|-----------|----------------|------------------|
| **Reversal Cost** | Trivial (<1 day) | Prohibitive (months+) |
| **Time Lock-In** | Reverse anytime | Crystallizes immediately |
| **Blast Radius** | Single component | Organization-wide |
| **Information Loss** | All options preserved | Critical paths closed |
| **Reputation Impact** | Internal only | Public trust at stake |

**RS = Sum / 25** → Routes to appropriate deliberation mode.

## Arguments

| Argument | Description |
|----------|-------------|
| `<problem>` | The decision/problem to deliberate (required unless --resume) |
| `--files <globs>` | Context files to analyze |
| `--assess-only` | Show RS assessment without full deliberation |
| `--express` | Force Type 2 mode (single expert, fast) |
| `--full-council` | Use all experts (override RS recommendation) |
| `--delphi` | Iterate until expert consensus (Type 1A+ mode) |
| `--thresholds <profile>` | Use preset threshold profile: `default`, `fast`, `cautious`, `startup`, `regulated` |
| `--resume <id>` | Resume interrupted session |
| `--from-brainstorm` | Import context from recent brainstorm |
| `--archive <name>` | Custom name for campaign archive |

### Threshold Profiles

| Profile | Express | Lightweight | Full Council | Use When |
|---------|---------|-------------|--------------|----------|
| `default` | 0.40 | 0.60 | 0.80 | General use |
| `fast` | 0.50 | 0.70 | 0.90 | Speed over process |
| `cautious` | 0.30 | 0.50 | 0.70 | Higher stakes environment |
| `startup` | 0.55 | 0.75 | 0.90 | Move fast, break things |
| `regulated` | 0.25 | 0.45 | 0.65 | Compliance-heavy industries |

Or customize at session start when prompted.

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
#    - Phase 0: Reversibility Assessment (immediate)
#      ↳ RS ≤ 0.40? → EXPRESS MODE (skip to Phase 7)
#    - Phase 1: Intelligence Gathering (parallel)
#    - Phase 2: Situation Assessment
#    - Phase 3: COA Development (parallel, anonymized)
#    - Escalation Check (Commander validates RS or overrides)
#    - Phase 4: Red Team Review
#    - Phase 5: Voting + Narrowing
#    - Phase 6: Premortem Analysis
#    - Phase 7: Supreme Commander Synthesis

# 3. Persist to Strategeion
#    ~/.claude/memory-palace/strategeion/war-table/{session-id}/

# 4. Output decision document with RS assessment
```

## Output

### Decision Document

```markdown
## SUPREME COMMANDER DECISION: war-room-20260120-153022

### Reversibility Assessment
| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Reversal Cost | 4/5 | Service decomposition hard to reverse |
| Time Lock-In | 3/5 | Architecture hardens over months |
| Blast Radius | 4/5 | Affects all teams |
| Information Loss | 3/5 | Some patterns locked |
| Reputation Impact | 2/5 | Internal decision |

**RS: 0.64 | Type: 1A | Mode: full_council**

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

### Reversal Plan
If microservices prove too complex for team size, consolidate to
modular monolith by: (1) merging services behind API gateway,
(2) replacing event bus with in-process pub/sub.

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

### Automatic (RS-Based)
Mode is automatically selected based on Reversibility Score:
- RS ≤ 0.40 → Express mode (or skip War Room entirely)
- RS 0.41-0.60 → Lightweight panel
- RS 0.61-0.80 → Full Council
- RS > 0.80 → Full Council + Delphi

### Manual Override
The Supreme Commander may override when:
- Multiple architectural trade-offs detected
- Significant expert disagreement
- Novel problem domain (uncertain reversibility)
- Precedent-setting decision

### De-escalation
Equally important—identify over-deliberation:
- Challenge "false irreversibility" claims
- Recommend express mode for clear Type 2 decisions
- Track de-escalation rate as health metric

Escalation/de-escalation requires written justification with RS assessment.

## Examples

### Example 1: Reversibility Assessment Only

```bash
/attune:war-room "Add retry logic to API client" --assess-only
```

**Output**:
```
Reversibility Assessment: Add retry logic to API client
─────────────────────────────────────────────────────────
Reversal Cost:      1/5 (can revert PR)
Time Lock-In:       1/5 (no deadline)
Blast Radius:       2/5 (single service)
Information Loss:   1/5 (all options preserved)
Reputation Impact:  1/5 (internal only)

RS: 0.24 | Type: 2 (Two-Way Door) | Mode: express

Recommendation: Skip War Room. Chief Strategist can decide immediately.
```

### Example 2: Type 2 Express Mode

```bash
/attune:war-room "Which logging library should we use?" --express
```

**Outcome**: Chief Strategist provides immediate recommendation (< 2 min). No full deliberation needed.

### Example 3: Architecture Decision (Type 1A)

```bash
/attune:war-room "Should we use microservices or monolith for order management?"
```

**Phase 0 Output**: RS = 0.64 → Type 1A → Full Council activated

**Outcome**: Full deliberation with 3 COAs, Red Team challenge, and final decision with reversal plan.

### Example 4: With Codebase Context

```bash
/attune:war-room "Best approach for database migration" --files src/models/**/*.py
```

**Outcome**: RS assessment triggers full council. Intelligence Officer analyzes full codebase, Tactician assesses implementation complexity.

### Example 5: High-Stakes Platform Decision (Type 1A+)

```bash
/attune:war-room "Long-term cloud provider strategy"
```

**Phase 0 Output**: RS = 0.88 → Type 1A+ → Full Council + Delphi

**Outcome**: Iterative Delphi rounds until 85% expert consensus. Maximum deliberation resources applied.

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
