# War Room Specification: Deliberation Protocol

**Part of**: [War Room Specification](war-room-spec-overview.md)

---

## Two-Round Default Flow

```
Round 1: Generation
├── Intel gathering (Scout, Intel Officer)
├── Situation assessment (Chief Strategist)
├── COA development (Strategist + available experts)
└── Commander escalation check

Round 2: Pressure Testing
├── Red Team review of all COAs
├── Voting/narrowing to top 2-3
├── Premortem on selected COA
└── Supreme Commander synthesis
```

## Delphi Extension (High-Stakes)

When high-stakes decision is detected or user requests:

```
Round 1: Generation (as above)
Round 2: First Pressure Test
Round 3: Expert Response to Red Team
Round 4: Convergence Check
├── If convergence < threshold: → Round 5
├── If convergence >= threshold: → Synthesis
Round 5+: Iterative refinement until convergence
Final: Supreme Commander synthesis
```

---

## Phase Specifications

### Phase 1: Intelligence Gathering

**Experts**: Scout (Qwen), Intelligence Officer (Gemini)
**Parallel**: Yes
**Output**: Intelligence reports with context analysis

### Phase 2: Situation Assessment

**Expert**: Chief Strategist (Sonnet)
**Input**: All intelligence reports
**Output**: Synthesized situation assessment

### Phase 3: COA Development

**Experts**: Multiple (configurable)
**Parallel**: Yes
**Anonymization**: Active
**Output**: 3-5 distinct approaches

### Phase 4: Red Team + Wargaming

**Expert**: Red Team Commander (Gemini Flash)
**Input**: All COAs (anonymized as A, B, C...)
**Output**: Challenge report for each COA

### Phase 5: Voting + Narrowing

**Method**: Hybrid aggregation
**Participants**: All active experts
**Output**: Top 2-3 COAs with aggregate scores

### Phase 6: Premortem

**Expert**: All available (parallel)
**Input**: Selected top COA(s)
**Output**: Failure mode catalog

### Phase 7: Supreme Commander Synthesis

**Expert**: Claude Opus
**Input**: All deliberation artifacts
**Output**: Final decision with rationale

---

## Prompt Templates

### System Context (Prepended to All Expert Prompts)

```
WAR ROOM DELIBERATION SESSION
=============================
Session ID: {session_id}
Phase: {current_phase}
Round: {round_number}

You are participating in a structured multi-expert deliberation.
Your responses will be anonymized and evaluated alongside other experts.
Focus on your assigned role and provide substantive analysis.

RULES:
1. Be specific and actionable - avoid vague recommendations
2. Support claims with evidence from provided context
3. Acknowledge uncertainties explicitly
4. Stay within your role's domain expertise
5. Format output as specified for parsing
```

### Scout Intelligence Report

```
MISSION BRIEFING: SCOUT INTELLIGENCE GATHERING
==============================================

You are the SCOUT - a rapid reconnaissance specialist.
Your mission: Quick initial survey of the problem space.

PROBLEM STATEMENT:
{problem_statement}

CONTEXT FILES PROVIDED:
{file_list}

YOUR TASK:
Perform rapid reconnaissance. Identify the key terrain of this problem.

REPORT FORMAT:
## SCOUT REPORT: {session_id}
### Terrain Overview
### Key Landmarks
### Obstacles Identified
### Points of Interest
### Fog of War
### Recommended Focus Areas
```

### Red Team Challenge Report

```
MISSION BRIEFING: RED TEAM CHALLENGE
====================================

You are the RED TEAM COMMANDER - the Devil's Advocate.
Your mission: Rigorously challenge each proposed approach.

FOR EACH APPROACH, IDENTIFY:
1. Hidden assumptions that may be wrong
2. Failure modes not addressed
3. Scenarios where this approach fails
4. What the proponent might be missing
5. Counter-arguments to stated benefits

BE RIGOROUS BUT CONSTRUCTIVE.
```

### Supreme Commander Synthesis

```
SUPREME COMMANDER SYNTHESIS
===========================

You are the SUPREME COMMANDER of this War Room session.

SYNTHESIZE FINAL DECISION:

## Selected Approach
## Rationale
## Implementation Guidance
## Watch Points
## Dissenting Views
```

---

**Next**: See [Data Structures](war-room-spec-data.md) for Merkle-DAG and persistence.
