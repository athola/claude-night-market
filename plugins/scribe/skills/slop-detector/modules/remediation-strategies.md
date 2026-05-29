---
module: remediation-strategies
category: writing-quality
dependencies: [Edit, Write]
estimated_tokens: 600
---

# AI Slop Remediation Strategies

Guidance for fixing detected slop patterns while preserving meaning.

## Core Principles

1. **Preserve meaning**: Never change what's said, only how it's said
2. **Match context**: Technical docs need different fixes than narratives
3. **Maintain voice**: If the document has established tone, preserve it
4. **Incremental changes**: Edit section by section, not wholesale rewrites
5. **Ask before gutting**: Major restructuring requires user approval

## Vocabulary Remediation

### Direct Substitutions

| AI Word | Context | Replacements |
|---------|---------|-------------|
| delve | exploration | explore, examine, look at, dig into |
| leverage | usage | use, apply, employ |
| utilize | usage | use |
| embark | starting | begin, start, launch |
| comprehensive | scope | thorough, complete, full |
| robust | quality | solid, strong, reliable |
| seamless | integration | smooth, easy, simple |
| pivotal | importance | key, important, critical |
| multifaceted | complexity | complex, varied, diverse |
| nuanced | detail | subtle, detailed, fine-grained |
| streamline | improvement | simplify, improve, speed up |
| optimize | improvement | improve, tune, adjust |
| facilitate | enablement | enable, help, allow |
| utilize | use | use |

### Phrase Substitutions

| AI Phrase | Replacement Options |
|-----------|---------------------|
| "In today's fast-paced world" | [Delete entirely] or start with the actual point |
| "It's worth noting that" | [Delete] - just state the thing |
| "At its core" | "Fundamentally" or [delete] |
| "Cannot be overstated" | "is important" or "matters because [reason]" |
| "Navigate the complexities" | "handle", "work through", "deal with" |
| "Unlock the potential" | "enable", "allow", "make possible" |
| "A testament to" | "shows", "demonstrates", "proves" |
| "Treasure trove" | "collection", "set", "many" |

## Structural Remediation

### Reducing Em Dashes

Replace with:
- Commas for brief asides
- Parentheses for tangential info
- Periods for complete thoughts
- Colons for introductions

Before: "The system—which was designed for scale—handles millions of requests."
After: "The system handles millions of requests. It was designed for scale."

### Converting Bullets to Prose

Before:
```
Key benefits:
- Fast processing
- Easy integration
- Low maintenance
```

After:
"The system processes quickly, integrates without friction, and requires little upkeep."

### Varying Sentence Length

If all sentences are 15-20 words, intersperse:
- Short punchy statements (5-8 words)
- Longer explanatory sentences (25-30 words)
- Questions or fragments for emphasis

### Adding Contractions

Replace formal constructions:
- "do not" -> "don't"
- "cannot" -> "can't"
- "it is" -> "it's"
- "we will" -> "we'll"

Exception: Legal, academic, or formal documents may require formality.

## Tone Remediation

### Removing Sycophancy

| Remove | Replace With |
|--------|--------------|
| "Great question!" | [Delete, just answer] |
| "I'd be happy to" | [Delete, just do it] |
| "Absolutely!" | [Delete or use sparingly] |
| "That's a wonderful point" | [Delete] |

### Adding Authorial Voice

Insert:
- First-person perspective where appropriate
- Specific examples from real experience
- Acknowledgment of limitations or unknowns
- Trade-off discussions with reasoning

Before: "This approach optimizes performance."
After: "We chose this approach because it cut latency by 40% in our tests, though it uses more memory."

### Grounding Abstract Claims

Before: "This provides comprehensive coverage."
After: "This covers all 47 API endpoints documented in v2.3."

## Section-by-Section Workflow

For documents over 200 lines:

1. **Scan entire document** for slop density
2. **Prioritize sections** by severity
3. **Present each section** to user with proposed changes
4. **Wait for approval** before proceeding
5. **Track changes** in a summary

```markdown
## Section 3: API Overview (Lines 45-89)

**Slop Score**: 4.2 (Moderate)

**Proposed Changes**:
1. Line 47: "delve into" -> "examine"
2. Line 52: Remove "In today's fast-paced world"
3. Lines 60-75: Convert bullet list to two paragraphs

Proceed with these changes? [Y/n/edit]
```

## Docstring Remediation

Special rules for code comments:

1. **Imperative mood**: "Validate" not "Validates"
2. **No surrounding code changes**: Only modify the comment text
3. **Preserve parameter documentation**: Keep Args/Returns format
4. **Brief is better**: Remove filler, keep essential info

Before:
```python
def process(data):
    """
    This function processes the data in a comprehensive manner,
    leveraging advanced algorithms to optimize the output.
    """
```

After:
```python
def process(data):
    """Process input data and return optimized result."""
```

## When NOT to Remediate

- **Quoted material**: Don't change quotes from other sources
- **Historical documents**: Preserve original language
- **Intentional style**: Some "AI-like" formality may be intentional
- **User preference**: If user wants formal tone, respect it

## Tier 5 / 2026 Remediations

These complement the older substitutions above. Apply during
the Pass-5 prose sweep and during prevention-mode generation.

