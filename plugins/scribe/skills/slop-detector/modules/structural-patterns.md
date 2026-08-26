---
module: structural-patterns
category: detection
dependencies: [Bash, Grep]
estimated_tokens: 600
---

# Structural Pattern Detection

AI-generated text exhibits distinctive structural patterns beyond vocabulary.

The Tier 5 regexes below (spatial copula, negative parallelism,
contrastive parallelism, three-fragment burst, smart quotes, plus-sign
conjunction, arrow connector, throat-clearing) are mirrored in the
runtime source at `data/languages/en.yaml` § `tier5` and exposed by
`pattern_loader.get_tier5_patterns()`. The YAML is the single source of
truth for the regex; this module is the prose reference. Keep the two in
sync when editing a pattern.

## Em Dash Analysis

AI uses em dashes (—) excessively as a rhetorical device. The
em-dash has become the most-cited single AI tell on Reddit,
HN, Wikipedia, and the Field Guide. Detection has two modes:
*audit* (forensic, applied to existing prose) and *prevention*
(applied to newly generated prose).

```bash
# Count em dashes per file
em_count=$(grep -o '—' "$file" | wc -l)
word_count=$(wc -w < "$file")
density=$((em_count * 1000 / word_count))
```

### Audit mode (existing prose)

| Density (per 1000 words) | Signal |
|--------------------------|--------|
| 0-1 | Normal |
| 2-4 | Elevated |
| 5-9 | High AI signal |
| 10+ | Very high AI signal |

### Prevention mode (newly generated prose)

**Target: zero em-dashes.** When the slop-detector runs on
docs that an agent just wrote (auto-invoked after `/doc-generate`,
`/doc-polish`, `/update-readme`, `/update-docs`, etc.), every
em-dash is a finding. Replace before write:

| Original em-dash use | Replacement |
|----------------------|-------------|
| Brief aside ("X — which is Y — does Z") | Commas: "X, which is Y, does Z" |
| Tangential info ("X — a Y — does Z") | Parentheses: "X (a Y) does Z" |
| Completed thought ("X. — Y") | Period: "X. Y." |
| Definition ("X — a tool that...") | Colon: "X: a tool that..." |
| Dramatic pause ("X — and that's why") | Rewrite without the pause |

The audit threshold is empirical (tolerant of human writers
who use em-dashes legitimately). The prevention threshold is
agent-applied and strict.

## Tricolon Detection (Rule of Three)

