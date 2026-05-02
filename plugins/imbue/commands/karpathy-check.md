---
name: karpathy-check
description: 'Pre-flight gate walking four Karpathy principles (think first, simplicity, surgical edits, goal-driven). Use before implementation.'
usage: /karpathy-check [task description]
---

# Karpathy Check

A four-question pre-flight gate adapted from
observations on common LLM coding pitfalls. Loads the
`imbue:karpathy-principles` skill and walks each
principle as a checkable question.

## Usage

```bash
# Run as an inline pre-flight before starting work
/imbue:karpathy-check

# Pass a task description to anchor the check
/imbue:karpathy-check Add rate limiting to the signup endpoint
```

## What It Does

1. Loads `Skill(imbue:karpathy-principles)`.
2. Walks the four-question battery:
   - Think Before Coding: did I list assumptions, or
     guess silently?
   - Simplicity First: would a senior engineer call
     this overcomplicated?
   - Surgical Changes: does every changed line trace to
     the request?
   - Goal-Driven Execution: can I prove this is done
     with a check, not a feeling?
3. For each question, captures the answer and any
   blockers.
4. Outputs a verdict: PASS, NEEDS CLARIFICATION, or
   REWORK.

## Verdict Semantics

- **PASS**: all four answered concretely. Begin
  implementation.
- **NEEDS CLARIFICATION**: at least one assumption or
  ambiguity needs the user's input. Surface the question,
  do not guess.
- **REWORK**: the plan as drafted will violate one or
  more principles. Reshape before starting.

## When to Use

- Before any non-trivial implementation
- When converting a vague request into a verifiable plan
- During code review, applied to your own diff
- When a task feels "too easy" (often a sign of hidden
  assumptions)

## When NOT to Use

- Trivial typos and one-line fixes
- Throwaway scripts and exploratory spikes
- Documentation-only changes
- Production fires where the failing test wait is too
  long

See `modules/tradeoff-acknowledgment.md` in the skill
for the full boundary discussion.

## Related

- `Skill(imbue:karpathy-principles)` - the underlying
  four-principle synthesis
- `Skill(imbue:scope-guard)` - worthiness scoring before
  the four-question gate
- `Skill(imbue:proof-of-work)` - Iron Law TDD enforcement
  after the gate clears
- `/imbue:justify` - post-implementation audit using the
  same principles in reverse
