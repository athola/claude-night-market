---
name: context-injector
description: >-
  Build structured revision prompts from feedback
  files so the planning skill addresses specific
  complaints in the next iteration.
parent_skill: attune:mission-orchestrator
category: workflow-orchestration
estimated_tokens: 150
---

# Context Injector

## Purpose

When a plan revision is requested, transform the
structured feedback into a prompt addition that guides
the planning skill to address the specific complaints
without repeating rejected patterns.

## Revision Prompt Template

The context injector reads the latest
`round-N.json` and builds this prompt block:

```
## Revision Context (Round {N} Feedback)

The previous plan version was reviewed. Address
these items in the revised plan:

### Sections Requiring Revision

**{section_name}** (verdict: {verdict})
Feedback: {rationale}
{annotations if any}

### Sections Approved (Do Not Change)

- {section_name}: approved, keep as-is

### Anti-Patterns to Avoid

Do NOT repeat these patterns from the rejected plan:
- {extracted patterns from rejected sections}

### Constraints Added by Reviewer

- {constraint annotations}
```

## Building the Prompt

### Algorithm

1. Read `.attune/plan-history/feedback/round-N.json`
2. For each section with verdict `revise` or `reject`:
   - Include the section name, verdict, and rationale
   - Include any typed annotations
   - Extract specific patterns to avoid from rejected
     content
3. For each section with verdict `approve`:
   - List as "keep as-is" to prevent regression
4. Collect all `constraint` type annotations into a
   dedicated section
5. If bias findings exist, include them as additional
   constraints

### Feeding Back to the Planning Skill

The revision prompt is passed as additional context
when re-invoking `Skill(attune:project-planning)`:

```
The orchestrator re-invokes the planning skill with:
1. The original specification (docs/specification.md)
2. The revision context block (built above)
3. The previous plan version for reference
```

The planning skill sees the revision context as
requirements that constrain its output.

## War Room Feedback

When the war room returns concerns or rejection:

1. Read the war-room verdict from mission state
2. Convert war-room concerns into the same revision
   prompt format
3. Include the prosecution counsel's specific
   objections as constraints
4. Mark this as "war-room feedback" so the planning
   skill knows the source

## Guard Rails

- The context injector NEVER modifies the plan directly
- It only produces prompt context for the planning skill
- Approved sections are explicitly marked "do not change"
  to prevent regression during revision
