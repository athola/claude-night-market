# Python Project Structure

## Overview

The Abstract plugin uses a standard Python `src/` layout that works with both `uv` package management and Claude Code plugin requirements.

## Directory Structure

```
abstract/
├── src/
│   └── abstract/              # Python package for shared modules
│       ├── __init__.py        # Package initialization
│       ├── config.py          # Configuration management
│       ├── errors.py          # Error handling utilities
│       ├── utils.py           # Common skill processing utilities
│       ├── py.typed           # Type hints marker (PEP 561)
│       └── README.md          # Package documentation
├── scripts/                   # Executable scripts
│   ├── abstract_validator.py # Validates meta-skill patterns
│   ├── context_optimizer.py  # Analyzes context window usage
│   └── README.md             # Scripts documentation
├── .pre-commit/              # Pre-commit hooks
│   └── validate_abstract.py
├── skills/                   # Claude Code skills
│   ├── modular-skills/
│   │   └── scripts/          # Module validation tools
│   └── skills-eval/
│       └── scripts/          # Skill evaluation utilities
├── config/                   # Configuration files (YAML only)
│   └── abstract_config.yaml
├── docs/                     # Documentation
│   ├── python-structure.md   # This file
│   └── skill-selection.md    # Meta-skills reference
├── tests/                    # Test suite
├── pyproject.toml           # Python project configuration
└── README.md                # Main documentation
```

## Package Design Rationale

### Why src/ Layout?

The `src/` layout is a Python packaging best practice (PEP 517/518) that:

1. **Prevents accidental imports**: Can't import uninstalled package during development
2. **Forces proper installation**: Tests run against installed package, not source
3. **Standard convention**: Expected by modern Python tooling (uv, pip, hatch)
4. **Clean namespace**: Avoids polluting project root with package modules

### Why Not Keep config/ and lib/?

The previous `config/` and `lib/` directories had issues:

1. **Import problems**: Hard to import from scripts without PYTHONPATH manipulation
2. **Not standard**: Python ecosystem expects packages in standard locations
3. **No install support**: Can't install as package for use across scripts
4. **Type checking issues**: Mypy and other tools expect standard structure

### New Structure Benefits

1. **Works with uv**: Standard package that uv can install and manage
2. **Editable installs**: `uv pip install -e .` for development
3. **Proper imports**: Scripts can do `from abstract.config import ...`
4. **Type checking**: Full mypy support with py.typed marker
5. **Testing**: Can test installed package properly
6. **Distribution**: Can publish to PyPI if needed

## Installation and Usage

### For Development

```bash
# Install in editable mode with dev dependencies
uv pip install -e ".[dev]"

# Run scripts (imports work automatically)
python scripts/abstract_validator.py
```

### For Scripts

Scripts can import from the package once installed:

```python
#!/usr/bin/env python3
"""Script using abstract package."""

from abstract.config import AbstractConfig
from abstract.errors import ErrorHandler

# Use shared configuration
config = AbstractConfig.from_yaml("config/abstract_config.yaml")

# Use shared error handling
errors = ErrorHandler("script-name")
```

### Without Installation

If you don't want to install the package:

```bash
# Add src to PYTHONPATH
PYTHONPATH=/path/to/abstract/src python scripts/my_script.py

# Or in the script itself
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

## Module Organization

### abstract.config

**Purpose**: Centralized configuration management

**Classes**:
- `AbstractConfig`: Main configuration with all settings
- `SkillValidationConfig`: Rules for skill validation
- `ToolConfig`: Tool-specific configuration
- `ContextOptimizerConfig`: Context window optimization thresholds

**Usage**:
```python
from abstract.config import AbstractConfig

# Load from YAML with automatic defaults
config = AbstractConfig.from_yaml("config/abstract_config.yaml")

# Access validation rules
max_size = config.skill_validation.MAX_SKILL_FILE_SIZE
required_fields = config.skill_validation.REQUIRED_FRONTMATTER_FIELDS
```

### abstract.errors

**Purpose**: Consistent error handling across tools

**Classes**:
- `ErrorHandler`: Centralized error management and logging
- `ErrorSeverity`: Error severity levels enum
- `ToolError`: Structured error information dataclass

**Usage**:
```python
from abstract.errors import ErrorHandler, ErrorSeverity, ToolError

errors = ErrorHandler("my-tool")

