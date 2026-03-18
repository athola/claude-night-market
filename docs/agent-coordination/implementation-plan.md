# Agent Coordination Architecture -- Implementation Plan v0.1.0

**Author**: Alex T
**Date**: 2026-03-17
**Sprint Length**: 1 sprint per phase (single-developer cadence)
**Team Size**: 1 (+ Claude agents)
**Target Completion**: Phased rollout, each phase independently
mergeable

## Architecture

### System Overview

The agent coordination system is a set of conventions,
skills, and validation hooks layered on top of the
existing night-market plugin infrastructure.
It does not introduce new runtime dependencies.
All coordination is file-based.

```
┌─────────────────────────────────────────────────┐
│                 Parent Agent                     │
│  ┌───────────┐  ┌───────────┐  ┌─────────────┐ │
│  │ Tier      │  │ Session   │  │ Contract    │ │
│  │ Router    │  │ Router    │  │ Validator   │ │
│  └─────┬─────┘  └─────┬─────┘  └──────┬──────┘ │
│        │              │               │         │
└────────┼──────────────┼───────────────┼─────────┘
         │              │               │
    ┌────▼────┐    ┌────▼────┐    ┌─────▼─────┐
    │ Tier 1  │    │ Agent A │    │ Validates  │
    │ git-log │    │ (area1) │    │ findings   │
    └────┬────┘    └────┬────┘    └───────────┘
         │              │
    ┌────▼────┐    ┌────▼──────────────────┐
    │ Tier 2  │    │  .coordination/       │
    │ targeted│    │    agents/a.findings  │
    └────┬────┘    │    agents/b.findings  │
         │         │    handoffs/          │
    ┌────▼────┐    │    tasks.json         │
    │ Tier 3  │    └───────────────────────┘
    │ full    │
    └─────────┘
```

### Components

#### Component: Tier Router

**Responsibility**: Determines audit scope and routes
to the appropriate tier (1/2/3).

**Technology**: Skill (Markdown + prompt engineering)

**Interfaces**:

- Input: Audit request (user prompt or egregore
  work item)
- Output: Tier selection + scope parameters
- Escalation: Tier 1 findings -> Tier 2 target list

**Dependencies**: Git CLI for Tier 1 analysis

---

#### Component: Output Contract Validator

**Responsibility**: Validates agent findings against
output contracts before the parent accepts them.

**Technology**: Python script (hooks/) or inline
skill validation

**Interfaces**:

- Input: Agent findings file + output contract spec
- Output: PASS/FAIL with detail of missing elements
- Retry: Specific feedback message for failed
  validation

**Dependencies**: imbue:proof-of-work evidence tag
pattern

---

#### Component: Coordination Workspace

**Responsibility**: Manages the `.coordination/`
directory lifecycle (create, populate, archive, clean).

**Technology**: Skill module + shell commands

**Interfaces**:

- Init: Creates directory structure + tasks.json
- Write: Agents write to `agents/{name}.findings.md`
- Handoff: Agents write to `handoffs/{from}-to-{to}.md`
- Archive: Moves completed workspace to timestamped
  archive
- Cleanup: Preserves on failure with reason file

**Dependencies**: None (pure file operations)

---

#### Component: Area-Agent Registry

**Responsibility**: Maps codebase directories to
specialist agent configurations.

**Technology**: Markdown files in `.claude/area-agents/`

**Interfaces**:

- Lookup: Given a file path, return matching area-agent
  config
- Fallback: Return generic template when no specific
  config exists
- Load: Inject area config into agent dispatch prompt

**Dependencies**: Existing `.claude/agents/` infrastructure

---

#### Component: Session Router

**Responsibility**: Decides whether work should use
subagents or dedicated sessions based on complexity.

**Technology**: Skill (decision logic in prompt)

**Interfaces**:

- Input: Task scope (areas touched, file count,
  estimated complexity)
- Output: Routing decision (subagent / dedicated
  session / sequential)
