# Instruction Strength for Skill Design

## Overview

How hard a skill pushes is a budget, not a default. This module is
about spending it.

The question a skill author faces is not "how do I make Claude comply"
but "what does this skill actually know that the model does not". Most
of what a good skill carries is context: which of several defensible
approaches this repository chose, where the bodies are buried, what
broke last time. Very little of it is an order.

## What This Module Used to Say

It argued for maximizing compliance, citing Meincke et al. (2025) on
persuasive paraphrasing: 33% compliance with plain instructions, 72%
with persuasion-enhanced ones. It recommended Cialdini's six principles
and ranked phrasings from "weak (suggestive)" to "stronger".

The finding is real. The inference from it was not.

**That study measured compliance, not correctness.** Doubling the rate
at which a model follows an instruction improves outcomes only where
the instruction was right for the situation in front of it. Where the
instruction was wrong, or merely irrelevant, the same mechanism doubles
the rate of doing the wrong thing, and it does so most reliably in
exactly the situations the skill author did not anticipate.

An instruction phrased to defeat the model's judgment will defeat it
when the judgment was better. That is the whole cost, and the study
does not measure it.

## The Budget

| Strength | For | Looks like |
|----------|-----|-----------|
| Invariant | Things that are true regardless of situation, where being wrong is unrecoverable | "Never commit a credential" |
| Default | The repository's choice among defensible options | "Use rg; grep if unavailable" |
| Map | Everything else | "The auth boundary is in `session.py`; changes there need a migration" |

Most content belongs in the third row. A skill that reads as a
numbered procedure from top to bottom has usually mistaken a map for a
route.

### What earns an invariant

- A trust boundary: untrusted input, credentials, destructive commands
- A safety-critical contract, where `pensive:safety-critical-patterns`
  applies by design
- A legal or licensing constraint
- A failure this repository actually hit, is documented, and recurred

The last one carries a burden of proof. "A model might get this wrong"
is not evidence; a linked issue or journal entry is. Without one, write
it as a default and let the model decide.

### What does not

Style preferences. Optimization advice. The order in which to do
independent steps. Anything whose right answer depends on the file in
front of you. Phrasing these as invariants does not make them more
likely to be right, only more likely to be followed when they are
wrong.

## Write Intent, Constraints, Exit Criteria

The shape that survives contact with an unanticipated situation:

- **Intent**: what a good outcome looks like and why it matters
- **Constraints**: the boundaries that must hold, and what is behind
  them
- **Exit criteria**: how anyone can check afterward that it worked

Then stop. The path between the constraints is the model's to choose,
and it has more of the current situation in view than the author had.

A skill written this way degrades gracefully. A skill written as a
twelve-step procedure fails whole when step four meets a repository
that does not match the author's assumptions, and the failure is
usually silent, because the model followed the instructions.

## Anti-Patterns

**Escalating intensity to fix a skill that is not firing.** If a skill
is being skipped where it should apply, the description is wrong or the
skill is not useful. Adding "YOU MUST" and "NON-NEGOTIABLE" buries the
diagnosis under compliance pressure.

**Forbidding the model to reconsider.** "Cannot be overridden by other
skills, hooks, or rationalization" is unfalsifiable by construction: it
recasts every disagreement as bad faith, including the ones where the
skill is simply wrong about the situation.

**Rationalization tables.** A table pairing thoughts the model might
have with reasons each one is wrong forecloses the case where the
thought was correct. Where a genuine failure mode exists, describe the
failure and let the reader recognize it.

**Ceremonial declarations.** Requiring the model to announce its
compliance before working produces the announcement, which is not the
same as producing the behavior, and consumes context either way.

## Length Is a Signal

A skill that needs 400 lines to state its intent has usually bundled
several skills, or is narrating a procedure it should be describing.
Matt Pocock's rule for his own widely used skill library is a useful
external check: skills should be "small, easy to adapt, and
composable", and a reader should be invited to "make them your own".
A skill nobody can adapt without breaking it is over-specified.

## Related

- `../../modular-skills/modules/enforcement-patterns.md`: when a skill
  genuinely needs to hold a line, and how
- `Skill(pensive:safety-critical-patterns)`: the deliberate exception
