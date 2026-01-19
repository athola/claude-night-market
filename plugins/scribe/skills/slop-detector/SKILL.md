---
name: slop-detector
description: |

  Triggers: ai slop, ai-generated, llm markers, chatgpt phrases, claude tells
  Detect and flag AI-generated content markers in documentation and prose.

  Triggers: slop detection, ai cleanup, humanize text, remove ai markers,
  detect chatgpt, detect llm, writing quality, ai tells

  Use when: reviewing documentation for AI markers, cleaning up LLM-generated
  content, auditing prose quality, preparing content for publication

  DO NOT use when: generating new content - use doc-generator instead.
  DO NOT use when: learning writing styles - use style-learner instead.

  Use this skill to identify and remediate AI slop in existing content.
category: writing-quality
tags: [ai-detection, slop, writing, cleanup, documentation, quality]
tools: [Read, Grep, TodoWrite]
complexity: medium
estimated_tokens: 2800
progressive_loading: true
modules:
  - vocabulary-patterns
  - structural-patterns
  - fiction-patterns
  - remediation-strategies
dependencies:
  - scribe:shared
---

# AI Slop Detection Skill

Identify linguistic markers that reveal AI-generated content and provide remediation guidance.

## Detection Philosophy

AI slop is not about individual words but patterns of usage. A single "delve" is fine; five instances with "tapestry," "embark," and "vibrant" signals generation. Detection focuses on:

1. **Density**: How many markers appear per 100 words
2. **Clustering**: Multiple markers in close proximity
3. **Context**: Whether usage fits the document type

## Required TodoWrite Items

1. `slop-detector:scan-initiated` - Target files identified
2. `slop-detector:vocabulary-checked` - Word/phrase patterns scanned
3. `slop-detector:structure-checked` - Structural patterns analyzed
4. `slop-detector:density-calculated` - Slop density score computed
5. `slop-detector:report-generated` - Findings documented

## Step 1: Scan Initialization

Identify target files and document types:

```bash
# Find markdown and text files
find . -name "*.md" -o -name "*.txt" -o -name "*.rst" | head -50

# Prioritize user-facing documentation
ls docs/ README.md CHANGELOG.md 2>/dev/null
```

Classify each file:
- **Technical docs**: READMEs, API docs, guides
- **Narrative prose**: Blog posts, tutorials, explanations
- **Fiction**: Creative writing, stories
- **Comments/docstrings**: Code documentation

## Step 2: Vocabulary Pattern Detection

Load: `@modules/vocabulary-patterns.md`

### Tier 1: High-Confidence Markers (Score: 3 each)

These words appear 10-100x more frequently in AI text than human text:

| Word | Context | Human Alternative |
|------|---------|-------------------|
| delve | "delve into" | explore, examine, look at |
| tapestry | "rich tapestry" | mix, combination, variety |
| realm | "in the realm of" | in, within, regarding |
| embark | "embark on a journey" | start, begin |
| beacon | "a beacon of" | example, model |
| spearheaded | formal attribution | led, started |
| multifaceted | describing complexity | complex, varied |
| comprehensive | describing scope | thorough, complete |
| pivotal | importance marker | key, important |
| nuanced | sophistication signal | subtle, detailed |
| meticulous/meticulously | care marker | careful, detailed |
| intricate | complexity marker | detailed, complex |
| showcasing | display verb | showing, displaying |
| leveraging | business jargon | using |
| streamline | optimization verb | simplify, improve |

### Tier 2: Medium-Confidence Markers (Score: 2 each)

Common but context-dependent:

| Category | Words |
|----------|-------|
| Transition overuse | moreover, furthermore, indeed, notably, subsequently |
| Intensity clustering | significantly, substantially, fundamentally, profoundly |
| Hedging stacks | potentially, typically, often, might, perhaps |
| Action inflation | revolutionize, transform, unlock, unleash, elevate |
| Empty emphasis | crucial, vital, essential, paramount |

### Tier 3: Phrase Patterns (Score: 2-4 each)

