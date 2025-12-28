# Quality Gates

Configuration for quality validation in the Claude Night Market project.

## Pre-commit Hooks

The project uses pre-commit hooks defined in `.pre-commit-config.yaml`:

### Plugin Validation
```yaml
validate-abstract-skills     # Validates skill frontmatter and structure
validate-imbue-skills         # Validates Imbue skill patterns
validate-*-plugin             # Structure validation per plugin
check-context-optimization    # Context window optimization checks
```

Scripts live in `plugins/abstract/scripts/`:
- `abstract_validator.py` - Skill validation
- `validate-plugin.py` - Plugin structure validation
- `context_optimizer.py` - Context optimization analysis

### Standard Checks
- `trailing-whitespace`, `end-of-file-fixer` - Formatting
- `check-yaml`, `check-toml`, `check-json` - Config validation
- `bandit` - Security scanning
- `ruff`, `ruff-format` - Linting and formatting
- `mypy` - Type checking

## Configuration Files

### Quality Gates (`.claude/quality_gates.json`)

Defines thresholds across four dimensions:

| Dimension | Key Settings |
|-----------|--------------|
| Performance | `max_file_size_kb: 20`, `max_tokens_per_file: 5000`, `max_complexity_score: 12` |
| Security | `block_hardcoded_secrets: true`, `block_insecure_functions: true` |
| Maintainability | `max_technical_debt_ratio: 0.3`, `max_nesting_depth: 5` |
| Compliance | `require_plugin_structure: true`, `require_proper_metadata: true` |

### Context Governance (`.claude/context_governance.json`)

Enforces context optimization patterns:

| Setting | Value |
|---------|-------|
| `require_progressive_disclosure` | `true` |
| `require_modular_structure` | `true` |
| `optimization_patterns.progressive_disclosure` | `["overview", "basic", "advanced", "reference"]` |
| `optimization_patterns.modular_structure` | `["modules/", "examples/", "scripts/"]` |

## Running Validation

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run specific hook
pre-commit run validate-abstract-skills --all-files

# Run context optimization check
python3 plugins/abstract/scripts/context_optimizer.py stats plugins/
```

## See Also

- [Plugin Development Guide](./plugin-development-guide.md)
- [Pre-commit configuration](../.pre-commit-config.yaml)
