# Doc Polish

Clean up AI-generated content and improve documentation quality.

## Usage

```bash
/doc-polish [target] [options]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `target` | File or directory to polish |

## Options

| Option | Description |
|--------|-------------|
| `--style` | Style profile to apply (default: none) |
| `--aggressive` | Apply all fixes without prompting |
| `--dry-run` | Show changes without applying |
| `--section` | Polish specific section only |
| `--docstrings` | Polish only docstrings in code files |

## Examples

```bash
# Polish README with prompts
/doc-polish README.md

# Apply style profile
/doc-polish docs/ --style project-docs

# Preview changes
/doc-polish api.md --dry-run

# Polish Python docstrings only
/doc-polish src/**/*.py --docstrings
```

## Workflow

1. **Scan** for slop markers
2. **Categorize** by severity
3. **Present** section-by-section changes
4. **Apply** approved changes
5. **Verify** improvement

## Interactive Mode

For each section with issues:

```
## Section: Overview (Lines 1-35)

Current slop score: 4.2

Proposed changes:
1. Delete opener "In today's fast-paced world..."
2. Replace "comprehensive" with "thorough"
3. Convert bullet list to prose

Before:
> In today's fast-paced world, comprehensive
> documentation is essential...

After:
> scribe detects AI patterns in documentation
> and helps you fix them.

Proceed? [Y]es / [N]o / [E]dit / [S]kip section
```

## Docstring Mode

When polishing code:

```python
# BEFORE
def process(data):
    """
    This function leverages advanced algorithms
    to comprehensively process the input data.
    """

# AFTER
def process(data):
    """Process input data and return result."""
```

Code logic remains untouched.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Polish complete |
| 1 | Some sections skipped |
| 2 | Error during polish |

## See Also

- `/slop-scan` - Detect issues first
- `Skill(scribe:doc-generator)` - Full generation skill
