---
name: rules-eval
description: Evaluate Claude Code rules in .claude/rules/ directories for quality
usage: /rules-eval [rules-path] [options]
---

# Rules-Eval

Evaluate and validate Claude Code rules in `.claude/rules/` directories. Checks YAML frontmatter, glob patterns, content quality, and directory organization.

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

## Scoring System (100 points)

| Category | Points | Focus |
|----------|--------|-------|
| Frontmatter Validity | 25 | YAML syntax, correct fields, no Cursor-specific fields |
| Glob Pattern Quality | 20 | Syntax, specificity, quoting |
| Content Quality | 25 | Actionable, concise, focused |
| Organization | 15 | Naming conventions, directory structure |
| Token Efficiency | 15 | Rule size, redundancy |

### Quality Levels

- **91-100**: Excellent - Production-ready
- **76-90**: Good - Minor improvements possible
- **51-75**: Basic - Needs optimization
- **26-50**: Below Standards - Significant issues
- **0-25**: Critical - Invalid or broken rules

## Key Validations

### Frontmatter
- Valid YAML syntax
- No Cursor-specific fields (`globs`, `alwaysApply`)
- `paths` is a list of quoted glob patterns
- Only known fields (`paths`, `description`)

### Glob Patterns
- Valid glob syntax
- Not overly broad (`**/*`)
- Properly quoted special characters

### Content
- Actionable guidance (not just descriptions)
- Concise (< 500 tokens per file)
- Single focused topic per file

### Organization
- Descriptive kebab-case filenames
- No generic names (`rules1.md`, `misc.md`)
- Subdirectories for large rule sets
- No broken symlinks

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
