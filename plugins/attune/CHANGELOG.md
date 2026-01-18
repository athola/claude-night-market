# Changelog

All notable changes to the Attune plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-02

### Added

#### Full-Cycle Workflow
- **brainstorm-plan-execute integration**: Complete workflow from ideation to implementation
- **superpowers integration**: Enhanced with Socratic method, structured planning, and TDD
- **spec-kit integration**: Aligned with spec-driven development methodology

#### New Commands
- `/attune:brainstorm` - Brainstorm project ideas using Socratic questioning and ideation techniques
- `/attune:specify` - Create detailed specifications from brainstorm output using spec-driven methodology
- `/attune:plan` - Plan architecture and break down implementation into tasks
- `/attune:execute` - Execute implementation tasks systematically with progress tracking

#### New Skills
- `project-brainstorming` - Socratic questioning and structured ideation methodology
- `project-specification` - Spec-driven requirement definition with testable acceptance criteria
- `project-planning` - Architecture design and dependency-ordered task breakdown
- `project-execution` - Systematic task execution with TDD and checkpoint validation

#### New Agents
- `project-architect` - Architecture design agent for requirement analysis and component design
- `project-implementer` - Implementation execution agent with TDD workflow and progress tracking

#### Documentation
- Complete full-cycle workflow guide (`docs/full-cycle-workflow-guide.md`)
- Enhanced README with workflow examples and integration patterns
- Detailed command documentation for all new workflow phases
- Comprehensive skill documentation with methodology and patterns

### Changed
- **Version**: Bumped to 1.0.0 to reflect major feature addition
- **Description**: Updated to emphasize full-cycle capabilities
- **Keywords**: Added full-cycle, brainstorm-plan-execute, spec-driven-development, superpowers-integration, spec-kit-integration

### Enhanced
- **Graceful degradation**: All workflow phases work standalone or enhanced with superpowers/spec-kit
- **Integration patterns**: Clean delegation to external plugins when available
- **Progress tracking**: Comprehensive execution state management and reporting

## [0.1.0] - 2026-01-01

### Added

#### Core Initialization Features
- Project initialization for Python, Rust, and TypeScript
- Git repository setup with .gitignore templates
- GitHub Actions workflows (test, lint, typecheck)
- Pre-commit hooks configuration
- Makefile generation with development targets
- Dependency management setup (uv, cargo, npm)

#### Commands
- `/attune:init` - Initialize new project with full setup
- `/attune:upgrade-project` - Add or update configurations in existing project
- `/attune:validate` - Validate project structure against best practices

#### Skills
- `project-init` - Interactive project initialization
- `makefile-generation` - Generate language-specific Makefile
- `workflow-setup` - Configure GitHub Actions workflows
- `precommit-setup` - Configure pre-commit hooks

#### Templates
- Python templates (pyproject.toml, .gitignore, workflows)
- Rust templates (Cargo.toml, .gitignore, workflows)
- TypeScript templates (package.json, tsconfig.json, workflows)

## Migration Guide

### Upgrading from 0.1.0 to 1.0.0

**No Breaking Changes**: All existing functionality remains unchanged. New workflow commands are additive.

**New Capabilities Available**:

1. **For new projects** - Use full workflow:
   ```bash
   /attune:brainstorm
   /attune:specify
   /attune:plan
   /attune:init
   /attune:execute
   ```

2. **For existing projects** - Continue using as before:
   ```bash
   /attune:init
   /attune:upgrade-project
   /attune:validate
   ```

3. **Enhanced with superpowers** (optional):
   ```bash
   /plugin marketplace add obra/superpowers
   /plugin install superpowers@superpowers-marketplace
   ```

4. **Enhanced with spec-kit** (optional):
   ```bash
   /plugin install spec-kit@claude-night-market
   ```

**Recommended**: Try the full workflow on a new project to experience systematic development.
