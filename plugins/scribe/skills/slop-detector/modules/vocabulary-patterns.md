---
module: vocabulary-patterns
category: detection
dependencies: [Grep, Read]
estimated_tokens: 800
---

# Vocabulary Pattern Detection

Comprehensive word and phrase lists for AI slop detection, organized by confidence level and category.

## Tier 1: Highest Confidence Words

These words appear dramatically more often in AI-generated text. Research shows some (like "delve") appeared 10-25x more frequently after 2023.

### Power Words (Overinflated Verbs)
```
delve, embark, unleash, unlock, revolutionize, spearhead,
foster, harness, elevate, transcend, forge, ignite,
propel, catalyze, galvanize, amplify
```

### Sophistication Signals (False Depth)
```
multifaceted, nuanced, intricate, meticulous, profound,
comprehensive, holistic, robust, pivotal, paramount,
indispensable, quintessential
```

### Metaphor Abuse
```
tapestry, beacon, realm, landscape, symphony, mosaic,
crucible, labyrinth, odyssey, cornerstone, bedrock,
linchpin, nexus
```

### Display Verbs
```
showcasing, exemplifying, demonstrating, illuminating,
underscoring, highlighting, epitomizing
```

## Tier 2: Medium Confidence Words

Context-dependent markers that become problematic in clusters.

### Transition Overuse
```
moreover, furthermore, indeed, notably, subsequently,
consequently, additionally, likewise, nonetheless,
henceforth, thereby, whereby
```

### Hedging Stacks
```
potentially, typically, generally, arguably, presumably,
ostensibly, conceivably, seemingly, perhaps, might
```

### Intensity Words
```
significantly, substantially, fundamentally, profoundly,
dramatically, tremendously, remarkably, exceedingly,
immensely, vastly
```

### Business Jargon
```
leverage, synergy, optimize, streamline, scalability,
actionable, deliverables, stakeholders, bandwidth,
paradigm, disruptive, ecosystem
```

### Tech Buzzwords
```
cutting-edge, state-of-the-art, next-gen, AI-powered,
game-changing, innovative, transformative, seamless,
user-friendly, best-in-class, world-class
```

### Empowerment / Quantity Cliches
```
empower, empowering, myriad, plethora, navigate (as metaphor)
```

Notes:
- "navigate" is fine for actual UI/wayfinding; flag when used
  for non-spatial concepts ("navigate the complexities").
- "myriad" — replace with "many" plus a count if you have one.
- "empower" — replace with "let users" plus a verb.

## Tier 3: Phrase Patterns

### Vapid Openers (Score: 4)
```
"In today's fast-paced world"
"In an ever-evolving landscape"
"In the dynamic world of"
"In this digital age"
"As technology continues to evolve"
"In the realm of"
```

### Empty Emphasis (Score: 3)
```
"cannot be overstated"
"goes without saying"
"needless to say"
"it bears mentioning"
"of paramount importance"
"absolutely essential"
```

### Filler Phrases (Score: 2)
```
"it's worth noting that"
"it's important to understand"
"at its core"
"from a broader perspective"
"through this lens"
"when it comes to"
"at the end of the day"
```

### Attribution Cliches (Score: 3)
```
"a testament to"
"serves as a reminder"
"stands as proof"
"speaks volumes about"
"a shining example of"
```

### Marketing/Sales Speak (Score: 4)
```
"look no further"
"unlock the potential"
"unleash the power"
"treasure trove of"
"game changer"
"take it to the next level"
"best kept secret"
```

### Travel/Place Cliches (Score: 4)
```
"nestled in the heart of"
"bustling streets"
"hidden gem"
"off the beaten path"
"steeped in history"
"a feast for the senses"
```

### Journey Metaphors (Score: 3)
```
"embark on a journey"
"navigate the complexities"
"pave the way"
"chart a course"
"at a crossroads"
```

## Tier 4: Research-Validated Markers (2025-2026)

From peer-reviewed studies on AI text detection (PMC12219543, arXiv 2503.01659v1).

