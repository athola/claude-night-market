# Attune

Full-cycle project development plugin for Claude Code. From ideation to implementation - brainstorm project ideas, create specifications, plan architecture, initialize projects, and execute implementation systematically.

## Overview

Attune integrates the **brainstorm-plan-execute** workflow from superpowers with **spec-driven development** from spec-kit to provide a complete project development lifecycle:

```
/attune:brainstorm  → Ideate and explore problem space
        ↓
/attune:specify     → Create detailed specifications
        ↓
/attune:plan        → Design architecture and break down tasks
        ↓
/attune:init        → Initialize project structure
        ↓
/attune:execute     → Implement systematically with tracking
```

## Features

### Supported Languages

- **Python**: uv-based dependency management, pytest, ruff, mypy
- **Rust**: cargo-based builds, clippy, rustfmt, CI workflows
- **TypeScript/React**: npm/pnpm/yarn, vite, jest, eslint, prettier

### What Gets Configured

- ✅ Git initialization with .gitignore
- ✅ GitHub Actions workflows (test, lint, typecheck, publish)
- ✅ Pre-commit hooks (formatting, linting, security)
- ✅ Makefile with common development targets
- ✅ Dependency management configuration
- ✅ Project structure and tooling setup

## Quick Start

### Initialize New Python Project

```bash
# Interactive mode (recommended for first time)
/attune:init

# Non-interactive with language specification
/attune:init --lang python --name my-project --author "Your Name"
```

### Upgrade Existing Project

```bash
# Add missing configurations to existing project
/attune:upgrade

# Validate project against best practices
/attune:validate
```

## Commands

### Full-Cycle Workflow

| Command | Description | Phase |
|---------|-------------|-------|
| `/attune:brainstorm` | Brainstorm project ideas using Socratic questioning | 1. Ideation |
| `/attune:specify` | Create detailed specifications from brainstorm | 2. Specification |
| `/attune:plan` | Plan architecture and break down into tasks | 3. Planning |
| `/attune:init` | Initialize project structure with tooling | 4. Initialization |
| `/attune:execute` | Execute implementation tasks systematically | 5. Implementation |

### Project Management

| Command | Description |
|---------|-------------|
| `/attune:upgrade` | Add or update configurations in existing project |
| `/attune:validate` | Validate project structure against best practices |

## Skills

### Full-Cycle Workflow Skills

| Skill | Description | Use When |
|-------|-------------|----------|
| `project-brainstorming` | Socratic questioning and ideation | Starting new project from idea |
| `project-specification` | Spec-driven requirement definition | Need detailed requirements |
| `project-planning` | Architecture design and task breakdown | Planning implementation |
| `project-execution` | Systematic task execution with TDD | Implementing planned tasks |

### Initialization Skills

| Skill | Description | Use When |
|-------|-------------|----------|
| `project-init` | Interactive project initialization | Setting up new project |
| `makefile-generation` | Generate language-specific Makefile | Need build automation |
| `workflow-setup` | Configure GitHub Actions workflows | Setting up CI/CD |
| `precommit-setup` | Configure pre-commit hooks | Enforcing code quality |

## Agents

| Agent | Description | Capabilities |
|-------|-------------|--------------|
| `project-architect` | Architecture design agent | Requirement analysis, component design, data modeling |
| `project-implementer` | Implementation execution agent | TDD workflow, checkpoint validation, progress tracking |

## Templates

Templates are based on proven patterns from reference projects:

- **Python**: Based on `simple-resume` project structure
- **Rust**: Based on `skrills` project structure
- **TypeScript**: Based on modern React/Vite patterns

### Python Template Includes

- `.gitignore` - Python-specific ignores
- `pyproject.toml` - uv-based dependency management
- `Makefile` - Development targets (test, lint, format, etc.)
- `.pre-commit-config.yaml` - Formatting, linting, type checking hooks
- `.github/workflows/test.yml` - CI testing workflow
- `.github/workflows/lint.yml` - Linting workflow
- `.github/workflows/typecheck.yml` - Type checking workflow

