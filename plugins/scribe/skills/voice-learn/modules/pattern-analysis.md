---
module: pattern-analysis
category: voice-learning
dependencies: [Read, Agent]
estimated_tokens: 500
---

# Pattern Analysis Module

Analyze diffs between post-review and post-edit snapshots
to extract recurring edit patterns.

## Diff Categories

| Category | Signal | Example |
|----------|--------|---------|
| tone_adjustment | Softened/strengthened claims | "This proves" -> "This suggests" |
| voice_insertion | Added writer-specific moves | Added parenthetical aside |
| structure_change | Reordered, split, merged | Broke long paragraph into two |
| precision_edit | Vague -> specific | "many people" -> "the 12 engineers" |
| deletion | Removed fluff | Cut "It's worth noting that" |
| addition | Added context | Added a concrete example |
| humor_or_irreverence | Added informal voice | Added "(fuck GPTZero)" |
| hedge_or_commit | Changed certainty level | "will" -> "should" or vice versa |

## Analysis Prompt

```
Compare these two versions of the same text:

VERSION A (post-review, before manual edits):
{post_review_text}

VERSION B (post-edit, after manual edits):
{post_edit_text}

For each change the writer made:
1. Identify the specific edit (what changed)
2. Categorize it (from the categories above)
3. Describe the pattern (what principle drove this edit?)
4. Assess specificity: is this a general writing preference
   or specific to this voice?

Focus on RECURRING patterns, not one-off fixes. If the same
type of edit appears 2+ times, that's a voice signal.

Output as a list of patterns with evidence.
```

## Pattern Matching Against Accumulator

For each identified pattern, check the accumulator:

```python
def match_pattern(new_pattern, accumulator):
    """Match using category + semantic similarity."""
    for existing in accumulator["patterns"]:
        if existing["category"] == new_pattern["category"]:
            # Semantic similarity check (same intent?)
            if similar_description(existing, new_pattern):
                return existing  # Merge with this entry
    return None  # New pattern
```

## Evidence Requirements

| Action | Threshold |
|--------|-----------|
| Apply to register | 3+ instances across 2+ pieces |
| Apply with accumulator match | 1-2 new + 2 prior instances |
| Hold in accumulator | 1-2 instances, no prior match |
| Discard | Contradicts 3+ counter-examples |

## Output Format

```json
{
  "patterns_found": [
    {
      "category": "tone_adjustment",
      "description": "Softens confident claims about capabilities",
      "instances": [
        {"line": 12, "before": "...", "after": "..."},
        {"line": 34, "before": "...", "after": "..."}
      ],
      "recommendation": "apply|hold|discard",
      "target": "register|craft-rules|prose-reviewer",
      "proposed_edit": "..."
    }
  ]
}
```
