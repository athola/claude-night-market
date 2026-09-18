---
module: audience-targeting
category: detection
dependencies: [Read, Grep]
estimated_tokens: 750
---

# Audience Targeting

**A document that serves everyone serves no one. Name the reader,
then cut what that reader does not need.**

Document economy asks whether a sentence earns its cost. This module
asks a prior question: earns it for whom. The same paragraph is
load-bearing for one reader and noise for another, so weight cannot be
scored until the reader is named.

Strength is a **Default, not an invariant**, in the `bounded-autonomy`
budget. No recorded failure in this repository justifies blocking a
draft on a missing tier, and that rule file measures instruction load
as a real cost. Deviate with a stated reason.

## When to apply

Any text a reader consults to learn something or to do something:
READMEs, tutorials, guides, skill files, ADR summaries, generated
docs, book chapters.

## When it must not apply

Creative cycles: `scribe:voice-generate`, the other `voice-` skills,
`style-learner`, `session-to-post` narrative output, and the
`fiction-patterns` module.

Creative work still names a reader. The cut test does not transfer,
because in creative prose the digressions are the point. Applying it
there deletes the work.

## The tiers

Declare one tier per document. Free-form `persona` is available when
none of the three fit.

| Tier | The reader | Assumes | Cut rule |
|------|-----------|---------|----------|
| `newcomer` | Has never seen this project | General literacy in the domain, nothing more | Cut internals, history, and comparisons. Keep the one path that works, end to end |
| `practitioner` | Knows the domain, not this repository | Can read the code and the error messages | Cut general-domain teaching. Keep the repo-specific facts the reader cannot derive |
| `expert` | Is already familiar with this material | Full context, including why the obvious approach fails | Cut everything derivable. Keep the novel claim, the numbers behind it, and the edge cases |
| `persona` | Free-form, one line | Whatever the line says | Written by the author alongside the persona |

A tier is a claim about prior knowledge, not about seniority. A
principal engineer reading this repository for the first time is a
`newcomer`.

## Declaring it: ask, do not guess

When a generation or rewrite request states no tier, **ask, do not
guess**. A guessed audience produces a document that reads as
competent and serves nobody, which is the expensive failure: it passes
review and wastes every reader afterward.

### Socratic set

Ask only what is still open. Stop when the tier is decided.

1. Who is the reader, and what do they already know? Name a role
   specific enough to point at someone who holds it.
2. What can they do after reading that they could not do before?
3. If they have never seen this project, what is the first thing on
   this page that would confuse them?
4. Which paragraphs would an expert skip? Move those to a deep
   dive.
5. Which paragraphs would a newcomer not survive? Those need a
   prerequisite link, not more prose.
6. Is this document teaching, or is it reference for someone who
   already learned? A page that tries both serves neither.

Record the answer in the request, and in the document's own lead when
a reader arriving cold would benefit from knowing who it is for.

## The cut test

Read each section against the declared tier. Four verdicts, so
cutting is never the only move:

- **Keep**: the reader needs this before they can act on the
  document's thesis.
- **Link**: the reader needs it eventually but not now. Replace with
  one line and a link.
- **Extract**: it is meaningful only to a reader above the declared
  tier. Move it to a deep dive, per the protocol below.
- **Delete**: no tier needs it. Throat-clears, restated headings, and
  padding land here.

Most failures come from treating Extract as Delete or as Keep. A
document that keeps everything buries its reader. A document that
deletes expert material destroys the only record of a hard-won
finding.

## Extraction protocol

**Never delete to hit a tier.** Move, then link.

**Skill files**: extract to the skill's `modules/` directory, add the
file to the `modules:` frontmatter list, and reference it from the
hub in one line. This is what `progressive_loading` already exists
for, so extraction costs the hub nothing at load time.

**Repo docs and book chapters**: extract to
`docs/deep-dive/<topic>.md`. It must be **linked from the lead** of
the parent document, with one line naming who it is for. Create the
directory on first use. Do not scaffold it empty.

Every deep dive **declares its own tier**, usually `expert`. Without
that, extraction becomes a place to hide material from the rule
rather than a place to serve a different reader.

## Worked example

A plugin README declared `newcomer`.

Before, the lead ran: install command, then four paragraphs on why
the hook fires on `PostToolUse` rather than `Stop`, then usage.

After: install command, the one usage path, and a closing line,
"Why the hook fires on `PostToolUse`: `docs/deep-dive/hook-timing.md`
(for readers already maintaining a hook)."

The rationale was not weak. It was answering a question the newcomer
had not asked yet.

## Anti-goals

- Do not lower a tier to justify cutting content you find tedious.
  The tier follows the reader. Editor boredom is not evidence.
- Do not use `persona` to avoid deciding. A persona is one specific
  line about one specific reader.
- Do not split a short document. Below roughly 200 lines, a marked
  section usually beats a second file the reader must find.
- Do not restate the parent document inside the deep dive. Link back
  once and start at the substance.

## Why this is not in `en.yaml`

The repo rule requires a new detectable pattern to ship with a YAML
section and a pattern test. Audience fit is exempt because **no regex
can decide it**: the same sentence passes for one reader and fails for
another, and the deciding fact is the declared tier, which does not
appear in the text being scanned. The guarantee here is the contract
test in `plugins/scribe/tests/test_audience_targeting.py`, which
anchors on the clauses above.
