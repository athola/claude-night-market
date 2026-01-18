---
name: init
description: Initialize project with git, workflows, hooks, and Makefiles
usage: /attune:init [--lang python|rust|typescript] [--name NAME]
---

# Attune Init Command

<identification>
triggers: init project, initialize project, new project, project setup

use_when:
- Starting a new project from scratch
- Setting up development infrastructure
</identification>

Initialize a new project with complete development infrastructure.

## Usage

```bash
# Interactive mode (recommended)
/attune:init

# Specify language
/attune:init --lang python

# Full specification
/attune:init --lang python --name my-project --author "Your Name"
```

## What This Command Does

1. **Detects or accepts language specification** (Python, Rust, TypeScript)
2. **Initializes git repository** (if not already initialized)
3. **Creates configuration files**:
   - `.gitignore` - Language-specific ignores
   - `Makefile` - Development automation
   - `.pre-commit-config.yaml` - Code quality hooks
   - `pyproject.toml` / `Cargo.toml` / `package.json` - Dependency management
4. **Sets up GitHub workflows**:
   - Test workflow
   - Lint workflow
   - Type check workflow
5. **Creates project structure**:
   - `src/` directory with initial module
   - `tests/` directory
   - `README.md`

## Workflow

```bash
# 1. Invoke skill to guide initialization
Skill(attune:project-init)

# 2. Gather project metadata
#    - Project name (default: directory name)
#    - Language (detect or ask)
#    - Author name
#    - Python version (if Python)
#    - License type

# 3. Run initialization script
python3 plugins/attune/scripts/attune_init.py \
  --lang python \
  --name "my-awesome-project" \
  --author "Your Name" \
  --path .

# 4. Validate setup
git status
make help
```

## Arguments

- `--lang <language>` - Project language (python, rust, typescript)
- `--name <name>` - Project name (default: directory name)
- `--author <name>` - Author name
- `--email <email>` - Author email
- `--python-version <version>` - Python version (default: 3.10)
- `--description <text>` - Project description
- `--path <path>` - Project path (default: current directory)
- `--force` - Overwrite existing files without prompting
- `--no-git` - Skip git initialization

## Interactive Mode

When no arguments provided, the skill guides you through:

1. **Language detection**: Auto-detect or let you choose
2. **Project metadata**: Name, author, description
3. **Feature selection**: Which components to initialize
4. **Confirmation**: Review before applying changes
5. **Execution**: Run initialization with your choices

## Safety Features

- **Non-destructive**: Prompts before overwriting existing files
- **Validation**: Checks for conflicts before copying templates
- **Dry-run option**: Preview changes without applying ([#97](https://github.com/athola/claude-night-market/issues/97))
- **Backup option**: Create backups of overwritten files ([#98](https://github.com/athola/claude-night-market/issues/98))

## Examples

### Example 1: New Python CLI Project

```bash
/attune:init --lang python --name awesome-cli --description "An awesome CLI tool"
```

Creates:
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

### Example 2: Initialize in Existing Project

```bash
cd my-existing-project
/attune:init --lang python
```

Prompts:
```
File exists: pyproject.toml. Overwrite? [y/N]: n
⊘ Skipped: pyproject.toml
File exists: Makefile. Overwrite? [y/N]: y
✓ Created: Makefile
...
```

### Example 3: Force Overwrite All Files

```bash
/attune:init --lang python --force
```

Overwrites all existing files without prompting.

## Post-Initialization Steps

After initialization, run:

```bash
# Install dependencies and set up pre-commit hooks
make dev-setup

# Verify installation
make test

# See all available targets
make help
```

## Troubleshooting

**Git not initialized**:
```bash
# Initialize manually
git init
/attune:init --lang python
```

**Permission denied on scripts**:
```bash
chmod +x plugins/attune/scripts/attune_init.py
```

**Missing uv command** (for Python projects):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Related Commands

- `/attune:upgrade-project` - Add missing configurations to existing project
- `/attune:validate` - Check project against best practices

## Related Skills

- `Skill(attune:project-init)` - Interactive initialization flow
- `Skill(attune:makefile-generation)` - Generate Makefile only
- `Skill(attune:workflow-setup)` - Set up GitHub Actions only
- `Skill(attune:precommit-setup)` - Configure pre-commit hooks only
