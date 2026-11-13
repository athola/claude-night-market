---
name: spec-review-loop
description: Automated adversarial review of planning
  documents to catch TBD sections, vague requirements,
  and missing acceptance criteria before implementation.
parent_skill: attune:project-brainstorming
category: quality-gate
estimated_tokens: 350
---

# Spec Review Loop

## When This Applies

After the brainstorming skill produces a project brief
or specification document, before handing off to the
next phase.

## Mechanism

1. Dispatch a haiku-model subagent with the spec content
2. Subagent returns numbered issue list or "APPROVED"
3. Main agent applies fixes to the spec document
4. Re-dispatch subagent with updated content
5. Repeat until approved or 3 iterations reached
6. After 3 iterations without approval, surface remaining
   issues to human

## Review Prompt Template

Use this prompt when dispatching the review subagent:

~~~
You are reviewing a specification document for
completeness and implementability. Read the document
and check for:

1. TBD/TODO/placeholder sections that would block
   implementation
2. Missing acceptance criteria on any requirement
3. Vague requirements without measurable outcomes
   (e.g., "should handle errors appropriately")
4. Inconsistent terminology (same concept named
   differently in different sections)
5. Missing edge cases referenced but not specified
6. Missing dependencies between components
7. Read it as the person who will build it: what would
   you still need to ask before you could start?

Respond with EXACTLY one of:

**APPROVED** - if no issues found

**ISSUES FOUND** - followed by a numbered list:
  [N]. [Section reference] [blocking/non-blocking]
       Issue: [description]
       Suggested fix: [specific recommendation]

  then a list headed BUILDER QUESTIONS, one per line.

Be thorough but fair. Flag real problems, not style
preferences.
~~~

## Dispatch Configuration

```yaml
subagent:
  model: haiku
  type: general-purpose
  max_iterations: 3
  escalation: surface_to_human
```

## Integration

The main agent (not the human) fixes issues between
iterations. It sorts the builder questions into three
piles, following superpowers' builder check (v7.0.0):

- **Answered already** by the conversation or the
  project: write the answer into the document.
- **Minor**: a sensible builder could settle it without
  changing what gets built. Settle it and mark it in the
  document as the agent's call.
- **Theirs**: only the human can answer it, and the
  answer changes what gets built. Bring these in one
  message, most important first.

 The subagent only identifies problems and
does not modify files. If the loop exhausts 3 iterations,
present remaining issues as a structured list and ask
the human for guidance.