- Integration: Feeds into plan-before-large-dispatch
  rule

**Dependencies**: Area-Agent Registry, Coordination
Workspace

---

#### Component: Agent Memory Manager

**Responsibility**: Manages the three-tier memory
hierarchy (hot/warm/cold) for long-running agents.

**Technology**: Skill + file conventions

**Interfaces**:

- Hot: `{agent-dir}/memory.md` (200-line limit)
- Warm: `{agent-dir}/topics/{topic}.md`
- Cold: `{agent-dir}/archive/{month}.md`
- Triage: Session-end protocol to promote/demote
  content between tiers

**Dependencies**: Existing conserve memory patterns

### Data Flow

```
User Request
    │
    ▼
Tier Router ──── Is scope specified? ──── Yes ──▶ Use specified tier
    │                                              │
    No                                             │
    │                                              │
    ▼                                              ▼
Tier 1: git log/diff/blame ──────────────▶ Findings file
    │                                        │
    ▼                                        ▼
Escalation needed? ── No ──▶ Contract Validator ──▶ Done
    │                              │
    Yes                         FAIL?
    │                              │
    ▼                              ▼
Tier 2: per-area audit ──▶ Retry with feedback
    │
    ▼
Area-Agent config loaded
    │
    ▼
Session Router: subagent or dedicated?
    │
    ▼
Agent writes to .coordination/agents/
    │
    ▼
Contract Validator
    │
    ▼
Parent reads summaries, deep-dives selectively
    │
    ▼
Synthesized report (raw findings preserved in files)
```

## Task Breakdown

### Phase 1: Output Contracts + Escalation Protocol (FR-006, FR-008)

*Highest leverage, lowest complexity.
Pure skill/prompt changes, no new infrastructure.*

---

#### TASK-001: Define Output Contract Schema

**Description**: Create a reusable output contract
format that specifies required sections, minimum
evidence count, and expected artifacts for any agent
dispatch.

**Type**: Implementation
**Priority**: P0 (Critical)
**Estimate**: 3 points
**Dependencies**: None
**Linked Requirements**: FR-006

**Acceptance Criteria**:

- [ ] Contract schema documented as a skill module
- [ ] Schema includes: required_sections (list),
  min_evidence_count (int), expected_artifacts (list),
  retry_budget (int)
- [ ] Example contracts for 3 common dispatch types:
  code review, audit, research
- [ ] Tests validate schema parsing

**Technical Notes**:

- Format as YAML frontmatter block embeddable in
  agent dispatch prompts
- Align with imbue:structured-output template pattern
- Evidence tags follow existing `[E1]`/`[E2]` convention

---

#### TASK-002: Build Contract Validator

**Description**: Create a validation function that
checks agent findings against an output contract and
returns PASS/FAIL with specific missing-element detail.

**Type**: Implementation
**Priority**: P0 (Critical)
**Estimate**: 5 points
**Dependencies**: TASK-001
**Linked Requirements**: FR-006

**Acceptance Criteria**:

- [ ] Validator checks: all required sections present
  in findings file
- [ ] Validator checks: evidence citation count >=
  min_evidence_count
- [ ] Validator checks: expected artifact files exist
- [ ] FAIL result includes specific list of what is
  missing
- [ ] Zero-evidence output is unconditionally rejected
- [ ] Unit tests cover PASS, FAIL (missing section),
  FAIL (low evidence), FAIL (zero evidence)

**Technical Notes**:

- Python function in a shared utility module
- Parse findings file as Markdown with YAML frontmatter
- Could also be implemented as a hook that runs
  post-agent-completion

---

#### TASK-003: Create Retry-with-Feedback Mechanism

**Description**: When contract validation fails, generate
a specific retry prompt that tells the agent exactly what
is missing, rather than re-dispatching from scratch.

**Type**: Implementation
**Priority**: P1 (High)
**Estimate**: 3 points
**Dependencies**: TASK-002
**Linked Requirements**: FR-006

