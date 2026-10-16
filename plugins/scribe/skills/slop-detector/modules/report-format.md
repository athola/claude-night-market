---
module: report-format
category: output
dependencies: [Read]
estimated_tokens: 600
---

# Summary Report Format

```markdown
## Slop Detection Report: [filename]

**Overall Score**: X.X / 10 (Rating)
**Word Count**: N words
**Markers Found**: N total

### CRITICAL (P0, must resolve before merge)
- Line 8: "As a large language model". IDENTITY LEAK
- Line 47: References `Client.connect_with_timeout(...)` —
  HALLUCINATION (method does not exist; closest match is
  `Client.connect`)
- Line 102: "production-ready" claim with no CI workflow
 . UNVERIFIED CLAIM

### High-Confidence Markers (vocabulary)
- Line 23: "delve into" -> consider: "explore"
- Line 45: "rich tapestry" -> consider: "variety"

### Structural Issues
- Em dash density: 8/1000 words (HIGH)
- Bullet ratio: 72% (ELEVATED)
- Sentence length SD: 3.2 words (LOW VARIANCE)

### Phrase Patterns
- Line 12: "In today's fast-paced world" (vapid opener)
- Line 89: "cannot be overstated" (empty emphasis)
- Line 134: "Let's dive into" (self-narration of structure)

### Tier 5 / 2026 Patterns
- Line 19: "The skill lives in `plugins/scribe/`" → "is in"
  (spatial copula, inanimate subject)
- Line 27: "hooks + skills" → "hooks and skills" (plus-sign
  conjunction in prose)
- Line 34: "It's not a tool, it's a transformation" →
  rewrite positively (negative parallelism / contrastive
  negation)
- Line 38: "Less config, more code" → state plainly
  (contrastive parallelism; keep only if load-bearing)
- Line 56: "Here's the thing," → delete (throat-clearing
  opener)
- Line 78: "Focused. Aligned. Measurable." → "Focused,
  aligned, and measurable." (three-fragment burst)
- Line 91: 3 smart quotes outside code blocks (Word-processor
  paste signature)

### Stub & Deferral
- Line 56: bare `// TODO: handle expired tokens` (no
  tracked issue link)
- Line 71: "for now, we recommend" (deferral language)

### Document Economy Score: X / 6
- Thesis-first: 1/2 (thesis present but buried in para 3)
- Sentence weight: 1/2 (~65% of sentences earn weight)
- Repetition: 2/2 (thesis echoed; ambient repetition cut)

### Recommendations
1. **CRITICAL**: delete line 8 identity leak before merge
2. **CRITICAL**: replace `Client.connect_with_timeout`
   with `Client.connect(opts)` and update example
3. **CRITICAL**: either add CI + version >= 1.0 to back
   "production-ready", or delete the claim
4. Replace [specific word] with [alternative]
5. Convert bullet list at line 34-56 to prose
6. Hoist the thesis (line 47) into the lead paragraph
7. Link bare TODOs to tracked issues or delete code path

### Confidence-low findings (require human decision)
- Line 89: bullet count of 8 may be appropriate for this
  enumeration; do not auto-flatten
- Line 156: `Manager` suffix may be domain-meaningful;
  verify before renaming
```
