# Safe Testing Module

Strategies for safely testing Makefile targets without side effects.

## Testing Philosophy

1. **Test Hook Logic, Not Tools**: Test your Makefile behavior, not system commands
2. **Use Dry-Run Mode**: Always preview before executing
3. **Categorize by Risk**: Know which targets are safe to run
4. **Validate Documentation**: Ensure help target is complete

## Safe Execution Patterns

### Dry-Run Testing

```bash
# Test target discovery and parsing
make -n help          # Show what would execute
make -n clean         # Verify clean commands without running
make -n test          # Check test commands safely
make -pn | grep '^VAR'  # Show variable definitions
```

## Target Categorization

### Safe Targets (Always Safe)

| Target Pattern | Examples |
|----------------|----------|
| Information | `help`, `status`, `info` |
| Listing | `list-*`, `show-*` |
| Validation | `check-*`, `validate-*`, `verify-*` |
| Read-only analysis | `lint`, `type-check`, `format-check` |

### Conditional Targets (Require Inspection)

| Target | Safe If |
|--------|---------|
| `test` | Tests exist and don't modify state |
| `lint` | Read-only checks |
| `format-check` | No auto-fix flag |

### Risky Targets (Never Run in CI Without Review)

| Category | Examples |
|----------|----------|
| Deletion | `clean`, `purge` |
| Installation | `install`, `deps-update` |
| Modification | `format`, `fix` |
| External | `publish`, `deploy` |

## Help System Validation

### Required Checks

```python
def validate_help(makefile_path: Path) -> bool:
    """Validate help target exists and is useful."""
    result = subprocess.run(
        ['make', '-n', 'help'],
        capture_output=True, text=True,
        cwd=makefile_path.parent
    )
    return result.returncode == 0
```

### Documentation Coverage

```python
def check_documentation_coverage(content: str) -> float:
    """Check what percentage of targets are documented."""
    targets = re.findall(r'^([a-zA-Z0-9_-]+):', content, re.MULTILINE)
    documented = re.findall(r'^([a-zA-Z0-9_-]+):.*?##', content, re.MULTILINE)
    return len(documented) / len(targets) if targets else 0
```

## Quick Test Patterns

### Unit Test Pattern

```python
def test_help_target_exists(makefile_path: Path):
    """Help target should exist and execute."""
    result = subprocess.run(
        ['make', '-n', 'help'],
        capture_output=True, text=True,
        cwd=makefile_path.parent
    )
    assert result.returncode == 0
```

### Risky Target Pattern

```python
@pytest.mark.parametrize("target", ["clean", "install"])
def test_risky_targets_dry_run(makefile_path: Path, target: str):
    """Risky targets should be testable with dry-run."""
    result = subprocess.run(
        ['make', '-n', target],
        capture_output=True, text=True,
        cwd=makefile_path.parent
    )
    assert result.returncode == 0
```

## Testing Checklist

Before deploying Makefiles, verify:

- [ ] **Help Target**: Exists and shows useful output
- [ ] **Documentation**: >80% of targets documented
- [ ] **Dry-Run**: All targets work in dry-run mode
- [ ] **Dependencies**: No missing target dependencies
- [ ] **Tools**: Required tools available
- [ ] **Safety**: Risky targets have safety measures

## Detailed Examples

For comprehensive test examples including:
- Full pytest test suite
- CI/CD GitHub Actions workflow
- Utility functions for testing
- Coverage checking patterns

Use `make -n <target>` for dry-run validation before executing targets.