| Phrase | Score | Issue |
|--------|-------|-------|
| "In today's fast-paced world" | 4 | Vapid opener |
| "It's worth noting that" | 3 | Filler |
| "At its core" | 2 | Positional crutch |
| "Cannot be overstated" | 3 | Empty emphasis |
| "A testament to" | 3 | Attribution cliche |
| "Navigate the complexities" | 4 | Business speak |
| "Unlock the potential" | 4 | Marketing speak |
| "Treasure trove of" | 3 | Overused metaphor |
| "Game changer" | 3 | Buzzword |
| "Look no further" | 4 | Sales pitch |
| "Nestled in the heart of" | 4 | Travel writing cliche |
| "Embark on a journey" | 4 | Melodrama |
| "Ever-evolving landscape" | 4 | Tech cliche |
| "Hustle and bustle" | 3 | Filler |

## Step 3: Structural Pattern Detection

Load: `@modules/structural-patterns.md`

### Em Dash Overuse

Count em dashes (—) per 1000 words:
- **0-2**: Normal human range
- **3-5**: Elevated, review usage
- **6+**: Strong AI signal

```bash
# Count em dashes in file
grep -o '—' file.md | wc -l
```

### Tricolon Detection

AI loves groups of three with alliteration:
- "fast, efficient, and reliable"
- "clear, concise, and compelling"
- "robust, reliable, and resilient"

Pattern: `adjective, adjective, and adjective` with similar sounds.

### List-to-Prose Ratio

Count bullet points vs paragraph sentences:
- **>60% bullets**: AI tendency
- **Emoji-led bullets**: Strong AI signal in technical docs

### Sentence Length Uniformity

Measure standard deviation of sentence lengths:
- **Low variance** (SD < 5 words): AI monotony
- **High variance** (SD > 10 words): Human variation

### Paragraph Symmetry

AI produces "blocky" text with uniform paragraph lengths. Check if paragraphs cluster around the same word count.

## Step 4: Sycophantic Pattern Detection

Especially relevant for conversational or instructional content:

| Phrase | Issue |
|--------|-------|
| "I'd be happy to" | Servile opener |
| "Great question!" | Empty validation |
| "Absolutely!" | Over-agreement |
| "That's a wonderful point" | Flattery |
| "I'm glad you asked" | Filler |
| "You're absolutely right" | Sycophancy |

These phrases add no information and signal generated content.

## Step 5: Calculate Slop Density Score

```
slop_score = (tier1_count * 3 + tier2_count * 2 + phrase_count * avg_phrase_score) / word_count * 100
```

| Score | Rating | Action |
|-------|--------|--------|
| 0-1.0 | Clean | No action needed |
| 1.0-2.5 | Light | Spot remediation |
| 2.5-5.0 | Moderate | Section rewrite recommended |
| 5.0+ | Heavy | Full document review |

## Step 6: Generate Report

Output format:

```markdown
## Slop Detection Report: [filename]

**Overall Score**: X.X / 10 (Rating)
**Word Count**: N words
**Markers Found**: N total

### High-Confidence Markers
- Line 23: "delve into" -> consider: "explore"
- Line 45: "rich tapestry" -> consider: "variety"

### Structural Issues
- Em dash density: 8/1000 words (HIGH)
- Bullet ratio: 72% (ELEVATED)
- Sentence length SD: 3.2 words (LOW VARIANCE)

### Phrase Patterns
- Line 12: "In today's fast-paced world" (vapid opener)
- Line 89: "cannot be overstated" (empty emphasis)

### Recommendations
1. Replace [specific word] with [alternative]
2. Convert bullet list at line 34-56 to prose
3. Vary sentence structure in paragraphs 3-5
```

## Integration with Remediation

After detection, invoke `Skill(scribe:doc-generator)` with `--remediate` flag to apply fixes, or manually edit using the report as a guide.

## Exit Criteria

- All target files scanned
- Density scores calculated
- Report generated with actionable recommendations
- High-severity items flagged for immediate attention