**Acceptance Criteria**:

- [ ] Retry prompt includes: original task, validation
  failure details, specific missing elements
- [ ] Retry budget is respected (max retries from
  contract)
- [ ] After budget exhausted, failure is escalated
  (not silently dropped)
- [ ] Test: simulated FAIL -> retry -> PASS flow

---

#### TASK-004: Define Tier Escalation Criteria

**Description**: Document the specific criteria that
trigger escalation from Tier 1 to Tier 2, and from
Tier 2 to Tier 3.

**Type**: Implementation
**Priority**: P0 (Critical)
**Estimate**: 2 points
**Dependencies**: None
**Linked Requirements**: FR-008, FR-001

**Acceptance Criteria**:

- [ ] Tier 1 -> 2 criteria documented: 3+ files in
  same module with repeated churn, suspicious patterns
  (e.g., reverted changes, fix-on-fix commits)
- [ ] Tier 2 -> 3 criteria documented: systemic issues
  (cross-cutting concerns, architectural problems)
- [ ] Escalation log format defined: tier, reason,
  target areas, triggering evidence
- [ ] Criteria are encoded in a skill module, not
  hardcoded in prompts

---

#### TASK-005: Build Tier 1 Git-History Audit Skill

**Description**: Create a skill that performs Tier 1
audit using git log, diff, and blame analysis to
identify areas of concern.

**Type**: Implementation
**Priority**: P0 (Critical)
**Estimate**: 8 points
**Dependencies**: TASK-004
**Linked Requirements**: FR-001, FR-008

**Acceptance Criteria**:

- [ ] Skill analyzes configurable commit range
  (default: current branch vs main)
- [ ] Outputs: churn hotspots, fix-on-fix patterns,
  large diffs, new file clusters
- [ ] Flags areas meeting Tier 2 escalation criteria
- [ ] Completes in < 30 seconds for 1000 commits
  (NFR-006)
- [ ] Output follows output contract format (TASK-001)
- [ ] Test: run on this repository's git history

---

#### TASK-006: Integrate Contracts into Existing Dispatch

**Description**: Update the plan-before-large-dispatch
rule and key agent dispatch patterns to include output
contracts.

**Type**: Integration
**Priority**: P1 (High)
**Estimate**: 3 points
**Dependencies**: TASK-001, TASK-002
**Linked Requirements**: FR-006

**Acceptance Criteria**:

- [ ] plan-before-large-dispatch template includes
  output contract column
- [ ] pensive:code-reviewer dispatch includes contract
- [ ] conserve:bloat-auditor dispatch includes contract
- [ ] At least 3 existing agent dispatches updated

---

#### TASK-007: Phase 1 Tests

**Description**: Test suite for output contracts,
validator, and tier escalation.

**Type**: Testing
**Priority**: P0 (Critical)
**Estimate**: 5 points
**Dependencies**: TASK-002, TASK-005
**Linked Requirements**: FR-006, FR-008

**Acceptance Criteria**:

- [ ] Unit tests for contract schema parsing
- [ ] Unit tests for validator (PASS/FAIL cases)
- [ ] Unit tests for escalation criteria matching
- [ ] Integration test: Tier 1 audit on test repo
- [ ] All tests pass in CI

---

### Phase 2: File-Based Communication + Tiered Audit (FR-001, FR-002, FR-007)

*The structural foundation.
Enables context isolation and detail preservation.*

---

#### TASK-008: Coordination Workspace Initialization

**Description**: Create skill module that initializes
`.coordination/` workspace with required structure.

**Type**: Implementation
**Priority**: P0 (Critical)
**Estimate**: 3 points
**Dependencies**: TASK-001
**Linked Requirements**: FR-002, FR-007

**Acceptance Criteria**:

