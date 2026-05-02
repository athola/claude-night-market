# Document Economy

**A document costs the sum of its readers' time. Earn that
cost or cut.**

This module adds **document-level** checks to the slop
detector. The other modules score sentences and words; this
one scores whether the document earns its existence at all.

## When to apply

Run this check on any document that will be read more than
once or by more than one person. Skip it for ephemeral
1:1 messages where a brain dump is fine.

The principle is invariant: writing time should scale with
total reader time. A 1:1 note absorbs no one else's hours,
so optimize for your throughput. A skill file loaded 50×
per day absorbs hours of reader-time per week, so optimize
for theirs.

## The three checks

### Check 1: Thesis-first

The first paragraph (or, for SKILL files, the activation
cue plus the first paragraph after the H1) must state the
single message you want the reader to walk away with.

A thesis is not a topic.

| Topic (weak) | Thesis (strong) |
|---|---|
| "This skill detects slop." | "Slop is a density problem, not a word problem." |
| "How to write tutorials." | "A tutorial moves a reader from cannot to can. Everything else is decoration." |
| "Code review checklist." | "Review for the bug you would ship, not the style you would prefer." |

**Failure modes:**

- "This document covers X, Y, and Z." That is a table of
  contents. It tells the reader what is in the document,
  not what to take from it.
- Burying the takeaway after 200 lines of context.
- Three competing theses fighting for the lead. Pick one.

**Fix:** rewrite the lead until you can highlight one
sentence and say "if the reader only reads this, the
document succeeded."

### Check 2: Sentence weight

Every sentence must do one of:

1. State the thesis.
2. Instance the thesis (a concrete example of it).
3. Bound the thesis (when it does not apply).
4. Repeat the thesis (allowed, see Check 3).

Sentences that do none of those four are bloat. Cut them.

**Common bloat patterns:**

- "It's also worth noting that..." — if it is worth
  noting, note it. Drop the throat-clear.
- "As mentioned above..." — if you must remind the
  reader, your structure is wrong.
- Restating the heading in the body. The heading
  already said it.
- Transitional connective tissue ("Now that we have
  covered X, let us turn to Y"). Just turn to Y.
- "In summary" sections that re-list bullets the reader
  just read.

### Check 3: The repetition rule

**Repeat the thesis. Cut everything else that repeats.**

The thesis is the message you want internalized. People
skim. They remember what they see three times. Echo the
thesis in the intro, in the middle, and at the close.
Vary the surface; hold the meaning.

Everything else that repeats is bloat:

- Restated headers.
- Multiple examples making the same sub-point. One is
  proof. Two is emphasis. Three is filler.
- "TL;DR" boxes that duplicate the conclusion.
- Section summaries that just re-list the section.

## The reader-time budget

Estimate before you write. Then check after.

| Audience | Reads | Time per read | Total budget |
|---|---|---|---|
| 1 person, 1:1 | 1 | 2 min | 2 min |
| 5-person team | 1 | 5 min | 25 min |
| 50-person org doc | 1 | 5 min | ~4 hours |
| 50-person skill, loaded daily | ~250/yr | 30 sec | ~10 hours/year |
| Public skill, 1000 users | varies | 30 sec | days/year |

The author's writing time should match the budget. If the
budget is 10 hours and you spent 30 minutes, you owe more
polish, more cuts, or both. If the budget is 5 minutes and
you spent a week, you over-built; ship and move on.

This is asymmetric on purpose. Cheap to write, expensive
to read is the failure mode worth catching.

## Scoring rubric

For each check, score 0-2:

| Score | Thesis-first | Sentence weight | Repetition |
|---|---|---|---|
| 0 | No identifiable thesis | <50% sentences earn weight | No thesis repetition; ambient repetition |
| 1 | Thesis present but buried or diluted | 50-80% earn weight | Some thesis repetition; some ambient |
| 2 | Thesis stated in lead, single and clear | >80% earn weight | Thesis repeated 3+ times; ambient cut |

**Document economy score: sum / 6.**

| Score | Action |
|---|---|
| 5-6 | Ship |
| 3-4 | Revise: identify the cuts |
| 0-2 | Restart from the thesis |

A document can have a clean sentence-level slop score
(0-1.0) and still score 0/6 here. Sentence cleanliness
is necessary, not sufficient.

## Worked example

**Before** (score: 1/6):

> # Logging Configuration Guide
>
> This document covers the various aspects of configuring
> logging in our system. Logging is an important part of
> any production application. There are many ways to
> configure logging and this guide will walk you through
> them. We will look at log levels, log destinations, log
> formatting, and log rotation. By the end of this guide
> you will understand how to configure logging.
>
> ## Log Levels
>
> Log levels are used to indicate the severity of a log
> message. There are several log levels you can use. The
> log levels are DEBUG, INFO, WARN, ERROR, and FATAL.
> [...]

Problems:
- No thesis, only a topic ("covers various aspects").
- "Logging is important" carries no information.
- The "we will look at" sentence is a TOC.
- "By the end of this guide" is filler.
- The Log Levels section restates the heading.

**After** (score: 5/6):

> # Logging Configuration
>
> **Log what you would page someone for. Drop the rest.**
>
> Most logging configuration time is spent suppressing
> noise from libraries you do not own. The defaults below
> bias toward silence; raise the volume only for the code
> you would actually wake up to debug.
>
> ## Log levels
>
> Use INFO for events you would mention in a postmortem.
> Use WARN for events that should not happen but did not
> break anything. Use ERROR for events that broke something
> a user could see. DEBUG and FATAL are mostly traps:
> DEBUG ships verbose noise to production, FATAL implies
> the process should die but rarely does.
> [...]

The thesis ("log what you would page someone for") shows
up in the lead, frames the level explanations, and would
recur in destinations and rotation sections.

## Integration

The full slop-detector pipeline now runs:

1. Sentence-level scoring (vocabulary, structure, sycophancy)
2. **Document-economy scoring (this module)**
3. Combined report

A document passes only when both layers pass. Sentence
slop is necessary; document economy is sufficient.
