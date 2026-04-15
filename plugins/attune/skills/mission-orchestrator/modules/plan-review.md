---
name: plan-review
description: >-
  Interactive section-by-section plan review in the
  terminal. Presents architecture first, then phases.
  Collects verdicts, tracks versions, injects feedback,
  governs iterations, and gates on war-room approval.
parent_skill: attune:mission-orchestrator
category: workflow-orchestration
dependencies:
- modules/plan-versioner.md
- modules/feedback-collector.md
- modules/context-injector.md
- modules/iteration-governor.md
- modules/mission-state.md
- leyline:additive-bias-defense
estimated_tokens: 400
---

# Plan Review

## Purpose

Replace the lightweight plan-to-execute checkpoint with
an interactive review loop. The user reviews the plan
section by section, provides verdicts, and the plan is
revised until approved or the iteration cap is reached.
After user approval, the plan must pass a mandatory
war-room review.

## Review Flow

```
plan skill produces docs/implementation-plan.md
         |
         v
Plan Versioner: copy to plan-v1.md
         |
         v
Iteration Governor: check round (1/3)
         |
         v
Additive Bias Scan: scan plan for unjustified additions
  (findings displayed alongside plan sections)
         |
         v
Plan Presenter: show architecture section
  user: approve / revise / reject
         |
Plan Presenter: show phase 1
  user: approve / revise / reject
         |
... (remaining phases) ...
         |
         v
Feedback Collector: write round-N.json
         |
         v
All sections approved?
  |                    |
  no                   yes
  |                    |
  v                    v
Context Injector    Mandatory War Room Gate
  build revision      Skill(attune:war-room)
  re-invoke planning    |
  increment round       v
  loop back           War Room approves?
                        |            |
                        yes          no
                        |            |
                        v            v
                      EXECUTE     Feedback from war room
                                  counts as next round
                                  loop back to review
```

## Section Parsing

Parse `docs/implementation-plan.md` into reviewable
sections:

1. **Architecture section**: everything from the start
   of the plan through the first `## Phase` or
   `## Task` heading. This includes the Goal,
   Architecture, Tech Stack, and File Structure.

2. **Phase sections**: each `## Phase N:` heading and
   its content through the next phase heading or EOF.

If the plan uses `### Task N:` without phase groupings,
group tasks into logical clusters of 3-5 tasks each.

## Presentation Format

### Section Display

```
--- Plan Review: {Section Name} (v{V}, round {R}/{MAX}) ---

{section content, verbatim from the plan}

{bias findings for this section, if any:}
  [BIAS] New caching layer -- which spec requirement
         demands this? (scrutiny Q4: no evidence)

------------------------------------------------------------
Verdict? [A]pprove / [R]evise / re[J]ect
>
```

### Revision Rationale Prompt

When verdict is `revise` or `reject`:

```
Rationale (what to change):
>
```

### Diff Summary (Round 2+)

At the start of round 2+, before section review:

```
--- Changes in v{V} (from round {R-1} feedback) ---
 {section}: +N lines, -M lines
   Addressed: "{feedback summary}"
 {section}: unchanged
-------------------------------------------------
```

## War Room Gate

After all sections are approved:

1. Save the approved plan as the final version
2. Invoke `Skill(attune:war-room)` with:
   - `docs/implementation-plan.md` (approved version)
   - `docs/specification.md` (cross-reference)
   - `.attune/plan-history/feedback/` (revision history)
   - `.attune/plan-history/plan-v*.md` (all versions)
   - Risk classification from `leyline:risk-classification`
   - Additive bias scan findings
3. The Prosecution Counsel role is always active
4. War room verdict determines next step:
   - APPROVE: proceed to execute phase
   - CONCERNS/REJECT: feedback enters revision loop,
     counts toward iteration cap

## Additive Bias Integration

Before presenting each section to the user, scan it
using `leyline:additive-bias-defense`:

1. Apply the 5 scrutiny questions to each proposed
   component or abstraction in the section
2. Flag items where evidence (Q4) or consequence (Q5)
   answers are weak
3. Display findings inline with the section content
4. Record findings in the feedback file

This means the user sees bias warnings before making
their verdict, giving them ammunition for targeted
revision requests.

## State Management

The plan-review module reads and writes the
`plan_review` object in `.attune/mission-state.json`.
See mission-state module for the full schema.

On each round:
- Increment `current_round`
- Append to `versions` array
- Update `status` (in_review / approved / rejected)
- Record `war_room_verdict` when available
