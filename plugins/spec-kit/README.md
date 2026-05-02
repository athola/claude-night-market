# spec-kit

Specification-driven development toolkit for Claude Code.

## Overview

Spec-kit provides a specification-driven workflow: writing a specification,
generating an implementation plan, breaking it into tasks,
and executing them with tracking.

## Installation

This plugin is part of the
[claude-night-market](https://github.com/athola/claude-night-market) collection.

```bash
# Add to your Claude Code plugins
claude plugins add spec-kit
```

**Requires**: `abstract` plugin for infrastructure.

## Workflow Commands

### Core Commands

| Command | Description |
|---------|-------------|
| `/speckit-startup` | Initialize the speckit workflow for the session |
| `/speckit-specify` | Create feature specifications from natural language |
| `/speckit-clarify` | Refine specifications with targeted questions |
| `/speckit-plan` | Execute the implementation planning workflow |
| `/speckit-tasks` | Generate dependency-ordered tasks (TDD on by default; `--no-tdd` to opt out, since 1.9.3) |
| `/speckit-implement` | Execute implementation tasks |
| `/speckit-analyze` | Analyze consistency across artifacts |
| `/speckit-checklist` | Generate quality checklists for requirements |
| `/speckit-constitution` | Manage project principles |

## Skills

### speckit-orchestrator

Workflow coordinator that validates skill loading
and maintains consistency throughout the command lifecycle.

### spec-writing

Guides the creation of testable specifications from natural language
descriptions.

### task-planning

Transforms specifications
and implementation plans into dependency-ordered tasks.

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

## Stewardship

Ways to leave this plugin better than you found it:

- The workflow example is an opportunity to include a
  sample specification so users can see the expected
  format before running `/speckit-specify`
- Task dependency ordering could document how circular
  dependencies are detected and reported
- The `/speckit-checklist` output would benefit from an
  example showing a passing vs. failing quality check
- Integration with the abstract plugin could be clarified
  with a diagram showing which abstract skills are called

See [STEWARDSHIP.md](../../STEWARDSHIP.md) for the full
stewardship principles guiding this project.

## License

MIT