### High-Frequency Shift Words

These common words had the largest frequency increase in post-ChatGPT text. Individually unremarkable; their co-occurrence is the signal.

**10-word co-occurrence test** (5+ in a single paragraph = strong signal):
```
across, additionally, comprehensive, crucial, enhancing,
exhibited, insights, notably, particularly, within
```

### New Verbs (Score: 3 each)
```
underscore(s), bolster, foster, harness, illuminate,
elucidate, grapple, reimagine, intertwine, exemplify,
evoke, emulate, transcend, unravel
```

Note: "underscores the importance" is a near-diagnostic construction (13.8x human baseline frequency).

### New Adjectives (Score: 2-3 each)
```
seamless, invaluable, dynamic, whimsical, vibrant,
timeless, sustainable (outside environmental context)
```

### New Adverbs (Score: 2 each)
```
aptly, tirelessly, seamlessly, vividly
```

### New Nouns (Score: 2 each)
```
interplay, facet, symphony (metaphorical), endeavor,
synergy, insights (as padding: "provides valuable insights")
```

### Hedging Constructions (Score: 2-3 each)
```
"It's important to note that"
"It's important to remember that"
"Generally speaking"
"To some extent"
"From a broader perspective"
"One might argue that"
"It could be said that"
"There is growing evidence that"
```

### Conclusion Starters (Score: 2 each)
```
"Overall, "
"In conclusion, "
"In summary, "
"Ultimately, "
"To sum up, "
```

These overwhelmingly start AI conclusions. Human writers end with specifics, callbacks, or questions.

### Sycophantic Positivity (Score: 3 each)
```
"areas for improvement" (avoids saying "problems")
"invaluable resource"
"exceptional"
"remarkable"
```

AI text is measured at 50% more sycophantic than human text (Georgetown AI Sycophancy Research, 2025).

## Tier 5: 2026 Patterns (Wikipedia, Field Guide, Stop-Slop)

These patterns crystallized in cross-source agreement during
early 2026. Wikipedia's *Signs of AI writing*, the Algorithmic
Bridge *10 Signs*, the Ignorance.ai *Field Guide to AI Slop*,
and Hardik Pandya's *Stop Slop* Claude skill all converge on
the same shapes. Treat them as Tier-1 weight when they appear.

### Copula-Avoidance Verbs (Score: 3 each)

AI substitutes weighty verbs for plain "is/are" to inject
false gravitas. The hallmark is a verb whose subject is
inanimate. *Wikipedia: "Avoidance of is/are."*

```
serves as, stands as, marks, represents, embodies,
constitutes, lives in, lives at, sits at, sits between,
sits within, rests on, rooted in, anchored in,
nestled in, situated at, exists at, dwells in,
boasts, features, maintains, offers, encompasses
```

| Pattern | Why it's slop | Human alternative |
|---------|---------------|-------------------|
| "The skill lives in `plugins/scribe/`" | A skill does not live | "The skill is in `plugins/scribe/`" |
| "The cache sits between the API and DB" | The cache does not sit | "The cache is between the API and DB" |
| "This serves as a foundation for X" | "Is" works | "This is the foundation for X" |
| "The function rests on three invariants" | Functions do not rest | "The function depends on three invariants" |
| "The library boasts 50 features" | Libraries cannot boast | "The library has 50 features" |
| "The framework stands as a testament to Y" | Frameworks do not stand | "The framework shows Y" or delete |

**Detection rule:** if the subject is inanimate and the verb
is one above (other than "is", "are", "has", "contains",
"depends on", "uses"), flag.

### Throat-Clearing Openers (Score: 3 each)

Discourse markers AI uses to *appear* conversational without
saying anything. *Stop-Slop catalog, Hardik Pandya 2026.*

```
"Here's the thing,"
"Look,"   (sentence opener)
"So,"     (sentence opener, when not contrastive)
"The thing is,"
"Let that sink in."
"The uncomfortable truth is"
"This matters because"
"To be clear,"
"Let me explain."
"Here's what I mean:"
"Bear with me."
```

