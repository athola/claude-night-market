---
name: workflow-improvement
description: |
  Retrospective workflow evaluation and improvement of skills, agents, commands, and hooks.

  Triggers: workflow improvement, retrospective, workflow efficiency
  Use when: workflow felt slow, confusing, or needs optimization
  DO NOT use when: implementing features - focus on feature work first.
category: workflow-ops
tags: [workflow, retrospective, efficiency, commands, agents, skills, hooks]
tools: [Read, Edit, Bash, TodoWrite]
complexity: medium
estimated_tokens: 900
dependencies:
  - sanctum:shared
---

# Workflow Improvement

## When to Use
Use this skill after running a command or completing a short session slice where execution felt slow, confusing, repetitive, or fragile.

This skill focuses on improving the *workflow assets* (skills, agents, commands, hooks) that were involved, not on feature work itself.

## Required TodoWrite Items
1. `fix-workflow:slice-captured`
2. `fix-workflow:workflow-recreated`
3. `fix-workflow:improvements-generated`
4. `fix-workflow:plan-agreed`
5. `fix-workflow:changes-implemented`
6. `fix-workflow:validated`

## Step 1: Capture the Session Slice (`slice-captured`)

Identify the **most recent command or session slice** in the current context window and capture:
- **Trigger**: What command / request started it (include the literal `/command` if present)
- **Goal**: What “done” meant for the user
- **Artifacts touched**: Skills, agents, commands, hooks (names + file paths)
- **Evidence**: Key tool calls / errors / retries that indicate inefficiency

If the slice is ambiguous, pick the most recent *complete* attempt and state the exact boundary you chose.

## Step 2: Recreate the Workflow (`workflow-recreated`)

Reconstruct the workflow as a numbered list of steps (5–20 steps):
- Inputs (what was assumed / required)
- Decisions (branch points)
- Outputs (files produced, state changes)

Also record friction points:
- Repeated steps / redundant tool calls
- Missing guardrails (validation too late, unclear prerequisites)
- Missing automation (manual steps that should be scripted)
- Confusing naming or discoverability gaps

## Step 3: Generate Improvements (`improvements-generated`)

Generate **3–5 distinct improvement approaches** and score each on:
- Impact (time saved, fewer errors, fewer steps)
- Complexity (how invasive is the change)
- Reversibility (easy to rollback)
- Consistency (matches existing sanctum patterns)

Prefer small, high-use changes:
- Tighten a skill’s steps and exit criteria
- Add a missing command option or usage clarity
- Improve a hook guardrail or make it observable
- Split an overloaded command into clearer phases

## Step 4: Agree on a Plan (`plan-agreed`)

Choose 1 approach and define:
- Acceptance criteria (“substantive difference”)
- Files to change
- Validation commands to run
- Out-of-scope items to defer

Keep the plan bounded: aim for ≤ 5 files changed unless the workflow truly spans more.

## Step 5: Implement (`changes-implemented`)

Apply changes following sanctum conventions:
- Keep naming consistent across `commands/`, `agents/`, `skills/`, `hooks/`
- Prefer documentation-first improvements if ambiguity was the primary issue
- If behavior changes, add/adjust tests in `plugins/sanctum/tests/`

## Step 6: Validate Substantive Improvement (`validated`)

Validation should include at least 2 of:
- Plugin validators / unit tests passing (targeted)
- Re-running the minimal workflow reproduction with fewer steps or less manual work
- A clear reduction in failure modes (e.g., earlier validation, clearer options)

Record the before/after comparison as *metrics*, not prose:
- Step count reduction
- Tool call reduction
- Errors avoided (what would have failed before)
