---
name: speckit-orchestrator
description: |
  Workflow orchestrator for Spec Driven Development. Coordinates skills and tracks progress.

  Triggers: speckit workflow, spec driven development, speckit commands
  Use when: starting any /speckit-* command or coordinating multi-phase development
category: workflow-orchestration
tags: [speckit, workflow, orchestration, planning, specification]
dependencies:
  - spec-kit:shared
  - sanctum:git-workspace-review
  - imbue:evidence-logging
  - superpowers:brainstorming
  - superpowers:writing-plans
  - superpowers:executing-plans
tools: []
modules:
  - command-skill-matrix
  - progress-tracking
progressive_loading: true
usage_patterns:
  - workflow-coordination
  - progress-tracking
  - skill-loading
complexity: intermediate
estimated_tokens: 1500
---

# Speckit Orchestrator

## Overview

Coordinates the Spec Driven Development workflow, skill loading, and progress tracking throughout the command lifecycle.

## When to Use

- Starting any `/speckit-*` command.
- Coordinating multi-phase development workflows.
- Tracking progress across specification, planning, and implementation.
- Ensuring skill dependencies are loaded.

## Core Workflow

### Session Initialization

1. **Verify Repository Context**
   - Confirm working directory is a speckit-enabled project.
   - Check for `.specify/` directory structure.
   - Validate required scripts exist.

2. **Load Command Dependencies**
   - Match current command to required skills.
   - Load complementary superpowers skills.

3. **Initialize Progress Tracking**
   - Create TodoWrite items for workflow phases.
   - Track completion status.

### Command-Skill Matrix

Quick reference for command-to-skill mappings:

| Command | Primary Skill | Complementary Skills |
|---------|--------------|---------------------|
| `/speckit-specify` | spec-writing | brainstorming |
| `/speckit-clarify` | spec-writing | brainstorming |
| `/speckit-plan` | task-planning | writing-plans |
| `/speckit-tasks` | task-planning | executing-plans |
| `/speckit-implement` | - | executing-plans, systematic-debugging |
| `/speckit-analyze` | - | systematic-debugging, verification |
| `/speckit-checklist` | - | verification-before-completion |

**For detailed patterns**: See `modules/command-skill-matrix.md` for complete mappings and loading rules.

### Progress Tracking Items

For each workflow session, track:
- [ ] Repository context verified.
- [ ] Prerequisites validated.
- [ ] Command-specific skills loaded.
- [ ] Artifacts created/updated.
- [ ] Verification completed.

**For detailed patterns**: See `modules/progress-tracking.md` for TodoWrite patterns and metrics.

## Exit Criteria

- Active command completed successfully.
- All required artifacts exist and are valid.
- Progress tracking reflects current state.
- No unresolved blockers.

## Related Skills

- `spec-writing`: Specification creation and refinement.
- `task-planning`: Task generation and planning.
- `superpowers:brainstorming`: Idea refinement.
- `superpowers:writing-plans`: Implementation planning.
- `superpowers:executing-plans`: Task execution.
