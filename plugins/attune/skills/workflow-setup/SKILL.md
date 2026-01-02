---
name: workflow-setup
description: Configure GitHub Actions workflows for CI/CD (test, lint, typecheck, publish)
model: claude-sonnet-4
tools: [Read, Write, Bash]
---

# Workflow Setup Skill

Set up GitHub Actions workflows for continuous integration and deployment.

## Use When

- Need CI/CD for a new project
- Adding missing workflows to existing project
- Updating workflow versions to latest

## Standard Workflows

### Python Workflows

1. **test.yml** - Run pytest on push/PR
2. **lint.yml** - Run ruff linting
3. **typecheck.yml** - Run mypy type checking
4. **publish.yml** - Publish to PyPI on release

### Rust Workflows

1. **ci.yml** - Combined test/lint/check workflow
2. **release.yml** - Build and publish releases

### TypeScript Workflows

1. **test.yml** - Run Jest tests
2. **lint.yml** - Run ESLint
3. **build.yml** - Build for production
4. **deploy.yml** - Deploy to hosting (Vercel, Netlify, etc.)

## Workflow

### 1. Check Existing Workflows

```bash
ls -la .github/workflows/
```

### 2. Identify Missing Workflows

```python
from project_detector import ProjectDetector

detector = ProjectDetector(Path.cwd())
language = detector.detect_language()

required_workflows = {
    "python": ["test.yml", "lint.yml", "typecheck.yml"],
    "rust": ["ci.yml"],
    "typescript": ["test.yml", "lint.yml", "build.yml"],
}

missing = detector.get_missing_configurations(language)
```

### 3. Render Workflow Templates

```python
workflows_dir = Path(".github/workflows")
workflows_dir.mkdir(parents=True, exist_ok=True)

for workflow in required_workflows[language]:
    template = templates_dir / language / "workflows" / f"{workflow}.template"
    output = workflows_dir / workflow

    engine.render_file(template, output)
    print(f"✓ Created: {output}")
```

### 4. Validate Workflows

```bash
# Syntax check (requires act or gh CLI)
gh workflow list

# Or manually check YAML syntax
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"
```

## Workflow Best Practices

### Use Latest Action Versions

```yaml
# Good - pinned to major version
- uses: actions/checkout@v4
- uses: actions/setup-python@v5

# Avoid - unpinned or outdated
- uses: actions/checkout@v2
- uses: actions/setup-python@latest
```

### Matrix Testing (Python)

```yaml
strategy:
  matrix:
    python-version: ["3.10", "3.11", "3.12"]
    os: [ubuntu-latest, macos-latest, windows-latest]
```

### Caching Dependencies

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.10'
    cache: 'pip'  # Cache pip dependencies
```

## Updating Workflows

To update workflows to latest versions:

```bash
/attune:upgrade --component workflows
```

## Related Skills

- `Skill(attune:project-init)` - Full project initialization
- `Skill(sanctum:pr-prep)` - PR preparation with CI checks
