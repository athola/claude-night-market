# Script Integration Pattern for Claude Code

This document defines the standard pattern for Python scripts that can be invoked by Claude Code for programmatic tool calling.

## Why This Matters

Standardizing script integration is necessary for several reasons. It allows Claude Code to parse tool output through structured JSON data and enables the chaining of operations by processing intermediate data outside the context window. Furthermore, idempotent operations permit safe retries by preventing unintended side effects, and an asynchronous design supports parallel execution of independent tasks.

Reference: [Anthropic Advanced Tool Use](https://www.anthropic.com/engineering/advanced-tool-use)

## Required Pattern

### 1. CLI with argparse

```python
#!/usr/bin/env python3
"""Tool description for Claude to understand purpose.

Returns:
    JSON object with:
    - field1 (str): Description of field
    - field2 (list): Description of list contents
    - success (bool): Whether operation succeeded
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Clear description of what this tool does"
    )

    # Required arguments
    parser.add_argument(
        "--input",
        required=True,
        help="Input file or directory path"
    )

    # Output format (REQUIRED)
    parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output results as JSON for programmatic use"
    )

    # OR use --format for multiple options
    parser.add_argument(
        "--format",
        choices=["text", "json", "table"],
        default="text",
        help="Output format (default: text)"
    )

    args = parser.parse_args()

    try:
        result = do_work(args.input)
        output_result(result, args)
        sys.exit(0)
    except Exception as e:
        output_error(str(e), args)
        sys.exit(1)


def output_result(result: dict, args) -> None:
    """Output result in requested format."""
    if getattr(args, 'output_json', False) or getattr(args, 'format', '') == 'json':
        print(json.dumps({
            "success": True,
            "data": result
        }, indent=2))
    else:
        # Human-readable format
        print(f"Result: {result}")


def output_error(message: str, args) -> None:
    """Output error in requested format."""
    if getattr(args, 'output_json', False) or getattr(args, 'format', '') == 'json':
        print(json.dumps({
            "success": False,
            "error": message
        }, indent=2))
    else:
        print(f"Error: {message}", file=sys.stderr)


if __name__ == "__main__":
    main()
```

### 2. JSON Output Structure

Always include in JSON output:
- `success` (bool): Whether the operation succeeded
- `data` or specific fields: The actual result
- `error` (str, optional): Error message if failed

```json
{
  "success": true,
  "data": {
    "files_processed": 10,
    "recommendations": ["...", "..."],
    "metrics": {"lines": 500, "tokens": 1200}
  }
}
```

### 3. Document Return Structure

In the module docstring, document what the tool returns:

```python
"""Analyze skill files for quality metrics.

Returns (JSON):
    success (bool): Whether analysis completed
    data.files_analyzed (int): Number of files processed
    data.issues (list): List of {severity, message, file, line}
    data.score (float): Overall quality score 0-100
"""
```

### 4. Idempotent Operations

Scripts should be safe to retry:

```python
def process_file(path: Path) -> dict:
    """Process file idempotently.

    - Check if already processed before modifying
    - Use atomic writes (write to temp, then rename)
    - Return same result if called multiple times
    """
    # Check cache/state
    if is_already_processed(path):
        return get_cached_result(path)

    # Process
    result = do_processing(path)

    # Cache result
    cache_result(path, result)

    return result
```

## Using abstract CLI Framework

For scripts in the abstract plugin ecosystem, use the built-in framework:

```python
from abstract.cli_framework import AbstractCLI, CLIResult, cli_main

class MyToolCLI(AbstractCLI):
    def __init__(self):
        super().__init__(
            name="my-tool",
            description="What this tool does",
            version="1.0.0"
        )

    def add_arguments(self, parser):
        parser.add_argument("--input", required=True)

    def run(self, args) -> CLIResult:
        result = do_work(args.input)
        return CLIResult(success=True, data=result)

if __name__ == "__main__":
    cli_main(MyToolCLI())
```

The framework automatically provides `--format json` support.

## SKILL.md Integration

In your SKILL.md, show both human and programmatic usage:

```markdown
## Script Integration

### Human-Readable Output
```bash
uv run python scripts/my_tool.py --input ./src
```

### Programmatic Output (for Claude Code)
```bash
uv run python scripts/my_tool.py --input ./src --output-json
```

### Return Structure
```json
{
  "success": true,
  "data": {
    "field1": "...",
    "field2": [...]
  }
}
```
```

## Checklist for Script Compliance

- [ ] Has argparse CLI with clear help text
- [ ] Supports `--output-json` or `--format json`
- [ ] JSON output includes `success` field
- [ ] Errors output as JSON when in JSON mode
- [ ] Module docstring documents return structure
- [ ] Operations are idempotent where possible
- [ ] Exit codes: 0 for success, 1+ for errors

## Scripts Needing Updates

Based on audit, these scripts need CLI/JSON integration:

| Script | Plugin | Priority | Status | Notes |
|--------|--------|----------|--------|-------|
| `test_generator.py` | sanctum | High | Complete | Added --output-json with structured output |
| `quality_checker.py` | sanctum | High | Complete | Fixed JSON output printing |
| `tracker.py` | minister | Medium | Complete | Added --output-json to project_tracker.py |
| `safe_replacer.py` | conserve | Medium | Complete | Added argparse with --output-json |
| `template_engine.py` | attune | Low | Deferred | Internal utility |
| `template_loader.py` | attune | Low | Deferred | Internal utility |
| `seed_corpus.py` | memory-palace | Low | Deferred | One-time setup |
| `build_indexes.py` | memory-palace | Low | Deferred | One-time setup |

## See Also

- [Anthropic Advanced Tool Use](https://www.anthropic.com/engineering/advanced-tool-use)
- [Common Workflows](./common-workflows.md)
- [abstract CLI Framework](../plugins/abstract/src/abstract/cli_framework.py)