These open paragraphs where the substance should. Delete and
start at the substantive content.

### Loop/Signal/Cascade Vocabulary (Score: 2-3 each)

Post-2025 AI develops a fondness for systems-theory-flavored
nouns. *George Kao, April 2026.* Individually unremarkable;
clustered they signal generated text.

```
loop, signal, cascade, drift, ripple, surface (as verb),
unpack (as verb), surface (as verb meaning "reveal"),
quiet/quietly (as evaluative adjective: "a quiet shift"),
sharp (as evaluative: "a sharp framing"),
fresh (as evaluative: "a fresh take")
```

| Phrase | Flag when |
|--------|-----------|
| "unpack this" | "unpack" used metaphorically; "explain" works |
| "surface the issue" | "raise" or "report" works |
| "a quiet shift" | evaluative; describe the shift instead |
| "the signal here is" | "the point is" works |
| "a feedback loop" | flag in non-control-theory prose |

### Significance & Legacy Cluster (Score: 3 each)

AI over-narrates importance. *Wikipedia, OliviaCal 2026.*

```
"stands as a testament to"
"marks a turning point"
"represents a shift"
"key turning point"
"focal point"
"indelible mark"
"deeply rooted"
"setting the stage for"
"contributing to the"
"shaping the future of"
"reflects broader"
"plays a key role in"
"plays a pivotal role"
"underscores the importance of"
```

Pattern: any sentence whose entire job is to assert that the
subject *matters*, without saying what it does. Cut the
sentence; the surrounding facts carry significance better.

### Notability & Attribution Inflation (Score: 2-3 each)

Post-GPT-5 patterns that overstate sourcing. *Wikipedia 2026
update.*

```
"independent coverage"
"covered by multiple outlets"
"active social media presence"
"written by a leading expert"
"profiled in"
"industry reports indicate"
"observers have cited"
"experts argue"
"several sources / publications"
```

Especially common in AI-generated bios and READMEs claiming
unverified third-party validation.

### Abstraction-Trap Adjectives (Score: 2-3 each)

The Algorithmic Bridge "Abstraction Trap": prefer concrete
over abstract. Flag when a sentence is *unvisualizable*.

```
foundational, conceptual, structural (as adjective),
strategic, holistic, systemic, principled,
foundational (repeat), underlying (as adjective filler)
```

### Negative Parallelism Phrases (Score: 4 each)

The strongest 2026 prose tell. Flagged independently by
Wikipedia, OliviaCal, ContentBeta, Stop-Slop, and George Kao.

```
"It's not X, it's Y"
"It's not just X, it's Y"
"Not just X, but Y"
"Not only X, but also Y"
"No X. No Y. Just Z."
"No X, no Y, no Z"
"Y, not X" (trailing corrective negation)
"Not because X. Because Y."
"X. That's it. That's the Y."
"Not a X, not a Y, just a Z"
"And that's okay."
```

Structural fingerprint, not just a phrase. See
`structural-patterns.md` for full detection. Listed here so
vocabulary scans surface the lexical version.

This is the **contrastive negation** half of the broader
**contrastive parallelism** (antithesis) family. The affirmative
half ("Less X, more Y"; "Where others X, we Y") has no "not"
anchor and is detected structurally; see
`structural-patterns.md` § Contrastive Parallelism. Avoid both
in all but the most necessary cases.

## Tier 5 Detection Regex Patterns

