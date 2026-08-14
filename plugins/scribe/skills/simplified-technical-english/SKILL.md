---
name: simplified-technical-english
description: Applies an ASD-STE100-derived register to operator and procedural text. Use when writing runbooks or steps. Do not use for docstrings, ADRs, or rationale.
globs: "**/*.md"
alwaysApply: false
category: writing-quality
tags:
- ste
- technical-writing
- procedures
- operator-communication
- controlled-language
tools: []
complexity: medium
model_hint: fast
estimated_tokens: 1200
progressive_loading: true
modules:
- modules/adopted-rules.md
- modules/scope-boundaries.md
- modules/reconciliation.md
- modules/licensing.md
---

# Simplified Technical English

ASD-STE100 is a controlled language written so that a maintenance
technician reading a second language can follow a procedure without
misreading it. It has two halves: writing rules, and a dictionary that
fixes one meaning per word.

This skill adopts part of the first half. It never ships the second.

## The one-line version

An operator can get most of the value by naming the standard:

```markdown
## Communication style
Use ASD-STE-100 when you speak to the operator.
```

That works because the name pulls a whole register the model already
knows, at a cost of one line. `Skill(imbue:latent-space-engineering)`
covers the technique in its named-register-invocation module, together
with the known failure mode: practitioners report that the constraint
decays partway through a long session. The checks below exist because
guidance decays and counting does not.

## What this skill is not

This is an STE-derived authoring aid. It is not an implementation of
ASD-STE100, and no output of it may be called STE compliant. Read
`modules/licensing.md` before writing anything that describes this
work to a reader outside the project. The short version: the standard
is free to download but not freely licensed, the controlled dictionary
cannot be redistributed, and ASD states that it does not endorse or
certify sellers of tools claimed to be fully compliant.

Vocabulary checking is therefore out of scope. Rules that depend on the
approved-word list are not adopted and cannot be.

## Decide the scope first

STE applies to some text in this repository and would damage the rest.
Get this wrong and the 20-word cap starts deleting the reasoning that
docstrings and ADRs exist to carry.

| Apply STE | Do not apply STE |
|-----------|------------------|
| Runbook and installation steps | Docstrings that explain why |
| Agent replies to the operator | ADRs and design rationale |
| Error messages and warnings | Book content and blog output |
| Command and skill instructions | Commit message bodies |
| Checklists | This repository's own prose docs |

The last row is the one that bites. These skill files are descriptive
repo prose, so the house rules govern them, not STE. Full reasoning and
worked before-and-after pairs: `modules/scope-boundaries.md`.

## The adopted rules

Four limits, corroborated across independent public restatements:

| Limit | Value |
|-------|-------|
| Procedural sentence | 20 words |
| Descriptive sentence | 25 words |
| Sentences per paragraph | 6 |
| Words in a noun cluster | 3 |

Plus: one instruction per sentence, active voice in procedures, simple
tenses only, no contractions, no semicolons, and American spelling.
Each restated in our own words in `modules/adopted-rules.md`, with the
rules deliberately not adopted and why.

## Running the checks

Three checks need counting or noun detection, so they are code:

```bash
cd plugins/scribe && PYTHONPATH=src uv run python -m scribe.ste FILE.md
```

Each finding prints as `file:line: [rule/confidence] detail`. The
command exits 0 whenever it could read the files, because these checks
are advisory and the noun-cluster rule must never gate a merge. Pass
`--no-noun-clusters` to see only the two counting rules, which is the
usual way to read a file that has never been checked before.

Four more are regex and live in the language pack, gated off so a
routine slop sweep never runs them:

```bash
cd plugins/scribe && uv run python -c "
import sys; sys.path.insert(0, 'src')
from scribe.pattern_loader import get_ste_patterns, load_language_patterns
for e in get_ste_patterns(load_language_patterns('en'), include_optional=True):
    print(e['category'], e['confidence'], len(e['patterns']), 'patterns')
"
```

Mask code, tables, and frontmatter before you run the regex set. The
`scribe.ste` checks already do this.

## Read the findings honestly

Measured across 5984 markdown files in this repository:

| Check | Files affected | Per file |
|-------|----------------|----------|
| `sentence_length` | 39% | 0.8 |
| `paragraph_length` | 1% | 0.0 |
| `noun_cluster` | 76% | 3.0 |

A noun-cluster finding is advisory. Detection subtracts function words
and verb forms and calls what is left a noun, which a real
part-of-speech tagger would do better. Reread the phrase it points at.
Do not rewrite on it, and never gate a merge on it.

## What the confidence on a finding means

Each finding prints its own confidence, and the three rules earn it
differently.

| Confidence | Where it appears |
|------------|------------------|
| `high` | Every paragraph finding, and any sentence over 25 words |
| `medium` | A sentence of 21 to 25 words whose register was inferred |
| `low` | Every noun-cluster finding |

Past 25 words a sentence is over both limits, so the count settles it
and the register does not matter. Between 21 and 25 words the finding
exists only because the sentence was read as procedural, and when that
reading came through a stripped label it is published as `medium`.
Across the corpus 11% of sentence findings are `medium`.

A label is stripped because list items here open with `**Label**:`, and
classifying on the label leaves most of them unreadable. The cost is
that the sentence's real opening is discarded. `Triggers: push to
master` then reads as an instruction to push rather than a description
of when a workflow fires, and no test on the tokens separates it from
`Merge to master`, which is a real instruction. The reading is right
about five times in six, so the class is kept and the doubt is
published with it. Read a `medium` finding before you act on it.

One limit worth knowing before you trust a clean run: 61% of
sentences cannot be classified as procedural or descriptive, and those
get the looser 25-word limit. The checker under-reports rather than
over-reports. A clean run is weaker evidence than a dirty one.

That number stays high because most sentences open with a noun, and no
word list reaches them. Across the corpus the unclassified sentences
begin with 9407 distinct words, of which the commonest 60 cover 30%.
Reclassifying them would also change almost nothing, because unknown
text already receives the descriptive limit. Only unknown text that is
really procedural is under-reported, and that was measured at about 20
findings across the whole repository.

## Exit Criteria

- [ ] The text's register is decided against the scope table above, and
      text outside the Apply column is left alone.
- [ ] `python -m scribe.ste` runs over the target file and every line
      it prints is read. The command exits 0 either way, so the exit
      state carries no information.
- [ ] Every `sentence_length` finding is fixed or has a stated reason
      to stand.
- [ ] No `noun_cluster` finding was auto-rewritten.
- [ ] Nothing produced claims STE compliance, certification, or
      endorsement.
- [ ] No word from the ASD controlled dictionary was copied into the
      repository.
