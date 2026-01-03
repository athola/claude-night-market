---
name: makefile-generation
description: Generate language-specific Makefile with common development targets
model: claude-sonnet-4
tools: [Read, Write, Bash]
---

# Makefile Generation Skill

Generate a Makefile with standard development targets for Python, Rust, or TypeScript projects.

## Use When

- Need a Makefile for a project without one
- Want to update Makefile with new targets
- Standardizing build automation across projects

## Standard Targets

### Python Makefile

**Common targets**:
- `help` - Show available targets
- `install` - Install dependencies with uv
- `lint` - Run ruff linting
- `format` - Format code with ruff
- `typecheck` - Run mypy type checking
- `test` - Run pytest
- `test-coverage` - Run tests with coverage report
- `check-all` - Run all quality checks
- `clean` - Remove generated files and caches
- `build` - Build distribution packages
- `publish` - Publish to PyPI

### Rust Makefile

**Common targets**:
- `help` - Show available targets
- `fmt` - Format with rustfmt
- `lint` - Run clippy
- `check` - Cargo check
- `test` - Run tests
- `build` - Build release binary
- `clean` - Clean build artifacts

### TypeScript Makefile

**Common targets**:
- `help` - Show available targets
- `install` - Install npm dependencies
- `lint` - Run ESLint
- `format` - Format with Prettier
- `typecheck` - Run tsc type checking
- `test` - Run Jest tests
- `build` - Build for production
- `dev` - Start development server

## Workflow

### 1. Detect Language

```bash
# Check for language indicators
if [ -f "pyproject.toml" ]; then
    LANGUAGE="python"
elif [ -f "Cargo.toml" ]; then
    LANGUAGE="rust"
elif [ -f "package.json" ]; then
    LANGUAGE="typescript"
fi
```

### 2. Load Template

```python
from pathlib import Path

template_path = Path("plugins/attune/templates") / language / "Makefile.template"
```

### 3. Collect Project Info

```python
metadata = {
    "PROJECT_NAME": "my-project",
    "PROJECT_MODULE": "my_project",
    "PYTHON_VERSION": "3.10",
}
```

### 4. Render Template

```python
from template_engine import TemplateEngine

engine = TemplateEngine(metadata)
engine.render_file(template_path, Path("Makefile"))
```

### 5. Verify

```bash
make help
```

## Customization

Users can add custom targets after the generated ones:

```makefile
# ============================================================================
# CUSTOM TARGETS
# ============================================================================

deploy: build ## Deploy to production
	./scripts/deploy.sh
```

## Related Skills

- `Skill(attune:project-init)` - Full project initialization
- `Skill(abstract:makefile-dogfooder)` - Makefile testing and validation
