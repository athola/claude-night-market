# spec-kit

Specification-driven development toolkit for Claude Code.

## Overview

Spec-kit provides a workflow for specification-driven development: writing a specification, generating an implementation plan, breaking it into tasks, and executing them with tracking.

## Installation

This plugin is part of the [claude-night-market](https://github.com/athola/claude-night-market) collection.

```bash
# Add to your Claude Code plugins
claude plugins add spec-kit
```

**Requires**: `abstract` plugin for infrastructure.

## Workflow Commands

### Core Commands

| Command | Description |
|---------|-------------|
| `/speckit-startup` | Initialize the speckit workflow for the session. |
| `/speckit-specify` | Create feature specifications from natural language. |
| `/speckit-clarify` | Refine specifications with targeted questions. |
| `/speckit-plan` | Execute the implementation planning workflow. |
| `/speckit-tasks` | Generate dependency-ordered tasks. |
| `/speckit-implement` | Execute implementation tasks. |
| `/speckit-analyze` | Analyze consistency across artifacts. |
| `/speckit-checklist` | Generate quality checklists for requirements. |
| `/speckit-constitution` | Manage project principles. |

## Skills

### speckit-orchestrator

Workflow coordinator that validates skill loading and maintains consistency throughout the command lifecycle.

### spec-writing

Guides the creation of testable specifications from natural language descriptions.

### task-planning

Transforms specifications and implementation plans into dependency-ordered tasks.

## Agents

### spec-analyzer

Analyzes artifacts for consistency, coverage, and quality.

### task-generator

Generates dependency-ordered implementation tasks.

### implementation-executor

Executes implementation tasks according to the task plan.

## Workflow Example

1. `/speckit-startup`: Initialize the session.
2. `/speckit-specify <feature>`: Create a specification.
3. `/speckit-clarify`: Refine requirements.
4. `/speckit-plan`: Generate an implementation plan.
5. `/speckit-tasks`: Create a task breakdown.
6. `/speckit-analyze`: Verify consistency.
7. `/speckit-implement`: Execute tasks.
8. `/speckit-checklist`: Run a final quality check.

## Dependencies

- **abstract**: Provides meta-skills infrastructure.

## License

MIT