# Report an error
errors.handle_error(ToolError(
    severity=ErrorSeverity.HIGH,
    error_code="VALIDATION_FAILED",
    message="Skill validation failed",
    suggestion="Check frontmatter format"
))
```

### abstract.utils

**Purpose**: Common utilities for skill file processing

This module consolidates all shared functionality used across scripts, eliminating ~449 lines of duplicate code.

**Project Navigation**:
- `find_project_root(start_path)`: Find project root by locating config/ or pyproject.toml
- `load_config_with_defaults(project_root)`: Load configuration with automatic defaults

**Frontmatter Processing**:
- `extract_frontmatter(content)`: Extract frontmatter and body from skill content
- `parse_frontmatter_fields(frontmatter)`: Parse YAML frontmatter into dictionary
- `parse_yaml_frontmatter(content)`: Full YAML parsing of frontmatter
- `validate_skill_frontmatter(content, config)`: Validate frontmatter fields

**Skill File Operations**:
- `find_skill_files(directory)`: Find all SKILL.md files recursively
- `load_skill_file(skill_path)`: Load skill file and parse frontmatter
- `get_skill_name(frontmatter, skill_path)`: Get skill name from frontmatter or filename

**Analysis Functions**:
- `estimate_tokens(text)`: Estimate token count for text
- `check_meta_skill_indicators(content, config, skill_name)`: Check for meta-skill indicators
- `format_score(score, max_score)`: Format score for display

**Usage**:
```python
from abstract.utils import (
    find_skill_files,
    load_skill_file,
    estimate_tokens,
    validate_skill_frontmatter,
)
from abstract.config import AbstractConfig

# Find all skills
skill_files = find_skill_files(Path("skills/"))

# Load and analyze a skill
content, frontmatter = load_skill_file(skill_files[0])
tokens = estimate_tokens(content)

# Validate frontmatter
config = AbstractConfig()
issues = validate_skill_frontmatter(content, config.skill_validation)
```

## Integration with Claude Code

The structure is designed to work seamlessly with Claude Code:

1. **Plugin files unchanged**: Skills, scripts, and plugin.json in expected locations
2. **Shared code accessible**: Python modules available to all scripts
3. **No conflicts**: Package doesn't interfere with Claude Code functionality
4. **Configuration separation**: YAML configs stay in `config/`, Python code in `src/`

## Migration from Old Structure

### Old Structure (Problems)
```
config/
├── abstract_config.py    #  Hard to import
└── abstract_config.yaml  # OK Keep here

lib/
└── error_handler.py      #  Hard to import

scripts/
└── *.py                  #  Can't import from config/lib
                          #  Each had duplicate utility functions
```

### New Structure (Solutions)
```
src/abstract/
├── config.py             # OK from abstract.config import ...
├── errors.py             # OK from abstract.errors import ...
└── utils.py              # OK Centralized utilities

config/
└── abstract_config.yaml  # OK Still here (YAML only)

scripts/
└── *.py                  # OK Can import from abstract package
                          # OK Use shared utilities from utils.py
```

## Refactoring Results

The centralized package structure eliminated significant code duplication:

### Scripts Refactored

**Main Scripts**:
- `.pre-commit/validate_abstract.py`: 178 → 98 lines (-45%)
- `scripts/context_optimizer.py`: 241 → 193 lines (-20%)

**Nested Scripts**:
- `skills/skills-eval/scripts/skill_utils.py`: 137 → 94 lines (-31%)

### Code Eliminated

**Total Reduction**: ~449 lines of duplicate code removed (-33%)

**Duplicated Functions Consolidated** (now in `abstract.utils`):
- `find_project_root()` - Was duplicated in 3 scripts
- `extract_frontmatter()` - Was duplicated in 4 scripts
- `parse_yaml_frontmatter()` - Was duplicated in 3 scripts
- `estimate_tokens()` - Was duplicated in 3 scripts
- `validate_skill_frontmatter()` - Was duplicated in 2 scripts
- `check_meta_skill_indicators()` - Was duplicated in 2 scripts
- Plus many more utility functions

### Benefits Achieved

1. **Single Source of Truth**: All utility functions in one place
2. **Easier Maintenance**: Fix bugs once, benefit everywhere
3. **Consistent Behavior**: Same logic across all scripts
4. **Better Testing**: Test utilities once, trust everywhere
5. **Type Safety**: Centralized type hints improve IDE support

## Best Practices

### For Script Authors

1. **Install the package**: Run `uv pip install -e .` in development
2. **Use proper imports**: `from abstract.config import ...`
3. **Document dependencies**: List any new dependencies in pyproject.toml
4. **Type hints**: Use type hints for better IDE support

### For Package Maintainers

1. **Keep modules focused**: Each module has single responsibility
2. **Document public APIs**: All exported functions/classes need docstrings
3. **Maintain backwards compatibility**: Don't break existing scripts
4. **Test thoroughly**: Test both installed and development modes

## Testing

Tests should import from the installed package:

```python
# tests/test_config.py
from abstract.config import AbstractConfig

def test_config_loading():
    config = AbstractConfig.from_yaml("config/abstract_config.yaml")
    assert config is not None
```

Run tests with:
```bash
# Install package first
uv pip install -e ".[dev]"

# Run tests
pytest tests/
```

## References

- [PEP 517 - Build System](https://peps.python.org/pep-0517/)
- [PEP 518 - Build Dependencies](https://peps.python.org/pep-0518/)
- [PEP 561 - Type Hints](https://peps.python.org/pep-0561/)
- [Python Packaging Guide - src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
