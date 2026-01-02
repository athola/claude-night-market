# abstract

Meta-skills infrastructure for the plugin ecosystem - skill authoring, hook development, and quality evaluation.

## Overview

The abstract plugin provides tools for building, evaluating, and maintaining Claude Code plugins. It's the toolkit for plugin developers.

## Installation

```bash
/plugin install abstract@claude-night-market
```

## Skills

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `skill-authoring` | TDD methodology for skill creation | Creating new skills with quality standards |
| `hook-authoring` | Security-first hook development | Building safe, effective hooks |
| `modular-skills` | Modular design patterns | Breaking large skills into modules |
| `skills-eval` | Skill quality assessment | Auditing skills for token efficiency |
| `hooks-eval` | Hook security scanning | Verifying hook safety |
| `escalation-governance` | Model escalation decisions | Deciding when to escalate models |
| `makefile-dogfooder` | Makefile analysis | Ensuring Makefile completeness |
| `shared-patterns` | Plugin development patterns | Reusable templates |

## Commands

| Command | Description |
|---------|-------------|
| `/validate-plugin [path]` | Check plugin structure against requirements |
| `/create-skill` | Scaffold new skill with best practices |
| `/create-command` | Scaffold new command |
| `/create-hook` | Scaffold hook with security-first design |
| `/analyze-hook` | Analyze hook for security and performance |
| `/analyze-skill` | Get modularization recommendations |
| `/bulletproof-skill` | Anti-rationalization workflow for hardening |
| `/context-report` | Context optimization report |
| `/estimate-tokens` | Estimate token usage for skills |
| `/hooks-eval` | detailed hook evaluation |
| `/make-dogfood` | Analyze and enhance Makefiles |
| `/skills-eval` | Run skill quality assessment |
| `/test-skill` | Skill testing with TDD methodology |
| `/validate-hook` | Validate hook compliance |

## Agents

| Agent | Description |
|-------|-------------|
| `meta-architect` | Designs plugin ecosystem architectures |
| `plugin-validator` | Validates plugin structure |
| `skill-auditor` | Audits skills for quality and compliance |

## Hooks

| Hook | Type | Description |
|------|------|-------------|
| `post-evaluation.json` | Config | Quality scoring and improvement tracking |
| `pre-skill-load.json` | Config | Pre-load validation for dependencies |

## Usage Examples

### Create a New Skill

```bash
/create-skill

# Claude will:
# 1. Use brainstorming for idea refinement
# 2. Apply TDD methodology
# 3. Generate skill scaffold
# 4. Create tests
```

### Evaluate Skill Quality

```bash
Skill(abstract:skills-eval)

# Scores skills on:
# - Token efficiency
# - Documentation quality
# - Trigger clarity
# - Modular structure
```

### Validate Plugin Structure

```bash
/validate-plugin /path/to/my-plugin

# Checks:
# - plugin.json structure
# - Required files present
# - Skill format compliance
# - Command syntax
```

## Best Practices

### Skill Design

1. **Single Responsibility**: Each skill does one thing well
2. **Clear Triggers**: Include "Use when..." in descriptions
3. **Token Efficiency**: Keep skills under 2000 tokens
4. **TodoWrite Integration**: Output actionable items

### Hook Security

1. **No Secrets**: Never log sensitive data
2. **Fail Safe**: Default to allowing operations
3. **Minimal Scope**: Request only needed permissions
4. **Audit Trail**: Log decisions for review

## Superpowers Integration

When superpowers is installed:

| Command | Enhancement |
|---------|-------------|
| `/create-skill` | Uses `brainstorming` for idea refinement |
| `/create-command` | Uses `brainstorming` for concept development |
| `/create-hook` | Uses `brainstorming` for security design |
| `/test-skill` | Uses `test-driven-development` for TDD cycles |

## Related Plugins

- **leyline**: Infrastructure patterns abstract builds on
- **imbue**: Review patterns for skill evaluation