- [ ] Creates `.coordination/agents/`, `handoffs/`
- [ ] Creates `tasks.json` with schema: array of
  `{id, agent, status, contract, findings_path,
  created_at, completed_at}`
- [ ] Idempotent: safe to call multiple times
- [ ] Adds `.coordination/` to `.gitignore`

---

#### TASK-009: Agent Findings File Format

**Description**: Define and document the structured
format for agent findings files.

**Type**: Implementation
**Priority**: P0 (Critical)
**Estimate**: 2 points
**Dependencies**: TASK-001
**Linked Requirements**: FR-002

**Acceptance Criteria**:

- [ ] Format defined: YAML frontmatter (agent, area,
  tier, evidence_count, validation_status) + Markdown
  body (summary, detailed findings, evidence refs)
- [ ] Documented as a skill module with examples
- [ ] Template file provided for agent prompts to
  reference

---

#### TASK-010: Selective Synthesis Skill

**Description**: Create a skill that reads only summary
sections from multiple findings files, then selectively
deep-dives based on severity or relevance.

**Type**: Implementation
**Priority**: P1 (High)
**Estimate**: 5 points
**Dependencies**: TASK-009
**Linked Requirements**: FR-002, NFR-001, NFR-002

**Acceptance Criteria**:

- [ ] Reads summary section (first N lines) from each
  findings file
- [ ] Identifies high-severity findings for deep-dive
- [ ] Synthesizes report referencing raw files for
  full detail
- [ ] Parent context usage for coordination < 20%
  (NFR-001)
- [ ] 100% of evidence-tagged findings accessible via
  raw files (NFR-002)

---

#### TASK-011: Workspace Archive and Cleanup

**Description**: Implement workspace lifecycle: archive
on success, preserve on failure.

**Type**: Implementation
**Priority**: P2 (Medium)
**Estimate**: 2 points
**Dependencies**: TASK-008
**Linked Requirements**: FR-007

**Acceptance Criteria**:

- [ ] Success: moves to `.coordination-archive/{ts}/`
- [ ] Failure: adds `_failure_reason.md`, preserves
  workspace
- [ ] Archive is gitignored

---

#### TASK-012: Tier 2 Targeted Area Audit Skill

**Description**: Create skill for Tier 2 sequential
per-area deep audit, consuming Tier 1 escalation
targets.

**Type**: Implementation
**Priority**: P1 (High)
**Estimate**: 8 points
**Dependencies**: TASK-005, TASK-008, TASK-009
**Linked Requirements**: FR-001

**Acceptance Criteria**:

- [ ] Reads Tier 1 escalation targets
- [ ] Audits each area sequentially (not parallel)
- [ ] Writes findings to `.coordination/agents/`
- [ ] Each area's findings follow output contract
- [ ] Passes contract validation

---

#### TASK-013: Tier 3 Gate Skill

**Description**: Create skill that gates Tier 3 full
codebase audit behind user confirmation.

**Type**: Implementation
**Priority**: P2 (Medium)
**Estimate**: 2 points
**Dependencies**: TASK-012
**Linked Requirements**: FR-001

**Acceptance Criteria**:

- [ ] Presents justification from Tier 2 findings
- [ ] Requires explicit user approval
- [ ] Recommends dedicated sessions over subagents
- [ ] Logs escalation decision

---

#### TASK-014: Phase 2 Tests

**Description**: Test suite for coordination workspace,
findings format, synthesis, and tiered audit flow.

**Type**: Testing
**Priority**: P0 (Critical)
**Estimate**: 5 points
**Dependencies**: TASK-010, TASK-012
**Linked Requirements**: FR-001, FR-002, FR-007

**Acceptance Criteria**:

- [ ] Unit tests for workspace init/archive/cleanup
- [ ] Unit tests for findings format parsing
- [ ] Integration test: multi-agent write + selective
  synthesis
- [ ] Integration test: Tier 1 -> Tier 2 escalation
  flow

---

### Phase 3: Auto-Role Assignment (FR-004)

