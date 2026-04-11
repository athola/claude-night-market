---
name: voice-learn
description: Run learning pass on manually edited text to improve voice profile
arguments:
  - name: file
    description: Path to the manually edited final version
    required: true
  - name: --profile
    description: Voice profile to update
    required: true
---

# /voice-learn Command

Capture manual edits and learn voice patterns from them.

## Usage

```bash
# After manually editing generated text
/voice-learn final-draft.md --profile myvoice
```

## What This Does

1. Saves post-edit snapshot
2. Loads matching pre-review and post-review snapshots
3. Compares post-review vs post-edit (your manual changes)
4. Categorizes edit patterns
5. Checks accumulator for matching prior patterns
6. Proposes register/rule updates for patterns with evidence
7. Holds patterns below threshold in accumulator
8. Applies user-approved updates to profile files

## When To Use

Run this AFTER you've manually edited a piece that was
generated with /voice-generate. The learning system needs
the comparison between what the pipeline produced and what
you actually wanted.

## Learning Over Time

Each time you run /voice-learn, the system accumulates
evidence. Patterns need 3+ instances before becoming rules.
This prevents one-off preferences from polluting your profile.

## Skill Invocation

```
Skill(scribe:voice-learn)
```
