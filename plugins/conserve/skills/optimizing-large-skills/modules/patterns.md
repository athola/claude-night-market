# Detailed Optimization Patterns

## Externalization Pattern

**Move heavy implementations to tools with CLI interfaces:**
- Functions >20 lines → dedicated tool files
- Always include `argparse` CLI interface
- Add `if __name__ == "__main__"` execution block
- Provide help documentation and JSON output options

### Example Structure

```python
#!/usr/bin/env python3
"""Tool description."""

import argparse
import json
from pathlib import Path

def main_function(input_file: Path, option: str) -> dict:
    """Core implementation logic."""
    # Heavy implementation here (>20 lines)
    return {"result": "data"}

def cli():
    """Command-line interface."""
    parser = argparse.ArgumentParser(description="Tool description")
    parser.add_argument("input_file", type=Path, help="Input file path")
    parser.add_argument("--option", default="default", help="Option value")
    parser.add_argument("--output-json", action="store_true", help="JSON output")
    args = parser.parse_args()

    result = main_function(args.input_file, args.option)

    if args.output_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Result: {result}")

if __name__ == "__main__":
    cli()
```

## Consolidation Pattern

**Merge similar functions with parameterization:**

### Before Consolidation

```python
def analyze_python_files(path):
    # 20 lines of similar logic
    pass

def analyze_javascript_files(path):
    # 20 lines of similar logic
    pass

def analyze_rust_files(path):
    # 20 lines of similar logic
    pass
```

### After Consolidation

```python
def analyze_files(path, language):
    """Unified file analysis with language parameter."""
    language_configs = {
        "python": {"extensions": [".py"], "analyzer": python_analyzer},
        "javascript": {"extensions": [".js", ".ts"], "analyzer": js_analyzer},
        "rust": {"extensions": [".rs"], "analyzer": rust_analyzer},
    }

    config = language_configs[language]
    # Single implementation using config
    return analyze_with_config(path, config)
```

**Benefits:**
- 60-80% reduction in code duplication
- Single source of truth for logic
- Easier to maintain and extend

## Progressive Loading Pattern

**Use frontmatter for focused context loading:**

### Frontmatter Configuration

```yaml
---
name: skill-name
token_budget: 25
progressive_loading: true
---
```

### Progressive Content Blocks

```markdown
<!-- progressive: advanced -->
## Advanced Usage

This content loads only when explicitly requested.

### Complex Scenarios
...detailed content...
<!-- /progressive -->
```

### Benefits

- **5-10% token reduction** by deferring non-essential content
- Faster initial skill loading
- User requests advanced content when needed

## File Organization

### Recommended Structure

```
skill-name/
  SKILL.md              # Core documentation (~150-200 lines)
  modules/
    examples.md         # Usage examples and anti-patterns
    patterns.md         # Detailed implementation patterns
  tools/
    analyzer.py         # Heavy implementations with CLI
    controller.py       # Control logic with CLI
    config.yaml         # Structured data
  examples/
    basic-usage.py      # Minimal working example
    advanced-usage.py   # Complex scenarios
```

### Size Targets

| File Type | Target Size | Maximum Size |
|-----------|-------------|--------------|
| SKILL.md | 150-200 lines | 300 lines |
| modules/*.md | 100-150 lines | 250 lines |
| tools/*.py | Any size | No limit (with CLI) |
| examples/*.py | 20-50 lines | 100 lines |

## Analysis & Planning

### Automated Analysis

```bash
# Generate detailed optimization plan
python skills/optimizing-large-skills/tools/optimization-patterns.py \
  your-skill.md --verbose --generate-plan

# JSON output for automation
python skills/optimizing-large-skills/tools/optimization-patterns.py \
  your-skill.md --output-json
```

### Manual Analysis Checklist

**Phase 1: Identification**
- [ ] Identify files >300 lines
- [ ] Count code blocks and functions
- [ ] Measure inline code vs documentation ratio
- [ ] Find repeated patterns and similar functions

**Phase 2: Categorization**
- [ ] Mark heavy implementations (>20 lines) for externalization
- [ ] Group similar functions for consolidation
- [ ] Identify non-essential content for progressive loading
- [ ] List structured data that can replace code

**Phase 3: Prioritization**
- [ ] Externalize first (highest impact: 60-70% reduction)
- [ ] Consolidate second (medium impact: 15-20% reduction)
- [ ] Progressive loading third (low impact: 5-10% reduction)

## Validation

### Post-Optimization Checklist

**Phase 4: Implementation**
- [ ] Move heavy implementations (>20 lines) to separate files
- [ ] Add CLI interfaces to externalized tools
- [ ] Create tool directory structure
- [ ] Merge similar functions with parameterization
- [ ] Replace code blocks with structured data where appropriate
- [ ] Implement progressive loading for non-essential content
- [ ] Update skill documentation to reference external tools
- [ ] Add usage examples for each tool

**Phase 5: Verification**
- [ ] Verify line count <300 (target: 150-200)
- [ ] Test all externalized tools work correctly
- [ ] Confirm progressive loading functions
- [ ] Run skills-eval validation to verify size reduction
- [ ] Check that all references to external tools are correct
- [ ] Ensure examples work and are clear

### Success Metrics

- **Line count**: Reduced by 50-70%
- **Token usage**: Reduced by 40-60%
- **Skills-eval**: No "Large skill file" warnings
- **Maintainability**: Clear separation of concerns
- **Usability**: Tools have clear CLI interfaces
