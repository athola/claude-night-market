---
name: skills-eval
description: Audit skill quality, frontmatter compliance, token efficiency, and activation reliability. Recommends improvements.
usage: /skills-eval [skill-name]
---

# Skills Evaluation Command

Invoke `Skill(abstract:skills-eval)`, which carries the evaluation criteria,
the workflow and the output format across its modules.

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
