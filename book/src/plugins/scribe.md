# scribe

Documentation review, cleanup, and generation with AI slop detection.

## Overview

Scribe helps maintain high-quality documentation by detecting AI-generated
content patterns ("slop"), learning writing styles from exemplars,
and generating or remediating documentation.
It integrates with sanctum's documentation workflows.

## Installation

```bash
/plugin install scribe@claude-night-market
```

## Skills

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `slop-detector` | Detect AI-generated content markers | Scanning docs for AI tells |
| `style-learner` | Extract writing style from exemplar text | Creating style profiles |
| `doc-generator` | Generate/remediate documentation | Writing or fixing docs |
| `doc-importer` | Import external documents (PDF, DOCX, PPTX) to markdown | Converting non-markdown files for editing |
| `tech-tutorial` | Plan, draft, and refine technical tutorials | Writing step-by-step developer guides |
| `session-to-post` | Convert sessions into blog posts or case studies | Sharing session outcomes |
| `session-replay` | Convert session JSONL into GIF/MP4/WebM replays | Creating animated session recordings |

## Commands

| Command | Description |
|---------|-------------|
| `/style-learn` | Create style profile from examples |
| `/doc-polish` | Clean up AI-generated content |
| `/doc-generate` | Generate new documentation |
| `/session-to-post` | Convert current session into a blog post or case study |
| `/session-replay` | Generate GIF/MP4/WebM replay from session JSONL |

## Agents

| Agent | Description |
|-------|-------------|
| `doc-editor` | Interactive documentation editing |
| `slop-hunter` | Full-document slop detection |
| `doc-verifier` | QA validation using proof-of-work methodology |

## Usage Examples

### Detect AI Slop

```bash
# Scan using the slop-detector skill
Skill(scribe:slop-detector)

# Or use the slop-hunter agent for thorough detection
Agent(scribe:slop-hunter)
```

### Clean Up Content

```bash
# Interactive polish
/doc-polish docs/guide.md

# Polish all markdown files
/doc-polish **/*.md
```

### Learn a Style

```bash
# Create style profile from examples
/style-learn good-examples/*.md --name house-style

# Generate with learned style
/doc-generate readme --style house-style
```

### Replay a Session

```bash
# Generate a GIF replay from a Claude Code session
/session-replay ~/.claude/projects/myproject/sessions/abc123.jsonl

# Codex sessions are auto-detected
/session-replay codex-session.jsonl --format mp4
```

### Verify Documentation

```bash
# Verify README claims and commands (now agent-only)
Agent(scribe:doc-verifier)

# For targeted verification, use the doc-generator skill
Skill(scribe:doc-generator)
```

## AI Slop Detection

Scribe detects patterns that reveal AI-generated content:

### Tier 1 Words (Highest Confidence)

Words that appear far more often in AI text than human text.
See `Skill(scribe:slop-detector)` for the full word list
and scoring weights.

### Phrase Patterns

Formulaic constructions: vapid openers, empty emphasis,
and attribution cliches. The detector scores these at 2-4
points each.

### Structural Markers

Overuse of em dashes, excessive bullet points, uniform sentence length,
perfect grammar without contractions.

## Writing Principles

Scribe enforces these principles:

1. **Ground every claim**: Use specifics, not adjectives
2. **Trim crutches**: No formulaic openers or closers
3. **Show perspective**: Include reasoning and trade-offs
4. **Vary structure**: Mix sentence lengths, balance bullets with prose
5. **Use active voice**: Direct statements over passive constructions

## Vocabulary Substitutions

Scribe suggests plain replacements for flagged words.
See `Skill(scribe:slop-detector)` for the full
substitution table with context-aware alternatives.

## Examples

These examples show slop remediation in practice.
Each pair includes a score reduction from the detector.

### Example 1: Vocabulary Slop (8/10 to 1/10)

A sentence with five Tier 1 words was reduced to plain
language. The fix replaced jargon verbs with "uses" and
"check," and removed unnecessary adjectives.

**After**:
> "This solution uses modern tools to check
> documentation quality."

### Example 2: Structural Patterns (7/10 to 1/10)

Four em dashes in a single sentence were collapsed into
one flowing statement using "and" and "to."

**After**:
> "The system processes requests and handles validation
> to ensure data integrity before returning results."

### Example 3: Phrase Patterns (9/10 to 1/10)

A vapid opener, a filler hedge, and an empty emphasis
phrase were all removed. The rewrite states the tool's
purpose directly.

**After**:
> "This tool improves documentation quality by detecting
> and flagging AI-generated patterns."

## Integration

Scribe integrates with sanctum documentation workflows:

| Sanctum Command | Scribe Integration |
|-----------------|-------------------|
| `/pr-review` | Runs `slop-detector` on changed `.md` files |
| `/update-docs` | Runs `slop-detector` on edited docs |
| `/update-docs --readme` | Runs `slop-detector` on README |
| `/prepare-pr` | Verifies PR descriptions with `slop-detector` |

## Dependencies

Scribe uses skills from other plugins:

- **imbue:proof-of-work**: Evidence-based verification (used by `doc-verifier`)
- **conserve:bloat-detector**: Token optimization

<div class="achievement-hint" data-achievement="doc-cleanup">
Clean up AI slop in 10 files to unlock: Documentation Purist
</div>
