---
name: validate
description: Validate project structure and configurations against best practices
---

# Attune Validate Command

Check project setup against best practices and identify issues.

## Usage

```bash
# Validate current project
/attune:validate

# Validate specific path
/attune:validate --path /path/to/project

# Show detailed report
/attune:validate --verbose
```

## What This Command Does

1. **Detects project language** and type
2. **Checks for required files** and configurations
3. **Validates file contents** (e.g., proper Makefile targets)
4. **Reports issues and recommendations**

## Validation Checks

### Git Configuration
- ✅ Git repository initialized
- ✅ .gitignore present and comprehensive
- ✅ No large files tracked
- ✅ No secrets in repository

### Build Configuration
- ✅ Makefile with standard targets (test, lint, format)
- ✅ Dependency file present (pyproject.toml, Cargo.toml, package.json)
- ✅ Version pinning for dependencies

### Code Quality
- ✅ Pre-commit hooks configured
- ✅ Linter configuration present
- ✅ Formatter configuration present
- ✅ Type checker configured

### CI/CD
- ✅ Test workflow configured
- ✅ Lint workflow configured
- ✅ Type check workflow configured
- ✅ Workflows use latest action versions

### Project Structure
- ✅ Source directory present (src/)
- ✅ Test directory present (tests/)
- ✅ README.md present
- ✅ License file present

## Output Format

```
Project Validation Report
========================
Project: my-awesome-project
Language: Python
Path: /home/user/my-awesome-project

Git Configuration
  ✅ Git repository initialized
  ✅ .gitignore present (50 patterns)

Build Configuration
  ✅ pyproject.toml present
  ✅ Makefile with 15 targets
  ⚠️  uv.lock is outdated (run: uv sync)

Code Quality
  ✅ Pre-commit hooks configured (7 hooks)
  ✅ Ruff configuration present
  ✅ MyPy strict mode enabled

CI/CD
  ✅ Test workflow (.github/workflows/test.yml)
  ✅ Lint workflow (.github/workflows/lint.yml)
  ❌ Missing: Type check workflow

Project Structure
  ✅ Source directory: src/my_awesome_project/
  ✅ Test directory: tests/
  ✅ README.md present
  ❌ Missing: LICENSE file

Score: 17/20 (85%)

Recommendations:
  1. Add .github/workflows/typecheck.yml (run: /attune:upgrade-project --component workflows)
  2. Add LICENSE file (run: Skill(sanctum:license-generation))
  3. Update uv.lock (run: make install)
```

## Exit Codes

- `0` - All checks passed
- `1` - Minor issues (warnings only)
- `2` - Major issues (missing required files)

## Examples

### Example 1: Quick Validation

```bash
/attune:validate
```

### Example 2: Verbose Report with Suggestions

```bash
/attune:validate --verbose --suggestions
```

Includes:
- Detailed explanation of each check
- Links to documentation
- Copy-paste commands to fix issues

### Example 3: CI Integration

```yaml
# .github/workflows/validate.yml
name: Project Structure Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate project structure
        run: |
          python3 plugins/attune/scripts/validate_project.py --strict
```

## Related Commands

- `/attune:init` - Initialize new project
- `/attune:upgrade-project` - Fix validation issues automatically
