---
name: project-init
description: |
  Interactive project initialization with git setup, workflows, hooks, and build configuration.

  Triggers: project setup, initialization, scaffold, bootstrap, new project
  Use when: starting new projects or initializing repositories
model: claude-sonnet-4
tools: [Read, Write, Bash, Glob]
modules:
  - ./modules/language-detection.md
  - ./modules/metadata-collection.md
  - ./modules/template-rendering.md
---

# Project Initialization Skill

Interactive workflow for initializing new software projects with complete development infrastructure.

## Use When

- Starting a new Python, Rust, or TypeScript project
- Need to set up git, GitHub workflows, pre-commit hooks, Makefile
- Want consistent project structure across team
- Converting unstructured project to best practices

## Workflow

### 1. Detect or Select Language

Load module: `Skill(attune:project-init#language-detection)`

- Auto-detect from existing files (pyproject.toml, Cargo.toml, package.json)
- If ambiguous or empty directory, ask user to select
- Validate language is supported (python, rust, typescript)

### 2. Collect Project Metadata

Load module: `Skill(attune:project-init#metadata-collection)`

Gather:
- Project name (default: directory name)
- Author name and email
- Project description
- Language-specific settings:
  - Python: version (default 3.10)
  - Rust: edition (default 2021)
  - TypeScript: framework (React, Vue, etc.)
- License type (MIT, Apache, GPL, etc.)

### 3. Review Existing Files

Check for existing configurations:
```bash
ls -la
```

If files exist (Makefile, .gitignore, etc.):
- Show what would be overwritten
- Ask for confirmation or selective overwrite
- Offer merge mode (preserve custom content)

### 4. Render and Apply Templates

Load module: `Skill(attune:project-init#template-rendering)`

Run initialization script:
```bash
python3 plugins/attune/scripts/attune_init.py \
  --lang {{LANGUAGE}} \
  --name {{PROJECT_NAME}} \
  --author {{AUTHOR}} \
  --email {{EMAIL}} \
  --python-version {{PYTHON_VERSION}} \
  --description {{DESCRIPTION}} \
  --path .
```

### 5. Initialize Git (if needed)

```bash
# Check if git is initialized
if [ ! -d .git ]; then
  git init
  echo "✓ Git repository initialized"
fi
```

### 6. Verify Setup

Run validation:
```bash
# Check Makefile targets
make help

# List created files
git status
```

### 7. Next Steps

Guide user on:
```bash
# Install dependencies and hooks
make dev-setup

# Run tests to verify setup
make test

# See all available commands
make help
```

## Error Handling

- **Language detection fails**: Ask user to specify `--lang`
- **Script not found**: Guide to plugin installation location
- **Permission denied**: Suggest `chmod +x` on scripts
- **Git conflicts**: Offer to stash or commit existing work

## Success Criteria

- ✅ All template files created successfully
- ✅ No overwrites without user confirmation
- ✅ Git repository initialized
- ✅ `make help` shows available targets
- ✅ `make test` runs without errors (even if no tests yet)

## Examples

### Example 1: New Python Project

```
User: /attune:init