*Builds on file patterns established in Phase 2.*

---

#### TASK-015: Area-Agent Config Format

**Description**: Define the format for area-agent
configuration files in `.claude/area-agents/`.

**Type**: Implementation
**Priority**: P1 (High)
**Estimate**: 2 points
**Dependencies**: None
**Linked Requirements**: FR-004

**Acceptance Criteria**:

- [ ] Format: YAML frontmatter (area_name, ownership
  globs, tags) + Markdown body (patterns, pitfalls,
  conventions, review focus)
- [ ] Documented with examples
- [ ] Generic fallback template defined

---

#### TASK-016: Create Initial Area-Agent Configs

**Description**: Write area-agent configs for the 5
largest codebase areas.

**Type**: Implementation
**Priority**: P1 (High)
**Estimate**: 5 points
**Dependencies**: TASK-015
**Linked Requirements**: FR-004

**Acceptance Criteria**:

- [ ] Configs for: plugins/abstract, plugins/egregore,
  plugins/conserve, plugins/imbue, plugins/sanctum
- [ ] Each config includes: ownership globs,
  architectural patterns, testing conventions,
  known pitfalls
- [ ] Verified by reviewing recent PRs in each area

---

#### TASK-017: Area-Agent Lookup Mechanism

**Description**: Create lookup function that matches
a file path to the correct area-agent config, with
fallback to generic template.

**Type**: Implementation
**Priority**: P1 (High)
**Estimate**: 3 points
**Dependencies**: TASK-015
**Linked Requirements**: FR-004

**Acceptance Criteria**:

- [ ] Given `plugins/egregore/agents/orchestrator.md`,
  returns `plugins-egregore.md` config
- [ ] Given `plugins/unknown/foo.md`, returns generic
  fallback
- [ ] Given files spanning 2 areas, returns both
  configs
- [ ] Unit tests for matching logic

---

#### TASK-018: Inject Area Config into Dispatch

**Description**: Update agent dispatch flow to
auto-load matching area-agent config into the agent's
prompt.

**Type**: Integration
**Priority**: P1 (High)
**Estimate**: 3 points
**Dependencies**: TASK-017
**Linked Requirements**: FR-004

**Acceptance Criteria**:

- [ ] Dispatch prompts for area-specific work include
  the matching area-agent context
- [ ] Context injection is optional (graceful no-op
  when no config exists)
- [ ] Integrated with at least 2 existing dispatch
  patterns (code review, audit)

---

#### TASK-019: Phase 3 Tests

**Description**: Test suite for area-agent registry.

**Type**: Testing
**Priority**: P1 (High)
**Estimate**: 3 points
**Dependencies**: TASK-017, TASK-018
**Linked Requirements**: FR-004

**Acceptance Criteria**:

- [ ] Unit tests for config format validation
- [ ] Unit tests for path-to-config matching
- [ ] Integration test: dispatch with area config
  injection

---

### Phase 4: Memory Tiers + Session Routing (FR-003, FR-005)

*The full system.
Extends existing conserve and continuation patterns.*

---

#### TASK-020: Agent Memory Directory Convention

**Description**: Define directory structure and
lifecycle for three-tier agent memory.

**Type**: Implementation
**Priority**: P2 (Medium)
**Estimate**: 3 points
**Dependencies**: None
**Linked Requirements**: FR-003

**Acceptance Criteria**:

- [ ] Hot tier: `{agent-dir}/memory.md`, 200-line
  hard limit documented
- [ ] Warm tier: `{agent-dir}/topics/*.md`
- [ ] Cold tier: `{agent-dir}/archive/*.md`
- [ ] Triage protocol documented as skill module

---

#### TASK-021: Session-End Triage Skill

**Description**: Create skill that runs at session end
to promote/demote content between memory tiers.

**Type**: Implementation
**Priority**: P2 (Medium)
**Estimate**: 5 points
**Dependencies**: TASK-020
**Linked Requirements**: FR-003

