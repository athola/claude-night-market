# Attune

Project development plugin for Claude Code. Support ideation, specification, architectural planning, project initialization, and implementation.

## Overview

Standardize project development:

1. **Brainstorm**: Ideate and explore problem space.
2. **War Room**: Multi-expert deliberation to select approach.
3. **Specify**: Create detailed specifications.
4. **Plan**: Design architecture and break down tasks.
5. **Init**: Initialize or update project structure.
6. **Execute**: Implement systematically with tracking.

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
/attune:project-init

# Language specification
/attune:project-init --lang python --name my-project --author "Your Name"
```

### Upgrade Existing Project

```bash
# Add missing configurations
/attune:upgrade-project

# Validate project structure
/attune:validate
```

## Commands

### Full-Cycle Workflow

| Command | Description | Phase |
|---------|-------------|-------|
| `/attune:brainstorm` | Brainstorm project ideas using Socratic questioning | 1. Ideation |
| `/attune:war-room` | **Multi-LLM expert deliberation for approach selection** | 2. Deliberation |
| `/attune:arch-init` | **Architecture-aware initialization with research** | 3. Architecture |
| `/attune:specify` | Create detailed specifications from war-room decision | 4. Specification |
| `/attune:plan` | Plan architecture and break down into tasks | 5. Planning |
| `/attune:project-init` | Initialize or update project structure with tooling | 6. Initialization |
| `/attune:execute` | Execute implementation tasks systematically | 7. Implementation |

**War Room Integration**: The war-room is a **mandatory phase** after brainstorming. It automatically routes to the appropriate deliberation intensity based on Reversibility Score (RS):
- **Express** (RS ≤ 0.40): Quick decision by Chief Strategist (<2 min)
- **Lightweight** (RS 0.41-0.60): 3-expert panel (5-10 min)
- **Full Council** (RS 0.61-0.80): 7-expert deliberation (15-30 min)
- **Delphi** (RS > 0.80): Iterative consensus for critical decisions (30-60 min)

The `war-room-checkpoint` skill can also trigger additional deliberation during planning or execution when high-stakes decisions arise.

### Project Management

| Command | Description |
|---------|-------------|
| `/attune:upgrade-project` | Add or update configurations in existing project |
| `/attune:validate` | Validate project structure against best practices |

## Skills

### Full-Cycle Workflow Skills

| Skill | Description | Use When |
|-------|-------------|----------|
| `project-brainstorming` | Socratic questioning and ideation | Starting new project from idea |
| `war-room` | **Multi-LLM expert council with Type 1/2 routing** | Complex strategic decisions (RS > 0.40) |
| `war-room-checkpoint` | **Inline RS assessment for embedded escalation** | Called by other commands at decision points |
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

# Output: docs/project-brief.md with problem, constraints, approaches

# 2. War Room deliberation (mandatory - auto-routes by complexity)
/attune:war-room --from-brainstorm

# Output: Decision document with selected approach
# - Simple choice? Express mode (<2 min)
# - Complex trade-offs? Full council deliberation

# 3. Create specification
/attune:specify

# Output: docs/specification.md with requirements and acceptance criteria

# 4. Plan implementation
/attune:plan

# Output: docs/implementation-plan.md with architecture and tasks

# 5. Initialize or update project
/attune:project-init --lang python

# Output: Complete project structure with tooling
# Note: For existing projects, detects and offers to update configurations

# 6. Execute implementation
/attune:execute

# Output: Systematic implementation with progress tracking
# Note: war-room-checkpoint can escalate at decision points during execution
```

## Usage Examples

### Add GitHub Workflows to Existing Project

```bash
# From project root
/attune:upgrade-project --component workflows
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

With the superpowers plugin, Attune integrates foundational methodology skills:

- **Brainstorming**: `Skill(superpowers:brainstorming)`
- **Planning**: `Skill(superpowers:writing-plans)`
- **Execution**: `Skill(superpowers:executing-plans)`
- **TDD**: Test-driven development during implementation.
- **Debugging**: `Skill(superpowers:systematic-debugging)`

### Spec-Kit Integration

With spec-kit, Attune aligns with specification patterns:

- **Specifications**: `Skill(spec-kit:spec-writing)`
- **Task Planning**: `Skill(spec-kit:task-planning)`

## Philosophy

Attune enforces structured workflows from ideation to implementation, integrating with plugins and requiring confirmation for file operations. Templates follow industry practices and support full customization.

## License

MIT

## Related Projects

- [simple-resume](https://github.com/athola/simple-resume) - Python reference project
- [skrills](https://github.com/athola/skrills) - Rust reference project
- [claude-night-market](https://github.com/athola/claude-night-market) - Plugin marketplace
