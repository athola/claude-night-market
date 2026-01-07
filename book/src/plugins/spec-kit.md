# spec-kit

Specification-Driven Development (SDD) toolkit for structured feature development.

## Overview

Spec-Kit enforces "define before implement" - you write specifications first, generate plans, create tasks, then execute. This reduces wasted effort and validates features match requirements.

## Installation

```bash
/plugin install spec-kit@claude-night-market
```

## Skills

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `spec-writing` | Specification authoring | Writing requirements from ideas |
| `task-planning` | Task generation | Breaking specs into tasks |
| `speckit-orchestrator` | Workflow coordination | Managing spec-to-code lifecycle |

## Commands

| Command | Description |
|---------|-------------|
| `/speckit-specify` | Create a new specification |
| `/speckit-plan` | Generate implementation plan |
| `/speckit-tasks` | Generate ordered tasks |
| `/speckit-implement` | Execute tasks |
| `/speckit-analyze` | Check artifact consistency |
| `/speckit-checklist` | Generate custom checklist |
| `/speckit-clarify` | Ask clarifying questions |
| `/speckit-constitution` | Create project constitution |
| `/speckit-startup` | Bootstrap workflow at session start |

## Agents

| Agent | Description |
|-------|-------------|
| `spec-analyzer` | Validates artifact consistency |
| `task-generator` | Creates implementation tasks |
| `implementation-executor` | Executes tasks and writes code |

## Usage Examples

### Full SDD Workflow

```bash
# 1. Create specification
/speckit-specify Add user authentication with OAuth2

# 2. Clarify requirements
/speckit-clarify

# 3. Generate plan
/speckit-plan

# 4. Create tasks
/speckit-tasks

# 5. Execute implementation
/speckit-implement

# 6. Verify consistency
/speckit-analyze
```

### Quick Specification

```bash
/speckit-specify Add dark mode toggle

# Claude will:
# 1. Ask clarifying questions
# 2. Generate spec.md
# 3. Identify dependencies
# 4. Suggest next steps
```

### Session Startup

```bash
/speckit-startup

# Loads:
# - Existing spec.md
# - Current plan.md
# - Outstanding tasks
# - Progress status
# - Constitution (principles/constraints)
```

## Artifact Structure

Spec-Kit creates three main artifacts:

### spec.md

```markdown
# Feature: User Authentication

## Overview
OAuth2-based authentication for web application.

## Requirements
- [ ] Google OAuth integration
- [ ] Session management
- [ ] Token refresh

## Acceptance Criteria
1. Users can sign in with Google
2. Sessions persist for 7 days
3. Tokens refresh automatically

## Non-Functional Requirements
- Login latency < 2s
- 99.9% availability
```

### plan.md

```markdown
# Implementation Plan

## Phase 1: OAuth Setup
- Configure Google OAuth credentials
- Implement OAuth callback handler

## Phase 2: Session Management
- Design session schema
- Implement token storage

## Phase 3: Integration
- Connect to frontend
- Add logout functionality
```

### tasks.md

```markdown
# Tasks

## Phase 1 Tasks
- [ ] Create OAuth config module
- [ ] Implement /auth/login endpoint
- [ ] Implement /auth/callback endpoint

## Phase 2 Tasks
- [ ] Design session table schema
- [ ] Create session service
- [ ] Implement token refresh logic
```

## Constitution

Project constitution defines principles:

```bash
/speckit-constitution

# Creates:
# - Coding standards
# - Architecture principles
# - Testing requirements
# - Documentation standards
```

## Consistency Analysis

```bash
/speckit-analyze

# Checks:
# - spec.md requirements map to plan.md
# - plan.md phases map to tasks.md
# - No orphan tasks
# - No missing implementations
```

## Checklist Generation

```bash
/speckit-checklist

# Generates custom checklist:
# - [ ] All acceptance criteria met
# - [ ] Tests written
# - [ ] Documentation updated
# - [ ] Security reviewed
```

## Dependencies

Spec-Kit uses imbue for analysis:

```
spec-kit
    |
    v
imbue (diff-analysis, evidence-logging)
```

## Superpowers Integration

| Command | Enhancement |
|---------|-------------|
| `/speckit-clarify` | Uses `brainstorming` for questions |
| `/speckit-plan` | Uses `writing-plans` for structure |
| `/speckit-tasks` | Uses `executing-plans`, `systematic-debugging` |
| `/speckit-implement` | Uses `executing-plans`, `systematic-debugging` |
| `/speckit-analyze` | Uses `systematic-debugging`, `verification-before-completion` |
| `/speckit-checklist` | Uses `verification-before-completion` |

## Best Practices

1. **Specify First**: Never skip the specification phase
2. **Clarify Ambiguity**: Use `/speckit-clarify` liberally
3. **Small Tasks**: Break into 1-2 hour chunks
4. **Verify Often**: Run `/speckit-analyze` after changes
5. **Update Artifacts**: Keep spec/plan/tasks in sync

## Workflow Tips

### Starting New Feature

```bash
/speckit-specify [feature description]
/speckit-clarify
/speckit-plan
```

### Resuming Work

```bash
/speckit-startup
# Review current state
/speckit-implement
```

### Before PR

```bash
/speckit-analyze
/speckit-checklist
```

## Related Plugins

- **imbue**: Provides analysis patterns
- **sanctum**: Integrates for PR preparation after implementation
