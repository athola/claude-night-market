# Choosing Whether a Skill Applies

## What This Replaces

This file was `skill-selection-judgment.md`. It carried a table pairing
thoughts a session might have with the reason each one was wrong, and
a rule that a skill must be read whenever there was "even 1% chance"
it applied. Sample rows:

| It said you might think | It answered |
|-------------------------|-------------|
| "This is a simple task" | Simple tasks compound into complex failures. Check the skill anyway. |
| "The skill is overkill for this" | If a skill exists, someone needed it. Use the skill. |
| "This situation is different" | If you're uncertain, the skill probably applies. |

Every row forecloses the case where the thought was correct. Some
tasks are simple. Some skills are overkill. Some situations genuinely
differ from the one the author imagined. A table that pre-labels those
judgments as rationalization removes the only mechanism that would
have caught a skill being applied where it does not fit.

The pattern also inverts under load. "If a skill exists, someone
needed it" is an argument for reading every skill ever written, which
is how a repository accumulates skills nobody prunes.

## What To Do Instead

Read the description. Decide. The description exists to answer exactly
this question, and if it cannot, that is a bug in the description.

Two questions settle most cases:

1. **Does this skill know something I do not?** Repository-specific
   context, a past failure, a convention with no other record. If yes,
   read it: that content is not reconstructible from first principles.
2. **Is it describing a general practice I can already apply?** Then
   the skill is a reminder rather than a source. Read it when the
   reminder is useful, skip it when it is not.

When the answer is genuinely unclear, reading a skill is cheap and
misapplying one is not. Bias toward reading. That is a bias, not a
rule, and it is allowed to lose to a specific reason.

## When a Skill Should Be Ignored

Say so out loud rather than silently skipping, so the record shows a
decision was made:

- Its stated preconditions do not hold
- It contradicts a direct instruction from the user
- Following it would cause the harm it exists to prevent
- The situation is one the author demonstrably did not anticipate

The last one carries the burden of saying what differs. "This feels
different" is not that; "this skill assumes a single-package repo and
this is a workspace" is.

## Pruning

Matt Pocock's talk on writing skills names this as one of four things
that separate good skill sets from bad ones: skills accumulate
sediment when people add and never remove. A skill that no longer
matches the codebase does not sit inert. It is read, believed, and
acted on.

Deleting a stale skill is maintenance, not loss of capability.

## Usage

Reference from a skill that needs to say something about its own fit:

```markdown
See [choosing whether a skill applies](../../shared-modules/skill-selection-judgment.md).
```

Most skills need no such section. An accurate description does this
job, and a body section restating it costs context on every read.
