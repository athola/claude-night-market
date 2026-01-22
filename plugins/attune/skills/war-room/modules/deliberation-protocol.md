---
name: deliberation-protocol
description: Phase definitions and flow control for War Room deliberation sessions
category: war-room-module
tags: [protocol, phases, workflow]
dependencies: []
estimated_tokens: 800
---

# Deliberation Protocol

## Session Lifecycle

```
Initialize
    |
    v
+-------------------+
| Phase 1: Intel    |  <-- Scout + Intel Officer (parallel)
+-------------------+
    |
    v
+-------------------+
| Phase 2: Assess   |  <-- Chief Strategist
+-------------------+
    |
    v
+-------------------+
| Phase 3: COA Dev  |  <-- Multiple experts (parallel, anonymized)
+-------------------+
    |
    v
+-------------------+
| Escalation Check  |  <-- Supreme Commander decides
+-------------------+
    |
    +---> [Escalate to Full Council if needed]
    |
    v
+-------------------+
| Phase 4: Red Team |  <-- Red Team Commander
+-------------------+
    |
    v
+-------------------+
| Phase 5: Voting   |  <-- All active experts
+-------------------+
    |
    v
+-------------------+
| Phase 6: Premortem|  <-- All active experts (parallel)
+-------------------+
    |
    v
+-------------------+
| Phase 7: Synthesis|  <-- Supreme Commander
+-------------------+
    |
    v
Persist to Strategeion
```

## Phase Definitions

### Phase 1: Intelligence Gathering

**Purpose**: Gather context and identify terrain before strategy.

**Experts**: Scout (Qwen Turbo), Intelligence Officer (Gemini Pro)

**Execution**: Parallel

**Inputs**:
- Problem statement
- Context files (if provided)

**Outputs**:
- Scout Report (quick terrain overview)
- Intelligence Report (deep analysis)

**Duration Target**: 30-60 seconds

### Phase 2: Situation Assessment

**Purpose**: Synthesize intelligence into actionable assessment.

**Expert**: Chief Strategist (Sonnet)

**Execution**: Sequential (after Phase 1)

**Inputs**:
- All intelligence reports from Phase 1

**Outputs**:
- Refined problem statement
- Prioritized constraints
- Strategic opportunities
- COA development guidance

**Duration Target**: 15-30 seconds

### Phase 3: COA Development

**Purpose**: Generate diverse courses of action.

**Experts**: Variable (based on mode)
- Lightweight: Chief Strategist only
- Full Council: Strategist + Tactician + Logistics Officer

**Execution**: Parallel, anonymized

**Inputs**:
- Situation assessment from Phase 2

**Outputs**:
- 3-5 distinct COAs
- Each with pros, cons, risks, effort estimate

**Duration Target**: 60-120 seconds

**Anonymization**: Responses labeled as "Response A, B, C..."

### Escalation Check

**Purpose**: Supreme Commander decides if more expertise needed.

**Triggers for Escalation**:
1. High complexity (multiple architectural trade-offs)
2. Significant expert disagreement
3. Novel problem domain
4. High stakes (irreversible decisions)
5. User explicitly requested full council

**If Escalated**:
- Invoke additional experts (Intel Officer, Tactician, Logistics)
- Gather additional COAs
- Merge with existing COAs

### Phase 4: Red Team + Wargaming

**Purpose**: Challenge assumptions and identify weaknesses.

**Expert**: Red Team Commander (Gemini Flash)

**Execution**: Sequential (after all COAs)

**Inputs**:
- All COAs (anonymized)
- Situation assessment

**Outputs**:
- Challenge report per COA
- Hidden assumptions identified
- Failure scenarios
- Cross-cutting concerns

**Duration Target**: 30-60 seconds

### Phase 5: Voting + Narrowing

**Purpose**: Aggregate expert rankings to identify top approaches.

**Experts**: All active experts

**Execution**: Parallel

**Inputs**:
- All COAs with Red Team challenges

**Outputs**:
- Expert rankings
- Aggregate scores (Borda count)
- Top 2-3 finalists

**Voting Method**: Borda count (rank-based scoring)

**Duration Target**: 30-45 seconds

### Phase 6: Premortem Analysis

**Purpose**: Imagine failure to identify risks.

**Experts**: All active experts

**Execution**: Parallel

**Inputs**:
- Selected COA(s) from voting

**Outputs**:
- Failure mode catalog
- Early warning signs
- Prevention strategies
- Contingency plans

**Duration Target**: 45-90 seconds

### Phase 7: Supreme Commander Synthesis

**Purpose**: Make final decision with full rationale.

**Expert**: Supreme Commander (Opus)

**Execution**: Sequential (final phase)

**Inputs**:
- All deliberation artifacts
- Full attribution (unsealed)

**Outputs**:
- Selected approach
- Detailed rationale
- Implementation orders
- Watch points
- Dissenting views acknowledged

**Duration Target**: 30-60 seconds

## Delphi Extension

For high-stakes decisions, iterate until convergence:

```
Round N:
  - Experts revise positions based on Red Team feedback
  - Re-vote
  - Check convergence score

Convergence Formula:
  score = 1 - (std_dev(rankings) / max_possible_std_dev)

Threshold: 0.85 (configurable)
Max Rounds: 5 (configurable)
```

## Error Handling

### Expert Failure

If an expert fails to respond:
1. Log the failure with reason
2. Continue with remaining experts
3. Note gap in synthesis
4. Do not block deliberation

### Timeout Handling

Default timeouts:
- External experts: 120 seconds
- Synthesis phases: 180 seconds

On timeout:
1. Use partial response if available
2. Log timeout event
3. Continue deliberation

### Session Recovery

Sessions are persisted after each phase:
- Can resume from last completed phase
- Use `--resume <session-id>` to continue

## Metrics

Track per session:
- Total duration
- Per-phase duration
- Token usage per expert
- Expert failure count
- Escalation occurred (y/n)
- Convergence rounds (if Delphi)
