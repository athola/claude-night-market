# Token Estimator - Redirect Notice

## Important: This tool has been consolidated

The token-estimator implementation has been moved to the **abstract** plugin for centralized maintenance and to eliminate duplication.

## Usage

### Via Makefile (Recommended)
```bash
# From the conservation directory
make token-estimate --file skills/resource-management/token-conservation/SKILL.md
make token-estimate --directory skills/ --include-dependencies
```

### Direct Execution
```bash
# From the abstract directory
cd ../abstract
uv run python scripts/token_estimator.py --file path/to/SKILL.md
uv run python scripts/token_estimator.py --directory ~/.claude/skills/
uv run python scripts/token_estimator.py --file SKILL.md --include-dependencies
```

## Why the Change?

The abstract plugin provides a more sophisticated implementation using:
- Centralized `TokenAnalyzer` class for consistent token counting
- Better CLI framework with structured output
- Enhanced dependency resolution
- Integration with abstract's utility functions

## Features (via abstract)

The tool calculates approximate token counts for a skill's frontmatter, body, and code blocks. It can include tokens from dependencies in its analysis. It supports analyzing single files or batch processing directories of skills. Based on usage patterns, it provides optimization recommendations.

## Output Components

- Total token count with character/line statistics
- Component breakdown (frontmatter, body, code blocks)
- Dependency analysis (when enabled)
- Optimization recommendations based on token thresholds
- Summary reports for batch operations

## Best Practices

- For a complete analysis, run the tool with the `--include-dependencies` flag.
- Token thresholds: 800-2000 optimal, 2000-3000 consider modularization, >3000 high priority for splitting
- When optimizing, consider extracting code examples to scripts/ directory
- Balance between code content and documentation for readability
