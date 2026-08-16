# Licensing: what this project may and may not say

Read this before you describe this work to anyone outside the project.
The constraints here are legal, not stylistic, and getting one wrong
costs more than a bad sentence does.

## The standard is free of charge and is not freely licensed

ASD-STE100 Issue 9 was released in January 2025 and can be downloaded
at no cost from `asd-ste100.org`. No cost is not the same as an open
license.

The copyright page grants free-use rights to a closed list of
organization categories: ASD, AIA, AIAC, and ICCAIA members and their
customers, defense ministries, A4A, airworthiness authorities, and
universities and research institutes for educational purposes. An
open-source plugin distributed on a public marketplace fits none of
those categories.

Reproduction is restricted on top of that. The specification states
that no reproduction or publication of it, in whole or in part, may be
made without written authority from an officer of ASD.

## What follows for this repository

The controlled dictionary cannot be redistributed here. It holds
roughly 900 approved words along with the unapproved words they
replace, and it is the half of the standard this project cannot ship.

That removes a whole class of rules from reach. Any rule that depends
on looking a word up in the approved list cannot be adopted, because
the list is not present. Vocabulary checking is out of scope for this
skill and for `scribe.ste`, and the code says so.

What remains available is the writing rules, restated in our own words.
An idea is not copyrightable. The expression of it is. So this project
describes what a rule requires and never reproduces the specification's
wording.

Rule numbers get the same treatment. Public sources corroborate what
the rules require but not how they are numbered, with one exception:
rule 8.1, the ban on the semicolon, appears with its number in an
independent MIT-licensed restatement. That is the only rule number this
project cites. Everything else is cited by what it says.

## What ASD says about tools

The official FAQ states that ASD and the STE Maintenance Group do not
endorse or certify any company, organization, or individual that sells
tools claimed to be "fully compliant" with ASD-STE100. It adds that
such providers have received no authorization to use the ASD logo,
copyright, or trademark.

Three rules follow for anything this project publishes.

1. Never call any output of this skill compliant or certified. The
   framing is "STE-derived authoring aid".
2. Never use the ASD logo, and never present the ASD-STE100 name as a
   badge or a mark of approval.
3. Never imply review, approval, or any relationship with ASD or the
   STEMG. There is none.

`scribe.ste` is not an implementation of ASD-STE100. It reads on a
subset of the writing rules and it approximates a counting convention
the specification defines and does not publish. Both facts are stated
in the module docstring so a reader of the code meets them before a
reader of the docs does.

## Prior art that reached the same reading

`danyuchn/asd-ste100-skill` is an MIT-licensed restatement of the
writing rules that ships no dictionary. `johnsaigle/ste-lint` carries
a disclaimer of the same shape. Two independent projects landing on
own-words restatement plus an explicit disclaimer is weak evidence,
and it is the strongest evidence available short of counsel.

## The honest limit

This posture rests on a reading of published terms, not on legal
advice. Own-words restatement of a rule is defensible. Verbatim
quotation is prohibited by the terms, and whether fair use would cover
it is unresolved. This project avoids verbatim text, which keeps the
question from arising.

One exception is deliberate. The FAQ sentence about endorsement is
quoted in part above because paraphrasing what a party says about
itself invites the paraphrase to drift. A short quotation of a public
FAQ, attributed and used to constrain rather than promote, is the
narrow case where quoting is the safer choice.
