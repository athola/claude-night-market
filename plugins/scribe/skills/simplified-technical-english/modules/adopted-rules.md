# The adopted subset

ASD-STE100 Part 1 holds 53 writing rules across 9 sections. This
project adopts the ones that survive two filters: the rule must not
depend on the controlled dictionary, and it must help text that an
operator reads under time pressure.

Every rule below is restated in our own words. Rule 8.1 is cited by
number because that number is verifiable in public sources. The rest
are cited by what they require, because the numbering is not.

## Adopted: the four limits

| Limit | Value | Enforced by |
|-------|-------|-------------|
| Words in a procedural sentence | 20 | `scribe.ste.check_sentence_length` |
| Words in a descriptive sentence | 25 | `scribe.ste.check_sentence_length` |
| Sentences in a paragraph | 6 | `scribe.ste.check_paragraph_length` |
| Words in a noun cluster | 3 | `scribe.ste.find_noun_clusters` |

The two sentence limits differ, so text has to be classified before it
is measured. A single global limit measures something the standard does
not define. `scribe.ste.classify_sentence` makes that call, and gives
text it cannot place the looser limit.

A noun cluster is a run of nouns used as one name, such as "runtime
capture pipeline root". Past three words a reader has to guess which
noun governs which. Break it with a preposition: "the root of the
capture pipeline".

## Adopted: sentence and verb rules

**One instruction per sentence.** Two actions joined by "and" become
two sentences, or two numbered steps. This is the rule that most often
fixes an over-long procedural sentence, and it beats deleting words.

**Active voice in procedures.** Name who acts. "Run the migration",
never "the migration should be run".

**Simple tenses only.** The infinitive, the imperative, the simple
present, the simple past, the simple future, and the past participle
used as an adjective. The perfect and continuous forms are out. Write
"the build finished", not "the build has finished".

**No contractions.** Write "do not", "cannot", "it is". A contraction
saves two characters and costs a reader who is parsing a second
language.

**Rule 8.1: no semicolons.** The standard bans the semicolon outright.
This repository's house rule is looser and keeps a semicolon when a
list's items carry internal commas. In STE-scoped text, use a period.

**American spelling.** Already implemented repository-wide in
`scribe.spelling`, so this rule needed no new code.

## Adopted: paragraph and structure rules

**Start an instruction with the verb.** "Set the version field", not
"The version field should be set".

**Keep a paragraph to one topic.** The six-sentence limit enforces this
from the outside. A paragraph that needs a seventh sentence is usually
two paragraphs.

## Not adopted, and why

| Rule area | Why not |
|-----------|---------|
| Approved-word vocabulary | The dictionary cannot be redistributed. See `licensing.md`. |
| One word, one meaning | Depends on the dictionary's fixed senses. |
| Approved verb forms per word | Depends on the dictionary. |
| Warning and caution formatting | Aviation-specific. This repository has no airworthiness surface. |
| Part numbers and placards | No physical equipment to label. |

The first three are not declined on judgment. They are unreachable
without the licensed word list, and a partial imitation of them would
be worse than leaving them out.

## What a rule cannot tell you

These rules make text easier to follow. They do not make it correct,
and they do not make it complete. A 20-word sentence that names the
wrong file is worse than a 30-word sentence that names the right one.

Fix the content first. Then fit the register.
