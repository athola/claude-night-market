---
name: hooks-eval
description: Evaluate all hooks in a plugin for quality and compliance
usage: /hooks-eval [plugin-path] [options]
---

# Hooks-Eval

Detailed evaluation framework for analyzing all hooks within a plugin (or across project/global scopes) with advanced security scanning, performance benchmarking, and compliance validation. Built on the same principles as skills-eval but specifically tailored for Claude Code hook architecture.

Invoke `Skill(abstract:hooks-eval)`, which carries the evaluation criteria,
the SDK hook types and the integration points.

## When To Use

Use this command when you need to:
- Evaluating all hooks in a plugin comprehensively
- Comparing multiple hooks
- Validating quality gates across hook portfolio
- Security scanning entire plugin's hooks

## When NOT To Use

Avoid this command if:
- Validating specific hook - use /validate-hook instead
- Creating new hooks - use /create-hook instead

## Usage

```bash
# Evaluate all hooks in current plugin
/hooks-eval

# Evaluate specific plugin directory
/hooks-eval /path/to/plugin

# Security-focused evaluation
/hooks-eval --security-only

# Performance benchmarking
/hooks-eval --performance-baseline

# Compliance checking
/hooks-eval --compliance-report

# Generate detailed report
/hooks-eval --detailed --format detailed

# Cross-scope evaluation (plugin → project → global)
/hooks-eval --all-scopes

# CI/CD integration
/hooks-eval --quality-gate --format json --output results.json
```

## Options

### Scope Selection
- `--plugin <path>`: Specific plugin directory (default: current plugin)
- `--scope <type>`: Evaluate specific scope (plugin, project, global)
- `--all-scopes`: Evaluate all scopes in priority order
- `--include-external`: Include hooks from external dependencies

### Analysis Focus
- `--security-only`: Focus exclusively on security vulnerabilities
- `--performance-check`: Analyze execution performance and resource usage
- `--compliance-check`: Validate against hook development standards
- `--detailed`: Full analysis across all dimensions (default)

### Output Control
- `--format <type>`: Output format (summary, detailed, json, sarif, dashboard)
- `--output <file>`: Write results to file
- `--verbose`: Show detailed analysis and recommendations
- `--quiet`: Minimal output, exit codes only
- `--severity <level>`: Minimum severity level to report

### Quality Gates
- `--quality-gate`: Enable quality gate checking with thresholds
- `--fail-on <level>`: Fail exit on specific severity level
- `--baseline <file>`: Compare against previous evaluation baseline

## Implementation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hooks_eval/hooks_auditor.py \
  --plugin-path "${1:-.}" \
  --scope "${2:-plugin}" \
  --analysis-type "${3:-detailed}" \
  --format "${4:-summary}"
```

## Quality Gates

Default quality gate thresholds can be customized:

```yaml
quality_gates:
  security_score: ">= 80"
  performance_score: ">= 70"
  compliance_score: ">= 85"
  reliability_score: ">= 85"
  overall_score: ">= 75"
  max_critical_issues: 0
  max_high_issues: 2
```

## Exit Codes

- `0`: Success - all quality gates passed
- `1`: Warnings - quality gates passed but issues found
- `2`: Quality gate failure - scores below thresholds
- `3`: Critical issues - security vulnerabilities found
- `4`: Execution error - analysis failed to complete

## Related Commands

- `/validate-hook` - Individual hook validation (security, performance, compliance)
- `/validate-plugin` - Complete plugin structure validation
- `/skills-eval` - Skill quality evaluation framework

## Related Skills

For detailed guidance on hook types, SDK integration, and evaluation criteria:

- **hooks-eval skill** (`skills/hooks-eval/SKILL.md`) - detailed hook evaluation framework
  - `modules/sdk-hook-types.md` - Python SDK hook types, callbacks, matchers
  - `modules/evaluation-criteria.md` - Detailed scoring rubric and quality gates
- **hook-scope-guide** - Decision framework for hook placement (plugin/project/global)

## Configuration

Create `.hooks-eval.yaml` in plugin root for custom configuration:

```yaml
hooks_eval:
  security_thresholds:
    critical_score: 80
    high_score: 70

  performance_thresholds:
    pre_tool_use_max_ms: 100
    post_tool_use_max_ms: 200
    max_memory_mb: 50

  compliance_requirements:
    require_documentation: true
    require_error_handling: true
    require_timeout_config: true

  custom_rules:
    - name: "no-hardcoded-secrets"
      pattern: "password|secret|token"
      severity: "high"
    - name: "require-shebang"
      pattern: "^#!"
      file_types: [".sh", ".py"]
      severity: "medium"
```
