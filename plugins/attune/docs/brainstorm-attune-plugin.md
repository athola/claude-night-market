# Attune Plugin - Project Initialization System

## Problem Statement

Developers need a consistent, automated way to initialize new software projects with proper:
- Version control (git init + .gitignore)
- CI/CD workflows (GitHub Actions)
- Pre-commit hooks (formatting, linting, security)
- Build automation (Makefiles)
- Dependency management (language-specific: uv, cargo, npm)
- Quality gates (tests, linting, type checking)

Currently, this requires manual setup or copying from reference projects, leading to:
- Inconsistent project structures
- Missing quality gates
- Incomplete CI/CD configurations
- Copy-paste errors
- Stale template files

## Goals

1. **One-command project initialization**: `attune init --lang python` creates a complete project structure
2. **Language-aware templates**: Python, Rust, TypeScript/React with proper tooling
3. **Extensible architecture**: Easy to add new languages or customize templates
4. **Integration with existing projects**: Can enhance/upgrade existing project configurations
5. **Best practices baked in**: Pre-commit hooks, GitHub workflows, Makefiles follow proven patterns

## Constraints

- Must work within claude-night-market plugin ecosystem
- Should leverage leyline for shared infrastructure patterns
- Should leverage abstract for skill/hook/command creation capabilities
- Must be non-intrusive (ask before overwriting files)
- Should be idempotent (running twice shouldn't break things)
- Templates must stay up-to-date with current best practices

## Brainstorming - Approaches

### Approach 1: Template-Based Generator

**Description**: Static template files stored in plugin, copied to target project with variable substitution.

**Pros**:
- Simple to implement
- Easy to understand and customize
- Fast execution
- Clear separation of templates

**Cons**:
- Templates can become stale
- Requires manual maintenance
- Hard to compose (combining multiple features)
- Limited flexibility for edge cases

**Trade-offs**:
- Simplicity vs. flexibility
- Maintenance burden vs. implementation speed

---

### Approach 2: Dynamic Generation (Code-First)

**Description**: Python/Rust code generates files programmatically based on project metadata and language detection.

**Pros**:
- Never stale (uses latest package syntax)
- Highly flexible
- Can query external sources (latest GitHub Actions versions)
- Composable logic

**Cons**:
- More complex implementation
- Harder to customize templates
- Slower execution (external queries)
- Testing is more complex

**Trade-offs**:
- Flexibility vs. complexity
- Freshness vs. speed

---

### Approach 3: Hybrid Template + Generation

**Description**: Base templates with programmatic enhancements and version detection.

**Pros**:
- Balance of simplicity and flexibility
- Templates for structure, code for dynamic content
- Can evolve incrementally
- Easier to test individual components

**Cons**:
- More architectural complexity
- Two systems to maintain
- Potential confusion about what goes where

**Trade-offs**:
- Balanced approach at cost of clarity
- More moving parts

---

### Approach 4: Skill-Driven Initialization

**Description**: Use claude-night-market skills to guide human through initialization, generate configurations with AI.

**Pros**:
- Leverages LLM strengths (understanding context)
- Highly adaptable to user needs
- Can explain choices
- Easy to update (just update skill docs)

**Cons**:
- Requires Claude Code interaction
- Slower than automated scripts
- Non-deterministic outputs
- Harder to version control templates

**Trade-offs**:
- Adaptability vs. reproducibility
- Human-in-loop vs. automation

---

### Approach 5: Reference Project Cloning

**Description**: Maintain reference projects (Python, Rust, TS) and clone + customize them.

**Pros**:
- Always working (reference projects are tested)
- Real-world validation
- Easy to update (just update reference projects)
- Dogfooding our own patterns

**Cons**:
- Heavyweight (copying unnecessary files)
- Coupling to specific project structures
- Cleanup required after cloning
- Hard to compose features

**Trade-offs**:
- Proven patterns vs. bloat
- Simplicity vs. customization

---

## Recommended Approach

**Hybrid Template + Generation (Approach 3)** with **Skill-Driven Orchestration (Approach 4)**

### Rationale

1. **Templates for static structure**: .gitignore, Makefile skeleton, workflow scaffolds
2. **Generation for dynamic content**: Latest GitHub Action versions, dependency versions, variable substitution
3. **Skills for orchestration**: Guide users through choices, explain trade-offs, compose features
4. **Scripts for automation**: Fallback CLI for CI/CD or non-interactive use

### Architecture

```
plugins/attune/
├── .claude-plugin/
│   ├── plugin.json
│   └── metadata.json
├── templates/
│   ├── python/
│   │   ├── .gitignore.template
│   │   ├── .pre-commit-config.yaml.template
│   │   ├── Makefile.template
│   │   ├── pyproject.toml.template
│   │   └── workflows/
│   │       ├── test.yml.template
│   │       ├── lint.yml.template
│   │       └── publish.yml.template
│   ├── rust/
│   │   ├── .gitignore.template
│   │   ├── Cargo.toml.template
│   │   ├── Makefile.template
│   │   └── workflows/
│   │       ├── ci.yml.template
│   │       └── release.yml.template
│   └── typescript/
│       ├── .gitignore.template
│       ├── package.json.template
│       ├── tsconfig.json.template
│       └── workflows/
│           ├── test.yml.template
│           └── build.yml.template
├── scripts/
│   ├── attune_init.py          # Main CLI
│   ├── template_engine.py      # Variable substitution
│   ├── version_fetcher.py      # Get latest versions
│   └── project_detector.py     # Detect existing project type
├── skills/
│   ├── project-init/           # Interactive initialization
│   ├── makefile-generation/    # Makefile creation
│   ├── workflow-setup/         # GitHub Actions setup
│   └── precommit-setup/        # Pre-commit hooks setup
├── commands/
│   ├── init.md                 # /attune:init
│   ├── upgrade.md              # /attune:upgrade
│   └── validate.md             # /attune:validate
└── README.md
```

### Core Features

1. **Language Detection**: Auto-detect project language or let user specify
2. **Template Variables**: PROJECT_NAME, AUTHOR, PYTHON_VERSION, etc.
3. **Incremental Setup**: Can add just workflows, or just Makefile, or full initialization
4. **Validation**: Check existing project against best practices
5. **Upgrade Path**: Update existing configurations to latest patterns

### Implementation Phases

**Phase 1: MVP (Python only)**
- Basic template engine
- Python .gitignore, Makefile, pyproject.toml
- Pre-commit hooks configuration
- Test workflow
- `/attune:init` command

**Phase 2: Multi-language**
- Rust templates (Cargo.toml, Makefile)
- TypeScript templates (package.json, tsconfig.json)
- Language detection logic
- `/attune:upgrade` command

**Phase 3: Advanced Features**
- Version fetching for GitHub Actions
- Custom template locations
- Template composition (mix features)
- `/attune:validate` command

**Phase 4: Integration**
- Leyline integration for shared patterns
- Abstract integration for plugin development projects
- Reference project synchronization
- Auto-update templates from reference projects

## Questions to Resolve

1. **Template format**: Jinja2, Mustache, or simple {{VAR}} replacement?
2. **Version pinning**: Pin GitHub Action versions or use @latest?
3. **Git initialization**: Should we auto-commit initial setup?
4. **Existing files**: Merge, backup, or error on conflict?
5. **Configuration storage**: Where to store user preferences (project type, author, etc.)?
6. **Template updates**: How to handle template evolution (migration scripts)?

## Success Criteria

1. ✅ Can initialize Python project in < 10 seconds
2. ✅ Generated projects pass all CI checks
3. ✅ Templates match reference project patterns
4. ✅ Can upgrade existing projects without breaking them
5. ✅ Skill-driven initialization asks < 5 questions
6. ✅ CLI mode works in CI/CD environments

## Out of Scope (For Now)

- Docker/container setup
- Database initialization
- Deployment configurations
- Language server configurations (LSP)
- IDE-specific files (.vscode, .idea)
- License file generation
- Contributing guide generation

## References

- ~/simple-resume: Python/uv reference project
- ~/skrills: Rust/cargo reference project
- ~/importobot: Python/uv multi-workspace reference
- plugins/leyline: Infrastructure patterns
- plugins/abstract: Plugin creation patterns
- plugins/sanctum: Workflow and git patterns

## Next Steps

1. Create plugin structure (`plugins/attune/`)
2. Implement template engine with variable substitution
3. Create Python templates from simple-resume reference
4. Implement `/attune:init` command
5. Create `project-init` skill for interactive mode
6. Test on fresh Python project
7. Iterate based on feedback

---

**Created**: 2026-01-02
**Status**: Draft - Awaiting feedback before implementation
