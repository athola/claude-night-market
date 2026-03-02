---
module: language-support
category: detection
dependencies: [Read]
estimated_tokens: 400
---

# Multi-Language Slop Detection

## Supported Languages

| Code | Language | Tier Coverage |
|------|----------|---------------|
| en | English | Full (Tier 1-4, phrases, fiction, sycophantic) |
| de | German | Core (Tier 1-2, key phrases) |
| fr | French | Core (Tier 1-2, key phrases) |
| es | Spanish | Core (Tier 1-2, key phrases) |

## Language Detection

Auto-detection uses function word frequency analysis. Common words like articles,
prepositions, and auxiliary verbs serve as language markers.

Detection is conservative: defaults to English unless another language has
significantly more markers in the text.

### Override

Specify language explicitly when auto-detection is unreliable:
- Mixed-language documents
- Short texts (< 100 words)
- Code-heavy documents

## Pattern Loading

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

## Cultural Considerations

Slop perception varies by culture:
- **German**: Formal register is more accepted; fewer words flagged as pretentious
- **French**: Literary flourishes are culturally valued; calibrate sensitivity
- **Spanish**: Formal transitions are standard in academic writing

Structural metrics (em dashes, bullet ratios) are language-agnostic.
