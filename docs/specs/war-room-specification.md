# War Room Specification

**Version**: 1.0.0-draft
**Date**: 2026-01-20
**Status**: Draft - Pending Review
**Branch**: war-room-brainstorm-1.3.1

---

## Executive Summary

The War Room is a multi-LLM deliberation system for pressure-based decision making. It orchestrates multiple AI experts (via conjure delegation) to analyze problems from diverse perspectives, challenge assumptions through adversarial review, and synthesize optimal approaches under the guidance of a Supreme Commander.

### Core Philosophy

> "The trick is that there is no trick. The power of intelligence stems from our vast diversity, not from any single, perfect principle."
> — Marvin Minsky, *Society of Mind*

The War Room draws from:
- **Sun Tzu**: Intelligence gathering through specialized agents
- **Clausewitz**: Acknowledging friction and fog in decision-making
- **Robert Greene**: Unity of command with participatory input
- **MDMP**: Structured course-of-action development and wargaming
- **Karpathy's LLM Council**: Anonymized peer review and chairman synthesis
- **Gary Klein**: Premortem analysis for failure mode identification

---

## Table of Contents

1. [Design Decisions Summary](#design-decisions-summary)
2. [The Strategeion: Memory Palace Integration](#the-strategeion-memory-palace-integration)
3. [Architecture Overview](#architecture-overview)
4. [Expert Panel Composition](#expert-panel-composition)
5. [Deliberation Protocol](#deliberation-protocol)
6. [Anonymization with Merkle-DAG](#anonymization-with-merkle-dag)
7. [Aggregation and Synthesis](#aggregation-and-synthesis)
8. [Session Persistence](#session-persistence)
9. [Conjure Integration](#conjure-integration)
10. [Command and Skill Specifications](#command-and-skill-specifications)
11. [Implementation Phases](#implementation-phases)
12. [Success Criteria](#success-criteria)

---

## Design Decisions Summary

| Decision | Selected Option |
|----------|-----------------|
| **Integration Point** | B+C: Separate `/attune:war-room` command + `Skill(attune:war-room)`, with hook option (D) for future gated auto-trigger |
| **Expert Panel** | Lightweight by default; Supreme Commander escalates to full council when justified |
| **Deliberation Rounds** | Two-round default; Delphi-style for high-stakes |
| **Anonymization** | Merkle-tree DAG with hash-masked attribution until decision finalized |
| **Aggregation** | Hybrid: voting to narrow to top 2-3, then Chairman synthesis; meritocracy override available |
| **Red Team Timing** | After all COAs generated + Premortem on selected approach |
| **Token Budget** | No cap; quality over cost; delegate lower-level thinking to cheaper models |
| **Session Persistence** | File-based JSON + Strategeion (war palace) in memory-palace |
| **Conjure Integration** | New `war_room_orchestrator.py` composing `delegation_executor` calls |
| **Failure Handling** | Graceful degradation with logged gaps |
| **Execution Permissions** | All conjured agents run with dangerous permissions (bypass permission prompts) |
| **Hook Auto-Trigger** | Hybrid: complexity score + user settings + keyword detection |

---

## Execution Permissions

### Dangerous Mode for All Experts

All conjured/delegated agents run with **dangerous permissions** to avoid interactive permission prompts that would block automated deliberation. This is safe because:

1. Experts are invoked with specific, audited prompts
2. Output is captured and reviewed by Supreme Commander before action
3. No file modifications occur during deliberation (read-only analysis)
4. Session is fully logged for audit

### Invocation Commands

| Service | Standard | Dangerous Mode (Required) |
|---------|----------|---------------------------|
| **Gemini** | `gemini -p "..."` | `gemini -p "..."` (no auth prompts) |
| **Qwen** | `qwen -p "..."` | `qwen -p "..."` (no auth prompts) |
| **GLM-4.7** | `claude-glm -p "..."` | `claude-glm --dangerously-skip-permissions -p "..."` |
| **Alias** | `ccg` | `ccgd` |

### GLM-4.7 Configuration

GLM-4.7 uses a dedicated configuration at `~/.claude-glm/`:

```bash
# ~/.local/bin/claude-glm script sets:
export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"
export ANTHROPIC_AUTH_TOKEN="<zai-api-key>"
export ANTHROPIC_MODEL="glm-4.7"
export ANTHROPIC_SMALL_FAST_MODEL="glm-4.5-air"
export CLAUDE_HOME="$HOME/.claude-glm"
```

**Invocation for War Room**:
```bash
# Preferred: alias with dangerous permissions
ccgd -p "Expert prompt here"

# Fallback: explicit command (if alias not configured)
claude-glm --dangerously-skip-permissions -p "Expert prompt here"
```

**Fallback Detection Logic**:
```python
def get_glm_command() -> list[str]:
    """
    Get GLM-4.7 invocation command with fallback.

    Priority:
    1. ccgd (alias) - fastest, if available
    2. claude-glm --dangerously-skip-permissions - explicit fallback
    """
    import shutil

    # Check if ccgd alias is available
    if shutil.which("ccgd"):
        return ["ccgd", "-p"]

    # Fallback to explicit command
    if shutil.which("claude-glm"):
        return ["claude-glm", "--dangerously-skip-permissions", "-p"]

    # Last resort: check common locations
    from pathlib import Path
    local_bin = Path.home() / ".local" / "bin" / "claude-glm"
    if local_bin.exists():
        return [str(local_bin), "--dangerously-skip-permissions", "-p"]

    raise RuntimeError(
        "GLM-4.7 not available. Install claude-glm or configure ccgd alias.\n"
        "See: ~/.local/bin/claude-glm or add to ~/.bashrc:\n"
        "  alias ccgd='claude-glm --dangerously-skip-permissions'"
    )
```

---

## The Strategeion: Memory Palace Integration

### Concept: The War Palace

The **Strategeion** (Greek: στρατηγεῖον, "general's headquarters") is a dedicated chamber within the Memory Palace for strategic deliberation. It extends the existing palace metaphor with spaces for war council sessions.

### Architectural Metaphor

```
memory-palace/
├── entrance/           # README, getting started
├── library/            # Documentation, ADRs
├── workshop/           # Development patterns
├── review-chamber/     # PR Reviews (existing)
├── garden/             # Evolving knowledge
│
└── strategeion/        # NEW: War Palace
    ├── war-table/      # Active deliberation sessions
    │   └── {session-id}/
    │       ├── intelligence/   # Expert reports
    │       ├── battle-plans/   # Courses of action
    │       ├── wargames/       # Red team challenges
    │       └── orders/         # Final decisions
    │
    ├── campaign-archive/  # Historical sessions
    │   └── {project}/
    │       └── {decision-date}/
    │
    ├── doctrine/          # Strategic principles learned
    │   ├── patterns/      # Recurring decision patterns
    │   └── lessons/       # Post-campaign analysis
    │
    └── armory/            # Expert configurations
        ├── panels/        # Saved expert compositions
        └── protocols/     # Custom deliberation flows
```

### The Crucible

Within the Strategeion, **The Crucible** is where raw ideas are pressure-tested:

```
                    ┌─────────────────────┐
                    │  PROBLEM STATEMENT  │
                    │    (Central Hub)    │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  INTELLIGENCE │    │   STRATEGY    │    │  FEASIBILITY  │
│    REPORTS    │    │   PROPOSALS   │    │  ASSESSMENTS  │
│   (Gemini)    │    │   (Sonnet)    │    │   (GLM-4.7)   │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   RED TEAM      │
                    │   CHALLENGE     │
                    │   (Gemini Flash)│
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   PREMORTEM     │
                    │   ANALYSIS      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    SUPREME      │
                    │   COMMANDER     │
                    │   SYNTHESIS     │
                    │    (Opus)       │
                    └─────────────────┘
```

### Integration Commands

```bash
# Access the Strategeion
/memory-palace:strategeion

# Review past campaigns
/memory-palace:strategeion archive --project claude-night-market

# Extract doctrine from campaign
/memory-palace:strategeion doctrine --extract {session-id}
```

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        WAR ROOM SYSTEM                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │  /attune:war-   │───▶│ Skill(attune:   │                    │
│  │     room        │    │   war-room)     │                    │
│  └─────────────────┘    └────────┬────────┘                    │
│                                  │                              │
│                                  ▼                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              WAR ROOM ORCHESTRATOR                         │ │
│  │  (plugins/conjure/scripts/war_room_orchestrator.py)       │ │
│  │                                                            │ │
│  │  - Session management                                      │ │
│  │  - Expert dispatch                                         │ │
│  │  - Response aggregation                                    │ │
│  │  - Merkle-DAG tracking                                     │ │
│  │  - Strategeion integration                                 │ │
│  └────────────────────────────┬──────────────────────────────┘ │
│                               │                                 │
│              ┌────────────────┼────────────────┐                │
│              │                │                │                │
│              ▼                ▼                ▼                │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │
│  │   DELEGATION  │  │   DELEGATION  │  │   CLAUDE CLI  │       │
│  │   EXECUTOR    │  │   EXECUTOR    │  │   --model     │       │
│  │   (Gemini)    │  │   (Qwen)      │  │   (GLM-4.7)   │       │
│  └───────────────┘  └───────────────┘  └───────────────┘       │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              MEMORY PALACE: STRATEGEION                    │ │
│  │  - Session persistence                                     │ │
│  │  - Campaign archive                                        │ │
│  │  - Doctrine extraction                                     │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Request
     │
     ▼
┌────────────────────┐
│ Session Initialize │ ──▶ Generate session_id
└─────────┬──────────┘     Create Merkle root
          │
          ▼
┌────────────────────┐
│ Phase 1: Intel     │ ──▶ Scout + Intel Officer
│ (Parallel)         │     gather context
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Phase 2: Situation │ ──▶ Chief Strategist
│ Assessment         │     synthesizes intel
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Phase 3: COA       │ ──▶ Multiple experts
│ Development        │     generate approaches
│ (Parallel)         │     (anonymized)
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐     ┌──────────────────┐
│ Commander Review   │────▶│ Escalate to Full │
│ (Lightweight?)     │ No  │ Council?         │
└─────────┬──────────┘     └────────┬─────────┘
          │ Yes                     │
          │◀────────────────────────┘
          ▼
┌────────────────────┐
│ Phase 4: Red Team  │ ──▶ Adversarial review
│ + Wargaming        │     of all COAs
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Phase 5: Voting    │ ──▶ Hybrid aggregation
│ + Narrowing        │     to top 2-3
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Phase 6: Premortem │ ──▶ "Imagine failure"
│ Analysis           │     on selected COA
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Phase 7: Supreme   │ ──▶ Final synthesis
│ Commander Decision │     + rationale
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Persist to         │ ──▶ JSON + Strategeion
│ Strategeion        │     archive
└────────────────────┘
```

---

## Expert Panel Composition

### Default Panel (Lightweight Mode)

| Role | LLM | Invocation | Purpose |
|------|-----|------------|---------|
| **Supreme Commander** | Claude Opus | Native session | Final synthesis, escalation decisions |
| **Chief Strategist** | Claude Sonnet | Native session | Approach generation, trade-off analysis |
| **Red Team** | Gemini Flash | `gemini --model gemini-2.0-flash-exp -p "..."` | Adversarial challenge, failure modes |

### Full Council (Escalated Mode)

| Role | LLM | Invocation | Purpose |
|------|-----|------------|---------|
| **Supreme Commander** | Claude Opus | Native session | Final synthesis |
| **Chief Strategist** | Claude Sonnet | Native session | Approach generation |
| **Intelligence Officer** | Gemini 2.5 Pro | `gemini --model gemini-2.5-pro-exp -p "..."` | Large context analysis (1M+ tokens) |
| **Field Tactician** | GLM-4.7 | `ccgd -p "..."` | Implementation feasibility |
| **Scout** | Qwen Turbo | `qwen --model qwen-turbo -p "..."` | Quick data gathering |
| **Red Team Commander** | Gemini Flash | `gemini --model gemini-2.0-flash-exp -p "..."` | Adversarial challenge |
| **Logistics Officer** | Qwen Max | `qwen --model qwen-max -p "..."` | Resource estimation |

### Expert Invocation Code

```python
EXPERT_CONFIGS = {
    "supreme_commander": {
        "role": "Supreme Commander",
        "service": "native",  # Uses current Claude session
        "model": "claude-opus-4",
        "dangerous": False,   # Native session, no subprocess
    },
    "chief_strategist": {
        "role": "Chief Strategist",
        "service": "native",
        "model": "claude-sonnet-4",
        "dangerous": False,
    },
    "intelligence_officer": {
        "role": "Intelligence Officer",
        "service": "gemini",
        "model": "gemini-2.5-pro-exp",
        "command": ["gemini", "--model", "gemini-2.5-pro-exp", "-p"],
        "dangerous": True,    # No interactive prompts
    },
    "field_tactician": {
        "role": "Field Tactician",
        "service": "glm",
        "model": "glm-4.7",
        "command_resolver": "get_glm_command",  # Dynamic resolution with fallback
        "preferred_alias": "ccgd",
        "fallback_command": ["claude-glm", "--dangerously-skip-permissions", "-p"],
        "dangerous": True,
    },
    "scout": {
        "role": "Scout",
        "service": "qwen",
        "model": "qwen-turbo",
        "command": ["qwen", "--model", "qwen-turbo", "-p"],
        "dangerous": True,
    },
    "red_team": {
        "role": "Red Team Commander",
        "service": "gemini",
        "model": "gemini-2.0-flash-exp",
        "command": ["gemini", "--model", "gemini-2.0-flash-exp", "-p"],
        "dangerous": True,
    },
    "logistics_officer": {
        "role": "Logistics Officer",
        "service": "qwen",
        "model": "qwen-max",
        "command": ["qwen", "--model", "qwen-max", "-p"],
        "dangerous": True,
    },
}
```

### Escalation Protocol

The Supreme Commander evaluates after Phase 3 (COA Development):

```python
def should_escalate(lightweight_coas: list[COA]) -> tuple[bool, str]:
    """
    Supreme Commander decides if full council is needed.

    Escalation triggers:
    - High complexity detected (multiple architectural trade-offs)
    - Significant disagreement between initial experts
    - Novel problem domain requiring specialized analysis
    - User explicitly requested full council
    - Stakes are high (irreversible decisions)
    """
    # Returns (should_escalate, justification)
```

---

## Deliberation Protocol

### Two-Round Default Flow

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

### Delphi Extension (High-Stakes)

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

### Phase Specifications

#### Phase 1: Intelligence Gathering

**Experts**: Scout (Qwen), Intelligence Officer (Gemini)
**Parallel**: Yes
**Output**: Intelligence reports with context analysis

```yaml
intel_prompt_template: |
  MISSION: Gather intelligence on the following problem.

  PROBLEM STATEMENT:
  {problem_statement}

  CONTEXT FILES:
  {file_references}

  YOUR ROLE: {role_description}

  REPORT FORMAT:
  ## Key Findings
  - [Finding 1]
  - [Finding 2]

  ## Constraints Identified
  - [Constraint 1]

  ## Opportunities
  - [Opportunity 1]

  ## Fog Areas (Uncertainties)
  - [Uncertainty 1]
```

#### Phase 2: Situation Assessment

**Expert**: Chief Strategist (Sonnet)
**Input**: All intelligence reports
**Output**: Synthesized situation assessment

```yaml
assessment_prompt_template: |
  MISSION: Synthesize intelligence into actionable assessment.

  INTELLIGENCE REPORTS:
  {intel_reports}

  SYNTHESIZE:
  1. Problem restatement (refined)
  2. Key constraints (prioritized)
  3. Strategic opportunities
  4. Critical uncertainties requiring resolution
  5. Recommended focus areas for COA development
```

#### Phase 3: COA Development

**Experts**: Multiple (configurable)
**Parallel**: Yes
**Anonymization**: Active
**Output**: 3-5 distinct approaches

```yaml
coa_prompt_template: |
  MISSION: Develop a course of action for the following situation.

  SITUATION ASSESSMENT:
  {situation_assessment}

  YOUR PERSPECTIVE: {role_perspective}

  DEVELOP ONE APPROACH:
  ## Approach: [Name]

  ### Description
  [2-3 sentences]

  ### Implementation
  - Step 1
  - Step 2

  ### Pros
  - [Advantage 1]

  ### Cons
  - [Disadvantage 1]

  ### Risks
  - [Risk 1 with likelihood and mitigation]

  ### Effort Estimate
  [S/M/L/XL with justification]
```

#### Phase 4: Red Team + Wargaming

**Expert**: Red Team Commander (Gemini Flash)
**Input**: All COAs (anonymized as A, B, C...)
**Output**: Challenge report for each COA

```yaml
red_team_prompt_template: |
  MISSION: Challenge each proposed approach as Devil's Advocate.

  SITUATION:
  {situation_assessment}

  PROPOSED APPROACHES:
  {anonymized_coas}

  FOR EACH APPROACH, IDENTIFY:
  1. Hidden assumptions that may be wrong
  2. Failure modes not addressed
  3. Scenarios where this approach fails
  4. What the proponent might be missing
  5. Counter-arguments to stated benefits

  BE RIGOROUS BUT CONSTRUCTIVE.
```

#### Phase 5: Voting + Narrowing

**Method**: Hybrid aggregation
**Participants**: All active experts
**Output**: Top 2-3 COAs with aggregate scores

```yaml
voting_prompt_template: |
  MISSION: Rank the proposed approaches.

  APPROACHES (with Red Team challenges):
  {coas_with_challenges}

  EVALUATION CRITERIA:
  - Technical feasibility
  - Resource efficiency
  - Risk/reward balance
  - Time to value
  - Maintainability

  PROVIDE RANKING:
  FINAL RANKING:
  1. Approach [X] - [Brief justification]
  2. Approach [Y] - [Brief justification]
  3. Approach [Z] - [Brief justification]
```

#### Phase 6: Premortem

**Expert**: All available (parallel)
**Input**: Selected top COA(s)
**Output**: Failure mode catalog

```yaml
premortem_prompt_template: |
  MISSION: Imagine this approach has failed spectacularly.

  SELECTED APPROACH:
  {selected_coa}

  IT IS ONE YEAR FROM NOW. This approach was implemented and
  FAILED COMPLETELY. The project is considered a disaster.

  WHAT WENT WRONG?

  List 5-10 specific reasons for failure:
  1. [Failure reason with specifics]
  2. [Failure reason with specifics]
  ...

  For each failure mode, suggest:
  - Early warning signs
  - Preventive measures
  - Contingency plans
```

#### Phase 7: Supreme Commander Synthesis

**Expert**: Claude Opus
**Input**: All deliberation artifacts
**Output**: Final decision with rationale

```yaml
synthesis_prompt_template: |
  SUPREME COMMANDER SYNTHESIS

  You are the Supreme Commander of this War Room session.

  DELIBERATION ARTIFACTS:
  - Intelligence Reports: {intel_reports}
  - Situation Assessment: {assessment}
  - Courses of Action: {coas_with_attribution}
  - Red Team Challenges: {red_team_report}
  - Voting Results: {voting_results}
  - Premortem Analysis: {premortem_results}

  SYNTHESIZE FINAL DECISION:

  ## Selected Approach
  [Name and brief description]

  ## Rationale
  [2-3 paragraphs explaining why, incorporating:
   - How it addresses key constraints
   - Why alternatives were not selected
   - How Red Team concerns are mitigated
   - How Premortem risks are addressed]

  ## Implementation Guidance
  - Priority 1: [Most critical first step]
  - Priority 2: [Next step]

  ## Watch Points
  [Early warning signs from Premortem to monitor]

  ## Dissenting Views
  [Acknowledge unresolved disagreements for the record]
```

---

## Detailed Prompt Templates

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

### Phase 1: Scout Intelligence Report

```
MISSION BRIEFING: SCOUT INTELLIGENCE GATHERING
==============================================

You are the SCOUT - a rapid reconnaissance specialist.
Your mission: Quick initial survey of the problem space.

PROBLEM STATEMENT:
{problem_statement}

CONTEXT FILES PROVIDED:
{file_list}

<context_files>
{file_contents}
</context_files>

YOUR TASK:
Perform rapid reconnaissance. Identify the key terrain of this problem.

REPORT FORMAT (follow exactly):

## SCOUT REPORT: {session_id}

### Terrain Overview
[2-3 sentence summary of what you're looking at]

### Key Landmarks
1. **[Landmark 1]**: [Brief description]
2. **[Landmark 2]**: [Brief description]
3. **[Landmark 3]**: [Brief description]

### Obstacles Identified
- [Obstacle 1]: [Why it matters]
- [Obstacle 2]: [Why it matters]

### Points of Interest
- [Interesting pattern or opportunity noticed]

### Fog of War
- [What information is missing or unclear]

### Recommended Focus Areas
- [Where should the Intelligence Officer dig deeper]

---
END SCOUT REPORT
```

### Phase 1: Intelligence Officer Deep Analysis

```
MISSION BRIEFING: INTELLIGENCE OFFICER ANALYSIS
===============================================

You are the INTELLIGENCE OFFICER - a deep analysis specialist.
Your mission: Comprehensive intelligence gathering with your 1M+ context capability.

PROBLEM STATEMENT:
{problem_statement}

SCOUT REPORT (if available):
{scout_report}

CONTEXT FILES:
{file_list}

<full_context>
{full_file_contents}
</full_context>

YOUR TASK:
Conduct thorough intelligence analysis. Map the entire landscape.

REPORT FORMAT (follow exactly):

## INTELLIGENCE REPORT: {session_id}

### Executive Summary
[3-5 sentence comprehensive overview]

### Detailed Findings

#### Technical Landscape
- **Architecture**: [What exists, how it's structured]
- **Dependencies**: [What this relies on]
- **Integration Points**: [Where this connects to other systems]

#### Constraints Analysis
| Constraint | Type | Severity | Flexibility |
|------------|------|----------|-------------|
| [Constraint 1] | [Tech/Resource/Time/Policy] | [High/Med/Low] | [Fixed/Negotiable] |
| [Constraint 2] | ... | ... | ... |

#### Opportunity Assessment
1. **[Opportunity 1]**: [Description and potential value]
2. **[Opportunity 2]**: [Description and potential value]

#### Risk Factors
| Risk | Likelihood | Impact | Early Warning Signs |
|------|------------|--------|---------------------|
| [Risk 1] | [H/M/L] | [H/M/L] | [What to watch for] |
| [Risk 2] | ... | ... | ... |

### Fog Areas (Uncertainties)
- **[Uncertainty 1]**: [What we don't know and why it matters]
- **[Uncertainty 2]**: [What we don't know and why it matters]

### Intelligence Assessment
[Your professional assessment of the situation]

### Recommendations for COA Development
- [Specific guidance for approach generation]

---
END INTELLIGENCE REPORT
```

### Phase 2: Chief Strategist Situation Assessment

```
MISSION BRIEFING: SITUATION ASSESSMENT
======================================

You are the CHIEF STRATEGIST.
Your mission: Synthesize all intelligence into an actionable assessment.

INTELLIGENCE REPORTS:
<reports>
{all_intel_reports}
</reports>

YOUR TASK:
Create a unified situation assessment that will guide COA development.

REPORT FORMAT (follow exactly):

## SITUATION ASSESSMENT: {session_id}

### Problem Restatement
[Refined problem statement based on intelligence - 2-3 sentences]

### Strategic Context
[The broader context this problem exists within]

### Key Constraints (Prioritized)
1. **[Most Critical]**: [Why it's #1]
2. **[Second]**: [Why it's #2]
3. **[Third]**: [Why it's #3]

### Strategic Opportunities
| Opportunity | Value | Effort | Priority |
|-------------|-------|--------|----------|
| [Opp 1] | [H/M/L] | [H/M/L] | [1-5] |
| [Opp 2] | ... | ... | ... |

### Critical Uncertainties
[What MUST be resolved for success]

### COA Development Guidance

**Approaches to Explore:**
1. [Suggested approach direction 1]
2. [Suggested approach direction 2]
3. [Suggested approach direction 3]

**Approaches to Avoid:**
- [Anti-pattern 1 and why]
- [Anti-pattern 2 and why]

### Success Criteria
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]
- [ ] [Measurable criterion 3]

### Commander's Assessment
[Your strategic assessment - what does winning look like?]

---
END SITUATION ASSESSMENT
```

### Phase 3: COA Development (Per Expert)

```
MISSION BRIEFING: COURSE OF ACTION DEVELOPMENT
==============================================

You are: {expert_role}
Your perspective: {role_perspective}

SITUATION ASSESSMENT:
<assessment>
{situation_assessment}
</assessment>

YOUR TASK:
Develop ONE distinct course of action from your perspective.
Make it substantively different from obvious approaches.

COA FORMAT (follow exactly):

## COURSE OF ACTION: [Descriptive Name]

### Approach Summary
[2-3 sentence description of the approach]

### Core Philosophy
[What principle or insight drives this approach?]

### Implementation Plan

#### Phase 1: [Name] (Week 1-2)
- [ ] [Task 1]
- [ ] [Task 2]
- [ ] [Task 3]

#### Phase 2: [Name] (Week 3-4)
- [ ] [Task 4]
- [ ] [Task 5]

#### Phase 3: [Name] (Week 5+)
- [ ] [Task 6]
- [ ] [Task 7]

### Technical Approach
```
[Code sketch, architecture diagram, or technical description]
```

### Advantages
1. **[Advantage 1]**: [Explanation]
2. **[Advantage 2]**: [Explanation]
3. **[Advantage 3]**: [Explanation]

### Disadvantages
1. **[Disadvantage 1]**: [Explanation and mitigation]
2. **[Disadvantage 2]**: [Explanation and mitigation]

### Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| [Risk 1] | [H/M/L] | [H/M/L] | [Strategy] |
| [Risk 2] | ... | ... | ... |

### Resource Requirements
- **Time**: [Estimate with confidence level]
- **Expertise**: [What skills are needed]
- **Dependencies**: [What must be true]

### Effort Estimate
**[S / M / L / XL]** - [Justification for estimate]

### Key Assumptions
1. [Assumption 1 - what must be true]
2. [Assumption 2 - what must be true]

### Success Indicators
- [How we know this is working]
- [Early win conditions]

---
END COA: [Name]
```

### Phase 4: Red Team Challenge Report

```
MISSION BRIEFING: RED TEAM CHALLENGE
====================================

You are the RED TEAM COMMANDER - the Devil's Advocate.
Your mission: Rigorously challenge each proposed approach.

SITUATION ASSESSMENT:
{situation_assessment}

PROPOSED COURSES OF ACTION (ANONYMIZED):
<approaches>
{anonymized_coas}
</approaches>

YOUR TASK:
Challenge each approach without knowing who proposed it.
Be rigorous but constructive - the goal is improvement, not destruction.

CHALLENGE REPORT FORMAT (follow exactly):

## RED TEAM CHALLENGE REPORT: {session_id}

### Challenge Methodology
[Brief description of your challenge approach]

---

### CHALLENGE: Response A

#### Hidden Assumptions
1. **[Assumption]**: [Why it might be wrong]
2. **[Assumption]**: [Why it might be wrong]

#### Failure Scenarios
1. **[Scenario]**: [How this leads to failure]
2. **[Scenario]**: [How this leads to failure]

#### Overlooked Factors
- [Factor not adequately addressed]
- [Factor not adequately addressed]

#### Counter-Arguments to Stated Benefits
| Claimed Benefit | Counter-Argument |
|-----------------|------------------|
| [Benefit 1] | [Why it might not materialize] |
| [Benefit 2] | [Why it might not materialize] |

#### Stress Test Questions
1. What happens if [adverse condition]?
2. How does this handle [edge case]?
3. What if [assumption] is false?

#### Verdict: [VIABLE / WEAK / FLAWED]
[One paragraph assessment]

---

### CHALLENGE: Response B
[Same structure as above]

---

### CHALLENGE: Response C
[Same structure as above]

---

### Cross-Cutting Concerns
[Issues that affect multiple or all approaches]

### Red Team Recommendations
1. [What would strengthen the approaches]
2. [What questions must be answered]

---
END RED TEAM CHALLENGE REPORT
```

### Phase 5: Voting Template

```
MISSION BRIEFING: EXPERT RANKING
================================

You are: {expert_role}

APPROACHES WITH RED TEAM CHALLENGES:
<approaches_with_challenges>
{coas_with_red_team}
</approaches_with_challenges>

YOUR TASK:
Rank the approaches based on the evaluation criteria.

EVALUATION CRITERIA:
1. **Technical Feasibility** (30%): Can this actually be built?
2. **Resource Efficiency** (20%): Time, cost, effort required
3. **Risk/Reward Balance** (20%): Upside vs. downside
4. **Time to Value** (15%): How quickly can we see results?
5. **Maintainability** (15%): Long-term sustainability

RANKING FORMAT (follow exactly):

## EXPERT RANKING: {expert_role}

### Evaluation Matrix

| Approach | Technical | Resources | Risk/Reward | Time | Maintain | TOTAL |
|----------|-----------|-----------|-------------|------|----------|-------|
| A | [1-5] | [1-5] | [1-5] | [1-5] | [1-5] | [sum] |
| B | [1-5] | [1-5] | [1-5] | [1-5] | [1-5] | [sum] |
| C | [1-5] | [1-5] | [1-5] | [1-5] | [1-5] | [sum] |

### Justifications

**Approach A**: [Why this ranking]
**Approach B**: [Why this ranking]
**Approach C**: [Why this ranking]

FINAL RANKING:
1. Approach [X] - [One sentence justification]
2. Approach [Y] - [One sentence justification]
3. Approach [Z] - [One sentence justification]

### Additional Notes
[Any caveats or conditions on your ranking]

---
END EXPERT RANKING
```

### Phase 6: Premortem Analysis

```
MISSION BRIEFING: PREMORTEM ANALYSIS
====================================

You are: {expert_role}

SELECTED APPROACH:
<selected>
{selected_coa}
</selected>

YOUR TASK:
Imagine it is ONE YEAR from now. This approach was implemented and
FAILED COMPLETELY. The project is considered a disaster.

What went wrong?

PREMORTEM FORMAT (follow exactly):

## PREMORTEM ANALYSIS: {expert_role}

### The Disaster Scenario
[Paint a vivid picture of what failure looks like]

### Root Cause Analysis

#### Technical Failures
1. **[Failure Mode]**
   - What happened: [Description]
   - Why it happened: [Root cause]
   - Early warning signs: [What we should have noticed]
   - Prevention: [What could have prevented this]

2. **[Failure Mode]**
   [Same structure]

#### Process Failures
1. **[Failure Mode]**
   [Same structure]

#### External Failures
1. **[Failure Mode]**
   [Same structure]

### Failure Mode Summary

| Failure Mode | Likelihood | Impact | Preventable? | Early Warning |
|--------------|------------|--------|--------------|---------------|
| [FM1] | [H/M/L] | [H/M/L] | [Y/N] | [Signal] |
| [FM2] | ... | ... | ... | ... |

### Critical Watch Points
[Top 3 things to monitor that would indicate we're heading toward failure]

1. **[Watch Point 1]**: [What to monitor, threshold for alarm]
2. **[Watch Point 2]**: [What to monitor, threshold for alarm]
3. **[Watch Point 3]**: [What to monitor, threshold for alarm]

### Contingency Recommendations
[If we see early warnings, what should we do?]

---
END PREMORTEM ANALYSIS
```

### Phase 7: Supreme Commander Synthesis

```
SUPREME COMMANDER SYNTHESIS
===========================

You are the SUPREME COMMANDER of this War Room session.
Your mission: Synthesize all deliberation into a final decision.

SESSION ARTIFACTS:

<intelligence_reports>
{intel_reports}
</intelligence_reports>

<situation_assessment>
{assessment}
</situation_assessment>

<courses_of_action>
{coas_with_full_attribution}
</courses_of_action>

<red_team_challenges>
{red_team_report}
</red_team_challenges>

<voting_results>
{voting_summary}
</voting_results>

<premortem_analyses>
{premortem_results}
</premortem_analyses>

YOUR TASK:
Make the final decision. Your word is law.

SYNTHESIS FORMAT (follow exactly):

## SUPREME COMMANDER DECISION: {session_id}

### Decision
**Selected Approach**: [Name]

### Executive Summary
[2-3 paragraph summary of the decision and key rationale]

### Rationale

#### Why This Approach
[Detailed explanation of why this approach was selected]

#### Why Not the Alternatives
| Alternative | Reason for Rejection |
|-------------|---------------------|
| [Approach X] | [Specific reason] |
| [Approach Y] | [Specific reason] |

#### How Red Team Concerns Are Addressed
| Red Team Concern | Mitigation Strategy |
|------------------|---------------------|
| [Concern 1] | [How we address it] |
| [Concern 2] | [How we address it] |

#### How Premortem Risks Are Managed
| Risk | Prevention Strategy | Contingency |
|------|---------------------|-------------|
| [Risk 1] | [Prevention] | [If it happens anyway] |
| [Risk 2] | [Prevention] | [If it happens anyway] |

### Implementation Orders

#### Immediate Actions (This Week)
1. [ ] [Action 1]
2. [ ] [Action 2]
3. [ ] [Action 3]

#### Short-Term Actions (This Month)
1. [ ] [Action 4]
2. [ ] [Action 5]

#### Success Metrics
- [Metric 1]: [Target value and timeline]
- [Metric 2]: [Target value and timeline]

### Watch Points
[From Premortem - what to monitor]
1. **[Watch Point 1]**: [Threshold for escalation]
2. **[Watch Point 2]**: [Threshold for escalation]

### Dissenting Views (For the Record)
[Acknowledge any unresolved disagreements or minority positions]

### Commander's Notes
[Any additional guidance or context for implementers]

---
DECISION RENDERED: {timestamp}
SESSION: {session_id}
COMMANDER: Claude Opus (Supreme Commander)
---
END SUPREME COMMANDER DECISION
```

---

## Anonymization with Merkle-DAG

### Rationale

Research shows LLMs exhibit "self-preference bias" - favoring their own outputs. Anonymization eliminates this while maintaining full traceability for post-decision analysis.

### Data Structure

```python
from dataclasses import dataclass
from hashlib import sha256
from typing import Optional
import json

@dataclass
class DeliberationNode:
    """A single contribution in the deliberation graph."""

    node_id: str           # SHA-256 hash of content + metadata
    parent_id: Optional[str]  # Previous version (for revisions)
    round_number: int      # Which deliberation round
    phase: str             # intel, coa, red_team, vote, etc.

    # Anonymized during deliberation
    anonymous_label: str   # "Response A", "Expert 2", etc.
    content: str           # The actual contribution

    # Revealed after decision
    expert_role: str       # "Intelligence Officer", "Red Team", etc.
    expert_model: str      # "gemini-2.5-pro", "qwen-turbo", etc.

    # Merkle linkage
    content_hash: str      # SHA-256 of content only
    metadata_hash: str     # SHA-256 of role + model
    combined_hash: str     # SHA-256 of content_hash + metadata_hash

    timestamp: str         # ISO format


@dataclass
class MerkleDAG:
    """
    Directed Acyclic Graph tracking deliberation history.

    Properties:
    - Each node is content-addressable via its hash
    - Parent links create revision history
    - Root hash summarizes entire deliberation
    - Attribution is masked until root is "unsealed"
    """

    session_id: str
    root_hash: Optional[str] = None
    nodes: dict[str, DeliberationNode] = field(default_factory=dict)

    def add_contribution(
        self,
        content: str,
        phase: str,
        round_number: int,
        expert_role: str,
        expert_model: str,
        parent_id: Optional[str] = None
    ) -> DeliberationNode:
        """Add a contribution and compute hashes."""

        content_hash = sha256(content.encode()).hexdigest()
        metadata_hash = sha256(
            f"{expert_role}:{expert_model}".encode()
        ).hexdigest()
        combined_hash = sha256(
            f"{content_hash}:{metadata_hash}".encode()
        ).hexdigest()

        node = DeliberationNode(
            node_id=combined_hash[:16],  # Short ID
            parent_id=parent_id,
            round_number=round_number,
            phase=phase,
            anonymous_label=self._generate_anonymous_label(phase),
            content=content,
            expert_role=expert_role,
            expert_model=expert_model,
            content_hash=content_hash,
            metadata_hash=metadata_hash,
            combined_hash=combined_hash,
            timestamp=datetime.now().isoformat()
        )

        self.nodes[node.node_id] = node
        self._update_root_hash()
        return node

    def get_anonymized_view(self) -> list[dict]:
        """Return contributions with attribution masked."""
        return [
            {
                "label": node.anonymous_label,
                "content": node.content,
                "phase": node.phase,
                "round": node.round_number,
                "hash": node.node_id  # Verifiable but not attributable
            }
            for node in self.nodes.values()
        ]

    def unseal(self) -> list[dict]:
        """Reveal full attribution after decision is made."""
        return [
            {
                "label": node.anonymous_label,
                "content": node.content,
                "phase": node.phase,
                "round": node.round_number,
                "expert_role": node.expert_role,
                "expert_model": node.expert_model,
                "hash": node.node_id,
                "verified": self._verify_hash(node)
            }
            for node in self.nodes.values()
        ]
```

### Version Tracking Across Rounds

```
Round 1                    Round 2                    Round 3
┌──────────────┐          ┌──────────────┐          ┌──────────────┐
│ COA-A (v1)   │────────▶ │ COA-A (v2)   │────────▶ │ COA-A (v3)   │
│ hash: abc123 │  revises │ hash: def456 │  revises │ hash: ghi789 │
│ parent: null │          │ parent: abc123│          │ parent: def456│
└──────────────┘          └──────────────┘          └──────────────┘

Root Hash (Round 3): SHA256(ghi789 + ... all leaf hashes)
```

---

## Aggregation and Synthesis

### Hybrid Method

```python
def aggregate_votes(votes: list[VoteResult]) -> AggregatedResult:
    """
    Hybrid aggregation: voting to narrow, then synthesis.

    Step 1: Collect rankings from all experts
    Step 2: Apply weighted scoring (equal weights by default)
    Step 3: Identify top 2-3 approaches
    Step 4: Check for meritocracy override
    Step 5: Pass to Chairman for synthesis
    """

    # Compute aggregate scores
    scores = defaultdict(float)
    for vote in votes:
        for rank, approach_id in enumerate(vote.ranking):
            # Borda count: higher rank = more points
            points = len(vote.ranking) - rank
            scores[approach_id] += points

    # Sort by score
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Top 2-3 for synthesis
    finalists = ranked[:3]

    return AggregatedResult(
        finalists=finalists,
        full_ranking=ranked,
        voting_method="borda_count",
        consensus_score=calculate_consensus(votes)
    )
```

### Meritocracy Override

The Supreme Commander may override voting when:

```python
def meritocracy_check(
    aggregated: AggregatedResult,
    expert_assessments: list[Assessment]
) -> Optional[MeritocracyOverride]:
    """
    Supreme Commander may override voting results.

    Justifiable overrides:
    - Expert with domain expertise strongly disagrees
    - Voting converged on popular but flawed approach
    - Critical insight from minority position
    - Strategic considerations beyond tactical voting

    Override MUST include written justification.
    """
    # Commander evaluates and decides
```

---

## Session Persistence

### Local JSON Cache

```json
{
  "session_id": "war-room-20260120-153022",
  "created_at": "2026-01-20T15:30:22Z",
  "status": "completed",
  "problem_statement": "...",

  "configuration": {
    "mode": "lightweight",
    "escalated": true,
    "escalation_reason": "High architectural complexity detected",
    "deliberation_rounds": 2,
    "experts_invoked": ["strategist", "intel_officer", "red_team"]
  },

  "merkle_dag": {
    "root_hash": "a1b2c3d4...",
    "nodes": { ... }
  },

  "phases": {
    "intel": { "status": "complete", "artifacts": [...] },
    "assessment": { "status": "complete", "artifact": "..." },
    "coa_development": { "status": "complete", "coas": [...] },
    "red_team": { "status": "complete", "challenges": [...] },
    "voting": { "status": "complete", "results": {...} },
    "premortem": { "status": "complete", "failure_modes": [...] },
    "synthesis": { "status": "complete", "decision": {...} }
  },

  "final_decision": {
    "selected_approach": "Approach B",
    "rationale": "...",
    "dissenting_views": [...],
    "watch_points": [...]
  },

  "metrics": {
    "total_tokens": 145000,
    "total_cost_usd": 8.50,
    "duration_seconds": 342,
    "experts_consulted": 5
  }
}
```

### Strategeion Archive Structure

```
~/.claude/memory-palace/strategeion/
├── war-table/
│   └── war-room-20260120-153022/
│       ├── session.json           # Full session state
│       ├── intelligence/
│       │   ├── scout-report.md
│       │   └── intel-officer-report.md
│       ├── battle-plans/
│       │   ├── coa-a.md
│       │   ├── coa-b.md
│       │   └── coa-c.md
│       ├── wargames/
│       │   ├── red-team-challenges.md
│       │   └── premortem-analysis.md
│       └── orders/
│           └── final-decision.md
│
├── campaign-archive/
│   └── claude-night-market/
│       └── 2026-01-20-war-room-feature/
│           └── ... (archived from war-table)
│
└── doctrine/
    ├── patterns/
    │   └── escalation-triggers.md
    └── lessons/
        └── 2026-01-20-multi-llm-deliberation.md
```

---

## Conjure Integration

### New Module: war_room_orchestrator.py

```python
#!/usr/bin/env python3
"""
War Room Orchestrator

Composes delegation_executor calls to orchestrate multi-LLM deliberation.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import asyncio
import json

from delegation_executor import Delegator, ExecutionResult


@dataclass
class ExpertConfig:
    """Configuration for a War Room expert."""
    role: str
    service: str  # gemini, qwen, claude
    model: str
    prompt_template: str
    phase: str


@dataclass
class WarRoomSession:
    """Active War Room deliberation session."""
    session_id: str
    problem_statement: str
    mode: str = "lightweight"  # or "full_council"
    merkle_dag: MerkleDAG = field(default_factory=MerkleDAG)
    experts: list[ExpertConfig] = field(default_factory=list)
    phases_completed: list[str] = field(default_factory=list)


class WarRoomOrchestrator:
    """
    Orchestrates multi-LLM deliberation sessions.

    Responsibilities:
    - Expert panel management
    - Phase sequencing
    - Parallel dispatch via delegation_executor
    - Response aggregation
    - Merkle-DAG maintenance
    - Strategeion persistence
    """

    def __init__(self, strategeion_path: Optional[Path] = None):
        self.delegator = Delegator()
        self.strategeion = strategeion_path or (
            Path.home() / ".claude" / "memory-palace" / "strategeion"
        )
        self.strategeion.mkdir(parents=True, exist_ok=True)

    async def convene_war_room(
        self,
        problem_statement: str,
        context_files: list[str] = None,
        mode: str = "lightweight"
    ) -> WarRoomSession:
        """
        Convene a new War Room session.

        Args:
            problem_statement: The problem to deliberate
            context_files: Files to include as context
            mode: "lightweight" or "full_council"

        Returns:
            WarRoomSession with completed deliberation
        """
        session = self._initialize_session(problem_statement, mode)

        # Phase 1: Intelligence gathering
        await self._phase_intel(session, context_files)

        # Phase 2: Situation assessment
        await self._phase_assessment(session)

        # Phase 3: COA development
        await self._phase_coa_development(session)

        # Escalation check
        if await self._should_escalate(session):
            session.mode = "full_council"
            await self._escalate_to_full_council(session)

        # Phase 4: Red Team + Wargaming
        await self._phase_red_team(session)

        # Phase 5: Voting
        await self._phase_voting(session)

        # Phase 6: Premortem
        await self._phase_premortem(session)

        # Phase 7: Supreme Commander synthesis
        await self._phase_synthesis(session)

        # Persist to Strategeion
        self._persist_to_strategeion(session)

        return session

    async def _dispatch_expert(
        self,
        expert: ExpertConfig,
        context: dict[str, Any],
        session: WarRoomSession
    ) -> str:
        """Dispatch a single expert and record contribution."""

        prompt = expert.prompt_template.format(**context)

        if expert.service == "native":
            # Use current Claude session (Supreme Commander, Chief Strategist)
            result = await self._invoke_native(prompt)
        elif expert.service == "glm":
            # GLM-4.7 with fallback resolution (see get_glm_command)
            result = await self._invoke_glm(prompt)
        else:
            # Use delegation_executor (gemini, qwen)
            result = self.delegator.execute(
                expert.service,
                prompt,
                options={"model": expert.model, "dangerous": True}
            )

        # Record in Merkle-DAG (anonymized)
        session.merkle_dag.add_contribution(
            content=result.stdout if hasattr(result, 'stdout') else result,
            phase=expert.phase,
            round_number=len(session.phases_completed) + 1,
            expert_role=expert.role,
            expert_model=expert.model
        )

        return result.stdout if hasattr(result, 'stdout') else result

    async def _invoke_glm(self, prompt: str) -> str:
        """
        Invoke GLM-4.7 with fallback command resolution.

        Priority:
        1. ccgd (alias) - if available in PATH
        2. claude-glm --dangerously-skip-permissions - fallback

        Uses asyncio.create_subprocess_exec (safe, no shell injection).
        """
        cmd = get_glm_command()  # Returns resolved command list
        cmd.append(prompt)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"GLM-4.7 invocation failed: {stderr.decode()}")

        return stdout.decode()

    async def _dispatch_parallel(
        self,
        experts: list[ExpertConfig],
        context: dict[str, Any],
        session: WarRoomSession
    ) -> list[str]:
        """Dispatch multiple experts in parallel."""
        tasks = [
            self._dispatch_expert(expert, context, session)
            for expert in experts
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

### Service Configuration Extension

```json
{
  "services": {
    "gemini": { ... },
    "qwen": { ... },
    "claude-glm": {
      "command": "claude",
      "args": ["--model", "glm-4.7", "-p"],
      "auth_method": "anthropic_api",
      "note": "Requires GLM-4 API configuration in settings.json"
    }
  },
  "war_room": {
    "default_mode": "lightweight",
    "escalation_threshold": 0.7,
    "delphi_convergence_threshold": 0.85,
    "max_delphi_rounds": 5
  }
}
```

---

## Command and Skill Specifications

### Command: /attune:war-room

```markdown
---
name: war-room
description: Convene a multi-LLM War Room for strategic decision making
---

# War Room Command

Orchestrate multi-expert deliberation for complex decisions.

## Usage

```bash
# Basic invocation
/attune:war-room "Problem statement here"

# With context files
/attune:war-room "Problem" --files src/**/*.py

# Force full council
/attune:war-room "Problem" --full-council

# High-stakes (Delphi mode)
/attune:war-room "Problem" --delphi

# Resume session
/attune:war-room --resume {session-id}
```

## Arguments

- `--files <globs...>` - Context files for analysis
- `--full-council` - Skip lightweight, use full expert panel
- `--delphi` - Use iterative Delphi convergence
- `--resume <session-id>` - Resume interrupted session
- `--archive <name>` - Name for campaign archive

## Workflow

1. Invokes `Skill(attune:war-room)`
2. Orchestrates expert panel via conjure
3. Persists to Strategeion
4. Outputs decision document
```

### Skill: attune:war-room

```markdown
---
name: war-room
description: Multi-LLM deliberation framework for strategic decisions
triggers: war room, strategic decision, multi-expert, deliberation, council
use_when: complex decisions requiring multiple perspectives
do_not_use_when: simple questions, routine tasks
category: strategic-planning
tags: [deliberation, multi-llm, strategy, decision-making]
dependencies:
  - conjure:delegation-core
  - memory-palace:strategeion
tools: [war-room-orchestrator]
complexity: advanced
estimated_tokens: 2000
progressive_loading: true
modules:
  - modules/expert-roles.md
  - modules/deliberation-protocol.md
  - modules/red-team-patterns.md
  - modules/synthesis-framework.md
  - modules/merkle-dag.md
---

# War Room Skill

## Overview

Orchestrate multi-LLM deliberation for complex strategic decisions.

## When to Use

- Architectural decisions with major trade-offs
- Multi-stakeholder problems requiring diverse perspectives
- High-stakes choices with significant consequences
- Novel problems without clear precedent

## Expert Panel

[See modules/expert-roles.md]

## Protocol

[See modules/deliberation-protocol.md]

## Integration

### With Brainstorm

War Room can be invoked from brainstorm when:
- Multiple strong approaches emerge
- User explicitly requests expert council
- Problem complexity exceeds threshold

### With Memory Palace

Sessions persist to Strategeion for:
- Future reference
- Doctrine extraction
- Pattern recognition
```

---

## Hook Auto-Trigger Configuration

The War Room can be automatically triggered via a hook using a hybrid approach combining three detection methods.

### Trigger Configuration

```json
{
  "war_room_auto_trigger": {
    "enabled": true,
    "require_user_opt_in": true,

    "complexity_threshold": {
      "enabled": true,
      "threshold": 0.7,
      "factors": {
        "architectural_trade_offs": 0.3,
        "stakeholder_count": 0.2,
        "reversibility": 0.2,
        "domain_novelty": 0.15,
        "time_pressure": 0.15
      }
    },

    "keyword_detection": {
      "enabled": true,
      "trigger_keywords": [
        "war room",
        "council",
        "deliberation",
        "strategic decision",
        "major trade-off",
        "architectural decision",
        "high stakes",
        "need multiple perspectives",
        "expert panel",
        "convene experts"
      ],
      "context_keywords": [
        "should we",
        "which approach",
        "trade-offs between",
        "pros and cons",
        "compare approaches",
        "best strategy"
      ]
    },

    "user_settings": {
      "enabled": true,
      "setting_key": "war_room.auto_trigger",
      "default": false
    }
  }
}
```

### Hybrid Trigger Logic

```python
def should_auto_trigger_war_room(
    prompt: str,
    context: SessionContext,
    settings: UserSettings
) -> tuple[bool, str]:
    """
    Hybrid approach: ALL conditions are evaluated, ANY can trigger.

    Returns:
        (should_trigger, reason)
    """
    reasons = []

    # 1. Keyword Detection (fastest, check first)
    if settings.war_room.keyword_detection.enabled:
        keyword_match = detect_war_room_keywords(prompt)
        if keyword_match:
            reasons.append(f"keyword_detected: {keyword_match}")

    # 2. User Setting (explicit opt-in)
    if settings.war_room.user_settings.enabled:
        user_opted_in = settings.get("war_room.auto_trigger", False)
        if user_opted_in:
            reasons.append("user_opted_in")

    # 3. Complexity Score (most expensive, check last)
    if settings.war_room.complexity_threshold.enabled:
        complexity = calculate_complexity_score(prompt, context)
        if complexity >= settings.war_room.complexity_threshold.threshold:
            reasons.append(f"complexity_score: {complexity:.2f}")

    # Trigger if ANY condition met
    if reasons:
        return True, " | ".join(reasons)

    return False, "no_trigger_conditions_met"


def detect_war_room_keywords(prompt: str) -> Optional[str]:
    """Fast keyword detection using compiled regex."""
    prompt_lower = prompt.lower()

    # Direct trigger keywords (high confidence)
    for keyword in TRIGGER_KEYWORDS:
        if keyword in prompt_lower:
            return f"direct:{keyword}"

    # Context keywords require multiple matches (medium confidence)
    context_matches = sum(
        1 for kw in CONTEXT_KEYWORDS
        if kw in prompt_lower
    )
    if context_matches >= 2:
        return f"context:{context_matches}_matches"

    return None


def calculate_complexity_score(
    prompt: str,
    context: SessionContext
) -> float:
    """
    Calculate problem complexity score.

    Factors (weights sum to 1.0):
    - architectural_trade_offs (0.30): Multiple valid architectures
    - stakeholder_count (0.20): Multiple affected parties
    - reversibility (0.20): How hard to undo
    - domain_novelty (0.15): Novel problem space
    - time_pressure (0.15): Urgency vs. importance
    """
    scores = {}

    # Architectural trade-offs
    trade_off_signals = [
        "vs", "or", "trade-off", "alternative",
        "approach", "strategy", "architecture"
    ]
    scores["architectural_trade_offs"] = min(
        sum(1 for s in trade_off_signals if s in prompt.lower()) / 4,
        1.0
    )

    # Stakeholder signals
    stakeholder_signals = [
        "team", "users", "customers", "stakeholders",
        "management", "developers", "ops"
    ]
    scores["stakeholder_count"] = min(
        sum(1 for s in stakeholder_signals if s in prompt.lower()) / 3,
        1.0
    )

    # Reversibility (inverse - hard to reverse = higher score)
    irreversible_signals = [
        "migration", "rewrite", "breaking change",
        "deprecate", "remove", "delete", "architecture"
    ]
    scores["reversibility"] = min(
        sum(1 for s in irreversible_signals if s in prompt.lower()) / 2,
        1.0
    )

    # Domain novelty
    novelty_signals = [
        "new", "first time", "never done", "unfamiliar",
        "research", "experiment", "prototype"
    ]
    scores["domain_novelty"] = min(
        sum(1 for s in novelty_signals if s in prompt.lower()) / 3,
        1.0
    )

    # Time pressure
    urgency_signals = [
        "urgent", "asap", "deadline", "critical",
        "immediately", "today", "this week"
    ]
    scores["time_pressure"] = min(
        sum(1 for s in urgency_signals if s in prompt.lower()) / 2,
        1.0
    )

    # Weighted sum
    weights = {
        "architectural_trade_offs": 0.30,
        "stakeholder_count": 0.20,
        "reversibility": 0.20,
        "domain_novelty": 0.15,
        "time_pressure": 0.15,
    }

    total = sum(
        scores[factor] * weight
        for factor, weight in weights.items()
    )

    return total
```

### Hook Implementation

```python
# hooks/war_room_trigger.py

from typing import Any
import json

def pre_tool_use_hook(
    tool_name: str,
    tool_input: dict[str, Any],
    session_context: dict[str, Any]
) -> dict[str, Any]:
    """
    PreToolUse hook to detect War Room trigger conditions.

    Only fires on specific tools that indicate decision-making:
    - UserPromptSubmit (new user message)
    - Skill invocation (brainstorming skills)
    """
    if tool_name not in ["UserPromptSubmit", "Skill"]:
        return {"continue": True}

    # Load settings
    settings = load_war_room_settings()
    if not settings.get("enabled", False):
        return {"continue": True}

    # Check if user requires opt-in
    if settings.get("require_user_opt_in", True):
        if not session_context.get("user_settings", {}).get(
            "war_room.auto_trigger", False
        ):
            return {"continue": True}

    # Get prompt content
    prompt = ""
    if tool_name == "UserPromptSubmit":
        prompt = tool_input.get("prompt", "")
    elif tool_name == "Skill":
        prompt = tool_input.get("skill_args", "")

    # Evaluate trigger conditions
    should_trigger, reason = should_auto_trigger_war_room(
        prompt=prompt,
        context=session_context,
        settings=settings
    )

    if should_trigger:
        return {
            "continue": True,
            "additional_context": (
                f"[War Room Auto-Trigger] Conditions met: {reason}\n"
                f"Consider invoking: /attune:war-room or Skill(attune:war-room)\n"
                f"To disable: set war_room.auto_trigger=false in settings"
            )
        }

    return {"continue": True}
```

### User Settings

Users can enable/disable auto-trigger in their settings:

```json
// ~/.claude/settings.json
{
  "war_room": {
    "auto_trigger": true,
    "complexity_threshold": 0.7,
    "always_suggest": false,
    "never_trigger_for": [
      "simple questions",
      "code formatting",
      "documentation"
    ]
  }
}
```

### Safeguards

1. **Opt-in by default**: Auto-trigger is disabled until user explicitly enables
2. **Suggestion mode**: Hook suggests War Room but doesn't auto-invoke
3. **Cooldown**: After triggering, wait N minutes before suggesting again
4. **Context awareness**: Don't trigger during active War Room session
5. **User override**: `--no-war-room` flag suppresses suggestions

---

## Implementation Phases

### Phase 1: Foundation (Week 1)

- [ ] Create `plugins/attune/skills/war-room/` structure
- [ ] Implement basic `war_room_orchestrator.py`
- [ ] Define expert prompt templates
- [ ] Create Merkle-DAG data structures
- [ ] Basic Strategeion directory structure

**Deliverable**: Minimal working War Room with 3 experts

### Phase 2: Deliberation Protocol (Week 2)

- [ ] Implement all 7 phases
- [ ] Add parallel dispatch via asyncio
- [ ] Implement anonymization layer
- [ ] Add voting aggregation
- [ ] Premortem integration

**Deliverable**: Full deliberation flow

### Phase 3: Memory Palace Integration (Week 3)

- [ ] Strategeion archive structure
- [ ] Campaign history commands
- [ ] Doctrine extraction skill
- [ ] Session resume capability

**Deliverable**: Persistent War Room with searchable history

### Phase 4: Escalation & Refinement (Week 4)

- [ ] Supreme Commander escalation logic
- [ ] Delphi convergence mode
- [ ] Meritocracy override
- [ ] Hook for auto-trigger (gated)
- [ ] Documentation and examples

**Deliverable**: Production-ready War Room

---

## Success Criteria

### Functional

- [ ] Can invoke War Room with problem statement
- [ ] Experts respond in parallel when possible
- [ ] Anonymization masks attribution until unsealed
- [ ] Red Team challenges all COAs
- [ ] Premortem identifies failure modes
- [ ] Supreme Commander synthesizes final decision
- [ ] Session persists to Strategeion

### Quality

- [ ] Deliberation improves decision quality vs single-model
- [ ] Diverse perspectives surface non-obvious risks
- [ ] Red Team catches at least 3 assumptions per COA
- [ ] Premortem identifies realistic failure modes

### Performance

- [ ] Lightweight mode completes in < 5 minutes
- [ ] Full council completes in < 15 minutes
- [ ] Graceful degradation when expert fails

### Integration

- [ ] Works with existing conjure delegation
- [ ] Integrates with memory-palace architecture
- [ ] Can be invoked from brainstorm workflow
- [ ] Session state is resumable

---

## References

### Strategic Frameworks
- [Sun Tzu - Art of War](https://classics.mit.edu/Tzu/artwar.html)
- [Clausewitz - On War](https://clausewitzstudies.org/readings/OnWar1873/BK1ch07.html)
- [Robert Greene - 33 Strategies](https://grahammann.net/book-notes/the-33-strategies-of-war-robert-greene)
- [MDMP - U.S. Army](https://www.army.mil/article/271773/military_decision_making_process_organizing_and_conducting_planning)

### Decision Methods
- [Gary Klein - Premortem](https://www.gary-klein.com/premortem)
- [Delphi Method](https://en.wikipedia.org/wiki/Delphi_method)
- [Six Thinking Hats](https://www.debonogroup.com/services/core-programs/six-thinking-hats/)

### Multi-Agent Systems
- [Karpathy LLM Council](https://github.com/karpathy/llm-council)
- [MIT Multi-AI Collaboration](https://news.mit.edu/2023/multi-ai-collaboration-helps-reasoning-factual-accuracy-language-models-0918)
- [Multi-Agent Debate](https://arxiv.org/abs/2305.14325)
- [Society of Mind](https://en.wikipedia.org/wiki/Society_of_Mind)

---

**Status**: Draft - Awaiting Review
**Next**: Implementation Phase 1 upon approval
