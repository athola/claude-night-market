# Agent Coordination Architecture -- Specification v0.1.0

**Author**: Alex T
**Date**: 2026-03-17
**Status**: Draft

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-03-17 | Alex T | Initial draft from deep research |

## Overview

**Purpose**: Eliminate quality degradation in multi-agent
workflows by replacing hub-and-spoke coordination with
file-based communication, tiered audit scoping, and
evidence-gated output contracts.

**Scope**:

- **IN**: Tiered audit strategy (S1), file-based
  inter-agent communication (S2), three-tier agent
  memory (S3), auto-role assignment per codebase area
  (S4), dedicated session routing (S5), output contracts
  and evidence gates (S6)
- **OUT**: Custom vector database infrastructure,
  Agent Teams API integration (experimental/upstream),
  cross-repository agent coordination, real-time agent
  streaming protocols

**Stakeholders**:

- **Plugin developers**: Need agents that produce
  reliable, detailed output when reviewing their code
- **Framework maintainer (Alex)**: Needs coordination
  patterns that scale without manual prompt engineering
- **Egregore orchestrator**: Needs file-based handoffs
  between pipeline stages

## Functional Requirements

### FR-001: Tiered Audit Scoping

**Description**: All codebase audit workflows MUST
default to a three-tier escalation model.
Tier 1 (git history) runs first.
Tier 2 (targeted area) runs only for areas flagged
by Tier 1.
Tier 3 (full codebase) requires explicit user approval.

**Acceptance Criteria**:

- [ ] Given an audit request without scope qualifiers,
  when the audit skill is invoked, then it begins with
  Tier 1 git-history analysis only
- [ ] Given Tier 1 results identifying 3 flagged areas,
  when escalating to Tier 2, then each area is audited
  sequentially (not in parallel) with full findings
  preserved per area
- [ ] Given a request for Tier 3 full-codebase audit,
  when the user has not explicitly approved escalation,
  then the system warns and requests confirmation before
  proceeding
- [ ] Given a Tier 1 audit of a repository with 500+
  commits, when running the audit, then only the
  relevant commit range is analyzed (not full history)

