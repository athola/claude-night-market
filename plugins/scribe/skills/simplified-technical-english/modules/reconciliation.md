# Reconciling STE with this repository's house rules

This repository already carries a body of writing rules. Adding a
second body creates the risk that an agent picks whichever one is
nearer to hand. This module resolves each conflict by naming which rule
wins in which scope.

## Which regime governs these docs

Start here, because it is the row most likely to be applied backwards.

**These skill files are descriptive repository prose. The house rules
govern them. STE does not.**

That means the slop detector, `markdown-formatting.md`, and
`slop-scan-for-docs.md` are the standards these very files were written
against. Running `scribe.ste` over `adopted-rules.md` and shortening
whatever it flags would be a misapplication of this skill by way of
this skill's own documentation.

The checker points outward, at procedures and operator replies. It does
not point at itself.

## The conflicts

| Conflict | House rule says | STE says | Winner |
|----------|-----------------|----------|--------|
| Governing regime for these docs | House rules govern repo prose | (silent) | House, always |
| Sentence length | 15-25 words is the AI tell, so vary deliberately | 20 words procedural, 25 descriptive | Scope decides |
| Sentence-length variance | Let some run past 35 words | Cap every sentence | Scope decides |
| Semicolons | Keep one when list items carry commas | Ban all | STE in scope, house elsewhere |
| Contractions | Used freely in house prose | Spell every word out | STE in scope, house elsewhere |
| Passive voice | Not a house rule | Active voice in procedures | STE in scope, silent elsewhere |
| American spelling | Required | Required | No conflict |
| Participial tails | Flagged as slop | Discouraged | No conflict |

## The sentence-length collision in detail

This is the one real contradiction, and it is head-on.

`Skill(scribe:slop-detector)`, in its structural-patterns module,
names **15-25 words per sentence** as the specific AI cluster, and
scores a document as machine-written when more than 70% of its
sentences fall in that band. Its prevention rule says to let some
sentences run past 35 words when the logic requires it.
Its remediation-strategies module goes further and prescribes
interspersing 25-30-word explanatory sentences.

STE's 20-word cap produces exactly the low-variance profile the slop
detector scores as machine-written.

Both rules are right about different text. Uniform sentence length is
evidence of a machine when the text is meant to read as a human
thinking. Uniform sentence length is a feature when the text is a
procedure someone follows at 3 a.m. The slop detector protects the
first case. STE serves the second.

So the tiebreak is not which rule is better. It is which kind of text
is in front of you, which is what `scope-boundaries.md` decides.

## Why the checks ship gated off

A rule that fires everywhere gets disabled, and a disabled rule
protects nothing.

Measured across 4620 markdown files in this repository, the STE regex
categories fire on 40% of files for semicolons, 45% for passive voice,
and 29% for contractions. Those are correct findings against text that
was never meant to be STE. Turning them on by default would bury the
house slop signal under a register mismatch.

Every STE category in `en.yaml` therefore sets
`default_enabled: false`, and `get_ste_patterns` returns nothing until
a caller asks. The surfaces where turning them on is right:

- Release runbook steps
- Command and skill instruction blocks
- Operator-facing error and warning text

## A note on the noun-cluster rule

The three-word cap collides with names this repository has already
settled on. "Code knowledge graph" and "blast radius analysis" are
product names, not accidental noun stacks, and renaming them to satisfy
a checker would cost more than it returns.

Treat a noun-cluster finding on an established name as answered. The
rule is aimed at phrases invented in the sentence you are writing now.
