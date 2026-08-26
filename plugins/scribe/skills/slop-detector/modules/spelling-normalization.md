---
module: spelling-normalization
category: detection
dependencies: [Read, Grep, Edit]
estimated_tokens: 850
---

# Spelling Normalization: British to American

The slop workflow normalizes British spellings to American by
default. This is a consistency concern, not a slop-density one, so it
runs as its own pass rather than feeding the tier scores.

This is orthography within English. It is not language detection
(`language-handling.md` handles English vs German vs French). A
British document is still English; only its spelling shifts.

## Default behavior

Convert British spellings to American in any scanned document, unless
the document opts out (see Opt-out) or a word is on the allowlist.
In prevention mode, meaning documents the agent just generated, the
target is zero British spellings.

## The one rule that matters

Use an explicit word list. Never apply a suffix transform.

A blanket "-ise becomes -ize" rule corrupts words that are -ise in
both dialects (surprise, exercise, advertise, comprise) and nouns
that are -ysis in both (analysis stays analysis). British English
also accepts -ize (Oxford spelling), so the suffix alone is not a
reliable signal. The curated map in
`data/spelling/british_american.yaml` lists explicit words and their
common inflections instead.

## Programmatic path (preferred)

The `scribe.spelling` module implements the pass and is unit-tested:

- `find_british_spellings(text, allowlist=None)` reports each
  occurrence with line, column, the matched word, and the American
  replacement. Use for flag-only review.
- `to_american(text, allowlist=None)` rewrites the text, preserving
  case (Colour to Color, COLOUR to COLOR) and leaving fenced code,
  inline code, and URLs untouched.

Both skip the per-document allowlist (case-insensitive). Conversion
is idempotent: no American value is also a British key.

## Manual detection (no Python available)

Grep for the highest-frequency families, then confirm each hit is
prose (not code, a URL, or a proper noun) before editing:

```bash
rg -n -i '\b(colou?r|behaviou?r|favou?rite|organis|recognis|optimis|\
analyse|centre|metre|licence|defence|catalogue|travell|grey|artefact)\w*' \
  --glob '*.md'
```

Treat matches inside code fences, inline code, and links as
false positives.

## What to leave alone (anti-goals)

- Code blocks, inline code, file paths, identifiers, and URLs. A CSS
  `color`, a variable `behaviour_flag`, or a link path is not prose.
- Proper nouns and cited titles: "Labour Party", "World Health
  Organisation", "Centre for Disease Control" (when quoting a name).
  Add these to the allowlist.
- Direct quotations of someone else's British text.
- Words that are identical in both dialects (do not "fix" surprise,
  exercise, analysis, focus, or status).

## Opt-out

A document or project may keep British spelling. Honor, in order:

1. `.slop-config.yaml` `spelling: british` (or `spelling: off`) for a
   project or subtree. See `config-file.md`.
2. The per-word `allowlist` in `.slop-config.yaml` for individual
   intentional terms.
3. An explicit user instruction in the session ("keep British
   spelling here").

When opted out, report British spellings as informational at most;
do not rewrite.

## Reporting

Group spelling hits separately from slop markers so the two concerns
stay legible:

```
### Spelling (British -> American)
- Line 12: "colour" -> "color"
- Line 40: "organisation" -> "organization"
- Skipped (allowlist): "Labour" x2
```
