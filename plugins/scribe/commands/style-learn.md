# Style Learn

Extract writing style from exemplar text to create a style profile.

## Usage

```bash
/style-learn [sources...] [options]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `sources` | Files to analyze as style exemplars |

## Options

| Option | Description |
|--------|-------------|
| `--name` | Profile name (default: "default") |
| `--output` | Output location (default: .scribe/style-profile.yaml) |
| `--merge` | Merge with existing profile |
| `--interactive` | Select exemplar passages interactively |

## Examples

```bash
# Learn from README
/style-learn README.md

# Learn from multiple files
/style-learn docs/*.md --name project-docs

# Interactive exemplar selection
/style-learn blog-posts/ --interactive
```

## Output

Creates a style profile with:

```yaml
# Style Profile: project-docs
# Generated: 2024-01-15
# Sources: README.md, docs/guide.md

voice:
  tone: professional
  perspective: first-person-plural
  formality: neutral

vocabulary:
  average_word_length: 5.2
  jargon_level: moderate
  contractions: frequent
  preferred_terms:
    - "use" over "utilize"
  avoided_terms:
    - delve
    - leverage

sentences:
  average_length: 16
  length_variance: high

exemplars:
  - label: "Technical explanation"
    text: |
      The cache sits between API and database...
```

## Workflow

1. Collect source files
2. Extract quantitative metrics
3. Select representative passages
4. Generate profile YAML
5. Validate with sample generation

## See Also

- `Skill(scribe:style-learner)` - Full style learning skill
- `/doc-generate` - Generate docs using learned style