```python
TIER5_COPULA_PATTERNS = [
    r'\b(?:lives?|sits?|stands?|rests?|dwells?)\s+(?:in|at|on|between|within|atop)\b',
    r'\bserves?\s+as\b',
    r'\bmarks?\s+(?:a|the|an)\s+(?:turning|pivotal|key|defining)\b',
    r'\brepresents?\s+(?:a|the|an)\s+(?:shift|transformation|paradigm)\b',
    r'\b(?:rooted|anchored|nestled|situated)\s+in\b',
    r'\bboasts?\s+(?:a|an|the|over|more than)\b',
]

TIER5_THROAT_CLEARING = [
    r"^Here's the thing,",
    r"^Look,\s+[A-Z]",
    r"^So,\s+[A-Z]",
    r"^The thing is,",
    r"\bLet that sink in\b",
    r"^The uncomfortable truth is",
    r"\bThis matters because\b",
    r"^Let me explain\.",
    r"^Bear with me\.",
]

TIER5_NEGATIVE_PARALLELISM = [
    # "It's not X, it's Y" — X can be multi-word (e.g., "a tool")
    r"\bIt's not [\w\s]+?,\s+it's \w+",
    r"\bNot just \w+,?\s+but (?:also )?\w+",
    r"\bNot only \w+,?\s+but (?:also )?\w+",
    r"\bNo \w+\.\s+No \w+\.\s+Just \w+",
    # Comma-joined variant: "No X, no Y, no Z"
    r"\bNo \w+,\s+no \w+(?:,\s+no \w+)*",
    # Trailing corrective negation: "Y, not X." -> "Y instead of X"
    r"\b\w+,\s+not\s+(?:just\s+)?\w+[.!?]",
    r"\bNot because \w+\.\s+Because \w+",
    r"\.\s+That's it\.\s+That's the\b",
    r"\bAnd that's okay\.",
]

TIER5_LOOP_VOCAB = [
    r'\bunpack (?:this|that|the)\b',
    r'\bsurface (?:the|a) (?:issue|question|tension|point)\b',
    r'\ba quiet (?:shift|revolution|change|moment)\b',
    r'\bthe signal (?:here|is)\b',
    r'\ba sharp (?:framing|take|distinction)\b',
]

TIER5_SIGNIFICANCE = [
    r'\bstands? as a testament to\b',
    r'\bmarks? a turning point\b',
    r'\brepresents? a (?:shift|transformation)\b',
    r'\bindelible mark\b',
    r'\bdeeply rooted\b',
    r'\bsetting the stage for\b',
    r'\bshaping the future of\b',
    r'\breflects broader\b',
    r'\bplays? a (?:key|pivotal|crucial) role\b',
    r'\bunderscores? the importance\b',
]
```

## Tier 5 False-Positive Exclusions

| Pattern | Skip when | Flag when |
|---------|-----------|-----------|
| "lives in" | Describing actual habitation ("the daemon lives in `/run`") | Files, skills, modules, abstractions "living" |
| "sits at" | Physical seating | Anything non-physical "sitting" |
| "serves as" | Military, restaurant, sports context | Abstractions "serving as" anything |
| "Look," | Inside dialogue or transcripts | Author voice outside quotation |
| "unpack" | Actual unpacking (luggage, archives) | Metaphorical use for "explain" |
| "rooted in" | Botanical, etymological | Abstract concepts "rooted" |
| "loop" | Code loops, control structures | "feedback loop" as metaphor |
| "signal" | Telecom, statistics, signals.h | Evaluative use ("the signal here is") |

## Detection Regex Patterns

For automated scanning:

