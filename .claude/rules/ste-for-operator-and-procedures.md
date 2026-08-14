**Write procedures and operator replies in the STE register. Leave
rationale alone.**

ASD-STE100 is Simplified Technical English, a controlled language for
procedures a technician follows in a second language. This repository
adopts part of it for text a reader executes, and keeps it away from
text a reader weighs.

Getting the scope wrong is the expensive failure. A 20-word cap applied
to a docstring deletes the reasoning the docstring exists to carry.

**Where it applies:**

- Runbook and installation steps
- Agent replies to the operator
- Error messages, warnings, and prompts
- Command and skill instruction blocks
- Checklists and acceptance criteria

**Where it must not:**

- Docstrings, ADRs, and design rationale
- `book/src/**` and blog output
- Commit message bodies
- The `scribe:voice-*` skills
- This repository's descriptive documentation, these rules included

**The adopted limits:** 20 words per procedural sentence, 25 per
descriptive sentence, 6 sentences per paragraph, 3 words per noun
cluster. One instruction per sentence. Active voice in procedures.
Simple tenses only. No contractions. No semicolons (rule 8.1).
American spelling, already enforced by `scribe.spelling`.

**Vocabulary rules are not adopted and cannot be.** The ASD controlled
dictionary is copyright and is not redistributable, so no approved-word
list ships here. Never describe any output as STE compliant or
certified. ASD does not endorse or certify sellers of tools claimed to
be fully compliant.

**Where it conflicts with the house rules:**

| Conflict | Resolution |
|----------|------------|
| Slop detector flags 15-25 word sentences as the AI tell | House rule wins outside the scope above, STE wins inside it |
| Slop detector says let some sentences run past 35 words | Same |
| House rule keeps a semicolon in a comma-heavy list | STE bans all semicolons, in scope only |
| House prose uses contractions freely | STE spells them out, in scope only |

The conflict is real and is resolved by scope, not by precedence. Both
rules are correct about different text: uniform sentence length is a
machine tell in prose meant to read as thinking, and a feature in a
procedure someone follows at 3 a.m.

**Checking it:** three checks need counting and live in `scribe.ste`
(`check_sentence_length`, `check_paragraph_length`,
`find_noun_clusters`). Four are regex and live in the `ste:` section of
`plugins/scribe/data/languages/en.yaml`, reachable through
`get_ste_patterns(patterns, include_optional=True)`. All of them ship
off by default, because measured across this repository they fire on
most files, and a check that noisy stops being run.

Noun-cluster findings are advisory. Detection has no part-of-speech
tagger, so it fires on 91% of files. Reread what it points at. Never
rewrite on it and never gate a merge on it.

**Full reference:** `Skill(scribe:simplified-technical-english)` and its
`scope-boundaries`, `reconciliation`, and `licensing` modules.
