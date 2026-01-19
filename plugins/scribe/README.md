# Scribe

Documentation review, cleanup, and generation with AI slop detection.

## Installation

```bash
claude plugins install scribe
```

Or reference from the marketplace:
```json
{
  "plugins": ["scribe@claude-night-market"]
}
```

## Features

### Skills

| Skill | Description |
|-------|-------------|
| **slop-detector** | Detect AI-generated content markers |
| **style-learner** | Extract writing style from exemplar text |
| **doc-generator** | Generate/remediate documentation |

### Commands

| Command | Description |
|---------|-------------|
| `/slop-scan` | Scan files for AI slop markers |
| `/style-learn` | Create style profile from examples |
| `/doc-polish` | Clean up AI-generated content |
| `/doc-generate` | Generate new documentation |
| `/doc-verify` | Validate documentation claims with proof-of-work |

### Agents

| Agent | Description |
|-------|-------------|
| **doc-editor** | Interactive documentation editing |
| **slop-hunter** | Comprehensive slop detection |
| **doc-verifier** | QA validation using proof-of-work methodology |

## Quick Start

### Detect AI Slop

```bash
# Scan current directory
/slop-scan

# Scan specific file with fix suggestions
/slop-scan README.md --fix
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
# Verify README claims and commands
/doc-verify README.md

# Verify with strict mode
/doc-verify docs/ --strict --report qa-report.md
```

## AI Slop Detection

Scribe detects patterns that reveal AI-generated content.

### Tier 1 Words (Highest Confidence)

Words that appear dramatically more often in AI text: delve, tapestry, realm, embark, beacon, multifaceted, nuanced, pivotal, meticulous, showcasing, leveraging, streamline, comprehensive.

### Phrase Patterns

Formulaic constructions like "In today's fast-paced world," "cannot be overstated," "navigate the complexities," and "treasure trove of."

### Structural Markers

Overuse of em dashes, excessive bullet points, uniform sentence length, perfect grammar without contractions.

### Fiction-Specific Tells

Physical cliches ("breath he didn't know he was holding"), emotion washing ("relief washed over"), vague depth markers ("something in his eyes").

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

## Plugin Structure

```
scribe/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   ├── doc-editor.md
│   ├── slop-hunter.md
│   └── doc-verifier.md
├── commands/
│   ├── slop-scan.md
│   ├── style-learn.md
│   ├── doc-polish.md
│   ├── doc-generate.md
│   └── doc-verify.md
├── skills/
│   ├── shared/
│   ├── slop-detector/
│   │   └── modules/
│   ├── style-learner/
│   │   └── modules/
│   └── doc-generator/
│       └── modules/
└── README.md
```

## Integration

Scribe integrates with other claude-night-market plugins:

- **imbue:proof-of-work**: Evidence-based verification methodology
- **sanctum:doc-updates**: Broader documentation maintenance
- **conserve:bloat-detector**: Token and content optimization
- **pensive:review skills**: Code review integration

## License

MIT
