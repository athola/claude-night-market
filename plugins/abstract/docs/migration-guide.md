# Migration Guide: Tools to Scripts

This document describes the migration from distributed tools to centralized utility scripts.

## Overview

The tools have been moved from individual skill directories to a centralized `scripts/` directory to improve maintainability and reduce code duplication.

## Migrated Tools

### From `skills/modular-skills/tools/`
- `module-validator` → `scripts/skill_analyzer.py`
- `skill-analyzer` → `scripts/skill_analyzer.py`
- `token-estimator` → `scripts/token_estimator.py`

### From `skills/skills-eval/tools/`
- `compliance-checker` → `scripts/abstract_validator.py`
- `improvement-suggester` → Integrated into `abstract.skills_eval` module
- `skills-auditor` → Integrated into `abstract.skills_eval` module

## Usage Changes

### Before
```bash
# Run tool from skill directory
cd skills/modular-skills
./tools/module-validator my-skill

# Or from repo root
./skills/modular-skills/tools/module-validator my-skill
```

### After
```bash
# Run from repo root
python scripts/skill_analyzer.py --validate my-skill

# Or use the CLI command
abstract-skills validate my-skill
```

## Updated Configuration

### pyproject.toml
```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
no_implicit_optional = true
explicit_package_bases = true
mypy_path = ["src"]  # Added for proper module resolution
exclude = ['^\.venv', '^\.uv-cache', '^fix_.*\.py$']
```

### Pre-commit hooks
```yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.11.0
  hooks:
    - id: mypy
      args: [src/]
      additional_dependencies:
        - types-PyYAML
      exclude: ^\.venv/|^\.uv-cache/|^fix_.*\.py$
```

## Benefits

1. **Centralized Management**: All utilities are in one place, easier to maintain
2. **Reduced Duplication**: Common functionality is shared across scripts
3. **Better Testing**: Centralized scripts can be properly tested
4. **CLI Integration**: All utilities available through `abstract-skills` command
5. **Type Safety**: Improved mypy configuration for better type checking

## Breaking Changes

- Tool paths have changed - update any scripts or documentation that reference the old paths
- Some command-line arguments may have changed - check `--help` for updated usage
- Direct execution of tools from skill directories is no longer supported

## Migration Checklist

- [ ] Update any scripts that reference old tool paths
- [ ] Update documentation to use new tool locations
- [ ] Update CI/CD pipelines that use the tools
- [ ] Install pre-commit hooks for mypy checking
- [ ] Run tests to verify migration is complete