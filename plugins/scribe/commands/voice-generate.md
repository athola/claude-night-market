---
name: voice-generate
description: Generate text in your extracted writing voice
arguments:
  - name: profile-name
    description: Name of the voice profile to use
    required: true
  - name: register
    description: Which register to use (default, casual, technical, etc.)
    required: false
    default: default
  - name: --review
    description: Run dual review agents after generation
    required: false
    default: "true"
  - name: --learn
    description: Enable learning mode (capture snapshots)
    required: false
    default: "true"
---

# /voice-generate Command

Generate text in a trained writing voice.

## Usage

```bash
# Generate with default register, review enabled
/voice-generate myvoice

# Use specific register, skip review
/voice-generate myvoice --register casual --review false

# Generate without learning snapshots
/voice-generate myvoice --learn false
```

## What This Does

1. Loads voice profile and selected register
2. Asks for source material (notes, topic, outline)
3. Frames source material as "raw notes to think through"
4. Generates text using Opus with full voice features
5. Auto-fixes hard failures (banned phrases, em dashes)
6. Dispatches prose + craft review agents (if --review)
7. Presents advisory tables for user decisions
8. Saves snapshots (if --learn)

## Source Material

Provide your source material when prompted. Best results
when framed as rough notes or ideas you're thinking through.
The skill automatically reframes input as raw notes unless
you explicitly request otherwise.

## Skill Invocation

```
Skill(scribe:voice-generate)
```
