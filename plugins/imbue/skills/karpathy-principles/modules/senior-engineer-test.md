# The Senior Engineer Test

A three-question battery to apply to your own code
before claiming it is done. The questions stand in
for the senior engineer who is not in the room.

Adapted from a self-check Karpathy calls out for
agentic coding: ask whether a senior engineer would
say this is overcomplicated. We expand the question
into three concrete sub-questions that map to common
LLM coding failures.

## The Question

> Would a senior engineer who is busy and a little
> grumpy say this code is overcomplicated?

If yes, the diff is not ready.

## The Three Sub-Questions

### Q1: Could this be 50% shorter without losing meaning?

Most LLM-written code can be cut by a third to a
half. If the diff is 200 lines, ask: which 100 lines
exist because the agent felt clever, not because the
problem demanded them?

Common 50% wins:

- Replace abstract base class plus two subclasses
  with one function plus a parameter.
- Replace try-except wrapping every call with a
  single boundary handler.
- Replace explicit getter and setter with direct
  attribute access.
- Replace nested conditionals with a flat early-return
  pattern.

### Q2: Are abstractions earning their weight?

An abstraction earns its weight when it is used three
or more times, or when it isolates a real boundary
(network, disk, locale). A class with one consumer is
ceremony. A factory with one product is ceremony.

Test: for every type, class, or helper added, count
the call sites. One call site means the abstraction
costs more than it saves.

### Q3: Could a junior dev follow this in six months?

Six months means: docs may have rotted, original
context is gone, the original author is on another
team. The code has to carry its own meaning.

Failure signals:

- Names that mean something only if you remember the
  ticket
- Comments that describe what the code does (the code
  shows that) instead of why
- Indirection that requires three jumps to find the
  actual logic
- Implicit invariants that nothing checks and nothing
  documents

## The Decision Tree

```
For each of Q1, Q2, Q3:
  - Yes -> next question
  - No  -> stop and address before shipping

If three Yes -> ship
If any No   -> rework that dimension first
```

A No answer is not a failure of the agent; it is the
agent doing its job. Catching the violation before
the senior engineer catches it is the entire point.

## Worked Example

Diff under review: a class hierarchy for a single
discount calculation.

- Q1 (50% shorter)? Yes obviously: one function
  replaces five classes.
- Q2 (abstractions earning weight)? No: zero
  additional call sites for the strategy pattern.
- Q3 (junior in six months)? No: two indirection hops
  to find the multiplication.

Two No answers means rework. Replace the hierarchy
with the function. Now Q1, Q2, Q3 are all yes.

## When the Test Does Not Apply

The senior-engineer test assumes the code will be
read again. For a one-shot data migration that runs
once and is deleted, the test is too strict. See
`tradeoff-acknowledgment.md` for the boundary cases.

## Cross-References

- `Skill(imbue:scope-guard)` formalizes Q2 (does the
  abstraction earn its weight) into the Worthiness
  formula.
- `Skill(conserve:code-quality-principles)` is the
  KISS / YAGNI / SOLID foundation that Q1 leans on.
- `Skill(leyline:additive-bias-defense)` is the
  burden-of-proof contract that backs Q2.