**Priority**: High
**Dependencies**: FR-006 (output contracts apply to
each tier's output)
**Estimated Effort**: M

---

### FR-002: File-Based Agent Communication

**Description**: Agents coordinating on shared work
MUST write findings to structured files in a
`.coordination/` workspace directory rather than
returning all results through the parent agent's
context window.

**Acceptance Criteria**:

- [ ] Given a multi-agent workflow with 3+ agents,
  when agents complete their work, then each agent's
  full findings exist as a separate file under
  `.coordination/agents/{agent-name}.findings.md`
- [ ] Given an agent writing findings, when the file
  is written, then it follows the structured findings
  format (metadata header, summary, detailed findings,
  evidence references)
- [ ] Given completed agent findings files, when the
  parent synthesizes results, then it reads only the
  summary sections first and deep-dives selectively
  into detailed findings as needed
- [ ] Given a coordination workspace, when the user
  inspects `.coordination/`, then they can read any
  agent's full unfiltered findings directly
- [ ] Given agent A discovering something relevant to
  agent B's scope, when agent A writes a handoff,
  then it creates `.coordination/handoffs/a-to-b.md`
  with the discovery context

**Priority**: High
**Dependencies**: None (foundational for S3-S5)
**Estimated Effort**: L

---

### FR-003: Three-Tier Agent Memory

**Description**: Long-running or frequently-invoked
agents MUST use a three-tier memory system (hot/warm/
cold) instead of relying on context window or
unbounded file accumulation.

**Acceptance Criteria**:

- [ ] Given an agent with a hot-tier memory file,
  when the file exceeds 200 lines, then the agent
  triages content by promoting critical items and
  archiving stale items to warm tier
- [ ] Given an agent starting a new session, when it
  loads context, then it loads only its hot-tier
  memory.md file automatically (warm/cold loaded
  on demand)
- [ ] Given an agent completing a session, when it
  saves state, then it runs a triage protocol:
  promote urgent findings to hot, move enduring
  work to warm, archive historical to cold
- [ ] Given two agents working on related areas, when
  agent A updates its warm-tier research file, then
  agent B can read that file on demand (but it is
  not auto-loaded into B's context)

**Priority**: Medium
**Dependencies**: FR-002 (file-based communication
provides the transport layer)
**Estimated Effort**: L

---

### FR-004: Auto-Role Assignment

**Description**: When work targets a specific codebase
area, the system MUST automatically load the matching
area-agent configuration, providing specialist context
without manual prompt engineering.

**Acceptance Criteria**:

- [ ] Given a task targeting `plugins/egregore/`,
  when an agent is dispatched, then it automatically
  loads `.claude/area-agents/plugins-egregore.md`
  containing area-specific patterns, pitfalls, and
  review focus
- [ ] Given a task spanning two areas
  (`plugins/abstract/` and `plugins/conserve/`),
  when agents are dispatched, then each area gets
  its own agent with its own area configuration
- [ ] Given a new plugin is added to the repository,
  when no area-agent config exists for it, then the
  system falls back to a generic plugin-area template
  with instructions to create a specific config
- [ ] Given an area-agent config file, when it is
  loaded, then it contains: ownership glob patterns,
  architectural decisions, testing conventions,
  known pitfalls, and preferred review tools

**Priority**: Medium
**Dependencies**: None (uses existing `.claude/agents/`
infrastructure)
**Estimated Effort**: M

---

### FR-005: Session Routing Strategy

**Description**: The system MUST route multi-area work
to the appropriate execution strategy based on
complexity: subagents for simple focused work, dedicated
sessions for complex multi-area work.

**Acceptance Criteria**:

- [ ] Given a task touching 1-3 files in a single area,
  when dispatching work, then a standard subagent is
  used with a tight scope prompt
- [ ] Given a task touching 4+ areas or requiring
  codebase-wide analysis, when dispatching work, then
  the system recommends dedicated sessions (tmux or
  Agent Teams) over subagents
- [ ] Given a dedicated-session workflow, when sessions
  coordinate, then they use `.coordination/` files
  (FR-002) rather than parent-mediated message passing
- [ ] Given a codebase-wide review, when routing to
  sessions, then areas are processed sequentially
  (one area per session completes before the next
  begins) with results accumulating in files

**Priority**: Low
**Dependencies**: FR-002 (file-based communication),
FR-004 (area-agent configs)
**Estimated Effort**: M

---

### FR-006: Output Contracts and Evidence Gates

**Description**: Every agent dispatch MUST include an
output contract specifying required sections, minimum
evidence count, and expected artifacts.
Agent output MUST be validated against the contract
before acceptance.

**Acceptance Criteria**:

- [ ] Given an agent dispatch prompt, when the prompt
  is constructed, then it includes an explicit output
  contract block listing: required sections, minimum
  number of evidence citations, and expected artifact
  files
- [ ] Given an agent returning results, when the output
  is received, then a validator checks: all required
  sections present, evidence count meets minimum,
  all `[E1]`/`[E2]` tags reference real commands or
  file reads
- [ ] Given an agent output that fails validation,
  when the validator detects missing sections or
  insufficient evidence, then the agent is retried
  with specific feedback about what is missing (not
  a wholesale re-dispatch)
- [ ] Given an agent output with 0 evidence citations,
  when validation runs, then the output is rejected
  unconditionally (no evidence = no acceptance)
- [ ] Given a validated agent output, when the parent
  synthesizes it, then the validation status
  (PASS/FAIL + detail) is included in the synthesis

**Priority**: High
**Dependencies**: None
**Estimated Effort**: M

---

### FR-007: Coordination Workspace Lifecycle

**Description**: The `.coordination/` workspace
directory MUST be created at workflow start, populated
during execution, and cleaned up after synthesis.

**Acceptance Criteria**:

- [ ] Given a multi-agent workflow starting, when the
  coordinator initializes, then it creates
  `.coordination/` with subdirectories `agents/`,
  `handoffs/`, and a `tasks.json` manifest
- [ ] Given a workflow completing successfully, when
  all findings are synthesized, then the coordinator
  archives `.coordination/` to
  `.coordination-archive/{timestamp}/` and cleans
  the working directory
- [ ] Given a workflow failing mid-execution, when the
  coordinator detects failure, then `.coordination/`
  is preserved for debugging with a
  `_failure_reason.md` file added
- [ ] Given `.coordination/tasks.json`, when any agent
  reads it, then it contains: task ID, assigned agent,
  status (pending/active/done/failed), output contract
  reference, and file paths for findings

**Priority**: Medium
**Dependencies**: FR-002, FR-006
**Estimated Effort**: S

---

### FR-008: Audit Tier Escalation Protocol

**Description**: Escalation between audit tiers MUST
follow a documented protocol with explicit criteria
for when escalation is warranted.

**Acceptance Criteria**:

- [ ] Given Tier 1 git-history results, when 3+ files
  in the same module show repeated churn or
  suspicious patterns, then that module is flagged
  for Tier 2 escalation
- [ ] Given Tier 1 results with no flags, when the
  audit completes, then the workflow terminates
  without escalation (no Tier 2 by default)
- [ ] Given Tier 2 findings for a specific module,
  when the findings indicate systemic issues
  (architectural, cross-cutting), then Tier 3 is
  recommended with a justification summary
- [ ] Given escalation to any tier, when the
  escalation occurs, then a log entry records: which
  tier, why escalated, which areas targeted, and
  the triggering evidence from the previous tier

**Priority**: High
**Dependencies**: FR-001
**Estimated Effort**: S

## Non-Functional Requirements

### NFR-001: Context Efficiency

**Requirement**: Multi-agent coordination overhead MUST
NOT exceed 20% of the parent agent's context window.

**Measurement**:

- Metric: Token count of coordination-related context
  (task manifests, summaries, routing decisions) vs
  total parent context
- Target: < 20% of parent context used for coordination
- Tool: Token counting via `wc -w` on coordination
  artifacts loaded into parent context

**Priority**: Critical

---

### NFR-002: Finding Preservation

**Requirement**: No agent finding with evidence
citations SHALL be lost during synthesis.
The user MUST be able to access 100% of raw agent
output.

**Measurement**:

- Metric: Count of evidence-tagged findings in raw
  agent output vs count in synthesized report +
  accessible files
- Target: 100% preservation (lossy synthesis is
  acceptable only if raw files are accessible)
- Tool: Diff between raw findings files and
  synthesized report

**Priority**: Critical

---

### NFR-003: Incremental Deployability

**Requirement**: Each solution area (S1-S6) MUST be
independently deployable without requiring the others.

**Measurement**:

- Metric: Each FR group can be implemented, tested,
  and merged as a standalone PR
- Target: Zero cross-FR-group dependencies for basic
  functionality
- Tool: PR review checklist

**Priority**: High

---

### NFR-004: Python 3.9 Compatibility

**Requirement**: All Python tooling MUST run on
Python 3.9+.

**Measurement**:

- Metric: CI passes on Python 3.9
- Target: Zero 3.10+ syntax or stdlib features
- Tool: `ruff` with `target-version = "py39"`

**Priority**: Critical

---

### NFR-005: No New Infrastructure

**Requirement**: Solutions MUST use file-system-based
coordination.
No databases, message queues, vector stores, or
external services.

**Measurement**:

- Metric: Zero new runtime dependencies beyond
  stdlib + existing project deps
- Target: All coordination via `.md`, `.json`, and
  `.txt` files
- Tool: Dependency audit

**Priority**: High

---

### NFR-006: Audit Tier 1 Performance

**Requirement**: Tier 1 git-history audit MUST complete
in under 30 seconds for repositories with up to 1000
commits in the analyzed range.

**Measurement**:

- Metric: Wall-clock time from audit invocation to
  Tier 1 findings file written
- Target: < 30 seconds for 1000-commit range
- Tool: `time` command wrapper

**Priority**: Medium

## Technical Constraints

### Technology Stack

- **Language**: Python 3.9+ for tooling, Markdown for
  agent configs and findings
- **Plugin model**: night-market plugin structure
  (skills, agents, hooks, commands)
- **Git**: All audit tier 1 analysis uses git CLI
  (`git log`, `git diff`, `git blame`)
- **File format**: JSON for structured data
  (`tasks.json`), Markdown for prose
  (findings, handoffs, configs)
- **Existing infrastructure**: Builds on imbue
  proof-of-work, conserve context-optimization,
  and existing `.claude/agents/` patterns

### Integration Points

- **imbue:proof-of-work**: Output contracts extend the
  existing evidence-tag pattern (`[E1]`, `[E2]`)
- **imbue:structured-output**: Findings format aligns
  with existing structured deliverable templates
- **conserve:subagent-coordination**: Tiered routing
  extends the existing subagent coordination module
- **conserve:clear-context**: Session routing integrates
  with existing continuation-agent pattern
- **plan-before-large-dispatch rule**: Tier 3 audits
  and 4+ agent dispatches trigger existing plan-mode
  requirement
- **egregore orchestrator**: Pipeline stages can use
  file-based coordination for inter-step handoffs

### Data Requirements

- `.coordination/tasks.json` schema: array of task
  objects with `id`, `agent`, `status`, `contract`,
  `findings_path`, `created_at`, `completed_at`
- Agent findings format: YAML frontmatter (agent name,
  area, tier, evidence count, validation status) +
  Markdown body
- Area-agent config format: YAML frontmatter (area
  name, ownership globs, tags) + Markdown body with
  patterns, pitfalls, conventions

## Out of Scope

### Out of Scope (v1.0)

- **Agent Teams API integration**: Experimental upstream
  feature; manual tmux approach works today
- **Vector embedding memory**: Pure file-based approach
  for v1.0; vector augmentation deferred to v2.0
- **Cross-repository coordination**: Single-repo focus
- **Real-time agent streaming**: Agents write completed
  findings; no partial/streaming updates
- **Automatic area-agent config generation**: v1.0
  requires manual creation; auto-generation from
  codebase analysis deferred
- **Custom agent models per area**: All agents use the
  same model; per-area model selection deferred

**Rationale**: Each exclusion reduces implementation
complexity while the core value (quality preservation,
context isolation) is delivered by the in-scope items.
These can be added incrementally in future versions.

## Dependencies

- **Existing plugins**: imbue (proof-of-work, structured
  output), conserve (context optimization, continuation
  agents), sanctum (git workflows)
- **Git CLI**: Required for Tier 1 audit analysis
- **Claude Code**: Subagent dispatch via Task tool,
  agent definitions via `.claude/agents/`
- **File system**: All coordination state is file-based

## Acceptance Testing Strategy

### Per-FR Testing

Each functional requirement is tested through:

1. **Unit tests**: Python tests for any coordination
   tooling (task manifest parsing, contract validation,
   findings format validation)
2. **Integration tests**: End-to-end workflow tests that
   create `.coordination/` workspaces, write mock
   findings, and verify synthesis
3. **Agent tests**: Manual or scripted agent invocations
   that verify output contracts are enforced

### Scenario Tests

| Scenario | Tests |
|----------|-------|
| Simple 2-agent review | Subagent routing, findings files created, parent reads selectively |
| 5-area audit | Tier 1 runs first, escalation protocol followed, dedicated sessions recommended |
| Agent returns incomplete output | Validator catches missing sections, retry with specific feedback |
| Coordination workspace cleanup | Archive created on success, preserved on failure |
| Area-agent config loading | Correct config loaded for target area, fallback for unknown areas |

## Success Criteria

- [ ] Multi-agent audit reports contain the same
  evidence count as the sum of individual agent
  findings (no evidence dropped in synthesis)
- [ ] Subagent outputs pass evidence-gate validation
  on first attempt > 80% of the time
- [ ] Default audit path is git-history-first with
  zero user intervention for Tier 1
- [ ] Parent agent context usage for coordination
  overhead < 20% of total context
- [ ] At least 5 codebase areas have area-agent
  configurations
- [ ] Complex multi-area work routes to dedicated
  sessions when 4+ areas are involved

## Glossary

| Term | Definition |
|------|------------|
| Context rot | Measurable degradation in LLM output quality as input context length increases |
| Hub-and-spoke | Coordination pattern where all agent communication flows through a central parent |
| Output contract | Explicit specification of required sections, evidence count, and artifacts an agent must produce |
| Evidence gate | Validation check that rejects agent output lacking evidence citations |
| Area-agent | A specialist agent configuration scoped to a specific codebase directory |
| Hot tier | Always-loaded agent memory (200-line limit) |
| Warm tier | On-demand topic files retrieved by agent choice |
| Cold tier | Searchable archive accessed only for historical investigation |
| Findings file | Structured Markdown file containing an agent's complete analysis output |
| Coordination workspace | `.coordination/` directory used for inter-agent file-based communication |

## References

- [Project Brief](project-brief.md)
- [Context Rot Research](https://www.morphllm.com/context-rot)
- [Multi-Agent Memory Architecture](https://arxiv.org/html/2603.10062)
- [RepoAudit: Repository-Level Code Auditing](https://arxiv.org/html/2501.18160v1)
- [Claude Code Sub-Agent Best Practices](https://claudefa.st/blog/guide/agents/sub-agent-best-practices)
- [Existing: imbue proof-of-work](../../plugins/imbue/skills/proof-of-work/SKILL.md)
- [Existing: conserve subagent coordination](../../plugins/conserve/skills/context-optimization/modules/subagent-coordination.md)
- [Existing: plan-before-large-dispatch rule](../../.claude/rules/plan-before-large-dispatch.md)
- [Existing: agent boundaries guide](../guides/agent-boundaries.md)
