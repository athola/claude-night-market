---
name: mission-orchestrator
description: Orchestrates full project lifecycle by auto-detecting state and routing to the correct phase. Use when starting or resuming a project mid-workflow.
alwaysApply: false
category: workflow-orchestration
tags:
- mission
- orchestrator
- lifecycle
- full-cycle
- automation
dependencies:
- attune:project-brainstorming
- attune:project-specification
- attune:project-planning
- attune:project-execution
- attune:war-room-checkpoint
- attune:war-room
- leyline:risk-classification
- leyline:damage-control
- leyline:additive-bias-defense
tools: []
provides:
  workflow:
  - mission-lifecycle
  - state-detection
  - phase-routing
  - session-recovery
usage_patterns:
- full-cycle-development
- mission-resume
- phase-routing
complexity: advanced
estimated_tokens: 1700
role: entrypoint
---

# Mission Orchestrator

## Overview

A router. Detect which phase the project is in, then call that phase's
skill with `Skill()`. Each phase skill runs its own workflow. The
orchestrator only picks the type, sequences the phases, checks each
phase's artifact, and records state so a later session can resume.

## When To Use

- Starting a new project from scratch (full lifecycle)
- Resuming an interrupted project workflow
- Running a focused tactical implementation from existing specs
- Quick-fixing from an existing implementation plan
- Auditing or dogfooding existing software (`review`)

## When NOT To Use

- Running a single phase directly (use `/attune:brainstorm`,
  `/attune:specify`, `/attune:blueprint`, `/attune:execute`)
- Non-project work such as debugging or research

## 1. Detect the Mission Type

Check the rows top to bottom and take the first match. `--type` and
`--phases` override detection.

| Type | Phases | Selected when |
|------|--------|---------------|
| `review` | scope, investigate, verify, report | The request asks to review, audit, dogfood, or assess existing software |
| `quickfix` | execute | `docs/implementation-plan.md` exists |
| `tactical` | plan, execute | `docs/specification.md` exists |
| `standard` | specify, plan, execute | `docs/project-brief.md` exists |
| `full` | brainstorm, specify, plan, execute | No artifact exists |

`review` is selected from request intent and is checked first, because
a tree of build artifacts looks the same whether the ask is "ship this"
or "audit this". When the wording is ambiguous, show both candidates
and ask. An artifact counts only when it is non-empty and has no
frontmatter `status` of `draft` or `in-progress`. The same names at the
repository root also count.

State the detected type, the reason, and the phases, then confirm
unless `--auto` is set. A `--phases` list must keep phase order, and a
mission either builds or reviews: the two phase sets do not mix.

## 2. Route Each Phase

| Phase | Skill Invoked | Artifact Produced |
|-------|--------------|-------------------|
| brainstorm | `Skill(attune:project-brainstorming)` | `docs/project-brief.md` |
| specify | `Skill(attune:project-specification)` | `docs/specification.md` |
| plan | `Skill(attune:project-planning)` | `docs/implementation-plan.md` |
| execute | `Skill(attune:project-execution)` | Code, tests, `.attune/execution-state.json` |
| scope | `Skill(pensive:tiered-audit)` | Tier selection and bounded scope |
| investigate | `Skill(imbue:feature-review)` plus the `pensive:*` domain lenses | Raw findings |
| verify | `Skill(imbue:proof-of-work)` | Evidence references per finding |
| report | `Skill(imbue:structured-output)` | `reports/<topic>-<YYYY-MM-DD>.md` |

For each phase in the sequence:

1. Confirm the prior phase's artifact exists. If it does not, stop and
   report the gap. Do not skip ahead.
2. Invoke the phase skill. Never re-implement its logic here.
3. Confirm the phase's artifact now exists. A missing artifact is a
   failed phase.
4. Update `.attune/mission-state.json`.
5. Checkpoint with the user (continue, pause, abort, re-run) unless
   `--auto` is set or a directive override applies.

After brainstorm and specify, open a GitHub issue for each "Out of
Scope" item that has no issue reference yet, and add the number to the
artifact. `--no-auto-issues` skips this.

On a failed phase, use `Skill(leyline:damage-control)` to classify it.
Retry a transient failure up to twice. Otherwise give the user the
choice to retry, skip (when safe), or abort.

## 3. Gate Plan to Execute

Before the execute phase, challenge the plan:

1. Run `Skill(leyline:additive-bias-defense)` over each plan section,
   then walk the user through the sections with the findings.
2. Send revisions back to `Skill(attune:project-planning)`. After three
   rounds, the user must approve as-is, abort, or restart from the
   specification.
3. Run `Skill(attune:war-room)` on the approved plan. Approval is
   required. Concerns or a rejection start another revision round.
4. Classify every task with `Skill(leyline:risk-classification)` and
   record the tier counts. RED and CRITICAL tasks go through
   `Skill(attune:war-room-checkpoint)` when execution reaches them.

A `review` mission never enters the war-room gate, because it has no
plan-to-execute transition.

## Delegation During a Mission

Missions delegate execution by default.
`Skill(conjure:delegation-core)` governs the decision, and its default
posture is on: a phase that reaches execution work hands it to an
external CLI without waiting to be asked.

| Phase | Delegates | Why |
|-------|-----------|-----|
| brainstorm | No | Reasoning; the Keep Local clause holds |
| specify | No | Reasoning |
| plan | No | Reasoning |
| execute | Yes, per task | Task execution is the eligible half |
| scope, investigate, verify, report | Report and verify only | Findings are judgment; bulk extraction is not |

The split follows conjure's own line: delegate execution, retain
reasoning.
A mission phase that is entirely judgment stays local and does not
consult the delegator at all.

Two outcomes need handling rather than reporting:

- `fallback_reason` is `providers_exhausted`: no CLI answered. Say which
  were tried, then hand the task to a subagent on the session's model.
  `Skill(attune:project-execution)` module `subagent-fallback.md`
  carries the rule: which agent each phase uses, how to keep the model
  and the branch, and when inline work is allowed. This is the ordinary
  path on a machine with no CLI installed and it does not fail the phase.
  Take the same path when conjure is not installed and its skill cannot
  load.
- `fallback_reason` is `delegation_disabled`: the operator declined.
  Do the task locally, because a subagent is still a delegation, and do
  not offer to re-enable it.

To run a whole mission without external models, set
`CONJURE_DELEGATION=off` before invoking it.

## User Directive Overrides

Read the command arguments and free text at mission start for trust
signals. "ignore scope guard", "ultrathink", "stop asking", and
"be autonomous" lower the checkpoint load. "supervised" and "ask before
each step" raise it. When several match, the most restrictive wins.
Acknowledge a matched directive once, record it, and stop asking for
the checkpoints it waives.

No directive waives the safety floor: pre-commit hooks, proof-of-work
evidence, confirmation before destructive operations, and confirmation
before external-facing actions.

## Mission State

`.attune/mission-state.json` is the resume contract. `/attune:mission`
and `Skill(attune:skill-library-mission)` both write it. Keep these
field names:

| Field | Holds |
|-------|-------|
| `mission_id` | A stable id such as `mission-YYYYMMDD-HHMMSS` |
| `type` | The mission type, or `custom` for a `--phases` list |
| `phases` | The ordered phase list, each with a status and artifact path |
| `current_phase` | The phase to run next |
| `decisions` | Each checkpoint choice, with a timestamp |
| `directive_overrides` | Each matched directive and what it waived |
| `risk_summary` | Task counts per risk tier, written after the plan gate |

To resume (`--resume`), load the file, confirm each recorded artifact
still exists, and continue from `current_phase`. `--resume --force`
resets a failed phase and retries it. With no state file, start fresh.

## Related Commands

- `/attune:mission` invokes this skill
- `/attune:mission --resume` resumes from saved state
- `/attune:mission --type tactical` overrides the detected type

## Exit Criteria

- [ ] Every phase in the mission type has status `completed` in
  `.attune/mission-state.json`
- [ ] The artifact listed for each completed phase exists on disk
- [ ] A build mission's state records a risk summary with tier counts
  across all tasks
- [ ] A build mission reached execute only after a war-room approval,
  recorded in `decisions`
- [ ] A review mission wrote `reports/<topic>-<YYYY-MM-DD>.md`
- [ ] Execute-phase work either delegated or held back by a named Keep
  Local clause, never skipped for want of a delegation decision
- [ ] Any `providers_exhausted` result completed by a session-model
  subagent, or inline when the harness has no subagent tool, and
  reported with the providers it tried
- [ ] Any failed phase is recorded with its recovery outcome, and none
  is left unresolved