**Acceptance Criteria**:

- [ ] Identifies hot-tier content that is stale
- [ ] Promotes urgent warm-tier findings to hot
- [ ] Archives old hot-tier content to cold
- [ ] Enforces 200-line limit on hot tier

---

#### TASK-022: Session Routing Decision Skill

**Description**: Create skill that analyzes task scope
and recommends subagent vs dedicated session.

**Type**: Implementation
**Priority**: P2 (Medium)
**Estimate**: 3 points
**Dependencies**: TASK-008, TASK-017
**Linked Requirements**: FR-005

**Acceptance Criteria**:

- [ ] 1-3 files in 1 area: recommends subagent
- [ ] 4+ areas or codebase-wide: recommends dedicated
  sessions
- [ ] Integrates with plan-before-large-dispatch rule
- [ ] Decision is logged with reasoning

---

#### TASK-023: Phase 4 Tests

**Description**: Test suite for memory tiers and
session routing.

**Type**: Testing
**Priority**: P2 (Medium)
**Estimate**: 3 points
**Dependencies**: TASK-021, TASK-022
**Linked Requirements**: FR-003, FR-005

**Acceptance Criteria**:

- [ ] Unit tests for triage protocol
- [ ] Unit tests for routing decision logic
- [ ] Integration test: session-end triage on
  sample agent directory

## Dependency Graph

```
TASK-001 (Contract Schema)
    ├──▶ TASK-002 (Contract Validator)
    │       ├──▶ TASK-003 (Retry Mechanism)
    │       ├──▶ TASK-006 (Integrate into Dispatch)
    │       └──▶ TASK-007 (Phase 1 Tests) ◀── TASK-005
    ├──▶ TASK-008 (Workspace Init)
    │       ├──▶ TASK-011 (Archive/Cleanup)
    │       ├──▶ TASK-012 (Tier 2 Audit) ◀── TASK-005
    │       └──▶ TASK-022 (Session Router) ◀── TASK-017
    └──▶ TASK-009 (Findings Format)
            ├──▶ TASK-010 (Selective Synthesis)
            └──▶ TASK-014 (Phase 2 Tests) ◀── TASK-012

TASK-004 (Escalation Criteria)
    └──▶ TASK-005 (Tier 1 Audit)
            └──▶ TASK-012 (Tier 2 Audit)
                    └──▶ TASK-013 (Tier 3 Gate)

TASK-015 (Area Config Format)
    ├──▶ TASK-016 (Initial Configs)
    ├──▶ TASK-017 (Lookup Mechanism)
    │       └──▶ TASK-018 (Inject into Dispatch)
    └──▶ TASK-019 (Phase 3 Tests)

TASK-020 (Memory Convention)
    └──▶ TASK-021 (Triage Skill)
            └──▶ TASK-023 (Phase 4 Tests)
```

**Critical Path**: TASK-001 -> TASK-002 -> TASK-007
(Phase 1 gate) -> TASK-008 + TASK-009 -> TASK-012 ->
TASK-014 (Phase 2 gate)

## Sprint Schedule

### Sprint 1: Output Contracts + Escalation (Phase 1)

**Goal**: Agents cannot submit work without evidence.
Audit scope defaults to git-history-first.

**Tasks (29 points)**:

- TASK-001: Contract Schema (3)
- TASK-002: Contract Validator (5)
- TASK-003: Retry Mechanism (3)
- TASK-004: Escalation Criteria (2)
- TASK-005: Tier 1 Audit Skill (8)
- TASK-006: Integrate Contracts (3)
- TASK-007: Phase 1 Tests (5)

**Deliverable**: Output contract validator working,
Tier 1 audit functional, escalation criteria defined.

**Risks**:

- Existing agent dispatch prompts may need significant
  rework to embed contracts
  (mitigation: start with 3 key dispatches, expand
  iteratively)

---

### Sprint 2: File-Based Communication (Phase 2)

