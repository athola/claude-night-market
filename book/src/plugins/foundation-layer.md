# Foundation Layer

The foundation layer provides core workflow methodologies that other plugins build upon.

## Purpose

Foundation plugins establish:

- **Analysis Patterns**: How to approach investigation and review tasks
- **Workspace Operations**: Git and file system interactions
- **Infrastructure Utilities**: Reusable patterns for building plugins

## Plugins

| Plugin | Description | Key Use Case |
|--------|-------------|--------------|
| [imbue](imbue.md) | Workflow methodologies | Analysis, evidence gathering |
| [sanctum](sanctum.md) | Git operations | Commits, PRs, documentation |
| [leyline](leyline.md) | Building blocks | Error handling, authentication |

## Dependency Flow

```
imbue (standalone)
  |
sanctum --> imbue
  |
leyline (standalone)
```

- **imbue**: No dependencies, purely methodology
- **sanctum**: Uses imbue for review patterns
- **leyline**: No dependencies, infrastructure patterns

## When to Use

### imbue
Use when you need to:
- Structure a detailed review
- Analyze changes systematically
- Capture evidence for decisions
- Prevent overengineering (scope-guard)

### sanctum
Use when you need to:
- Understand repository state
- Generate commit messages
- Prepare pull requests
- Update documentation

### leyline
Use when you need to:
- Implement error handling patterns
- Add authentication flows
- Build plugin infrastructure
- Standardize testing approaches

## Key Workflows

### Pre-Commit Flow
```bash
Skill(sanctum:git-workspace-review)
Skill(sanctum:commit-messages)
```

### Review Flow
```bash
Skill(imbue:review-core)
Skill(imbue:evidence-logging)
Skill(imbue:structured-output)
```

### PR Preparation
```bash
Skill(sanctum:git-workspace-review)
Skill(sanctum:pr-prep)
```

## Installation

```bash
# Minimal foundation
/plugin install imbue@claude-night-market

# Full foundation
/plugin install imbue@claude-night-market
/plugin install sanctum@claude-night-market
/plugin install leyline@claude-night-market
```
