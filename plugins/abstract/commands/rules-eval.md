---
name: rules-eval
description: Evaluate Claude Code rules in .claude/rules/ directories for quality
usage: /rules-eval [rules-path] [options]
---

# Rules-Eval

Evaluate and validate Claude Code rules in `.claude/rules/` directories. Checks YAML frontmatter, glob patterns, content quality, and directory organization.

Runs `Skill(abstract:rules-eval)`, which with its four modules carries the
scoring, the frontmatter and glob validations and the organization
patterns. The script invocation below belongs to the command.

## When To Use

Use this command when you need to:
- Validate rule files before deployment
- Audit frontmatter for YAML errors or Cursor-specific fields
- Check glob patterns for syntax and specificity issues
- Assess overall rules organization and naming

## When NOT To Use

Avoid this command if:
- Evaluating skills - use /skills-eval instead
- Evaluating hooks - use /hooks-eval instead
- Validating full plugin structure - use /validate-plugin instead

## Usage

```bash
# Evaluate rules in current project
/rules-eval

# Evaluate specific directory
/rules-eval .claude/rules/

# Detailed analysis with per-file breakdown
/rules-eval --detailed

# Evaluate a plugin's rules
/rules-eval plugins/conserve/.claude/rules/
```

## Implementation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/rules_validator.py \
  "${1:-.claude/rules}" \
  ${2:+--detailed}
```

## Related Commands

- `/skills-eval` - Skill quality evaluation
- `/hooks-eval` - Hook quality evaluation
- `/validate-plugin` - Complete plugin structure validation

## Related Skills

- **rules-eval skill** (`skills/rules-eval/SKILL.md`) - Detailed evaluation framework
  - `modules/frontmatter-validation.md` - YAML/frontmatter checks
  - `modules/glob-pattern-analysis.md` - Glob pattern validation
  - `modules/content-quality-metrics.md` - Content quality assessment
  - `modules/organization-patterns.md` - Directory organization
