---
description: Assess the codebase against spec, plan, and tasks, then append unbuilt work as new convergence tasks
argument-hint: "Path to spec/plan/tasks artifacts"
---

Before proceeding, load the `speckit-orchestrator` skill for workflow
coordination. Consider loading complementary skills like
`superpowers:executing-plans` and `superpowers:verification-before-completion`
for gap assessment.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Close the gap between what a feature's specification, plan, and tasks call
for and what the codebase currently implements. Read `spec.md`, `plan.md`,
and `tasks.md` as the **sole source of intent** (with the constitution as
governing constraints), assess the current state of the code, determine
which requirements, acceptance criteria, plan decisions, and tasks are
unmet, incomplete, or only partially satisfied, and **append each piece of
remaining work as a new, traceable task** at the bottom of `tasks.md` so
`/speckit-implement` can complete it.

This command MUST run only after `/speckit-implement` has run on the current
`tasks.md`, and after `/speckit-tasks` has produced a complete `tasks.md`.

This is **not** a diff tool and does **not** track changes. It assesses the
present state of the code relative to the feature's artifacts: no git, no
branch comparison, no history.

## Operating Constraints

**APPEND-ONLY, NEVER REWRITE**: The command's **only** write is appending a
new `## Phase N: Convergence` section to `tasks.md`. It MUST NOT:

- modify `spec.md` or `plan.md` in any way;
- rewrite, renumber, reorder, or delete any existing task, including tasks
  from a prior Convergence phase;
- modify, create, or delete application code. Completing the appended tasks
  is the job of `/speckit-implement`.

When the codebase already satisfies everything, the command MUST leave
`tasks.md` **byte-for-byte unchanged** (no empty Convergence header) and
report a clean result.

**Constitution Authority**: The project constitution
(`.specify/memory/constitution.md`) is **non-negotiable**. Code that
violates a MUST principle is the highest-severity finding and produces a
corresponding remediation task. If the constitution is an unfilled template,
skip constitution checks gracefully rather than failing.

## Execution Steps

### 1. Initialize Convergence Context

Run
`.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`
once from repo root and parse JSON for FEATURE_DIR and AVAILABLE_DOCS.
Derive absolute paths:

- SPEC = FEATURE_DIR/spec.md
- PLAN = FEATURE_DIR/plan.md
- TASKS = FEATURE_DIR/tasks.md
- CONSTITUTION = `.specify/memory/constitution.md` (if present)

If `spec.md`, `plan.md`, or `tasks.md` is missing, STOP with a clear,
actionable message naming the prerequisite command to run (`/speckit-specify`
for a missing spec, `/speckit-plan` for a missing plan, `/speckit-tasks` for
missing tasks). Do not produce partial output.

For single quotes in args like "I'm Groot", use escape syntax: e.g
'I'\''m Groot' (or double-quote if possible: "I'm Groot").

### 2. Load Artifacts (Progressive Disclosure)

Load only the minimal necessary context from each artifact:

**From spec.md:**

- Functional Requirements (FR-###)
- Success Criteria (SC-###) requiring buildable work; exclude post-launch
  outcome metrics and business KPIs
- User Stories and their Acceptance Scenarios
- Edge Cases (if present)

**From plan.md:**

- Architecture and stack choices and technical decisions
- Data Model references
- Phases and named touch-points (files and components the plan says will be
  created or edited)

**From tasks.md:**

- Existing task IDs, descriptions, and phase grouping
- Tasks already marked complete `[X]` versus incomplete `[ ]`
- Any prior `## Phase N: Convergence` section (do not duplicate its work)

**From constitution** (`.specify/memory/constitution.md`, when it holds real
principles rather than an unfilled template):

- MUST principles to check the codebase against

### 3. Assess the Current Codebase

For each requirement, acceptance criterion, plan touch-point, and incomplete
task, determine the code's present state:

- **Met**: code satisfies the requirement or task.
- **Partial**: code addresses part but leaves a gap (happy path without the
  edge case, endpoint without its error path).
- **Unmet**: no code addresses it.

Read only the files the plan and tasks reference plus obviously related
sources; do not enumerate the entire repository. Infer state from what the
code does today, not from git history.

### 4. Detect Constitution Violations

For each MUST principle in the constitution, scan the implemented code for
violations. A violation is the highest-severity finding and MUST produce a
remediation task in the next step.

### 5. Append Convergence Tasks (the only write)

If there are no unmet, partial, or violating items, leave `tasks.md`
byte-for-byte unchanged and report a clean result (step 6).

Otherwise append one new section at the bottom of `tasks.md`:

```markdown
## Phase N: Convergence

Appended by `/speckit-converge` on review of the current codebase against
spec/plan/tasks. Complete with `/speckit-implement`.

- [ ] T-NNN: <traceable task> <!-- gap: <requirement or SC or plan-point> -->
- [ ] T-NNN: <traceable task> <!-- gap: <requirement or SC or plan-point> -->
```

Rules for the appended section:

- `N` is the next phase number after the highest existing phase (or after
  the last Convergence phase if one already exists; never reuse a number).
- Each task is traceable: include a comment naming the spec requirement,
  success criterion, or plan touch-point it closes.
- One task per discrete gap; do not bundle unrelated gaps into one task.
- Follow the existing task format (checkboxes, IDs, file references).
- Do not renumber, reorder, or edit any pre-existing task or section.

### 6. Report

Output a compact convergence report:

- **Clean**: state that `tasks.md` was left unchanged because the codebase
  satisfies spec/plan/tasks and the constitution.
- **Appended**: list the number of new tasks and the phase header added,
  with a one-line summary of each gap closed, constitution violations first.

Then direct the user to run `/speckit-implement` to complete the appended
tasks. Do not run implement automatically.

### Record Lessons Learned (decision journal)

If this convergence surfaced a recurring gap pattern, a failed approach, or a
blocker, record it to `docs/lessons-learned.md` so the insight survives past
the session (draft and confirm):

- If leyline is installed, invoke `Skill(leyline:decision-journal)` and
  append a lesson entry (`what_happened`, `what_didnt_work`, `root_cause`,
  `action`; set `phase` to `execute`). Show the draft; append on
  confirmation.
- Fallback (leyline absent): append to `docs/lessons-learned.md` using the
  in-file ENTRY TEMPLATE; assign the next `LL-NNN` id.

Note: This command assumes `/speckit-implement` has already run on a complete
`tasks.md`. It assesses present state, not changes; it is not a substitute
for `/speckit-analyze` (cross-artifact consistency) or `/speckit-checklist`
(quality verification).
