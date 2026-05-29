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

## Tricolon Detection

AI produces alliterative groups of three with suspicious frequency.

Pattern examples:
- "clear, concise, and compelling"
- "fast, flexible, and free"
- "robust, reliable, and resilient"

Detection approach:
```python
# Look for: adjective, adjective, and adjective
tricolon_pattern = r'\b(\w+), (\w+),? and (\w+)\b'
# Flag if words share first letter or similar endings
```

## Sentence Length Uniformity

Human writing varies naturally. AI tends toward medium-length sentences.

```python
def sentence_uniformity(sentences):
    lengths = [len(s.split()) for s in sentences]
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    std_dev = variance ** 0.5
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

```bash
# Count bullet lines vs total lines
bullet_lines=$(grep -c '^\s*[-*]' file.md)
total_lines=$(wc -l < file.md)
ratio=$((bullet_lines * 100 / total_lines))
```

| Ratio | Signal |
|-------|--------|
| 0-30% | Normal |
| 30-50% | Elevated |
| 50-70% | High (check context) |
| 70%+ | Very high AI signal |

**Emoji bullets** (e.g., lines starting with emoji) in technical documentation are a strong AI tell.

## Five-Paragraph Essay Structure

AI defaults to: intro, three body sections, and conclusion recap.

Check for:
1. Opening paragraph that restates the question
2. Three distinct middle sections
3. Closing paragraph that summarizes without adding new information

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
participial_tail = r',\s+\w+ing\s+[\w\s]+\.$'
# 3+ matches in a paragraph is a strong signal
```

| Count per 500 words | Signal |
|---------------------|--------|
| 0-1 | Normal |
| 2-3 | Elevated |
| 4+ | Strong AI signal |

## "From X to Y" Range Construction

AI uses this template to express scope at much higher rates than human writers.

Examples:
- "From bustling cities to serene landscapes"
- "From beginners to experts"
- "From ancient traditions to modern innovations"

```python
from_to_pattern = r'\bfrom\s+[\w\s]+\s+to\s+[\w\s]+'
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
| `It's not X, it's Y` | "It's not a tool, it's a transformation" |
| `Not just X, but Y` | "Not just fast, but elegant" |
| `Not only X, but also Y` | "Not only saves time, but also improves quality" |
| `No X. No Y. Just Z.` | "No friction. No setup. Just code." |
| `No X, no Y, no Z` | "No friction, no setup, no config." |
| `Y, not X` (trailing) | "The API is clear, not clever." |
| `Not because X. Because Y.` | "Not because it's hard. Because it matters." |
| `X. That's it. That's the Y.` | "Documentation. That's it. That's the feature." |
| `And that's okay.` | (closing reassurance with no information) |

```python
NEGATIVE_PARALLELISM = [
    # "It's not X, it's Y" — X can be multi-word (e.g., "a tool")
    r"\bIt's not [\w\s]+?,\s+it's \w+",
    r"\bNot just \w+,?\s+but (?:also )?\w+",
    r"\bNot only \w+,?\s+but (?:also )?\w+",
    r"\bNo \w+\.\s+No \w+\.\s+Just \w+",
    # Comma-joined variant: "No X, no Y, no Z"
    r"\bNo \w+,\s+no \w+(?:,\s+no \w+)*",
    # Trailing corrective negation: "Y, not X." Genuine either/or
    # choices (e.g. "Python, not Java") are slop too; rewrite as
    # "Y instead of X" to keep the contrast without the negation.
    r"\b\w+,\s+not\s+(?:just\s+)?\w+[.!?]",
    r"\bNot because \w+\.\s+Because \w+",
    r"\.\s+That's it\.\s+That's the\b",
    r"\bAnd that's okay\.",
]
```

### Prevention rule

Any match in newly generated docs is a hard failure. Rewrite
positively: state what the thing *is* rather than what it
isn't, then what it does.

| Slop | Rewrite |
|------|---------|
| "Not just fast, but elegant" | "Fast and elegant" or "Fast; the API is also clean" |
| "It's not a tool, it's a transformation" | "It is a tool. It changes how you do X." |
| "No friction. No setup. Just code." | "Zero-setup. Drop in and run." |
| "No friction, no setup, no config." | "Zero-setup and zero-config." |
| "The API is clear, not clever." | "The API is clear." (drop the corrective tail) |
| "We use Python, not Java." | "We use Python instead of Java." (keep the contrast, drop the negation) |

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
three_fragment = r'\b([A-Z][a-z]+)\.\s+([A-Z][a-z]+)\.\s+([A-Z][a-z]+)\.'
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

## Sentence Length Clustering (Refined)

Beyond uniformity (tracked above), the specific AI cluster is **15-25 words per sentence**. Human writing ranges from 3-word fragments to 40+ word complex sentences. AI avoids both extremes.

```python
def length_clustering(sentences):
    lengths = [len(s.split()) for s in sentences]
    in_range = sum(1 for l in lengths if 15 <= l <= 25)
    return in_range / len(lengths)

# > 0.7 (70% of sentences in 15-25 range): strong AI signal
```

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

## Structural Score Calculation

```python
def structural_score(metrics):
    score = 0
    if metrics['em_dash_density'] > 5:
        score += 2
    if metrics['sentence_std_dev'] < 5:
        score += 2
    if metrics['bullet_ratio'] > 0.5:
        score += 2
    if metrics['paragraph_uniformity'] > 0.8:
        score += 2
    if metrics['zero_contractions']:
        score += 1
    if metrics['emoji_bullets']:
        score += 3
    # New patterns (2025-2026 research)
    if metrics.get('participial_tail_count', 0) > 3:
        score += 2
    if metrics.get('sentence_length_cluster_ratio', 0) > 0.7:
        score += 2
    if metrics.get('semicolon_count', 1) == 0 and metrics.get('em_dash_density', 0) > 3:
        score += 1  # em dashes without semicolons
    if metrics.get('correlative_pairs', 0) > 2:
        score += 1
    if metrics.get('arrow_connectors', 0) > 0:
        score += 1
    if metrics.get('plus_conjunctions', 0) > 1:
        score += 1
    # Tier 5 / 2026 structural patterns
    if metrics.get('spatial_copula_count', 0) >= 1:
        score += 2
    if metrics.get('negative_parallelism_count', 0) >= 1:
        score += 3
    # Affirmative antithesis: comparative form scores; judgment-level
    # matches (subject-swap, chiasmus) are surfaced, not scored.
    if metrics.get('contrastive_parallelism_count', 0) >= 1:
        score += 2
    if metrics.get('three_fragment_burst_count', 0) >= 2:
        score += 2
    if metrics.get('smart_quote_count', 0) >= 3:
        score += 1
    # Prevention mode: any em-dash in fresh prose is a finding
    if metrics.get('mode') == 'prevention' and metrics.get('em_dash_count', 0) > 0:
        score += min(5, metrics['em_dash_count'])
    return min(10, score)
```
