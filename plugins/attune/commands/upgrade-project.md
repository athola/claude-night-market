---
name: upgrade-project
description: Add or update configurations in an existing project to match current best practices
---

# Attune Upgrade-Project Command

Add missing configurations or update existing ones in a project.

## Usage

```bash
# Interactive upgrade - shows what's missing
/attune:upgrade-project

# Upgrade specific component
/attune:upgrade-project --component workflows
/attune:upgrade-project --component makefile
/attune:upgrade-project --component pre-commit
```

## What This Command Does

1. **Detects project language** and existing configurations
2. **Identifies missing configurations**
3. **Offers to add/update** specific components
4. **Preserves custom modifications** (merge mode)

## Workflow

```bash
# 1. Detect project and show status
python3 plugins/attune/scripts/project_detector.py .

# 2. Show missing configurations
# Example output:
# Project: my-project (Python)
# ✅ .gitignore present
# ✅ pyproject.toml present
# ⚠️  Makefile outdated (from 2023, current: 2026)
# ❌ .pre-commit-config.yaml missing
# ❌ .github/workflows/typecheck.yml missing

# 3. Ask which to add/update
# Which configurations to upgrade?
#   [x] Add .pre-commit-config.yaml
#   [x] Add .github/workflows/typecheck.yml
#   [ ] Update Makefile (will preserve custom targets)

# 4. Apply selected upgrades
```

## Components

Available components to upgrade:

- `makefile` - Update Makefile with new targets
- `workflows` - Add/update GitHub Actions workflows
- `pre-commit` - Update pre-commit hook configurations
- `gitignore` - Update .gitignore with new patterns
- `dependencies` - Update dependency specifications

## Safety Features

- **Merge mode**: Preserves custom modifications when updating
- **Backup creation**: Creates `.bak` files before overwriting
- **Diff preview**: Shows changes before applying
- **Selective upgrade**: Choose which components to update

## Examples

### Example 1: Add Missing GitHub Workflows

```bash
/attune:upgrade-project --component workflows
```

Output:
```
Detecting project type... Python
Checking existing workflows...
  ✅ .github/workflows/test.yml exists
  ❌ .github/workflows/lint.yml missing
  ❌ .github/workflows/typecheck.yml missing

Add missing workflows? [Y/n]: y
✓ Created: .github/workflows/lint.yml
✓ Created: .github/workflows/typecheck.yml
```

### Example 2: Update Outdated Makefile

```bash
/attune:upgrade-project --component makefile
```

Shows diff and asks for confirmation before updating.

## Validation After Upgrade

```bash
/attune:validate
```

Check that all configurations are up-to-date.

## Related Commands

- `/attune:project-init` - Initialize new project from scratch
- `/attune:validate` - Validate current project setup
