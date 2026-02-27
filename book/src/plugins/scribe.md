# scribe

Documentation review, cleanup, and generation with AI slop detection.

## Overview

Scribe helps maintain high-quality documentation by detecting AI-generated content patterns ("slop"), learning writing styles from exemplars, and generating or remediating documentation. It integrates with sanctum's documentation workflows.

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

## Commands

| Command | Description |
|---------|-------------|
| `/style-learn` | Create style profile from examples |
| `/doc-polish` | Clean up AI-generated content |
| `/doc-generate` | Generate new documentation |

## Agents

| Agent | Description |
|-------|-------------|
| `doc-editor` | Interactive documentation editing |
| `slop-hunter` | Comprehensive slop detection |
| `doc-verifier` | QA validation using proof-of-work methodology |

## Usage Examples

### Detect AI Slop

```bash
# Scan using the slop-detector skill
Skill(scribe:slop-detector)

# Or use the slop-hunter agent for comprehensive detection
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

Words that appear dramatically more often in AI text: delve, tapestry, realm, embark, beacon, multifaceted, nuanced, pivotal, meticulous, showcasing, leveraging, streamline, comprehensive.

### Phrase Patterns

Formulaic constructions like "In today's fast-paced world," "cannot be overstated," "navigate the complexities," and "treasure trove of."

### Structural Markers

Overuse of em dashes, excessive bullet points, uniform sentence length, perfect grammar without contractions.

## Writing Principles

Scribe enforces these principles:

1. **Ground every claim**: Use specifics, not adjectives
2. **Trim crutches**: No formulaic openers or closers
3. **Show perspective**: Include reasoning and trade-offs
4. **Vary structure**: Mix sentence lengths, balance bullets with prose
5. **Use active voice**: Direct statements over passive constructions

## Vocabulary Substitutions

| Instead of | Use |
|------------|-----|
| leverage | use |
| utilize | use |
| comprehensive | thorough |
| robust | solid |
| facilitate | help |
| optimize | improve |
| delve | explore |
| embark | start |

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
