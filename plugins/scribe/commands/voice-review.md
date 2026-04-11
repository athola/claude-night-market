---
name: voice-review
description: Review existing text against a voice profile
arguments:
  - name: file
    description: Path to the text file to review
    required: true
  - name: --profile
    description: Voice profile to compare against
    required: true
  - name: --register
    description: Which register to use for comparison
    required: false
    default: default
---

# /voice-review Command

Review existing text for voice drift and craft quality.

## Usage

```bash
# Review a file against your voice profile
/voice-review draft.md --profile myvoice

# Use specific register
/voice-review draft.md --profile myvoice --register casual
```

## What This Does

1. Reads the target file
2. Loads voice profile and register
3. Dispatches prose reviewer (AI patterns, voice drift)
4. Dispatches craft reviewer (naming, structure, anchoring)
5. Auto-fixes hard failures
6. Presents advisory tables for user decisions
7. Applies accepted fixes

## Standalone vs Pipeline

This command runs review independently of generation. Use
when you have existing text (written by hand or generated
elsewhere) that you want to check against your voice profile.

## Skill Invocation

```
Skill(scribe:voice-review)
```
