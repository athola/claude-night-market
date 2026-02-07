---
name: skills-eval
description: Evaluate skills for quality, compliance, and improvements
usage: /skills-eval [skill-name]
---

# Skills Evaluation Command

## When To Use

Use this command when you need to:
- Auditing skill ecosystem quality
- Discovering implementation patterns
- Planning skill improvements
- Checking compliance with standards
- Generating improvement recommendations

## When NOT To Use

Avoid this command if:
- Evaluating hooks - use /hooks-eval instead
- Validating plugin structure - use /validate-plugin instead
- Creating new skills - use /create-skill instead

## Usage

Evaluates all Claude Skills in your ~/.claude/ ecosystem for quality, compliance, and potential improvements.

### Basic Usage
```
/prompt:skills-eval
```
Evaluates all discovered skills and generates improvement recommendations.

### Specific Skill Evaluation
```
/prompt:skills-eval <skill-name>
```
Evaluates a specific skill (e.g., `/prompt:skills-eval modular-skills`).

## What It Does

1. **Discovers Skills**: Finds all SKILL.md files in ~/.claude/ hierarchy
2. **Quality Analysis**: Evaluates structure, content, token efficiency, and activation reliability
3. **Compliance Checking**: Validates against Claude Skills standards and security guidelines
4. **Improvement Generation**: Provides specific improvement suggestions
5. **Prioritization**: Ranks improvements by impact and effort

## Evaluation Criteria

- **Structure Compliance**: YAML frontmatter, progressive disclosure, organization
- **Content Quality**: Clarity, completeness, practical value
- **Token Efficiency**: Content density, loading optimization
- **Activation Reliability**: Naming, tags, trigger patterns
- **Tool Integration**: Executable components, automation value
- **Security Compliance**: Safe practices, dependency validation

## Output Format

For each skill, provides:
- Overall quality score (0-100)
- Detailed breakdown by category
- Specific improvement recommendations
- Priority ranking and estimated effort
- Implementation roadmap

## Examples

```
/prompt:skills-eval
# Evaluates all 50+ skills, identifies 5 critical issues and 20+ improvements

/prompt:skills-eval modular-skills
# Deep dive on specific skill with detailed improvement plan
```

## Integration with Tools

This command uses the skills-eval skill's specialized tools:
- `skills-auditor`: Quality analysis
- `improvement-suggester`: Actionable recommendation generation
- `compliance-checker`: Standards and security validation

This evaluation validates an efficient skills ecosystem that follows Claude Skills best practices.