**Goal**: Agents write to files, parent reads
selectively, detail preserved.

**Tasks (27 points)**:

- TASK-008: Workspace Init (3)
- TASK-009: Findings Format (2)
- TASK-010: Selective Synthesis (5)
- TASK-011: Archive/Cleanup (2)
- TASK-012: Tier 2 Audit (8)
- TASK-013: Tier 3 Gate (2)
- TASK-014: Phase 2 Tests (5)

**Deliverable**: Full tiered audit flow (1->2->3)
with file-based coordination.

**Risks**:

- Selective synthesis may still miss important
  findings
  (mitigation: always link to raw files, user can
  inspect directly)

---

### Sprint 3: Auto-Role Assignment (Phase 3)

**Goal**: Agents auto-load area-specific context.

**Tasks (16 points)**:

- TASK-015: Config Format (2)
- TASK-016: Initial Configs (5)
- TASK-017: Lookup Mechanism (3)
- TASK-018: Inject into Dispatch (3)
- TASK-019: Phase 3 Tests (3)

**Deliverable**: 5 codebase areas with specialist
agent configs, auto-loaded on dispatch.

**Risks**:

- Area configs may become stale as code evolves
  (mitigation: include "last reviewed" date, flag
  stale configs in audits)

---

### Sprint 4: Memory + Session Routing (Phase 4)

**Goal**: Long-running agents manage memory
deliberately. Complex work routes to dedicated
sessions.

**Tasks (14 points)**:

- TASK-020: Memory Convention (3)
- TASK-021: Triage Skill (5)
- TASK-022: Session Router (3)
- TASK-023: Phase 4 Tests (3)

**Deliverable**: Three-tier memory working for
egregore orchestrator, session routing integrated.

**Risks**:

- 200-line hot-tier limit may be too restrictive for
  some agents
  (mitigation: configurable per-agent, 200 is default)

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Contract validation too strict, causes excessive retries | High | Medium | Configurable strictness levels; start permissive, tighten over time |
| File-based coordination adds latency vs in-context | Medium | Low | File I/O is fast; the bottleneck is LLM inference, not disk |
| Area-agent configs become stale | Medium | High | Include review dates; flag stale configs during audits |
| Tier 1 audit misses issues that git history doesn't reveal | Medium | Medium | Tier 1 is a filter, not a gate; users can always request Tier 2+ |
| Agent Teams API changes break session routing | Low | Medium | Session routing is a recommendation, not enforcement; tmux fallback always works |
| Memory triage skill makes wrong promote/demote decisions | Medium | Medium | Hot tier is append-only during session; triage only runs at session end |

## Success Metrics

- [ ] Output contract validator catches > 80% of
  incomplete agent outputs on first pass
- [ ] Tier 1 audit completes in < 30 seconds for
  1000-commit range
- [ ] Parent context usage for coordination < 20%
  measured across 5 multi-agent workflows
- [ ] 5+ area-agent configs created and actively used
- [ ] Zero evidence-tagged findings lost in synthesis
  (verified by diff between raw files and report)
- [ ] Complex audits (4+ areas) default to sequential
  execution, not parallel subagent blast

## Timeline

| Sprint | Focus | Deliverable | Points |
|--------|-------|-------------|--------|
| 1 | Output Contracts + Escalation | Evidence gates, Tier 1 audit | 29 |
| 2 | File-Based Communication | Coordination workspace, Tier 2/3 | 27 |
| 3 | Auto-Role Assignment | Area-agent configs + lookup | 16 |
| 4 | Memory + Session Routing | Three-tier memory, routing | 14 |

Total: 86 story points across 23 tasks in 4 sprints.

## Next Steps

1. Create new branch `agent-coordination` from master
2. Start Sprint 1 with TASK-001 (Contract Schema)
3. Each sprint is independently mergeable to master
4. Review and adjust after Sprint 1 based on real-world
   results
