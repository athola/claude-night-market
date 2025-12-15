# Skills-Eval Scripts

This directory contains evaluation and analysis tools for Claude Skills, along with shared utilities.

## Shared Utilities

### skill_utils.py

Shared utilities module that provides common functions for skill parsing, token estimation, and analysis. Other plugins can import these utilities to avoid duplication.

**Available Functions:**

```python
from skill_utils import (
    parse_frontmatter,    # Parse YAML frontmatter from skill content
    estimate_tokens,      # Estimate token count (4 chars/token)
    load_skill_file,      # Load and parse a skill file
    get_skill_name,       # Extract skill name from frontmatter
    format_score,         # Format scores for display
    get_efficiency_grade, # Calculate efficiency grades (A-D)
    get_optimization_level # Get optimization level descriptions
)
```

**Usage in Other Plugins:**

```python
import sys
from pathlib import Path

# Add abstract's scripts directory to path (installed from claude-night-market marketplace)
abstract_scripts = Path.home() / ".claude/plugins/marketplaces/claude-night-market/plugins/abstract/skills/skills-eval/scripts"
sys.path.insert(0, str(abstract_scripts))

# Import shared utilities
from skill_utils import parse_frontmatter, estimate_tokens, load_skill_file

# Use the utilities
content, frontmatter = load_skill_file("path/to/SKILL.md")
tokens = estimate_tokens(content)
```

## Evaluation Tools

### token-usage-tracker

Advanced token optimization analysis tool for Claude Agent SDK compliance.

**Features:**
- Token efficiency grading (A-D scale)
- Context compression analysis
- Progressive disclosure scoring
- Optimization suggestions with estimated savings
- Benchmarking against 2024 targets

**Usage:**
```bash
# Basic analysis
./token-usage-tracker --skill-path path/to/SKILL.md

# Markdown report
./token-usage-tracker --skill-path path/to/SKILL.md --format markdown

# JSON output
./token-usage-tracker --skill-path path/to/SKILL.md --format json

# With context analysis
./token-usage-tracker --skill-path path/to/SKILL.md --context-analysis
```

### tool-performance-analyzer

Analyzes tool use performance based on Claude Developer Platform research.

**Features:**
- Dynamic tool discovery efficiency
- Programmatic calling patterns
- Context preservation metrics
- Token reduction potential
- Latency optimization scores

**Usage:**
```bash
# Basic analysis
./tool-performance-analyzer --skill-path path/to/SKILL.md

# Specific metrics
./tool-performance-analyzer --skill-path path/to/SKILL.md --metrics discovery,calling

# Markdown report
./tool-performance-analyzer --skill-path path/to/SKILL.md --format markdown
```

### skills-auditor

Comprehensive skill discovery and analysis across all `~/.claude/` locations.

**Features:**
- Multi-dimensional quality scoring
- Integration, scalability, and reliability metrics
- API compliance checking
- Context optimization analysis
- Batch analysis of all skills

**Usage:**
```bash
# Scan all skills
./skills-auditor --scan-all --format table

# Analyze specific skill
./skills-auditor --skill-path path/to/SKILL.md --format markdown

# High-priority issues only
./skills-auditor --scan-all --priority high
```

### improvement-suggester

Generates prioritized, actionable improvement recommendations.

**Features:**
- Category-based improvements (critical, high, medium, low)
- Specific actions with code examples
- Effort and impact estimates
- Implementation order suggestions
- 2024 SDK compliance improvements

**Usage:**
```bash
# All improvements
./improvement-suggester --skill-path path/to/SKILL.md

# High-priority only
./improvement-suggester --skill-path path/to/SKILL.md --priority critical,high

# Markdown report
./improvement-suggester --skill-path path/to/SKILL.md --format markdown
```

### compliance-checker

Standards validation and security checking.

**Features:**
- Claude Skills v2 standards compliance
- Frontmatter validation
- Security issue detection
- Auto-fix for common issues

**Usage:**
```bash
# Check compliance
./compliance-checker --skill-path path/to/SKILL.md

# Auto-fix issues
./compliance-checker --skill-path path/to/SKILL.md --auto-fix

# Specific standard
./compliance-checker --skill-path path/to/SKILL.md --standard claude-skills-v2
```

## Output Formats

All tools support multiple output formats:

- **table** (default): Clean, console-friendly output
- **markdown**: Detailed reports with sections
- **json**: Machine-readable for automation

Example:
```bash
./token-usage-tracker --skill-path SKILL.md --format json > analysis.json
```

## Integration Examples

### In Other Plugins

Conservation plugin example:

```python
#!/usr/bin/env python3
"""Conservation tool that uses abstract's utilities"""

import sys
from pathlib import Path

# Import from abstract (installed from claude-night-market marketplace)
abstract_scripts = Path.home() / ".claude/plugins/marketplaces/claude-night-market/plugins/abstract/skills/skills-eval/scripts"
sys.path.insert(0, str(abstract_scripts))
from skill_utils import estimate_tokens, parse_frontmatter

def analyze_resource_usage(skill_path: str):
    """Analyze resource usage using abstract's utilities"""
    with open(skill_path) as f:
        content = f.read()

    tokens = estimate_tokens(content)
    frontmatter = parse_frontmatter(content)

    # Conservation-specific analysis
    # ...
```

### In CI/CD Pipelines

```yaml
name: Skill Quality Checks
on: [push, pull_request]

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Token Budget Check
        run: |
          ./skills/skills-eval/scripts/token-usage-tracker \
            --skill-path path/to/SKILL.md \
            --format json > tokens.json
          # Parse and fail if over budget
      - name: Compliance Check
        run: |
          python skills/skills-eval/scripts/compliance_checker.py \
            --skill-path path/to/SKILL.md \
            --standard claude-skills-v2
```

### In Pre-commit Hooks

```bash
#!/bin/bash
# .git/hooks/pre-commit

for skill in $(git diff --cached --name-only | grep SKILL.md); do
    echo "Checking $skill..."

    # Run token analysis
    ./skills/skills-eval/scripts/token-usage-tracker \
        --skill-path "$skill" \
        --format table

    # Run compliance check
    python skills/skills-eval/scripts/compliance_checker.py \
        --skill-path "$skill" \
        --standard claude-skills-v2 || exit 1
done
```

## Development

### Adding New Utilities

When adding new shared utilities to `skill_utils.py`:

1. Keep functions pure and focused
2. Add type hints
3. Include docstrings
4. Consider backward compatibility
5. Update this README

Example:
```python
def new_utility_function(param: str) -> Dict:
    """
    Brief description of what this does.

    Args:
        param: Description of parameter

    Returns:
        Description of return value
    """
    # Implementation
    pass
```

### Testing

```bash
# Test shared utilities
python3 -c "from skill_utils import *; print(estimate_tokens('test' * 100))"

# Test individual tools
./token-usage-tracker --skill-path ../SKILL.md
./tool-performance-analyzer --skill-path ../SKILL.md
./skills-auditor --skill-path ../SKILL.md
```

## Dependencies

All tools use:
- Python 3.12+
- Standard library modules
- `yaml` library for frontmatter parsing

No external dependencies required for basic usage.

## See Also

- **../SKILL.md** - Main skills-eval documentation
- **../modules/** - Detailed evaluation frameworks and guides
- **../2024-UPDATES.md** - Latest enhancements and standards
- **../../DEDUPLICATION_REPORT.md** - Architecture and deduplication strategy
