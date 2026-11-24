---
module: sico-extraction
category: voice-extraction
dependencies: [Agent]
estimated_tokens: 800
---

# SICO Extraction Module

Comparative feature extraction using SICO Phase 1 methodology.

## Baseline Generation

For each sample, generate Claude's default output on a
matched topic. The baseline reveals what the model does
naturally so the extraction can identify divergences.

**Baseline prompt** (per sample):

```
Write a short piece (~{word_count} words) about the following
topic. Use your natural default style. Do not try to match
any particular voice or style. Write naturally.

Topic: {topic_summary_from_sample}
```

Store baselines in memory (not persisted). They exist only
for the comparison step.

## Pass 1: Broad Comparative Extraction

**Prompt structure:**

```
I will show you pairs of text. In each pair:
- Text A is written by a specific person
- Text B is your default output on the same topic

Describe what the writer of Text A does differently from your
default style. Focus on:

1. STRUCTURAL PATTERNS
   - Paragraph shapes and lengths
   - Section architecture (how pieces are organized)
   - Information sequencing (when details arrive)

2. RHETORICAL MOVES
   - How arguments build (linear? recursive? tangential?)
   - Transition style (smooth? abrupt? absent?)
   - How evidence is introduced

3. TONAL DEVICES
   - Hedging patterns (where they commit vs equivocate)
   - Authority level (when do they assert vs defer?)
   - Humor or irreverence patterns

4. SENTENCE-LEVEL TECHNIQUES
   - Clause structure and complexity
   - Fragment usage and placement
   - Parenthetical habits (anticipating objections? asides?)

5. VOCABULARY TENDENCIES
   - Abstract vs physical language
   - Technical vs conversational register
   - Specific word preferences or avoidances

6. DISTINCTIVE HABITS
   - Unnamed patterns that don't fit other categories
   - Recurring moves unique to this writer

7. STRATEGIC INEFFICIENCIES
   - Deliberate detours, pauses, tangents
   - Syntactic variations that serve no logical purpose but
     create texture
   - Places where the writer is "inefficient" on purpose
   - These are what LLMs naturally optimize away, so they
     are critical to preserve

8. NEGATIONS (what this writer would NEVER do)
   - Phrases or structures they avoid
   - Tones they never adopt
   - Moves that would feel wrong in their voice
   - This is often MORE revealing than positive patterns

Write each finding as an actionable instruction someone could
follow to reproduce this voice. NOT observational language
("tends to use"). Instead: "Use X when Y" or "Open with Z".
For negations: "NEVER do X" or "Avoid Y because it clashes
with Z characteristic".

---

{pairs of samples and baselines}
```

## Pass 2: Pressure Test

After Pass 1 produces a feature description, run the
pressure test to eliminate generic observations:

```
Review your feature description below. Apply three checks:

SPECIFICITY CHECK:
For each feature, ask: "Would 50% of writers do this?"
If yes, either make it more specific or remove it.
- BAD: "Varies sentence length" (everyone does this)
- GOOD: "Alternates 3-word fragments after 30-word
  accumulative sentences to create rhythmic punch"

COMPLETENESS CHECK:
Scan the samples again for patterns you missed:
- How do they handle uncertainty?
- What are their opening moves?
- Do they use parentheticals? How?
- What is the rhythm between caution and commitment?
- How do they ground abstractions in physical language?
- Do they anticipate reader objections? Where?

OPERATIONALITY CHECK:
Convert each feature to a followable instruction.
Test: "Could someone reproduce this pattern from
my description alone, without seeing the samples?"
If not, add a concrete example from the text.

Revise the full description. Output the final version.

---

Current description:
{pass_1_output}
```

## Quality Gate

Reject extraction output that contains these generic phrases:

- "uses varied sentence lengths"
- "maintains a conversational tone"
- "balances formal and informal"
- "engages the reader"
- "creates a sense of"
- "tends to"
- "often uses"
- "frequently employs"

If any are present, re-run with: "Your description contains
generic observations. Be more specific. Each feature must
describe something THIS writer does that most writers don't."

## Output Format

The final extraction goes into `extraction.md` with four
sections matching the register template:

1. **Vocabulary** - Word choice patterns, formality, terminology
2. **Sentence Structure** - Length patterns, complexity, rhythm
3. **Rhetorical Techniques** - Argument structure, evidence, logic
4. **Voice Qualities** - Personality, tone, reader relationship
