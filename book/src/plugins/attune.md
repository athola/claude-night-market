# Attune

Full-cycle project development from ideation to implementation.

## Overview

Attune integrates the brainstorm-plan-execute workflow from superpowers with spec-driven development from spec-kit to provide a complete project lifecycle.

## Workflow

```mermaid
graph LR
    A[Brainstorm] --> B[War Room]
    B --> C[Specify]
    C --> D[Plan]
    D --> E[Initialize]
    E --> F[Execute]

    style A fill:#e1f5fe
    style B fill:#fff9c4
    style C fill:#f3e5f5
    style D fill:#fff3e0
    style E fill:#e8f5e8
    style F fill:#fce4ec
```

## Commands

| Command | Phase | Description |
|---------|-------|-------------|
| `/attune:brainstorm` | 1. Ideation | Socratic questioning to explore problem space |
| `/attune:war-room` | 2. Deliberation | Multi-LLM expert deliberation with reversibility-based routing |
| `/attune:specify` | 3. Specification | Create detailed specs from war-room decision |
| `/attune:plan` | 4. Planning | Design architecture and break down tasks |
| `/attune:init` | 5. Initialization | Generate or update project structure with tooling |
| `/attune:execute` | 6. Implementation | Execute tasks with TDD discipline |
| `/attune:upgrade-project` | Maintenance | Add configs to existing projects |
| `/attune:validate` | Quality | Validate project structure |

## Supported Languages

- **Python**: uv, pytest, ruff, mypy, pre-commit
- **Rust**: cargo, clippy, rustfmt, CI workflows
- **TypeScript/React**: npm/pnpm/yarn, vite, jest, eslint, prettier

## What Gets Configured

- Git initialization with detailed .gitignore
- ✅ GitHub Actions workflows (test, lint, typecheck, publish)
- ✅ Pre-commit hooks (formatting, linting, security)
- ✅ Makefile with standard development targets
- ✅ Dependency management (uv/cargo/package managers)
- ✅ Project structure (src/, tests/, README.md)

## Quick Start

### New Python Project

```bash
# Interactive mode
/attune:init

# Non-interactive
/attune:init --lang python --name my-project --author "Your Name"
```

### Full Cycle Workflow

```bash
# 1. Brainstorm the idea
/attune:brainstorm

# 2. War room deliberation (auto-routes by complexity)
/attune:war-room --from-brainstorm

# 3. Create specification
/attune:specify

# 4. Plan architecture
/attune:plan

# 5. Initialize project
/attune:init

# 6. Execute implementation
/attune:execute
```

## Skills

| Skill | Purpose |
|-------|---------|
| `project-brainstorming` | Socratic ideation workflow |
| `war-room` | Multi-LLM expert council with Type 1/2 decision routing |
| `war-room-checkpoint` | Inline RS assessment for embedded escalation during workflow |
| `project-specification` | Spec creation from war-room decision |
| `project-planning` | Architecture and task breakdown |
| `project-init` | Interactive project initialization |
| `project-execution` | Systematic implementation |
| `makefile-generation` | Generate language-specific Makefiles |
| `workflow-setup` | Configure CI/CD pipelines |
| `precommit-setup` | Set up code quality hooks |

## Agents

| Agent | Role |
|-------|------|
| `project-architect` | Guides full-cycle workflow (brainstorm → plan) |
| `project-implementer` | Executes implementation with TDD |

## Integration

Attune combines capabilities from:
- **superpowers**: Brainstorming, planning, execution workflows
- **spec-kit**: Specification-driven development
- **abstract**: Plugin and skill authoring for plugin projects

## War Room Integration

The war room is a mandatory phase after brainstorming. It automatically routes to the appropriate deliberation intensity based on Reversibility Score (RS):

| Mode | RS Range | Duration | Description |
|------|----------|----------|-------------|
| Express | ≤ 0.40 | <2 min | Quick decision by Chief Strategist |
| Lightweight | 0.41-0.60 | 5-10 min | 3-expert panel |
| Full Council | 0.61-0.80 | 15-30 min | 7-expert deliberation |
| Delphi | > 0.80 | 30-60 min | Iterative consensus for critical decisions |

The `war-room-checkpoint` skill can also trigger additional deliberation during planning or execution when high-stakes decisions arise.

## Examples

### Initialize Python CLI Project

```bash
/attune:init --lang python --type cli
```

Creates:
- `pyproject.toml` with uv configuration
- `Makefile` with test/lint/format targets
- GitHub Actions workflows
- Pre-commit hooks for ruff and mypy
- Basic CLI structure

### Upgrade Existing Project

```bash
# Add missing configs
/attune:upgrade-project

# Validate structure
/attune:validate
```

## Configuration

### Custom Templates

Place custom templates in:
- `~/.claude/attune/templates/` (user-level)
- `.attune/templates/` (project-level)
- `$ATTUNE_TEMPLATES_PATH` (environment variable)

### Reference Projects

Templates sync from reference projects:
- `simple-resume` (Python)
- `skrills` (multi-language)
- `importobot` (automation)

<div class="achievement-hint" data-achievement="project-initialized">
Initialize your first project with /attune:init to unlock: Project Architect
</div>
