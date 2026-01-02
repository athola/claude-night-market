# spec-kit

Spec Driven Development toolkit for Claude Code.

## Overview

Spec-kit implements the Speckit workflow: write a specification, generate a plan, break it into tasks, and implement them with tracking.

## Installation

This plugin is part of the [claude-night-market](https://github.com/athola/claude-night-market) collection.

```bash
# Add to your Claude Code plugins
claude plugins add spec-kit
```

**Requires**: `abstract` plugin for meta-skills infrastructure.

## Workflow Commands

### Core Speckit Commands

| Command | Description |
|---------|-------------|
| `/speckit-startup` | Bootstrap speckit workflow at session start |
| `/speckit-specify` | Create feature specifications from natural language |
| `/speckit-clarify` | Refine specifications with targeted questions |
| `/speckit-plan` | Execute implementation planning workflow |
| `/speckit-tasks` | Generate dependency-ordered tasks |
| `/speckit-implement` | Execute implementation tasks |
| `/speckit-analyze` | Cross-artifact consistency analysis |
| `/speckit-checklist` | Generate requirement quality checklists |
| `/speckit-constitution` | Manage project principles |

## Skills

### speckit-orchestrator

Workflow coordinator that validates skill loading, progress tracking, and consistency throughout the speckit command lifecycle.

### spec-writing

Guides creation of clear, complete, and testable specifications from natural language descriptions.

### task-planning

Transforms specifications and implementation plans into actionable, dependency-ordered tasks.

## Agents

### spec-analyzer

Analyzes specification artifacts for consistency, coverage, and quality issues.

### task-generator

Generates dependency-ordered implementation tasks from specifications and plans.

### implementation-executor

Executes implementation tasks systematically following the task plan.

## Typical Workflow

```
/speckit-startup           # Initialize session
/speckit-specify <feature> # Create specification
/speckit-clarify           # Refine requirements
/speckit-plan              # Generate implementation plan
/speckit-tasks             # Create task breakdown
/speckit-analyze           # Verify consistency
/speckit-implement         # Execute tasks
/speckit-checklist         # Final quality check
```

## Dependencies

- **abstract**: Provides meta-skills infrastructure.

## License

MIT
