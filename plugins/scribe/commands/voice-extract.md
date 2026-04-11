---
name: voice-extract
description: Extract your writing voice from samples into a reusable profile
arguments:
  - name: profile-name
    description: Name for the voice profile (e.g., "personal", "work")
    required: true
  - name: samples-dir
    description: Path to directory containing writing samples (.md/.txt)
    required: false
---

# /voice-extract Command

Extract a voice profile from writing samples using SICO
comparative analysis.

## Usage

```bash
# From a directory of samples
/voice-extract myvoice --samples-dir ~/writing-samples/

# Interactive mode (paste samples one at a time)
/voice-extract myvoice
```

## What This Does

1. Collects writing samples (directory or interactive paste)
2. Anonymizes samples (strips context labels)
3. Generates Claude's baseline output on matched topics
4. Runs SICO Pass 1 (broad comparative extraction)
5. Runs Pass 2 (pressure test for specificity)
6. Creates voice profile at ~/.claude/voice-profiles/{name}/
7. Generates default register

## After Extraction

- Review the extraction: `cat ~/.claude/voice-profiles/{name}/extraction.md`
- Generate in voice: `/voice-generate {name}`
- Add more samples later: `/voice-extract {name} --add`

## Skill Invocation

```
Skill(scribe:voice-extract)
```