## Quick Start - Full Cycle

### Complete Project Development

```bash
# 1. Brainstorm the project
/attune:brainstorm --domain "CLI tool"

# Output: docs/project-brief.md with problem, constraints, approach

# 2. Create specification
/attune:specify

# Output: docs/specification.md with requirements and acceptance criteria

# 3. Plan implementation
/attune:plan

# Output: docs/implementation-plan.md with architecture and tasks

# 4. Initialize project
/attune:init --lang python

# Output: Complete project structure with tooling

# 5. Execute implementation
/attune:execute

# Output: Systematic implementation with progress tracking
```

## Usage Examples

### Example 1: Full-Cycle Web Application

```bash
# Start with brainstorming
/attune:brainstorm --domain "web application"

# Interactive session guides you through:
# - Problem definition
# - Constraint identification
# - Approach comparison
# - Decision documentation

# Output: docs/project-brief.md

# Create specification
/attune:specify

# Transform brief into testable requirements
# Output: docs/specification.md

# Plan architecture
/attune:plan

# Design system components and tasks
# Output: docs/implementation-plan.md

# Initialize project
/attune:init --lang python --name tech-debt-tracker

# Set up full project structure
# Output: Complete Python project with CI/CD

# Execute implementation
/attune:execute

# Systematic task-by-task implementation
# Output: Working implementation with tests
```

### Example 2: New Python CLI Project (Traditional)

```bash
/attune:init --lang python --name awesome-cli --type cli
```

Generates:
```
awesome-cli/
├── .git/
├── .gitignore
├── .pre-commit-config.yaml
├── pyproject.toml
├── Makefile
├── README.md
├── src/
│   └── awesome_cli/
│       └── __init__.py
├── tests/
│   └── __init__.py
└── .github/
    └── workflows/
        ├── test.yml
        ├── lint.yml
        └── typecheck.yml
```

### Example 2: Add GitHub Workflows to Existing Project

```bash
# From project root
/attune:upgrade --component workflows
```

### Example 3: Validate Project Structure

```bash
/attune:validate
```

Output:
```
✅ Git repository initialized
✅ .gitignore present and comprehensive
✅ Pre-commit hooks configured
✅ GitHub Actions workflows configured
✅ Makefile with development targets
⚠️  Missing: Type checker configuration (mypy)
❌ Missing: Test coverage configuration
```

## Configuration

Attune can be configured via `.attune.yaml` in your project:

```yaml
language: python
python_version: "3.10"
package_manager: uv
author: "Your Name"
license: MIT

features:
  pre_commit: true
  github_workflows: true
  makefile: true
  type_checking: true
  testing: true

customization:
  makefile_targets:
    - name: custom-task
      command: ./scripts/custom.sh
```

## Template Customization

### Override Templates

Place custom templates in `~/.claude/attune/templates/`:

```
~/.claude/attune/templates/
└── python/
    ├── .gitignore.template
    └── Makefile.template
```

### Template Variables

Available in all templates:

- `{{PROJECT_NAME}}` - Project name (e.g., "awesome-cli")
- `{{PROJECT_MODULE}}` - Python module name (e.g., "awesome_cli")
- `{{AUTHOR}}` - Project author
- `{{PYTHON_VERSION}}` - Python version (e.g., "3.10")
- `{{YEAR}}` - Current year
- `{{LICENSE}}` - License type

## Integration with Other Plugins

### Superpowers Integration

When superpowers plugin is installed, attune enhances workflows:

- **brainstorming** → Uses `Skill(superpowers:brainstorming)` for Socratic method
- **writing-plans** → Uses `Skill(superpowers:writing-plans)` for planning
- **executing-plans** → Uses `Skill(superpowers:executing-plans)` for execution
- **test-driven-development** → Uses TDD workflow during implementation
- **systematic-debugging** → Uses debugging framework for blockers

