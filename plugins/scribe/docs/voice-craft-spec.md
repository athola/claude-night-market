# Voice Craft Specification

## Overview

Extend the scribe plugin with SICO-based voice extraction,
generation in learned voice, dual review agents, and an
iterative learning loop. Any user can train it with their
writing samples to build a persistent voice profile.

## Core Concepts

### SICO Comparative Extraction

Rather than measuring surface metrics (word length, sentence
counts), the extraction compares user writing samples against
Claude's default output on matched topics. The model describes
what the user does differently. This produces voice descriptions
that encode implicit structural patterns.

### Register System

One user can have multiple voice registers (casual, technical,
narrative). Each register has its own feature description from
extraction. Craft rules and banned phrases are shared across
registers within a profile.

### Source Material Framing

The single largest variable in output quality. Material framed
as "raw notes I'm still thinking through" produces dramatically
better output than framing it as summaries or transcripts.

## Storage Model

### Per-User (primary)

```
~/.claude/voice-profiles/
  {profile-name}/
    manifest.json         # Sample tracking, metadata
    samples/              # Raw writing samples (anonymized)
    extraction.md         # SICO feature description
    craft-rules.md        # Shared craft techniques
    banned-phrases.md     # Anti-patterns to auto-fix
    registers/
      default.md          # Default voice register
      {name}.md           # Additional registers
    learning/
      accumulator.json    # Pending pattern observations
      snapshots/          # Text at 3 stages for comparison
```

### Per-Project Override (optional)

```
.voice/
  override.md             # Project-specific voice adjustments
  registers/              # Project-specific registers
```

## User Stories

### US-1: Extract Voice Profile

As a user, I want to provide my writing samples and have the
system extract a voice profile so that future generated text
sounds like me.

**Acceptance criteria:**
- Accepts 3+ writing samples (min 500 words total)
- Samples are anonymized (stripped of context labels)
- Generates Claude's baseline output on matched topics
- Runs SICO Phase 1 comparative extraction
- Produces feature description in extraction.md
- Runs pressure-test pass for specificity
- Profile reads like followable instructions, not a book report

### US-2: Generate in Voice

As a user, I want to provide source material and have text
generated in my extracted voice, using a specified register.

**Acceptance criteria:**
- Source material framed as "raw notes to think through"
- Applies extraction features + craft rules
- Selects register (defaults to "default")
- Output avoids banned phrases
- No structural rules that increase detectability
- Uses Opus for voice-dependent generation

### US-3: Prose Review

As a user, I want generated text reviewed for AI patterns,
banned phrases, and voice drift against my register.

**Acceptance criteria:**
- Catches AI vocabulary (furthermore, utilize, etc.)
- Detects frictionless transitions
- Flags structural monotony
- Auto-fixes hard fails (banned phrases)
- Returns advisory table for soft issues
- User accepts/rejects/rewrites each advisory row

### US-4: Craft Review

As a user, I want generated text evaluated for craft quality:
naming opportunities, aphoristic destinations, dwelling,
structural devices, and human-moment anchoring.

**Acceptance criteria:**
- Evaluates 5 dimensions (naming, aphoristic destinations,
  central-point dwelling, structural literary devices,
  human-moment anchoring)
- Rates each dimension (Strong/Adequate/Opportunity)
- Proposes improvements for Opportunity items
- Returns advisory table

### US-5: Learning Loop

As a user, I want the system to learn from my manual edits so
the voice profile improves over time.

**Acceptance criteria:**
- Snapshots text at 3 points (pre-review, post-review,
  manually-edited)
- Compares snapshots to identify recurring edit patterns
- Proposes register/rule updates with evidence
- Patterns below threshold stored in accumulator
- Accumulator checked on each learning pass

### US-6: Sample Intake

As a user, I want to provide samples via directory or
interactive paste, with manifest tracking.

**Acceptance criteria:**
- Accepts directory path containing .md/.txt files
- Accepts interactive paste-one-at-a-time workflow
- Manifest tracks source, word count, date added
- Validates minimum word count per sample
- Anonymizes labels (Sample 1, Sample 2, etc.)

## Technical Constraints

- Voice profiles stored per-user at ~/.claude/voice-profiles/
- Optional per-project .voice/ directory for overrides
- Extraction uses Opus (higher quality feature descriptions)
- Generation uses Opus (tonal shifts, parenthetical subversion)
- Review agents can use Sonnet (structured enough prompts)
- No structural rules that increase AI detectability
- Craft techniques are detection-neutral (concrete-first,
  naming, opening moves)
- Feature descriptions replace voice-level rules (sentence
  variety, clause density are redundant with good extraction)

## Skills to Create

1. `voice-extract` - SICO comparative extraction
2. `voice-generate` - Generate text in learned voice
3. `voice-review` - Dispatch dual review agents
4. `voice-learn` - Learning loop from edit comparison

## Agents to Create

1. `prose-reviewer` - AI patterns, banned phrases, voice drift
2. `craft-reviewer` - Naming, structure, quality dimensions

## Commands to Create

1. `voice-extract` - Extract voice from samples
2. `voice-generate` - Generate in voice
3. `voice-review` - Review generated text
4. `voice-learn` - Run learning pass on edited text
