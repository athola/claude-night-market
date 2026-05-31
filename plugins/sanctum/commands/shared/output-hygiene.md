# Output Hygiene (Shared Module)

Single source of truth for the text every sanctum workflow emits:
commit messages, PR/MR comments, thread replies, summaries, issue
bodies, and PR descriptions. Two contracts apply to all of it.

> **Consumers**: `commit-msg`, `commit-messages`, `pr-review`
> (Phase 1.7 and output phases), `fix-pr` (commit, summary, thread
> replies). Each consumer also carries a compact inline fallback so
> the rule holds when this module is not installed.

## Contract A: Strip character-level slop before emitting

The word-level slop list (`leverage`, `seamless`, `comprehensive`,
`delve`, ...) is necessary but not sufficient. The markers that leak
most often are punctuation, not words. Before writing any commit
message or posting any comment, scan the text and replace these:

| Marker | Example in | Replace with |
|--------|------------|--------------|
| `+` as a prose conjunction | `parser + validator` | `and` (`parser and validator`) |
| em-dash `—` | `nulls — prevents crash` | colon, period, comma, or rephrase |
| double-dash `--` in prose | `nulls -- prevents crash` | a real `—` is still slop here: use `:` or rewrite |
| ASCII arrow `->` as connector | `input -> output` | `to` / `into` / `produces` |
| unicode arrow `→` as connector | `input → output` | `to` / `into` / `produces` |
| smart quotes `“ ” ‘ ’` | `the “fix”` | straight quotes `"` and `'` |

Keep these (not slop):

- `+` in version strings (`1.2.0+build`), math, code, and diagram
  labels.
- `->`, `→`, `=>` inside code spans, type signatures, and fenced code
  blocks.
- `--` as a real CLI end-of-options separator inside a code span or
  command (`git log --`).
- `--` inside markdown table delimiter rows (`| -- |`).

Detection snippet (run against the text you are about to emit, not
the diff being reviewed):

```bash
# $TEXT holds the message/comment body about to be posted.
printf '%s\n' "$TEXT" | grep -nE '\w \+ \w' && echo "fix: '+' conjunction"
printf '%s\n' "$TEXT" | grep -n '—'          && echo "fix: em-dash"
printf '%s\n' "$TEXT" | grep -n ' -- '        && echo "fix: double-dash"
printf '%s\n' "$TEXT" | grep -nE '[^`]( -> | → )[^`]' && echo "fix: arrow connector"
printf '%s\n' "$TEXT" | grep -nE '[“”‘’]'      && echo "fix: smart quotes"
```

Any match is fixed in the text before posting, not just reported.
The full prose rule set lives in
`.claude/rules/slop-scan-for-docs.md` and
`Skill(scribe:slop-detector)`.

## Contract B: Describe the effect, never the slop or what was stripped

When a commit removes AI slop, strips AI-generated content, replaces
em-dashes, deletes AI phrasing, or de-slops prose, the commit message
MUST describe the change by its reader-facing effect. It names
**neither** the AI origin **nor** the specific marker that was
removed.

**Why.** The git history should not reveal that AI was used to write
the code, and it should not reveal that AI was used to remove the
markers of AI usage. Naming the origin (`AI slop`) discloses the
first. Naming the stripped marker (`replace em-dashes`) discloses the
second: it implies the prose carried AI fingerprints worth scrubbing,
which is itself a disclosure that AI authored it. A clean message
describes the improvement a human reader sees and stops there.

Do not write subjects or bodies that mention:

- **Origin or process**: `AI slop`, `AI-generated content`, `AI
  phrasing`, `AI markers`, `slop markers`, `de-slop`, `remove AI`,
  `strip AI`, or similar.
- **The specific stripped artifact**: `em-dash`, `em dashes`, `smart
  quotes`, `curly quotes`, `replace arrows`, `remove the plus signs`,
  or naming any marker from Contract A as the thing removed.

Classify the change normally (`docs`, `style`, `refactor`, ...) and
state what the prose or code now reads like or does:

| Instead of | Write |
|------------|-------|
| `docs: remove AI slop from README` | `docs: tighten README install steps` |
| `style: replace em-dashes with colons` | `docs: clarify the setup section` |
| `chore: de-slop the tutorial` | `docs: rewrite tutorial intro for clarity` |
| `docs: strip AI phrasing from guide` | `docs: rewrite guide in plain language` |
| `style: remove smart quotes and arrows` | `style: simplify the overview wording` |

The test: read the subject without knowing a slop pass happened. If
it still describes a real improvement to the reader, it passes. If it
only makes sense as "I cleaned up AI output", rewrite it.

Guard before committing:

```bash
SUBJECT_BODY=$(cat ./commit_msg.txt 2>/dev/null || true)
if printf '%s' "$SUBJECT_BODY" | grep -iqE \
  'ai[ -]?slop|ai[ -]?generated|ai[ -]?phrasing|slop marker|de-?slop|remove[d]? ai|strip ai|em[ -]?dash|emdash|smart quote|curly quote'; then
  echo "Rewrite: describe the reader-facing effect, not the slop or the marker removed"
fi
```

This contract is about the *commit message subject matter*. It does
not stop you from removing slop, it stops you from announcing it or
the markers you took out.
