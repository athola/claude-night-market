---
name: hooks-eval
description: Comprehensive evaluation framework for analyzing all hooks in a plugin with security scanning, performance analysis, and compliance checking
usage: /hooks-eval [plugin-path] [options]
---

# Hooks-Eval

Comprehensive evaluation framework for analyzing all hooks within a plugin (or across project/global scopes) with advanced security scanning, performance benchmarking, and compliance validation. Built on the same principles as skills-eval but specifically tailored for Claude Code hook architecture.

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
/hooks-eval --comprehensive --format detailed

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
- `--comprehensive`: Full analysis across all dimensions (default)

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

## Evaluation Framework

### Scoring System (100 points total)

**Security Analysis (30 points)**
- Critical vulnerabilities: -15 points each
- High-risk issues: -8 points each
- Medium-risk issues: -4 points each
- Low-risk issues: -1 point each

**Performance Analysis (25 points)**
- Execution time efficiency: 10 points
- Memory usage optimization: 8 points
- I/O operation efficiency: 4 points
- Resource cleanup: 3 points

**Compliance Analysis (20 points)**
- Structure compliance: 8 points
- Documentation completeness: 6 points
- Error handling: 4 points
- Best practices: 2 points

**Reliability Analysis (15 points)**
- Error handling robustness: 6 points
- Timeout management: 4 points
- Idempotency: 3 points
- Graceful degradation: 2 points

**Maintainability (10 points)**
- Code structure: 4 points
- Documentation clarity: 3 points
- Modularity: 2 points
- Test coverage: 1 point

### Quality Levels

- **91-100**: Excellent - Production-ready, follows all best practices
- **76-90**: Good - Minor improvements suggested
- **51-75**: Acceptable - Some issues requiring attention
- **26-50**: Poor - Significant issues need addressing
- **0-25**: Critical - Major security or reliability issues

## Output Examples

### Basic Evaluation
```bash
/hooks-eval
# === Hooks Evaluation Report ===
# Plugin: abstract (v1.0.0)
# Scope: Plugin hooks only
# Total hooks found: 5 (4 JSON, 1 Python script)
#
# === Overall Scores ===
# Security Score: 82/100 (Good)
# Performance Score: 78/100 (Good)
# Compliance Score: 85/100 (Good)
# Reliability Score: 88/100 (Good)
# Maintainability Score: 75/100 (Good)
# Overall Score: 81/100 (Good)
#
# === Critical Issues ===
# [CRITICAL] hooks/gemini/bridge.on_tool_start:23 - eval() with user input
#
# === Recommendations ===
# 1. Replace eval() with JSON parsing for security
# 2. Add timeout configuration to JSON hooks
# 3. Implement input validation for all script hooks
```

### Security-Only Evaluation
```bash
/hooks-eval --security-only --format sarif
# {
#   "version": "2.1.0",
#   "runs": [{
#     "tool": {"name": "hooks-eval"},
#     "results": [
#       {
#         "ruleId": "command-injection",
#         "level": "error",
#         "message": {"text": "Use of eval() with user input"},
#         "locations": [{
#           "physicalLocation": {
#             "artifactLocation": {"uri": "hooks/gemini/bridge.on_tool_start"},
#             "region": {"startLine": 23}
#           }
#         }]
#       }
#     ]
#   }]
# }
```

### Performance Benchmarking
```bash
/hooks-eval --performance-baseline --format detailed
# === Performance Analysis ===
# Hook Performance Benchmarks:
#
# hooks/pre-skill-load.json:
#   Estimated execution: 15ms (threshold: 100ms) ✓
#   Memory usage: 2MB (threshold: 50MB) ✓
#   I/O operations: 0 (minimal) ✓
#
# hooks/post-evaluation.json:
#   Estimated execution: 25ms (threshold: 200ms) ✓
#   Memory usage: 5MB (threshold: 100MB) ✓
#   Complex logic: Medium complexity ⚠️
#
# hooks/gemini/bridge.on_tool_start:
#   Estimated execution: 180ms (threshold: 100ms) ❌
#   Memory usage: 45MB (threshold: 50MB) ⚠️
#   File I/O: Multiple stat() calls ⚠️
#
# === Performance Recommendations ===
# 1. Optimize gemini bridge hook for better performance
# 2. Cache file statistics to reduce system calls
# 3. Consider async processing for large file operations
```

## Integration with Other Tools

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Evaluate Hooks
  run: |
    /hooks-eval --quality-gate --format json --output hooks-report.json
    if [ $? -ne 0 ]; then
      echo "Hooks evaluation failed - check hooks-report.json"
      exit 1
    fi
```

### Development Workflow
```bash
# During development
/analyze-hook hooks/new-hook.py --security-scan
/analyze-hook hooks/new-hook.py --performance-check
/hooks-eval --compliance-check

# Before release
/hooks-eval --comprehensive --quality-gate
/hooks-eval --all-scopes --format detailed > release-report.md
```

### Integration with Skills-Eval
```bash
# Complete plugin evaluation
/skills-eval --comprehensive
/hooks-eval --comprehensive
/validate-plugin .
```

## Implementation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/hooks_eval/hooks_auditor.py \
  --plugin-path "${1:-.}" \
  --scope "${2:-plugin}" \
  --analysis-type "${3:-comprehensive}" \
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

- `/analyze-hook` - Individual hook analysis
- `/validate-plugin` - Complete plugin structure validation
- `/skills-eval` - Skill quality evaluation framework

## Related Skills

For detailed guidance on hook types, SDK integration, and evaluation criteria:

- **hooks-eval skill** (`skills/hooks-eval/SKILL.md`) - Comprehensive hook evaluation framework
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
