# Where STE applies, and where it does damage

STE was built for one job: a technician follows a procedure, in a
second language, and a misreading has physical consequences. Inside
that job the rules are close to unarguable. Outside it they remove the
things that make prose worth reading.

This module draws the line and shows what crossing it costs.

## The line

**Apply STE** where the reader is executing rather than deciding:

- Runbook and installation steps
- Agent replies to the operator
- Error messages, warnings, and prompts
- Command and skill instructions
- Checklists and acceptance criteria

**Do not apply STE** where the reader is deciding rather than
executing:

- Docstrings that explain why a thing works the way it does
- ADRs and design rationale
- Book content under `book/src/` and blog output
- Commit message bodies
- The `scribe:voice-*` skills, whose whole purpose is reproducing an
  individual author's voice
- This repository's own descriptive documentation, including these
  skill files

## Why the second list exists

A 20-word cap is a budget. In a procedure the budget is affordable,
because a step names an action and an object and little else. In
rationale the budget is spent before the reasoning starts, and what
gets cut is the subordinate clause carrying the cause.

Here is a real docstring sentence from `scribe.ste`:

> A base-form verb opening a sentence is an imperative. Elsewhere a
> bare base form is more often a noun, so only inflected forms count.

The second sentence runs 19 words and states a rule plus the reason
behind it. Push it under a strict budget and the reason goes first:

> Only inflected forms count.

That version obeys the limit and teaches nothing. A reader who meets it
in six months cannot tell whether the rule is deliberate or a bug. The
rationale was the valuable half.

## Procedural text, before and after

STE earns its keep here. From this repository's release runbook:

> Merge to master. `trust-attestation.yml` fires on the push: it
> rebuilds each plugin, compares the digest against the tag, and
> publishes the attestation.

That is one step carrying an instruction and an explanation, at 26
words. Split by register:

> Merge to master.
>
> `trust-attestation.yml` then fires on the push. It rebuilds each
> plugin. It compares each digest against the tag. It publishes the
> attestation.

The instruction is now four words and impossible to miss. The
explanation follows as description, where the looser limit applies.
Nothing was deleted.

## The failure mode this module prevents

An agent reads "the repository adopted STE", runs the checker over
every markdown file, and starts shortening docstrings and ADRs. The
checker reports a real violation each time, because it measures against
the strict limit whenever it cannot tell the register. The agent is
following the tool correctly and destroying the documentation.

Two guards are in place. `scribe.ste` gives unclassifiable text the
looser limit, so it under-reports rather than over-reports. And the
scope table above says which files are eligible at all.

Neither guard is automatic. A human decides which files to run the
checker on, and that decision is the one this module exists to inform.

## When the two registers meet in one file

Most files here mix them. A skill file has procedural steps inside
descriptive framing. Run the checker, then read each finding against
the scope table rather than fixing the list top to bottom.

A finding on a numbered step is usually worth acting on. A finding on
a paragraph explaining a trade-off usually is not.