Install superpowers:
```bash
/plugin marketplace add obra/superpowers
/plugin install superpowers@superpowers-marketplace
```

### Spec-Kit Integration

When spec-kit plugin is installed, attune enhances specification workflow:

- **spec-writing** → Uses `Skill(spec-kit:spec-writing)` for specifications
- **task-planning** → Uses `Skill(spec-kit:task-planning)` for task breakdown
- **implementation-executor** → Aligns with spec-kit implementation patterns

Install spec-kit:
```bash
/plugin install spec-kit@claude-night-market
```

### Other Plugin Integration

- **leyline**: Uses shared infrastructure patterns for service integration
- **abstract**: Follows plugin development best practices
- **sanctum**: Complements git workflow and documentation updates
- **parseltongue**: Leverages Python development patterns
- **imbue**: Uses scope-guard for anti-overengineering

## Philosophy

1. **Full-cycle thinking**: From idea to implementation, not just initialization
2. **Systematic execution**: Structured workflows prevent ad-hoc development
3. **Graceful degradation**: Works standalone or enhanced with superpowers/spec-kit
4. **Non-invasive**: Always ask before overwriting files
5. **Idempotent**: Safe to run multiple times
6. **Best practices**: Templates follow proven patterns from production projects
7. **Customizable**: Easy to override templates or add custom configurations
8. **Educational**: Explain choices and provide documentation

## Workflow Comparison

### Traditional Ad-Hoc Development

```
Idea → Code → (Maybe tests) → Debug → More code → Eventually works
```
**Problems**: Scope creep, unclear requirements, rework, technical debt

### Attune Full-Cycle Development

```
Brainstorm → Specify → Plan → Initialize → Execute → Validate
```
**Benefits**: Clear requirements, systematic execution, measurable progress, quality built-in

## Development Status

**Current Version**: 1.0.0

### Implementation Status

#### Core Initialization (Complete)

- [x] **Phase 1**: Python template system with basic initialization
- [x] **Phase 2**: Rust and TypeScript support
- [x] **Phase 3**: Advanced features (version fetching, project validation)
- [x] **Phase 4**: Integration (template customization, upgrade mode, plugin projects, reference sync)

#### Full-Cycle Workflow (New in 1.0.0)

- [x] **Brainstorm Phase**: Socratic questioning and ideation
- [x] **Specification Phase**: Spec-driven requirement definition
- [x] **Planning Phase**: Architecture design and task breakdown
- [x] **Execution Phase**: Systematic implementation with tracking
- [x] **Superpowers Integration**: Enhanced with brainstorm-plan-execute
- [x] **Spec-Kit Integration**: Aligned with spec-driven development

### Supported Features

| Feature | Python | Rust | TypeScript |
|---------|--------|------|------------|
| Git init | ✅ | ✅ | ✅ |
| .gitignore | ✅ | ✅ | ✅ |
| Build config | ✅ pyproject.toml | ✅ Cargo.toml | ✅ package.json + tsconfig.json |
| Makefile | ✅ | ✅ | ✅ |
| Pre-commit | ✅ | ⏳ | ⏳ |
| Test workflow | ✅ | ✅ | ✅ |
| Lint workflow | ✅ | ✅ (clippy) | ✅ |
| Type check | ✅ | ✅ | ✅ |
| Validation | ✅ | ✅ | ✅ |

## Contributing

Templates are stored in `plugins/attune/templates/`. To add or improve templates:

1. Modify template files
2. Test with `/attune:init`
3. Update documentation
4. Submit PR with examples

## License

MIT

## Related Projects

- [simple-resume](https://github.com/athola/simple-resume) - Python reference project
- [skrills](https://github.com/athola/skrills) - Rust reference project
- [claude-night-market](https://github.com/athola/claude-night-market) - Plugin marketplace
