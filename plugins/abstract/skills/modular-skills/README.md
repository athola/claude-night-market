# Modular Skills Framework

Design patterns and implementation guidelines for reusable skill components.

## Core Principles

- **Single Responsibility**: One focused purpose per skill
- **Composable Design**: Skills are composable
- **Clear Interfaces**: Well-defined tool contracts
- **Token Efficiency**: Minimal context overhead

## Quick Start

```bash
# Analyze existing skills
skill-analyzer --scan

# Validate module structure
module_validator --check-all

# Estimate token usage
token-estimator --skill <path>
```

## Module Structure

```
skill-name/
├── SKILL.md           # Skill definition
├── modules/           # Optional sub-modules
└── scripts/           # Associated scripts
```

## Design Patterns

### Focused Modules
- Single purpose tools
- Minimal dependencies
- Clear success criteria

### Hierarchical Dependencies
- Parent-child relationships
- Dependency injection
- Interface contracts

### Cross-Cutting Concerns
- Shared utilities
- Common patterns
- Standard interfaces

## Validation Tools

- **module_validator**: Structure and quality checks
- **skill-analyzer**: detailed skill analysis
- **token-estimator**: Context usage optimization

## Best Practices

1. Keep skills under 1000 tokens
2. Use clear, descriptive names
3. Document tool contracts
4. Test thoroughly
5. Follow established patterns
