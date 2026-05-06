---
module: language-handling
category: detection
dependencies: [Read, Grep]
estimated_tokens: 1100
---

# Language Handling: Detection and i18n Patterns

Two related concerns are bundled in one module:

1. **Language detection and calibration** -- which languages are
   supported, how to detect them, and how to calibrate scores.
2. **Concrete pattern sets** for non-English slop (German, French,
   Spanish, with extension hooks for Portuguese and Italian).

Merged from `language-support.md` + `i18n-patterns.md` (P-14).

## Part 1: Supported Languages

| Code | Language | Tier Coverage | Calibration |
|------|----------|---------------|-------------|
| en | English | Full (Tier 1-4, phrases, fiction, sycophantic) | 1.0 (baseline) |
| de | German | Core (Tier 1-2, key phrases) | 0.85 |
| fr | French | Core (Tier 1-2, key phrases) | 0.80 |
| es | Spanish | Core (Tier 1-2, key phrases) | 0.85 |
| pt | Portuguese | Core (Tier 1-2, key phrases) | 0.85 |
| it | Italian | Core (Tier 1-2, key phrases) | 0.80 |

## Part 2: Language Selection

### Step 1 -- Check config

Look for a `languages` key in `.slop-config.yaml`:

```yaml
languages:
  - en
  - de
```

If `languages` is set, scan only those pattern sets. If absent, fall back to
heuristic detection.

### Step 2 -- Heuristic (no config)

Sample the first 200 words. Count function-word hits:

| Language | Function words |
|----------|----------------|
| German   | der, die, das, und, ist, nicht, mit, von |
| French   | le, la, les, et, est, pas, avec, une, dans |
| Spanish  | el, la, los, las, es, con, una, por, que |

Use the highest-scoring language. If the top score is below 5, treat the document
as English only and skip i18n pattern matching.

Detection is conservative: defaults to English unless another language has
significantly more markers in the text.

### Override

Specify language explicitly when auto-detection is unreliable:

- Mixed-language documents
- Short texts (< 100 words)
- Code-heavy documents

## Part 3: Pattern File Layout

Patterns are stored in `data/languages/{code}.yaml` with consistent structure:

```yaml
language: xx
name: Language Name
tier1:
  power_words: [...]
  sophistication_signals: [...]
  metaphor_abuse: [...]
tier2:
  transition_overuse: [...]
  hedging: [...]
  business_jargon: [...]
phrases:
  vapid_openers:
    score: 4
    patterns: [...]
  filler:
    score: 2
    patterns: [...]
```

## Part 4: Cultural Calibration

Slop perception varies by culture:

- **German**: Formal register is more accepted; fewer words flagged as pretentious
- **French**: Literary flourishes are culturally valued; calibrate sensitivity
- **Spanish**: Formal transitions are standard in academic writing
- **Portuguese**: Academic norms closely follow Spanish; formal phrasing less penalised
- **Italian**: Literary style is culturally valued, similar to French calibration

Structural metrics (em dashes, bullet ratios) are language-agnostic.

Each language has a calibration factor (see `LANGUAGE_CALIBRATION` in `pattern_loader.py`).
Multiply raw slop scores by this factor before reporting. English is the baseline (1.0).
Languages with a factor below 1.0 are less penalised for formal or literary register.

## Part 5: Concrete Pattern Sets (de/fr/es)

The same density scoring applies: tier-1 words score 3 each, tier-3
phrases score 4 each, normalised per 100 words.

### German (de)

```python
DE_TIER1_PATTERNS = [
    r'\bumfassend\w*\b',    # umfassend, umfassende, umfassender ...
    r'\bnutzen\b',
    r'\bvielf[äa]ltig\w*\b',
    r'\btiefgreifend\w*\b',
    r'\bbahnbrechend\w*\b',
    r'\bganzheitlich\w*\b',
    r'\bmaßgeblich\w*\b',
    r'\bwegweisend\w*\b',
]

DE_PHRASE_PATTERNS = [
    r'in der heutigen schnelllebigen welt',  # vapid opener
    r'es sei darauf hingewiesen',            # filler
]
```

### French (fr)

`tirer parti de` is a multi-word phrase treated as a single tier-1 unit.

```python
FR_TIER1_PATTERNS = [
    r'\btirer parti de\b',
    r'\bexhaustif(?:ve)?\b|\bexhaustive\b',  # exhaustif / exhaustive
    r'\bpolyvalent\w*\b',
    r'\bincontournable[s]?\b',
    r'\bnovateur\b|\bnovatrice\b',
    r'\bprimordial\w*\b',
]

FR_PHRASE_PATTERNS = [
    r"dans le monde d'aujourd'hui",  # vapid opener
    r'il convient de noter que',     # filler
]
```

### Spanish (es)

```python
ES_TIER1_PATTERNS = [
    r'\baprovechar?\b',          # aprovechar
    r'\bintegral[e-z]?\b',       # integral
    r'\bpolifac[eé]tico[s]?\b',  # polifacético
    r'\binnovador[a-z]?\b',      # innovador
    r'\bfundamental[e-z]?\b',    # fundamental
    r'\bimprescindible[s]?\b',   # imprescindible
]

ES_PHRASE_PATTERNS = [
    r'en el mundo acelerado de hoy',  # vapid opener
    r'cabe destacar que',             # filler
]
```

## Part 6: Scoring and Reporting

Add i18n matches to the overall document score:

```
slop_score += (tier1_count * 3 + phrase_count * 4) / word_count * 100
```

Report language-specific hits in a subsection:

```
### Non-English Markers (de)
- Line 4: "bahnbrechend" -> consider: "neu" or be specific
- Line 12: "In der heutigen schnelllebigen Welt" (vapid opener)
```

If two or more languages score above 5 in the heuristic, apply all matching
pattern sets and label each match with its language code.
