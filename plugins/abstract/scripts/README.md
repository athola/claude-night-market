# Scripts Directory

Python scripts for validation, optimization, and analysis of Abstract plugin skills.

## Available Scripts

### abstract_validator.py
Validates Abstract meta-skill patterns and dependencies.

**Usage**:
```bash
# Scan for dependency issues
python scripts/abstract_validator.py --scan

# Generate report
python scripts/abstract_validator.py --report

# Both
python scripts/abstract_validator.py --report --scan
```

### context_optimizer.py
Analyzes skill files for context window optimization.

**Usage**:
```bash
# Analyze single skill
python scripts/context_optimizer.py analyze path/to/SKILL.md

# Generate directory report
python scripts/context_optimizer.py report skills/

# Show statistics
python scripts/context_optimizer.py stats skills/
```

## Nested Scripts

Skills may contain their own specialized scripts:

- `skills/skills-eval/scripts/` - Skill evaluation utilities
- `skills/modular-skills/scripts/` - Module validation tools
- `skills/performance-optimization/scripts/` - Example optimization scripts

## Python Package Integration

All scripts use the centralized `abstract` package for shared functionality:

```python
from abstract.config import AbstractConfig
from abstract.utils import (
    find_skill_files,
    load_skill_file,
    estimate_tokens,
    parse_yaml_frontmatter,
)
```

See `src/abstract/` for available modules and `docs/python-structure.md` for details.

## Running Scripts

### With Package Installed
```bash
# Install in editable mode
uv pip install -e .

# Run scripts directly
python scripts/abstract_validator.py --scan
```

### Without Installation
```bash
# Scripts auto-detect and add src/ to PYTHONPATH
python scripts/abstract_validator.py --scan
```

## Adding New Scripts

When creating new scripts:

1. Import from `abstract` package for common functionality
2. Add fallback import path if package not installed
3. Include `--help` documentation
4. Follow existing patterns for argument handling
5. Add tests to `tests/` directory

**Example structure**:
```python
#!/usr/bin/env python3
"""Script description."""

import sys
from pathlib import Path

try:
    from abstract.config import AbstractConfig
    from abstract.utils import find_skill_files
except ImportError:
    src_path = Path(__file__).parent.parent / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))
        from abstract.config import AbstractConfig
        from abstract.utils import find_skill_files
    else:
        print("ERROR: Cannot import abstract package", file=sys.stderr)
        sys.exit(1)

def main():
    # Script logic here
    pass

if __name__ == "__main__":
    main()
```

## Development

Use the Makefile for common tasks:
```bash
make format     # Format all Python scripts
make lint       # Run linting checks
make typecheck  # Run mypy type checking
make security   # Run security scans
make test       # Run all quality checks
```
