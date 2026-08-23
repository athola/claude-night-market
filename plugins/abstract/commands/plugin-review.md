---
name: plugin-review
description: "Tiered plugin quality review: branch (quick gates),
  pr (quality scoring), release (full ecosystem audit).
  Detects affected plugins from git diff and reviews
  related plugins for side effects."
usage: "/plugin-review [plugin-name...] [--tier branch|pr|release]
  [--focus skills|hooks|bloat|tokens|all]
  [--format summary|detailed|json] [--plan]"
---

# Plugin Review

Tiered plugin quality review: branch (quick gates),
pr (quality scoring), release (full ecosystem audit).
Detects affected plugins from git diff and reviews
related plugins for side effects.

Runs `Skill(abstract:plugin-review)`, which with its four modules carries
the tier definitions, the scope detection, the verdict and the output
format. The CI wiring and the script invocation below belong to the
command.

## When To Use

Use this command when you need to:
- Assessing overall plugin/skill architecture health
- Pre-release validation of plugin quality
- Quarterly maintenance audits
- New contributor onboarding to understand plugin structure
- Identifying improvement priorities across skills/commands/hooks
- Validating plugin meets quality standards

## When NOT To Use

Avoid this command if:
- Single skill analysis - use /analyze-skill
- Single hook analysis - use /analyze-hook
- Creating new skills - use /create-skill
- Token estimation only - use /estimate-tokens

## Usage

```bash
# Review current plugin (default: all checks)
/plugin-review

# Review specific plugin
/plugin-review plugins/abstract

# Focus on specific aspect
/plugin-review --focus skills
/plugin-review --focus hooks
/plugin-review --focus bloat
/plugin-review --focus tokens

# Output format
/plugin-review --format summary   # High-level scores (default)
/plugin-review --format detailed  # Full findings and recommendations
/plugin-review --format json      # Machine-readable for CI

# CI/CD quality gate mode
/plugin-review --quality-gate --fail-on warning
```

## Quality Levels

| Score | Level | Meaning |
|-------|-------|---------|
| 91-100 | EXCELLENT | Production-ready, best practices |
| 76-90 | GOOD | Minor improvements suggested |
| 51-75 | OK | Issues requiring attention |
| 26-50 | POOR | Significant issues |
| 0-25 | CRITICAL | Major problems blocking release |

## CI/CD Integration

```yaml
# GitHub Actions example
- name: Plugin Quality Gate
  run: |
    /plugin-review --quality-gate --format json --output report.json
    EXIT_CODE=$?
    if [ $EXIT_CODE -ge 2 ]; then
      echo "Quality gate failed (exit code $EXIT_CODE)"
      exit 1
    elif [ $EXIT_CODE -eq 1 ]; then
      echo "Quality gate passed with warnings"
    fi
```

Exit codes:
- `0`: All quality gates passed
- `1`: Warnings present but gates passed (non-blocking)
- `2`: Quality gate failures (blocking)
- `3`: Critical issues found (blocking)

## Implementation

This command orchestrates multiple evaluation tools:

1. **Plugin structure validation**: `validate_plugin.py`
2. **Skills evaluation**: `skill_analyzer.py --scan-all`
3. **Token analysis**: `context_optimizer.py report`
4. **Hooks evaluation**: `Skill(abstract:hooks-eval)` (if hooks exist)
5. **Bloat detection**: Uses conserve:bloat-detector patterns
6. **Aggregate results**: Combine scores and generate report

## Related Commands

- `/validate-plugin` - Structure validation only
- `/skills-eval` - Skills quality evaluation only
- `/hooks-eval` - Hooks evaluation only
- `/context-report` - Token analysis only
- `/bloat-scan` - Bloat detection only
- `/analyze-skill` - Single skill deep dive
- `/analyze-hook` - Single hook deep dive

## Related Skills

- `abstract:skills-eval` - Skill quality framework
- `abstract:modular-skills` - Architecture patterns
- `abstract:hooks-eval` - Hook evaluation framework
- `conserve:bloat-detector` - Bloat detection
- `conserve:token-conservation` - Token optimization
