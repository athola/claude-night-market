---
name: plugin-review
description: Comprehensive plugin architecture review - skills, commands, hooks, agents, tokens, bloat
usage: /plugin-review [plugin-path] [--focus skills|hooks|bloat|tokens|all] [--format summary|detailed|json]
---

# Plugin Review

<identification>
triggers: skill review, plugin review, architecture review, plugin health, skill audit, comprehensive review, plugin quality, quality check, health check, skill portfolio

use_when:
- Assessing overall plugin/skill architecture health
- Pre-release validation of plugin quality
- Quarterly maintenance audits
- New contributor onboarding to understand plugin structure
- Identifying improvement priorities across skills/commands/hooks
- Validating plugin meets quality standards

do_not_use_when:
- Single skill analysis - use /analyze-skill
- Single hook analysis - use /analyze-hook
- Creating new skills - use /create-skill
- Token estimation only - use /estimate-tokens
</identification>

Comprehensive review of plugin architecture quality. Orchestrates multiple evaluation tools to provide a unified health report covering skills, commands, hooks, agents, token efficiency, and bloat detection.

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

## What It Reviews

### 1. Plugin Structure Validation
Validates plugin.json, directory structure, naming conventions, and path references.

**Source**: `abstract:plugin-validator` agent, `validate_plugin.py` script

### 2. Skills Quality Assessment
Evaluates all skills against quality standards:
- Structure compliance (frontmatter, modular design)
- Content quality (clarity, completeness, examples)
- Token efficiency (progressive loading, context optimization)
- Trigger reliability (activation patterns, discoverability)
- Tool integration (executable components, error handling)

**Source**: `abstract:skills-eval` skill, `skill_analyzer.py` script

### 3. Commands Review
Checks all commands for:
- Proper frontmatter (name, description, usage)
- Argument documentation
- Implementation references
- Integration with skills/agents

**Source**: `validate_plugin.py` command validation

### 4. Hooks Evaluation
Comprehensive hook analysis:
- Security scanning (command injection, secrets exposure)
- Performance benchmarking (execution time, memory usage)
- Compliance validation (structure, error handling)
- Reliability assessment (timeout management, idempotency)

**Source**: `abstract:hooks-eval` skill, hooks evaluation scripts

### 5. Agent Assessment
Reviews all agents for:
- Model appropriateness (haiku vs sonnet vs opus)
- Escalation rules configuration
- Tool restrictions
- Description clarity and examples

**Source**: Plugin structure validation

### 6. Token Efficiency Analysis
Evaluates context window impact:
- Total token budget across all skills
- Large file identification (>5KB threshold)
- Progressive loading implementation
- Module structure optimization

**Source**: `context_optimizer.py`, `token_estimator.py` scripts

### 7. Bloat Detection
Identifies codebase bloat:
- Dead code and unused files
- Duplicate content across skills
- Overly verbose documentation
- Stale files (unchanged 6+ months)

**Source**: `conserve:bloat-detector` skill

## Output Format

### Summary Report (Default)

```
PLUGIN ARCHITECTURE REVIEW - abstract v1.2.4

HEALTH SCORES
-------------------------------------------------------------
Plugin Structure    ████████████████████░░  85/100 GOOD
Skills Quality      █████████████████████░  92/100 EXCELLENT
Commands            ████████████████████░░  88/100 GOOD
Hooks               ████████████████░░░░░░  75/100 OK
Token Efficiency    ████████████████████░░  82/100 GOOD
Bloat Score         ████████████████████░░  90/100 GOOD
-------------------------------------------------------------
OVERALL SCORE       ████████████████████░░  85/100 GOOD

INVENTORY
-------------------------------------------------------------
Skills:   18 (15 passing, 3 need attention)
Commands: 12 (all passing)
Hooks:     5 (4 passing, 1 security warning)
Agents:    4 (all passing)
Modules:  24 (23 optimal size, 1 needs split)

TOP PRIORITIES
-------------------------------------------------------------
[HIGH] hooks/gemini-bridge.py:23 - unsafe dynamic code execution
[MED]  skills/legacy-workflow/SKILL.md - 847 lines
[MED]  skills/old-patterns/ - unchanged 8 months
[LOW]  3 skills missing trigger phrases

RECOMMENDATION: Address HIGH priority security issue before release.
Run `/plugin-review --format detailed` for full analysis.
```

### Detailed Report

Includes:
- Per-skill breakdown with scores
- Per-hook security analysis
- Token budget breakdown by file
- Bloat candidates with remediation steps
- Compliance checklist

### JSON Report

```json
{
  "plugin": "abstract",
  "version": "1.2.4",
  "timestamp": "2025-01-10T12:34:56Z",
  "scores": {
    "structure": 85,
    "skills": 92,
    "commands": 88,
    "hooks": 75,
    "tokens": 82,
    "bloat": 90,
    "overall": 85
  },
  "findings": [...],
  "recommendations": [...]
}
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
    if [ $? -ne 0 ]; then
      echo "Quality gate failed"
      exit 1
    fi
```

Exit codes:
- `0`: All quality gates passed
- `1`: Warnings present but gates passed
- `2`: Quality gate failures
- `3`: Critical issues found

## Implementation

This command orchestrates multiple evaluation tools:

1. **Plugin structure validation**: `validate_plugin.py`
2. **Skills evaluation**: `skill_analyzer.py --scan-all`
3. **Token analysis**: `context_optimizer.py report`
4. **Hooks evaluation**: `hooks_auditor.py` (if hooks exist)
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
- `conserve:resource-management` - Token optimization

## Configuration

Create `.plugin-review.yaml` in plugin root for custom thresholds:

```yaml
plugin_review:
  quality_gates:
    structure_min: 80
    skills_min: 75
    hooks_min: 70
    tokens_max_total: 50000
    bloat_max_percentage: 15

  focus_areas:
    - skills
    - hooks
    - tokens

  exclude_patterns:
    - "*/legacy/*"
    - "*/deprecated/*"

  severity_overrides:
    missing_description: warning  # default: error
    large_file: info             # default: warning
```
