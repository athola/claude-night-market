# Attune

Project development plugin for Claude Code. Supports ideation, specification, architectural planning, project initialization, and implementation.

## Overview

Attune standardizes project development:

1. **Brainstorm**: Ideate and explore problem space.
2. **Specify**: Create detailed specifications.
3. **Plan**: Design architecture and break down tasks.
4. **Init**: Initialize project structure.
5. **Execute**: Implement systematically with tracking.

## Features

### Supported Languages

- **Python**: uv, pytest, ruff, mypy.
- **Rust**: cargo, clippy, rustfmt.
- **TypeScript/React**: npm/pnpm/yarn, vite, jest, eslint.

### Configuration

- Git initialization with .gitignore.
- GitHub Actions workflows (test, lint, typecheck).
- Pre-commit hooks and Makefiles.
- Dependency management and project structure.

## Quick Start

### Architecture-Aware Initialization

```bash
# Interactive mode with architecture selection
/attune:arch-init --name my-project
```

### Standard Initialization

```bash
# Interactive mode
/attune:init

# Language specification
/attune:init --lang python --name my-project --author "Your Name"
```

### Upgrade Existing Project

```bash
# Add missing configurations
/attune:upgrade

# Validate project structure
/attune:validate
```

## Commands

### Full-Cycle Workflow

| Command | Description | Phase |
|---------|-------------|-------|
| `/attune:brainstorm` | Brainstorm project ideas using Socratic questioning | 1. Ideation |
| `/attune:arch-init` | **Architecture-aware initialization with research** | 1.5. Architecture |
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
| `architecture-aware-init` | **Research-based architecture selection and template customization** | Need architecture guidance |
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
[OK] Git repository initialized
[OK] .gitignore present and complete
[OK] Pre-commit hooks configured
[OK] GitHub Actions workflows configured
[OK] Makefile with development targets
[WARN] Missing: Type checker configuration (mypy)
[FAIL] Missing: Test coverage configuration
```

## Configuration

Attune can be configured via `.attune.yaml`:

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

- `{{PROJECT_NAME}}` - Project name.
- `{{PROJECT_MODULE}}` - Python module name.
- `{{AUTHOR}}` - Project author.
- `{{PYTHON_VERSION}}` - Python version.
- `{{YEAR}}` - Current year.
- `{{LICENSE}}` - License type.

## Integration with Other Plugins

### Superpowers Integration

When the superpowers plugin is installed, attune integrates foundational methodology skills:

- **Brainstorming**: `Skill(superpowers:brainstorming)`
- **Planning**: `Skill(superpowers:writing-plans)`
- **Execution**: `Skill(superpowers:executing-plans)`
- **TDD**: Test-driven development during implementation.
- **Debugging**: `Skill(superpowers:systematic-debugging)`

### Spec-Kit Integration

When spec-kit is installed, attune aligns with specification patterns:

- **Specifications**: `Skill(spec-kit:spec-writing)`
- **Task Planning**: `Skill(spec-kit:task-planning)`

## Philosophy

1. **Cycle support**: Ideas to implementation.
2. **Structured workflows**: Prevent ad-hoc development.
3. **Progressive enhancement**: Integrates with companion plugins.
4. **Safety**: Confirmation required before overwriting files.
5. **Idempotency**: Safe for multiple runs.
6. **Production patterns**: Templates follow established industry practices.
7. **Customization**: Support for template overrides.

## Development Status

**Current Version**: 1.0.0

### Implementation Status

#### Core Initialization

- [x] Python template system.
- [x] Rust and TypeScript support.
- [x] Version fetching and project validation.
- [x] Template customization and reference sync.

#### Development Workflow

- [x] Brainstorming and ideation.
- [x] Specification definition.
- [x] Architectural design and planning.
- [x] Implementation with tracking.

### Supported Features

| Feature | Python | Rust | TypeScript |
|---------|--------|------|------------|
| Git init | [OK] | [OK] | [OK] |
| .gitignore | [OK] | [OK] | [OK] |
| Build config | [OK] | [OK] | [OK] |
| Makefile | [OK] | [OK] | [OK] |
| Pre-commit | [OK] | [TODO] | [TODO] |
| Test workflow | [OK] | [OK] | [OK] |
| Lint workflow | [OK] | [OK] | [OK] |
| Type check | [OK] | [OK] | [OK] |
| Validation | [OK] | [OK] | [OK] |

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
