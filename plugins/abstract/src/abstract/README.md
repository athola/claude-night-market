# Abstract Python Package

Centralized Python package for shared modules used across the Abstract plugin.

## Structure

```
src/abstract/
├── __init__.py      # Package initialization
├── config.py        # Configuration management
├── errors.py        # Error handling utilities
├── utils.py         # Common utilities for skill processing
├── py.typed         # Type hints marker (PEP 561)
└── README.md        # This file
```

## Installation

```bash
# Install in editable mode with development dependencies
uv pip install -e ".[dev]"

# Or just the package
uv pip install -e .
```

## Module Reference

### `abstract.config`
Configuration management for the Abstract plugin.

**Classes**:
- `AbstractConfig`: Main configuration with skill validation, tool settings, and context optimizer config
- `SkillValidationConfig`: Validation rules for skill frontmatter, meta-indicators, and file size limits
- `ToolConfig`: Tool-specific settings
- `ContextOptimizerConfig`: Context window optimization thresholds

**Usage**:
```python
from abstract.config import AbstractConfig

# Load from YAML with automatic fallback to defaults
config = AbstractConfig.from_yaml("config/abstract_config.yaml")

# Access validation rules
max_size = config.skill_validation.MAX_SKILL_FILE_SIZE
required_fields = config.skill_validation.REQUIRED_FRONTMATTER_FIELDS
```

### `abstract.errors`
Consistent error handling across all tools.

**Classes**:
- `ErrorHandler`: Centralized error management and logging
- `ErrorSeverity`: Error severity levels enum
- `ToolError`: Structured error information dataclass

**Usage**:
```python
from abstract.errors import ErrorHandler, ErrorSeverity, ToolError

errors = ErrorHandler("my-script")
errors.handle_error(
    ToolError(
        severity=ErrorSeverity.HIGH,
        error_code="VALIDATION_FAILED",
        message="Skill validation failed",
        suggestion="Check frontmatter format"
    )
)
```

### `abstract.utils`
Common utilities for skill file processing. All scripts use these functions to eliminate code duplication.

**Project Navigation**:
- `find_project_root(start_path)`: Find project root by locating config/ or pyproject.toml
- `load_config_with_defaults(project_root)`: Load configuration with automatic defaults

**Frontmatter Processing**:
- `extract_frontmatter(content)`: Extract frontmatter and body from skill content
- `parse_frontmatter_fields(frontmatter)`: Parse YAML frontmatter into dictionary
- `parse_yaml_frontmatter(content)`: Full YAML parsing of frontmatter
- `validate_skill_frontmatter(content, config)`: Validate frontmatter fields against config

**Skill File Operations**:
- `find_skill_files(directory)`: Find all SKILL.md files recursively
- `load_skill_file(skill_path)`: Load skill file and parse frontmatter
- `get_skill_name(frontmatter, skill_path)`: Get skill name from frontmatter or filename

**Analysis Functions**:
- `estimate_tokens(text)`: Estimate token count for text (~1.3 tokens per character)
- `check_meta_skill_indicators(content, config, skill_name)`: Check for meta-skill indicators
- `format_score(score, max_score)`: Format score for display

**Usage Example**:
```python
from abstract.utils import (
    find_skill_files,
    load_skill_file,
    estimate_tokens,
    parse_yaml_frontmatter,
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

## Complete Usage Example

```python
#!/usr/bin/env python3
"""Example script using the abstract package."""

import sys
from pathlib import Path

# Import with fallback for non-installed package
try:
    from abstract.config import AbstractConfig
    from abstract.utils import find_skill_files, load_skill_file, estimate_tokens
    from abstract.errors import ErrorHandler, ErrorSeverity, ToolError
except ImportError:
    src_path = Path(__file__).parent.parent / "src"
    if src_path.exists():
        sys.path.insert(0, str(src_path))
        from abstract.config import AbstractConfig
        from abstract.utils import find_skill_files, load_skill_file, estimate_tokens
        from abstract.errors import ErrorHandler, ErrorSeverity, ToolError
    else:
        print("ERROR: Cannot import abstract package", file=sys.stderr)
        sys.exit(1)

def main():
    # Initialize error handler
    errors = ErrorHandler("my-script")

    # Load configuration
    config = AbstractConfig.from_yaml("config/abstract_config.yaml")

    # Find and analyze skills
    skill_files = find_skill_files(Path("skills/"))

    for skill_path in skill_files:
        try:
            content, frontmatter = load_skill_file(skill_path)
            tokens = estimate_tokens(content)
            print(f"{skill_path}: {tokens} tokens")
        except Exception as e:
            errors.handle_error(
                ToolError(
                    severity=ErrorSeverity.MEDIUM,
                    error_code="LOAD_FAILED",
                    message=f"Failed to load {skill_path}",
                    details=str(e)
                )
            )

if __name__ == "__main__":
    main()
```

## Development Practices

The package follows Python best practices:
- **PEP 517/518**: Standard src/ layout for proper package structure
- **PEP 561**: Type hints with py.typed marker for full mypy support
- **Centralized utilities**: All common functions in utils.py to eliminate duplication
- **Fallback imports**: Scripts work with or without package installation
- **Testing**: Compatible with pytest (tests in tests/ directory)

## Integration with Claude Code

The package structure is compatible with Claude Code plugin layout:
- Plugin files in expected locations (skills/, scripts/, etc.)
- Shared code accessible via abstract package
- No conflicts with Claude Code functionality
- YAML configs remain in config/ directory

## Scripts Using This Package

All Python scripts in this project use the abstract package:

**Main Scripts** (scripts/):
- `abstract_validator.py`: Validates meta-skill patterns
- `context_optimizer.py`: Analyzes context window usage

**Pre-commit Hooks** (.pre-commit/):
- `validate_abstract.py`: Pre-commit validation hook

**Nested Scripts** (skills/*/scripts/):
- `skills/skills-eval/scripts/skill_utils.py`: Imports and extends abstract.utils

This eliminates ~449 lines of duplicate code across the project.
