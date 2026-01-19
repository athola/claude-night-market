# Doc Generate

Generate new documentation with human-quality writing.

## Usage

```bash
/doc-generate [type] [options]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `type` | Document type: readme, guide, api, tutorial, changelog |

## Options

| Option | Description |
|--------|-------------|
| `--style` | Style profile to apply |
| `--output` | Output file path |
| `--context` | Additional context files to reference |
| `--length` | Target length: short, medium, long |

## Examples

```bash
# Generate README from codebase
/doc-generate readme

# Generate API docs with style
/doc-generate api --style project-docs --output docs/api.md

# Generate tutorial with context
/doc-generate tutorial --context src/main.py examples/
```

## Document Types

### readme

Project overview with:
- One-line description
- Installation
- Quick start
- Key features
- License

### guide

User guide with:
- Introduction (brief)
- Prerequisites
- Step-by-step workflow
- Common patterns
- Troubleshooting

### api

API reference with:
- Endpoint/function listing
- Parameters
- Return values
- Examples
- Error handling

### tutorial

Learning-focused with:
- Goal statement
- Prerequisites
- Incremental steps
- Explanations
- Final result

### changelog

Version history with:
- Version headers
- Change categories (Added, Changed, Fixed, Removed)
- Brief descriptions
- Breaking change notices

## Quality Enforcement

All generated content automatically:

1. Avoids tier-1 slop words
2. Follows grounding principle (specifics over adjectives)
3. Uses appropriate sentence variation
4. Skips formulaic openers/closers
5. Runs through slop-detector before output

## Output

Generated file with quality report:

```
Generated: docs/guide.md (1,245 words)

Quality Check:
- Slop score: 0.8 (clean)
- Tier 1 words: 0
- Em dashes: 2/1000
- All claims grounded: yes

File written successfully.
```

## See Also

- `/style-learn` - Create style profile first
- `/doc-polish` - Refine generated content
- `Skill(scribe:doc-generator)` - Full generation skill