```python
TIER1_PATTERNS = [
    r'\bdelve\b', r'\bembark\b', r'\btapestry\b', r'\brealm\b',
    r'\bbeacon\b', r'\bmultifaceted\b', r'\bpivotal\b', r'\bnuanced\b',
    r'\bmeticulous(?:ly)?\b', r'\bintricate\b', r'\bshowcasing\b',
    r'\bleveraging\b', r'\bstreamline\b', r'\bunleash\b',
]

TIER1_NEW_PATTERNS = [
    r'\bunderscore[sd]?\b', r'\bbolster\b', r'\bfoster\b',
    r'\billuminat[es]\b', r'\belucidat[es]\b', r'\bgrapple\b',
    r'\breimagin[es]\b', r'\bintertwine[ds]?\b', r'\bexemplif(?:y|ies)\b',
    r'\bseamless(?:ly)?\b', r'\binvaluable\b', r'\bvibrant\b',
    r'\binterplay\b', r'\bfacet[s]?\b', r'\bendeavor[s]?\b',
    r'\baptly\b', r'\btirelessly\b', r'\bvividly\b',
]

PHRASE_PATTERNS = [
    r"in today's fast-paced",
    r'cannot be overstated',
    r"it's worth noting",
    r'at its core',
    r'a testament to',
    r'unlock the (?:full )?potential',
    r'embark on (?:a |the )?journey',
    r'nestled in the heart',
    r'treasure trove',
    r'game[- ]changer',
    r"it's important to (?:note|remember|understand) that",
    r'generally speaking',
    r'from a broader perspective',
    r'one might argue',
    r'it could be said',
    r'there is growing evidence',
    r'areas for improvement',
    r'invaluable resource',
    r'underscores the importance',
]

# Conclusion starters (check first word of last paragraph)
CONCLUSION_STARTERS = [
    r'^Overall,',
    r'^In conclusion,',
    r'^In summary,',
    r'^Ultimately,',
    r'^To sum up,',
]

# Co-occurrence test: 5+ of these in one paragraph = strong signal
HIGH_FREQ_SHIFT_WORDS = [
    'across', 'additionally', 'comprehensive', 'crucial', 'enhancing',
    'exhibited', 'insights', 'notably', 'particularly', 'within',
]
```

## False-Positive Exclusions

Always define what to detect AND what to ignore.
Flagging legitimate usage erodes trust in the detector.

### Word-Level Exclusions

| Word | Skip When | Flag When |
|------|-----------|-----------|
| delve | Technical deep-dive, data analysis | Generic "delve into the topic" |
| leverage | Physics, mechanics, finance (actual leverage) | Business jargon substitute for "use" |
| robust | Engineering specs, statistical methods | Marketing claims, feature descriptions |
| seamless | Measured UX testing results with data | Feature descriptions without evidence |
| journey | Actual travel, user journey maps with data | Metaphor for any process or experience |
| comprehensive | Describing verified 100% coverage | Filler adjective for any collection |
| nuanced | Academic analysis with cited evidence | Flattery or vague praise |
| foster | Childcare, horticulture, proper nouns | Generic "foster collaboration/innovation" |
| landscape | Geography, actual visual design | "the AI landscape", "competitive landscape" |
| ecosystem | Biology, verified platform with APIs | Vague reference to any group of things |
| insights | Data analysis with specific findings | "provides valuable insights" (padding) |
| dynamic | Physics, runtime behavior (code) | Filler adjective for any changing thing |

### Phrase-Level Exclusions

| Phrase | Skip When | Flag When |
|--------|-----------|-----------|
| "at its core" | Describing actual CPU/kernel internals | Filler for "basically" |
| "it's worth noting" | Preceding a genuine caveat with evidence | Preceding obvious information |
| "generally speaking" | Qualifying a statistical claim | Hedging an opinion |
| "areas for improvement" | Formal performance review documents | Avoiding saying "problems" or "bugs" |

### Structural Exclusions

Do not flag these as slop even if they match patterns:

- **Quoted text**: Content inside blockquotes or citation marks
- **Code examples**: Technical terms inside backticks or code blocks
- **Proper nouns**: Product names, titles, organizations
- **Direct citations**: Attributed quotes from named sources
- **Glossary definitions**: Defining a term that happens to be a slop word
- **Changelogs**: Version history entries using standardized language
- **Generated output**: Content explicitly marked as AI-generated for comparison

## Scoring Formula

```python
def calculate_vocabulary_score(text, word_count):
    tier1_matches = count_tier1_matches(text)
    tier2_matches = count_tier2_matches(text)
    phrase_matches = count_phrase_matches(text)

    raw_score = (tier1_matches * 3) + (tier2_matches * 2) + (phrase_matches * 3)
    normalized = (raw_score / word_count) * 100

    return min(10.0, normalized)  # Cap at 10
```