AI produces groups of three with suspicious frequency:
both alliterative tricolons and structurally parallel
triads. Reddit citation data (2026) puts this at 1.2%
of audited posts, likely under-ranked because auditors
flag it in prose ("uses three-part structures
constantly") rather than in keyword searches.

Pattern examples:
- "clear, concise, and compelling" (alliterative)
- "fast, flexible, and free"
- "robust, reliable, and resilient"
- "It's fast. It's cheap. It's reliable." (three-fragment burst)
- "We tackle speed, cost, and quality" (reflexive tripling)

Detection approach:
```python
# Look for: adjective, adjective, and adjective
tricolon_pattern = r"\b(\w+), (\w+),? and (\w+)\b"
# Flag if words share first letter or similar endings

# Count three-item lists of any kind per 500 words
# > 2 triads in 500 words: signal (humans use one or two,
#   not reflexively every paragraph)
```

**Audit-mode threshold:** 2+ triads per 500 words is a
signal. 4+ is a strong AI signal. See also
`## Three-Fragment Burst` for the short-sentence variant.

## Sentence Length Uniformity

Human writing varies naturally. AI tends toward medium-length sentences.

```python
def sentence_uniformity(sentences):
    lengths = [len(s.split()) for s in sentences]
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    std_dev = variance**0.5
    return std_dev


# std_dev < 5: Suspicious uniformity
# std_dev 5-15: Normal variation
# std_dev > 15: High variation (human)
```

## Paragraph Symmetry

AI produces "blocky" text with uniform paragraph lengths.

```bash
# Check paragraph length distribution
awk '/^$/{if(p)print p; p=0; next}{p+=NF}END{print p}' file.md | sort -n | uniq -c
```

If most paragraphs cluster around the same length (e.g., 40-60 words), flag as AI signal.

## Bullet-to-Prose Ratio

AI defaults to bullet points, especially with emojis.
Reddit citation data (2026) puts excessive bullet use
at 1.7% of audited posts (#6 most-cited tell),
with both keyword and citation passes in agreement.
"5 ways to…" / "7 signs…" scaffolding reads as AI
even when the content is original.

```bash
# Count bullet lines vs total lines
if command -v rg &>/dev/null; then
  bullet_lines=$(rg -c '^\s*[-*]' "$file" || echo 0)
else
  bullet_lines=$(grep -c '^\s*[-*]' "$file" || echo 0)
fi
total_lines=$(wc -l < "$file")
ratio=$((bullet_lines * 100 / total_lines))
```

| Ratio | Signal |
|-------|--------|
| 0-30% | Normal |
| 30-50% | Elevated |
| 50-70% | High (check context) |
| 70%+ | Very high AI signal |

**Emoji bullets** (lines starting with emoji) in
technical documentation are a strong AI tell.

**Numbered "N things" listicles** ("5 ways to…",
"7 signs you might be…") are a format tell
independent of bullet count. Flag when the heading
encodes a count and the body is pure bullets.

## Five-Paragraph Essay Structure

AI defaults to intro, three body sections, and conclusion
recap. Reddit citation data (2026) puts this at 2.5% of
audited posts, the #5 most-cited tell. Auditors
noted it is likely under-counted (keyword regex at 0.5%
badly under-catches it because "formulaic-ness" requires
reading the whole structure). The signal is structural,
not lexical. A sentence-level scan will miss it.

Check for:
1. Opening paragraph that restates the prompt or question
2. Exactly three distinct middle sections
3. Closing paragraph that summarizes without adding new
   information ("in conclusion, we have explored...")

The "in conclusion" closer is the lexical handle
(detected in `vocabulary-patterns.md` Tier 4). When
combined with opener-restates-prompt and three-body,
treat as a confirmed pattern regardless of vocabulary.

## Perfect Grammar Signals

| Pattern | Human Range | AI Signal |
|---------|-------------|-----------|
| Contractions | Common | Rare/absent |
| Oxford commas | Variable | Always present |
| Typos | Occasional | None |
| Sentence fragments | Present | Rare |
| Starting with "And" or "But" | Common | Rare |

## Register Uniformity

Human writing shifts between abstract and concrete, formal and casual. AI maintains consistent register throughout.

Check for:
- Absence of colloquialisms
- No slang or informal expressions
- Uniform formality level across all sections

## Participial Phrase Tail-Loading

AI appends present participial (-ing) phrases to sentence ends at 2-5x the human rate (Wagner 2025).

Pattern: `[Main clause], [present participle] [detail].`

Examples:
- "The team developed a framework, **enabling** researchers to analyze data."
- "The policy was implemented, **marking** a shift in approach."
- "She published findings, **contributing** to the body of research."

```python
# Detect sentences ending with ", [word]-ing ..."
participial_tail = r",\s+\w+ing\s+[\w\s]+\.$"
# 3+ matches in a paragraph is a strong signal
```

The generic detector catches any comma-led `-ing` tail. The
runtime also pins the highest-signal specific words in
`tier5.participial_tail` (`data/languages/en.yaml`):
`, highlighting`, `, showcasing`, `, underscoring`,
`, paving the way for`, `, demonstrating`, `, proving that`,
`, reinforcing`, `, enabling`. These fake-analysis tack-ons are
high-confidence. Flag any match.

| Count per 500 words | Signal |
|---------------------|--------|
| 0-1 | Normal |
| 2-3 | Elevated |
| 4+ | Strong AI signal |

## Emphasis Crutches

Manufactured-importance terminators AI stamps onto a sentence to
inject authority or drama. Mirrors `tier5.emphasis_crutch` in
`data/languages/en.yaml`.

| Phrase | Why it's slop |
|--------|---------------|
| "Full stop." | Pseudo-authoritative period-stamp |
| "Make no mistake" | Dramatic-declarative throat-clearing |
| "Read that again." | Emphasis crutch for a stat |
| "Mark my words" | Prophetic-authority filler |

```python
TIER5_EMPHASIS_CRUTCH = [
    r"\bfull stop\.",
    r"\bmake no mistake\b",
    r"\bread that again\.?",
    r"\bmark my words\b",
]
```

## "From X to Y" Range Construction

AI uses this template to express scope at much higher rates than human writers.

Examples:
- "From bustling cities to serene landscapes"
- "From beginners to experts"
- "From ancient traditions to modern innovations"

```python
from_to_pattern = r"\bfrom\s+[\w\s]+\s+to\s+[\w\s]+"
```

## Correlative Conjunction Overuse

AI over-relies on correlative pairs in close proximity:

| Pattern | Example |
|---------|---------|
| "whether...or" | "Whether you're a beginner or an expert" |
| "not only...but also" | "Not only does it improve X, but also Y" |
| "not just...but" | "Not just a tool, but a transformation" |

2+ correlative pairs in the same paragraph is a signal.

## ASCII Arrow Prose Connector

AI uses `->` and `→` as prose shorthand instead of writing
"to", "into", or "produces". Arrows are fine in code, type
signatures, and diagrams but mark AI-generated prose.

Examples:
- "spec -> plan -> tasks" (slop)
- "spec to plan to tasks" (human)
- "returns `int -> str`" (fine, code context)

```bash
# Detect arrows in prose (exclude code blocks)
awk '/^```/{c=!c}!c' file.md | grep -oP '\s->\s|→' | wc -l
```

## Plus-Sign Conjunction

AI uses `+` as a conjunction ("X + Y") in prose instead of
"and" or "with". This is a strong AI tell because human writers
almost never reach for `+` in prose. They have the word "and"
available. Fine in code, math, labels, version strings.

Examples:
- "hooks + skills" (slop)
- "hooks and skills" (human)
- "1 + 1 = 2" (fine, math)
- "Python 3.11+" (fine, version)
- "PostgreSQL + Redis stack" (slop in body prose; ok in a
  diagram label or stack-name tag)

```bash
# Detect prose plus signs (word + word pattern, exclude code)
awk '/^```/{c=!c}!c' file.md | grep -oP '\w\s\+\s\w' | wc -l
```

### Prevention rule

In newly generated prose, **every prose `+` is a finding.**
Replace `X + Y` with `X and Y`, `X with Y`, or restructure.

## Spatial Copula / Animated Inanimates

AI substitutes spatial or animate verbs for plain "is/are"
to inject false gravitas. The hallmark is a verb whose subject
is *inanimate* but the verb implies *agency or embodiment*. See
also `vocabulary-patterns.md` Tier 5 for the word list.

Trigger verbs (flag when the subject is inanimate and the
verb is one of these):

```
lives in, lives at, sits at, sits between, sits within,
stands as, rests on, dwells in, exists at,
serves as, marks, represents, embodies, constitutes,
boasts, features, maintains, encompasses,
rooted in, anchored in, nestled in, situated at
```

Examples:

- "The skill **lives in** `plugins/scribe/`" (slop;
  the skill **is in** `plugins/scribe/`)
- "The cache **sits between** the API and database"
  (slop; the cache **is between**...)
- "The library **boasts** 50 features" (slop; the
  library **has** 50 features)
- "The framework **stands as a testament to** Y"
  (slop; delete or rewrite)

```bash
# Detect spatial copula verbs (exclude code blocks)
awk '/^```/{c=!c}!c' file.md | \
  grep -oP '\b(lives?|sits?|stands?|rests?|dwells?)\s+(in|at|on|between|within)\b' | \
  wc -l
```

| Count per 1000 words | Signal |
|----------------------|--------|
| 0 | Normal |
| 1-2 | Elevated; check subject animacy |
| 3+ | Strong AI signal |

### When to skip

- Subject is literally animate ("the developer lives in
  Berlin").
- Subject is a daemon, process, container, or service that
  has actual runtime presence ("the agent **runs** at
  `/var/run/...`", though prefer "runs" over "lives").
- Inside dialogue, quotations, or transcripts.
- Botanical/biological/etymological context ("the variant
  is rooted in Latin").

## Negative Parallelism Constructions (Contrastive Negation)

The strongest non-vocabulary 2026 prose tell. Independently
flagged by Wikipedia, OliviaCal, ContentBeta, Stop-Slop, and
George Kao. AI reaches for these rhetorical scaffolds when it
has no real argument to make.

In linguistics this family is **contrastive negation**: a
clause that negates one element to assert another ("not X,
but Y"). It is one half of a broader device, **contrastive
parallelism** (antithesis); the affirmative half, which has no
"not" anchor, is covered in the next section. Treat both the
same way: avoid them in all but the most necessary cases. The
test for "necessary" is whether deleting the contrast loses
information. "We use Python instead of Java" keeps a fact;
"It's not a tool, it's a transformation" keeps nothing.

| Pattern | Example |
|---------|---------|
| `It's not X, it's Y` (leading) | "It's not a tool, it's a transformation" |
| `It's X, not Y` (copula-led trailing) | "It's a tool, not a toy" |
| `Not just X, but Y` | "Not just fast, but elegant" |
| `Not only X, but also Y` | "Not only saves time, but also improves quality" |
| `No X. No Y. Just Z.` | "No friction. No setup. Just code." |
| `No X, no Y, no Z` | "No friction, no setup, no config." |
| `Y, not X` (bare trailing) | "The API is clear, not a gimmick." |
| `Not because X. Because Y.` | "Not because it's hard. Because it matters." |
| `X. That's it. That's the Y.` | "Documentation. That's it. That's the feature." |
| `And that's okay.` | (closing reassurance with no information) |

The copula-led trailing form ("It's X, not Y", "This is X, not Y")
is the one that survives casual proofreading: the opener reads as
a plain definition, so the corrective tail slips through. It is the
same scaffold as the leading "It's not X, it's Y", just reordered.

```python
NEGATIVE_PARALLELISM = [
    # "It's not X, it's Y" — X can be multi-word (e.g., "a tool")
    r"\bIt's not [\w\s]+?,\s+it's \w+",
    r"\bNot just \w+,?\s+but (?:also )?\w+",
    r"\bNot only \w+,?\s+but (?:also )?\w+",
    r"\bNo \w+\.\s+No \w+\.\s+Just \w+",
    # Comma-joined variant: "No X, no Y, no Z"
    r"\bNo \w+,\s+no \w+(?:,\s+no \w+)*",
    # Copula-led trailing corrective: "It's X, not Y" / "This is X,
    # not Y". The opener marks a definitional statement, so the regex
    # is high-precision even mid-sentence and with an article on Y.
    r"\b(?:It's|It is|This is|That's|That is|These are|Those are)\s+[\w\s]+?,\s+not\b",
    # Bare trailing corrective negation: "Y, not X." The optional
    # article catches "clear, not a gimmick." as well as "clear, not
    # clever." Genuine either/or choices (e.g. "Python, not Java") are
    # slop too; rewrite as "Y instead of X" to keep the contrast
    # without the negation.
    r"\b\w+,\s+not\s+(?:just\s+|a\s+|an\s+|the\s+)?\w+[.!?]",
    r"\bNot because \w+\.\s+Because \w+",
    r"\.\s+That's it\.\s+That's the\b",
    r"\bAnd that's okay\.",
]
```

These mirror `data/languages/en.yaml` § `tier5.negative_parallelism`
(the runtime source). When you change one, change the other and run
`pytest tests/test_slop_patterns.py tests/test_pattern_loader.py`.

### Prevention rule

Any match in newly generated docs is a hard failure. Rewrite
positively: state what the thing *is* rather than what it
isn't, then what it does.

| Slop | Rewrite |
|------|---------|
| "Not just fast, but elegant" | "Fast and elegant" or "Fast; the API is also clean" |
| "It's not a tool, it's a transformation" | "It is a tool. It changes how you do X." |
| "It's a tool, not a toy." | "It is a tool." (drop the corrective tail) |
| "No friction. No setup. Just code." | "Zero-setup. Drop in and run." |
| "No friction, no setup, no config." | "Zero-setup and zero-config." |
| "The API is clear, not clever." | "The API is clear." (drop the corrective tail) |
| "We use Python, not Java." | "We use Python instead of Java." (keep the contrast, drop the negation) |

## Trailing Contrastive Negation (mid-sentence)

The bare trailing regex above requires the sentence to end one word
after "not", so a longer tail slips past it. "The third sends your
code, not just a status check." was live in this repository's README
until review caught it by eye.

Four surface forms, all named independently by GC AI, Programmer.ie,
the Wikipedia *Negative parallelism* article, and DEV Community:

| Pattern | Example | Rewrite |
|---------|---------|---------|
| `X, not just Y` (any position) | "sends your code, not just a status check" | "sends the contents of your files" |
| `isn't just X, but Y` | "isn't just a linter, but a review harness" | "is a review harness" |
| `more than X, it's Y` | "more than a document, it's a co-editing surface" | "is a co-editing surface" |
| `not about X, it's about Y` | "not about looking modern, it's about being usable" | "is about being usable" |

The negated half has to be an elevation for this to fire. "The probe
does not run, because gemini authenticates by key" states a fact and
is deliberately unmatched: every regex needs "just", "about ... it's
about", or a copula after the comma.

Runtime source: `data/languages/en.yaml` §
`tier5.contrastive_negation_trailing`, scored `high` confidence.

## Contrastive Scaffold ("rather than" / "instead of", opt-in)

A definitional frame built on a connective: "the gate reports the
failure rather than swallowing it".

**This is not a documented AI tell, and the category is off by
default.** No source in the contrastive-negation literature names
either connective, and both are ordinary English. Measured across this
repository's markdown, "rather than" appears 504 times and "instead
of" 299, almost all correctly, including in the rule files that define
house style. A default-on version would bury a real finding under
hundreds of correct sentences.

Enable it for a documentation audit where defining things by contrast
is the suspected habit. Surface every hit for a human; never
auto-rewrite. It is scoped to the verb-phrase form, so the
"Y instead of X" rewrite recommended in the table above stays valid:
that is a noun comparison, and it keeps the alternative the reader
needed.

Runtime source: `data/languages/en.yaml` § `tier5.contrastive_scaffold`,
`default_enabled: false`, `confidence: low`.

## Negative Framing (Litotes, Vacuous Negation, Negative Definition)

Negative parallelism above is a scaffold: *not X, but Y*. This is a
different failure, and it has three shapes plus a document-level
measure. All four mirror `data/languages/en.yaml`; change one, change
the other, and run `pytest tests/test_slop_patterns.py
tests/test_negation_density.py`.

### Litotes (double negation)

`tier5.litotes`. Score 2, high confidence, on by default. Two
negations to say one positive thing costs the reader a step and buys
nothing, and the positive form always exists, so these are safe to
rewrite rather than merely surface.

| Slop | Rewrite |
|------|---------|
| "This failure is not uncommon" | "This failure is common" or give the rate |
| "The syntax is not unlike Python" | "The syntax resembles Python" |
| "The cost is not insignificant" | "The cost is 40ms per call" |
| "It never fails to surface the bug" | "It surfaces the bug every time" |
| "The argument is not without merit" | "The argument has merit" |

The stems are enumerated in the YAML rather than matched with
`not\s+(?:un|in)\w+`. The general form fires on "not until", "not
inside", "not intended" and "not include", which are ordinary prose.

### Vacuous negation

`tier5.vacuous_negation`. Score 2, high confidence, on by default.
Negation clichés that claim weight and supply none. The test is
deletion: if the sentence says the same thing without the phrase, the
phrase was filler.

| Slop | Rewrite |
|------|---------|
| "The importance cannot be overstated" | State the consequence, or delete |
| "The risk is not to be underestimated" | Name the risk and its size |
| "It goes without saying that X" | "X" |
| "Needless to say, Y" | "Y" |
| "Shipping this was no small feat" | Say what made it hard |

Negation carrying a fact is left alone: "the hook cannot reach the
registry, so it warns" is a mechanism, not a cliché.

### Negative definition (opt-in)

`tier5.negative_definition`. Score 1, low confidence,
`default_enabled: false`. Behavior described only by what it will not
do leaves the reader to infer the rest.

| Slop | Rewrite |
|------|---------|
| "The parser doesn't handle nested blocks" | "The parser accepts flat blocks" |
| "The exporter does not support CSV" | "The exporter emits JSON and Parquet" |
| "The daemon is unable to recover" | "The daemon requires a clean restart" |

This one stays gated off for the same reason as
`anthropomorphism_low`: precise negation is how contracts,
invariants and trust boundaries are correctly written, and a rule file
built out of "do not use for", "must not" and "never" is doing its
job. A default-on version buries one real finding under hundreds of
correct sentences. Enable it when auditing reference documentation,
where negative definition is a genuine tell. Surface every hit for a
human to judge; never auto-rewrite. Prohibitions, invariants, and a
bare "cannot" carrying a fact are deliberately unmatched.

### Density (the "overly relies" measure)

`scribe.negation.check_negation_density`. A regex counts instances and
cannot measure over-reliance, which is a property of the page: a
document where most sentences say what something will not do reads as
evasive even when every sentence is correct.

The check splits prose into sentences, drops fenced and inline code,
and reports the share carrying a negation marker against an advisory
bar of 35%, with a floor of 8 sentences because a ratio over a handful
of sentences describes the sample rather than the writing. The finding
carries its own arithmetic so a reader can check it without rerunning.

Advisory only. Never gate a merge on it.

## Contrastive Parallelism (Affirmative Antithesis)

The affirmative sibling of contrastive negation: two parallel
clauses set in opposition with no "not" anchor. AI reaches for
antithesis to manufacture punch, the same impulse behind the
negation form, but without the "not" it slips past a scan that
only looks for "not X, but Y".

| Pattern | Example |
|---------|---------|
| `Less X, more Y` / `More X, less Y` | "Less config, more code" |
| `Where others X, we Y` | "Where others add complexity, we remove it" |
| Subject-swap clauses | "Humans propose; machines dispose" |
| `Old way: X. New way: Y.` framing | "Old way: tickets. New way: chat" |
| Chiasmus (reversed repetition) | "Code you can read, read code you can trust" |

```python
# Only the comparative form is reliable enough to flag
# automatically; the rest are judgment-level (confidence: low).
CONTRASTIVE_PARALLELISM = [
    # "Less X, more Y" / "More X, less Y" — comparative antithesis
    r"\b(?:Less|More)\s+\w+,\s+(?:less|more)\s+\w+",
    # "Where others X, we Y" — pronoun guard limits locative false
    # positives ("where the file is, the system...") but not all
    r"\bWhere\s+[\w\s]+?,\s+(?:we|you|they|it)\b",
]
```

Subject-swap clauses, `Old way:/New way:` framing, and chiasmus
resist a tight regex (the opposition is semantic, not lexical).
Flag them by reading, mark `confidence: low`, and surface for
human decision rather than auto-rewriting. `Before:`/`After:`
labels are common in legitimate code examples; do not flag them
as antithesis.

### Prevention rule

In newly generated docs, treat affirmative antithesis the same
as contrastive negation: avoid in all but the most necessary
cases. Keep it only when both sides are concrete, the contrast
is load-bearing, and you use it once rather than as a rhythm.
Rewrite decorative antithesis as a plain statement.

| Slop | Rewrite |
|------|---------|
| "Less config, more code" | "Setup is one file; the rest is code" |
| "Where others add complexity, we remove it" | "This removes a configuration step competitors require" |
| "Humans propose; machines dispose" | "A human picks the option; the agent applies it" |

## Three-Fragment Burst

AI loves three short fragments in a row, usually adjectives
or verbs separated by periods. ContentBeta and the Stop-Slop
skill both name this directly.

Examples:

- "Focused. Aligned. Measurable."
- "Fast. Reliable. Cheap."
- "Built. Tested. Shipped."

```python
# Detect three single-word sentences in sequence
three_fragment = r"\b([A-Z][a-z]+)\.\s+([A-Z][a-z]+)\.\s+([A-Z][a-z]+)\."
```

| Count per 1000 words | Signal |
|----------------------|--------|
| 0-1 | Normal (legitimate punchy close) |
| 2+ | Strong AI signal; formulaic |

### When to skip

- The fragments are proper nouns or technical terms (e.g.,
  "Rust. Python. Go.").
- Inside a heading or chapter title.

## Smart Quotes / Curly Quotation Marks

AI tools default to smart quotes (`"`, `"`, `'`, `'`)
because their copy-paste source was a word processor. In
plain-text docs, source code, and most markdown, prefer
straight quotes (`"`, `'`).

```bash
# Detect smart quotes outside code blocks
awk '/^```/{c=!c}!c' file.md | grep -oP '[“”‘’]' | wc -l
```

| Count per 1000 words | Signal |
|----------------------|--------|
| 0 | Normal for technical docs |
| 1-2 | Elevated (probable AI paste) |
| 3+ | Strong AI signal |

### When to skip

- The project is fiction or long-form publishing where smart
  quotes are house style.
- The match is inside a quoted excerpt from a published source.

## Colon Addiction

AI uses colons to introduce explanations at 3-5x the human rate.

Pattern: "Topic: explanation" as a sentence structure.

```bash
# Count colons used as sentence-internal punctuation
grep -oP '(?<=[a-z]): (?=[A-Z])' file.md | wc -l
```

Combined with em dash overuse, this creates a "punctuation for professionalism" signature.

## Semicolon Avoidance

AI rarely uses semicolons. The ratio of em dashes to semicolons is skewed compared to human writing, where semicolons appear in roughly 1 in 50 sentences for experienced writers.

```bash
em_dashes=$(grep -o '—' file.md | wc -l)
semicolons=$(grep -o ';' file.md | wc -l)
# Human ratio: roughly equal. AI ratio: 10:1 or worse.
```

The avoidance heuristic is about a *missing* semicolon where a
human would use one. It is not a license to add them. The
opposite failure, below, is now the more common one.

## Semicolon Splice

Newer models reach for the semicolon as a sophistication
marker, splicing two independent clauses where a period or a
coordinating conjunction reads more naturally. The clause after
the semicolon could stand alone as its own sentence, and almost
always reads better that way. Use a semicolon in prose only
when it is absolutely necessary: a list whose items already
carry internal commas is the one durable case.

Examples:

- "The system is fast; it handles a million requests." (slop;
  split into two sentences, or join with "and")
- "Run the tests; they validate the change." (slop; "Run the
  tests. They validate the change.")
- "The cache holds three tiers: hot, in memory; warm, on
  local disk; and cold, in object storage." (fine; the items
  carry internal commas, so the semicolons disambiguate)

Rephrase, in order of preference:

1. Split into two sentences (period). Default choice.
2. Join with a coordinating conjunction ("and", "but", "so")
   when the clauses are tightly linked.
3. Keep the semicolon only when removing it creates ambiguity
   (a list with internal commas).

```bash
# Detect prose semicolons (word ; word). The awk pass strips
# fenced code; the sed pass strips inline code (`x;`) and URLs,
# so a backticked `arr.push();` never counts. This mirrors the
# spelling normalizer's protected spans (fenced + inline + URL).
# Confidence is low: every remaining hit is surfaced for human
# judgment, not auto-rewritten. A list with internal commas is
# a keep.
awk '/^```/{c=!c}!c' file.md \
  | sed -E 's/`[^`]*`//g; s#https?://[^ ]*##g' \
  | grep -oP '\w;\s+\w' | wc -l
```

## Sentence Length Clustering (Refined)

**Reddit citation data (2026) puts flat sentence rhythm
at 4.0% — the #2 most-cited human tell**, behind only
the em dash. It is also the most important regex-blind
tell: no keyword scanner can catch it. Readers describe
it as "the same cadence", "syntactic mad-lib",
"recognizable rhythm even without looking at the words."

The specific AI cluster is **15-25 words per sentence**.
Human writing ranges from 3-word fragments to 40+
word complex sentences. AI avoids both extremes.

```python
def length_clustering(sentences):
    lengths = [len(s.split()) for s in sentences]
    in_range = sum(1 for l in lengths if 15 <= l <= 25)
    return in_range / len(lengths)


# > 0.7 (70% of sentences in 15-25 range): strong AI signal
# > 0.85: very strong; only a deliberate style choice
#         would produce this in human writing
```

**Detection note:** rhythm uniformity and the 15-25
word cluster are complementary. A low `sentence_std_dev`
(see `## Sentence Length Uniformity` above) catches
uniform-but-short or uniform-but-long writing. The
cluster ratio catches the specific medium-sentence band
AI prefers. Run both.

**Prevention rule:** vary sentence length deliberately.
Let some sentences be 4-6 words. Let some run past 35
words when the logic requires it. The test: read it
aloud. If it sounds like a metronome, rewrite.

## Topic-Evidence-Summary Paragraph Template

AI paragraphs follow a rigid structure:
1. Topic sentence (states the point)
2. Supporting detail (1-3 sentences)
3. Summary/transition (restates or bridges)

Human writers vary this: some paragraphs are all evidence, some start with a question, some end abruptly.

Detection: check if the first and last sentences of each paragraph express the same idea using different words.

## Conclusion Mirroring

AI introductions and conclusions are near-paraphrases of each other. Check cosine similarity between first and last paragraphs.

Human writing ends with specifics, callbacks to earlier points, questions, or simply stops.

## Sycophancy / Position-Avoidance

**Reddit citation data (2026): 2.5% — the #4 tell.**
Auditors believe this is significantly under-ranked
because it is hard to isolate in a keyword pass.
One auditor found it rivals the em dash for citation
density within long posts about AI writing quality.

**Radar pattern (two behaviors, same root cause):**

1. **Sycophancy** — agrees, flatters, or hedges instead
   of taking a position. Opener-level: "Great question!",
   "You're absolutely right!", "Absolutely!". Body-level:
   qualifies every claim ("it depends", "it could be
   argued", "there are several approaches").

2. **Position-avoidance** — gives a menu instead of an
   answer. "On one hand X, on the other hand Y" without
   concluding. Listing every option when the user asked
   for a recommendation. Ending with "it's up to you"
   after presenting options.

Both behaviors trace to the same RLHF pressure: the
model is tuned toward agreement and safety, which
produces a voice that never commits. One Reddit commenter
quoted: *"Default Claude hedges everything. 'It depends
on your needs.' 'There are several approaches.'"*

**Detection (reader-level only; no regex can catch this):**

Ask these questions after reading a document:

- Does the author ever disagree with anything?
- Does the author give a direct answer, or a menu?
- When asked for a recommendation, does it arrive?
- Is the tone uniformly positive? No friction anywhere?
- Does every section end with a caveat or qualifier?

4+ "yes" answers = strong sycophancy signal.

**Boilerplate sycophancy phrases** (these ARE catchable):

```python
SYCOPHANCY_BOILERPLATE = [
    r"\bgreat question\b",
    r"\bexcellent question\b",
    r"\bthank you for (?:asking|raising|bringing)\b",
    r"\byou(?:'re| are) absolutely right\b",
    r"\bwould you like me to\b",
    r"\bI hope this helps\b",
    r"\bfeel free to ask\b",
    r"\blet me know if you (?:have|need)\b",
    r"\bplease (?:let me know|feel free)\b",
]
```

These are the lexical surface of a deeper pattern.
Their presence confirms sycophancy; their absence does
not rule it out. See also `identity-and-voice-leaks.md`
for the full boilerplate artifact list.

**Scoring:** in the structural score, 1+ boilerplate
phrases = +2. Reader-detected position-avoidance = +3
(flag in findings as `confidence: reader`).

## Fluent-but-Empty Prose

**Reddit citation data (2026): 0.7% — the #9 tell.**
Multiple auditors flag it as under-counted because it
is the hardest tell to isolate and the hardest to
articulate: *"AI writes word salad — beautiful looking
but has no nutritional value."* Another: *"No grammar
mistakes on essays that use elevated language but
ultimately say very little."*

**Root cause:** the model is optimized for fluency and
positive assessment, not for making claims. It produces
sentences that are grammatically correct, confident in
register, and contain no verifiable assertion.

**Detection test per paragraph:**

1. Identify the claim the paragraph makes.
2. Could you replace it with a single concrete fact,
   a number, or a named example?
3. If yes, the original paragraph is likely empty —
   the concrete version carries all the information.

**Pattern indicators (no regex; requires reading):**

- Every sentence is grammatically complete but none
  makes a falsifiable claim.
- Abstract nouns stack: "approach", "framework",
  "methodology", "strategy", "solution", "value."
- Sentences can be swapped between paragraphs without
  changing meaning.
- Removing a sentence does not change what the reader
  learns.
- The "word count" increases without the "information
  count" increasing.

**Prevention rule:** every paragraph must carry at
least one concrete item — a named example, a number,
a verifiable fact, or a specific decision. If it
cannot, delete it or compress it to one sentence.

**Scoring:** reader-detected; flag as `confidence:
reader`, add +2 to structural score per confirmed
empty paragraph (max 3 instances to cap at +6).

## Structural Score Calculation

```python
def structural_score(metrics):
    score = 0
    if metrics["em_dash_density"] > 5:
        score += 2
    if metrics["sentence_std_dev"] < 5:
        score += 2
    if metrics["bullet_ratio"] > 0.5:
        score += 2
    if metrics["paragraph_uniformity"] > 0.8:
        score += 2
    if metrics["zero_contractions"]:
        score += 1
    if metrics["emoji_bullets"]:
        score += 3
    # 2025-2026 research patterns
    if metrics.get("participial_tail_count", 0) > 3:
        score += 2
    # Sentence rhythm (#2 Reddit tell, 4.0% citation rate):
    # weighted higher than in earlier versions.
    if metrics.get("sentence_length_cluster_ratio", 0) > 0.7:
        score += 3  # was 2; elevated to match empirical ranking
    if metrics.get("sentence_length_cluster_ratio", 0) > 0.85:
        score += 1  # extra point for extreme clustering
    if metrics.get("semicolon_count", 1) == 0 and metrics.get("em_dash_density", 0) > 3:
        score += 1
    if metrics.get("correlative_pairs", 0) > 2:
        score += 1
    if metrics.get("arrow_connectors", 0) > 0:
        score += 1
    if metrics.get("plus_conjunctions", 0) > 1:
        score += 1
    if metrics.get("triad_count", 0) > 2:
        score += 1  # rule of three (#8 tell, 1.2% citation)
    # Tier 5 / 2026 structural patterns
    if metrics.get("spatial_copula_count", 0) >= 1:
        score += 2
    if metrics.get("negative_parallelism_count", 0) >= 1:
        score += 3
    if metrics.get("litotes_count", 0) >= 1:
        score += 2
    if metrics.get("vacuous_negation_count", 0) >= 1:
        score += 2
    # negative_definition and negation density are surfaced, not scored:
    # one is opt-in and low confidence, the other is a document-level
    # reading rather than a per-instance finding.
    # Affirmative antithesis: comparative form scores; judgment-level
    # matches (subject-swap, chiasmus) are surfaced, not scored.
    if metrics.get("contrastive_parallelism_count", 0) >= 1:
        score += 2
    if metrics.get("three_fragment_burst_count", 0) >= 2:
        score += 2
    if metrics.get("smart_quote_count", 0) >= 3:
        score += 1
    if metrics.get("emphasis_crutch_count", 0) >= 1:
        score += 2
    # Sycophancy / position-avoidance (#4 Reddit tell, 2.5% citation):
    # boilerplate phrases are lexically detectable.
    if metrics.get("sycophancy_boilerplate_count", 0) >= 1:
        score += 2
    # Reader-detected sycophancy / fluent-empty prose: surfaced with
    # confidence:reader, not auto-scored. Callers may inject via:
    #   metrics['reader_sycophancy'] = True  (from manual review)
    #   metrics['reader_empty_prose_count'] = N (paragraphs)
    if metrics.get("reader_sycophancy", False):
        score += 3
    score += min(6, metrics.get("reader_empty_prose_count", 0) * 2)
    # Prevention mode: any em-dash in fresh prose is a finding
    if metrics.get("mode") == "prevention" and metrics.get("em_dash_count", 0) > 0:
        score += min(5, metrics["em_dash_count"])
    return min(10, score)
```