### Copula-Avoidance Verbs (Spatial / Animated)

| Slop | Replacement |
|------|-------------|
| "lives in" / "lives at" | "is in" / "is at" |
| "sits at" / "sits between" / "sits within" | "is at" / "is between" / "is in" |
| "stands as" | "is" or delete |
| "rests on" | "depends on" / "uses" |
| "rooted in" | "based on" / "comes from" |
| "anchored in" | "based on" / delete |
| "nestled in" | "in" |
| "serves as" | "is" |
| "marks" (a turning point/shift) | "starts" / "begins" / delete |
| "represents" (a shift/transformation) | "is" or delete |
| "embodies" | "is" or "shows" |
| "boasts" | "has" |
| "features" (as main verb) | "has" / "includes" |
| "encompasses" | "covers" / "includes" |

**Heuristic:** if the subject cannot literally do the verb,
replace with "is", "has", or "uses".

### Plus-Sign Conjunction

| Slop | Replacement |
|------|-------------|
| "hooks and skills" | "hooks and skills" |
| "Python and Rust workflow" | "Python and Rust workflow" |
| "API and cache" | "API and cache" |
| "fast and cheap" | "fast and cheap" |

Exception: keep in code blocks, version strings ("3.11+"),
stack labels in diagrams, math.

### Em-Dash Replacement (Prevention Mode)

| Original | Replacement | When |
|----------|-------------|------|
| "X — Y — Z" | "X, Y, Z" | Brief aside |
| "X — a Y — Z" | "X (a Y) Z" | Tangential definition |
| "X — and Y" | "X. And Y." | Dramatic pause |
| "X — Y." | "X: Y." | Definition / list-lead |
| "X — Y." | "X. Y." | Two complete thoughts |

### Negative Parallelism (Contrastive Negation)

| Slop | Replacement |
|------|-------------|
| "It's not X, it's Y" | "It is Y" (state Y positively; avoid the "Y, not X" tail, which is itself flagged) |
| "Y, not X" (trailing) | "Y instead of X" (when the contrast carries information) or "Y" (drop the tail) |
| "Not just X, but Y" | "X and Y" or "X. Also Y." |
| "Not only X, but also Y" | "X and Y" |
| "No X. No Y. Just Z." | "Zero X. Zero Y. Only Z." (rare) or "Z, with no X or Y" |
| "No X, no Y, no Z" | "Z, with no X or Y" |
| "Not because X. Because Y." | "Because Y" (drop the "not X" half) |
| "X. That's it. That's the Y." | "X is the Y." |
| "And that's okay." | Delete |

The replacements remove the rhetorical scaffold and state the
claim directly.

### Contrastive Parallelism (Affirmative Antithesis)

The affirmative sibling: parallel clauses in opposition with no
"not" anchor. Keep it only when the contrast is load-bearing
and used once; otherwise state the point plainly.

| Slop | Replacement |
|------|-------------|
| "Less config, more code" | "Setup is one file; the rest is code" |
| "Where others X, we Y" | "We do Y" (drop the unnamed comparison) |
| "Humans propose; machines dispose" | "A human picks; the agent applies" (when both sides are concrete) |
| "Old way: X. New way: Y." | "Y replaces X" |

Subject-swap clauses and chiasmus are judgment-level
(`confidence: low`); surface for human decision rather than
auto-rewriting. Leave `Before:`/`After:` labels on code
examples alone.

### Throat-Clearing Openers

| Slop opener | Replacement |
|-------------|-------------|
| "Here's the thing," | Delete; start at substance |
| "Look," (sentence opener) | Delete |
| "So," (non-contrastive) | Delete |
| "The thing is," | Delete |
| "Let that sink in." | Delete |
| "The uncomfortable truth is" | Delete; state the truth directly |
| "This matters because" | Delete the framing; state why directly |
| "Let me explain." | Delete; just explain |
| "Bear with me." | Delete |

### Significance Cluster

| Slop | Replacement |
|------|-------------|
| "stands as a testament to" | "shows" / delete |
| "marks a turning point" | "is when X changed" |
| "represents a shift" | "is a shift" or describe the shift |
| "indelible mark" | name the specific effect |
| "deeply rooted" | "old" / "longstanding" |
| "setting the stage for" | "before" / "leading to" |
| "shaping the future of" | name the specific influence |
| "underscores the importance" | "is important because" |
| "plays a pivotal role" | "is central" or describe the role |

### Three-Fragment Burst

When you see "X. Y. Z." with three short fragments, ask:
*does the rhythm carry information, or is it ornament?* If
ornament, replace with a complete sentence.

| Slop | Replacement |
|------|-------------|
| "Focused. Aligned. Measurable." | "Focused, aligned, measurable." or full sentence |
| "Fast. Reliable. Cheap." | "Fast, reliable, and cheap." |
| "Built. Tested. Shipped." | "Built, tested, and shipped." |

### Loop/Signal/Cascade Vocabulary

| Slop | Replacement |
|------|-------------|
| "unpack this" | "explain" / "go through" |
| "surface the issue" | "raise" / "report" |
| "a quiet shift" | name the shift |
| "the signal here is" | "the point is" |
| "a sharp framing" | describe the framing |
| "feedback loop" (non-control) | describe the actual mechanism |
