---
module: generation-pipeline
category: voice-generation
dependencies: [Read, Write, Agent]
estimated_tokens: 500
---

# Generation Pipeline Module

End-to-end generation flow from source material to reviewed text.

## Pipeline Stages

```
Source Material
    |
    v
[Frame as raw notes]
    |
    v
[Load profile + register + craft rules]
    |
    v
[Generate with Opus]
    |
    v
[Auto-fix: banned phrases, em dashes]
    |
    v
[Snapshot: pre-review] (if learning active)
    |
    v
[Dispatch review agents] (optional)
    |
    v
[Present advisories to user]
    |
    v
[Apply user decisions]
    |
    v
[Snapshot: post-review] (if learning active)
    |
    v
Final text (user may edit further)
    |
    v
[/voice-learn captures post-edit] (user-triggered)
```

## Auto-Fix Rules (Silent)

Applied immediately after generation, before review:

```bash
# Em dash replacement (context-aware)
# Before a clause: use comma or colon
# Parenthetical: use parentheses
# List separator: use semicolons

# Banned phrase removal
# "Furthermore," -> "" (start sentence without it)
# "It's important to note" -> "" (remove entirely)
# "delve" -> "explore" or "examine"
# "utilize" -> "use"
# "leverage" -> "use" or remove
# "comprehensive" -> "thorough" or "complete"
# "robust" -> "solid" or remove
# "seamless" -> "smooth" or remove
```

## Model Routing

| Stage | Model | Reason |
|-------|-------|--------|
| Generation | Opus | Tonal shifts, parenthetical subversion |
| Auto-fix | Regex/local | No model needed |
| Prose review | Sonnet | Structured detection prompts |
| Craft review | Sonnet | Structured evaluation prompts |
| Learning analysis | Opus | Nuanced pattern comparison |

## Error Recovery

If generation fails quality checks (> 5 hard failures):
1. Re-generate with stronger emphasis on banned phrases
2. If second attempt still fails, present to user with warning
3. Never loop more than twice (prevents infinite retry)

## Streaming Considerations

For long-form content (> 1000 words):
- Generate in sections (one per major heading)
- Apply auto-fix per section
- Allow user to review section-by-section or all at once
- Snapshot captures the complete assembled text
