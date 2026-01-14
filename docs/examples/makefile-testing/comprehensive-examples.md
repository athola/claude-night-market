# Makefile Testing Examples

Comprehensive test examples for Makefile validation. For testing strategies and quick reference, see the [testing module](../../../plugins/abstract/skills/makefile-dogfooder/modules/testing.md).

## Complete Test Suite Template

```python
"""Test suite for Makefile validation."""
import pytest
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict

class TestMakefileSafety:
    """Test safe execution patterns."""

    @pytest.fixture
    def makefile_path(self, project_root: Path) -> Path:
        """Get the Makefile path."""
        return project_root / "Makefile"

    def test_help_target_exists(self, makefile_path: Path):
        """Help target should exist and execute."""
        result = subprocess.run(
            ['make', '-n', 'help'],
            capture_output=True,
            text=True,
            cwd=makefile_path.parent
        )
        assert result.returncode == 0, "Help target not found"

    def test_help_target_documentation(self, makefile_path: Path):
        """Help should show well-formatted documentation."""
        result = subprocess.run(
            ['make', 'help'],
            capture_output=True,
            text=True,
            cwd=makefile_path.parent
        )

        # Should have multiple documented targets
        lines = [l for l in result.stdout.split('\n') if '  ' in l]
        assert len(lines) >= 5, "Help should document at least 5 targets"

        # Should have consistent formatting
        formatted_lines = [l for l in lines if l.strip().startswith('  ')]
        assert len(formatted_lines) > 0, "Help should use standard formatting"

    def test_pretty_target_exists(self, makefile_path: Path):
        """Pretty target should exist."""
        result = subprocess.run(
            ['make', '-n', 'pretty'],
            capture_output=True,
            text=True,
            cwd=makefile_path.parent
        )
        assert result.returncode == 0, "Pretty target not found"

    @pytest.mark.parametrize("target", ["clean", "install", "deps-update"])
    def test_risky_targets_dry_run(self, makefile_path: Path, target: str):
        """Risky targets should be testable with dry-run."""
        result = subprocess.run(
            ['make', '-n', target],
            capture_output=True,
            text=True,
            cwd=makefile_path.parent
        )
        # Should execute without errors in dry-run
        assert result.returncode == 0, f"{target} should work in dry-run mode"

    def test_no_missing_dependencies(self, makefile_path: Path):
        """All target dependencies should exist."""
        # Get all targets
        result = subprocess.run(
            ['make', '-p'],
            capture_output=True,
            text=True,
            cwd=makefile_path.parent
        )

        # Extract targets and their dependencies
        target_lines = [
            line for line in result.stdout.split('\n')
            if ':' in line and not line.startswith('#')
            and not line.startswith('\t')
        ]

        for line in target_lines:
            if ':' in line:
                target, deps = line.split(':', 1)
                target = target.strip()
                deps = deps.strip()

                if deps and not target.startswith('.'):
                    for dep in deps.split():
                        # Skip variables and file extensions
                        if not (dep.startswith('$') or '.' in dep):
                            # Check dependency exists
                            dep_result = subprocess.run(
                                ['make', '-n', dep],
                                capture_output=True,
                                text=True,
                                cwd=makefile_path.parent
                            )
                            assert dep_result.returncode == 0, f"Missing dependency: {dep} for target: {target}"

    def test_required_tools_available(self, makefile_path: Path):
        """All required tools should be available."""
        # Get commands that would be executed
        result = subprocess.run(
            ['make', '-n', 'all'],
            capture_output=True,
            text=True,
            cwd=makefile_path.parent
        )

        if result.returncode == 0:
            commands = result.stdout.split('\n')
            tools = set()

            for cmd in commands:
                cmd = cmd.strip()
                if cmd and not cmd.startswith('@'):
                    tool = cmd.split()[0]
                    tools.add(tool)

            missing = []
            for tool in tools:
                if not shutil.which(tool):
                    missing.append(tool)

            assert not missing, f"Missing required tools: {missing}"

class TestMakefileQuality:
    """Test Makefile quality and best practices."""

    @pytest.fixture
    def makefile_content(self, makefile_path: Path) -> str:
        """Get Makefile content."""
        return makefile_path.read_text()

    def test_pretty_includes_formatters(self, makefile_content: str):
        """Pretty target should include code formatting."""
        formatters = ['black', 'ruff format', 'prettier']
        has_formatter = any(fmt in makefile_content for fmt in formatters)
        assert has_formatter, "Pretty target should include a code formatter"

    def test_clean_target_safety(self, makefile_content: str):
        """Clean target should use safe deletion patterns."""
        # Should use -f flag or check existence
        dangerous_patterns = ['rm -rf', 'del /q']
        lines = makefile_content.split('\n')

        clean_section = False
        for i, line in enumerate(lines):
            if line.strip().startswith('clean:'):
                clean_section = True
            elif clean_section and line.strip().startswith('#'):
                break
            elif clean_section and line.strip():
                # Check for unsafe deletion
                if any(pattern in line for pattern in dangerous_patterns):
                    # Should have safety measures
                    assert '-f' in line or '2>/dev/null' in line, f"Unsafe deletion: {line}"

    def test_consistent_error_handling(self, makefile_content: str):
        """Targets should have consistent error handling."""
        error_patterns = ['|| {', '&&', 'set -e']
        has_error_handling = any(pattern in makefile_content for pattern in error_patterns)

        # Not required but recommended
        if not has_error_handling:
            pytest.skip("No explicit error handling found (optional)")
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/makefile-validation.yml
name: Makefile Validation

on: [push, pull_request]

jobs:
  validate-makefiles:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        plugin: [abstract, conjure, conserve, imbue, sanctum]

    steps:
    - uses: actions/checkout@v3

    - name: Validate Makefile structure
      run: |
        cd plugins/${{ matrix.plugin }}

        # Check help target
        make -n help

        # Validate documentation
        python3 -c "
import subprocess
import re

# Get all targets
result = subprocess.run(['make', '-p'], capture_output=True, text=True)
targets = re.findall(r'^([a-zA-Z0-9_-]+):', result.stdout, re.MULTILINE)

# Check documentation
with open('Makefile') as f:
    content = f.read()

documented = re.findall(r'^([a-zA-Z0-9_-]+):.*?##', content, re.MULTILINE)
undocumented = set(targets) - set(documented)

if undocumented:
    print(f'Undocumented targets: {undocumented}')
    exit(1)

print('All targets documented [OK]')
"

        # Test risky targets in dry-run
        for target in clean install deps-update; do
            if grep -q "^$target:" Makefile; then
                echo "Testing $target in dry-run mode..."
                make -n $target
            fi
        done

        echo "Makefile validation passed for ${{ matrix.plugin }}"
```

## Utility Functions

### Command Preview Mode

```python
def preview_makefile_execution(makefile_path: Path, target: str) -> list[str]:
    """Get list of commands that would be executed."""
    result = subprocess.run(
        ['make', '-n', '-f', str(makefile_path), target],
        capture_output=True,
        text=True,
        cwd=makefile_path.parent
    )
    return [line.strip() for line in result.stdout.split('\n') if line.strip()]
```

### Safe Command Substitution

```python
import shlex
import re

def make_safe_preview(command: str) -> str:
    """Replace dangerous commands with safe previews."""
    dangerous_patterns = {
        r'rm\s+-rf': 'echo "Would remove: "',
        r'mkdir\s+-p': 'echo "Would create directory: "',
        r'touch\s+': 'echo "Would create file: "',
        r'pip\s+install': 'echo "Would install: "',
        r'curl\s+': 'echo "Would download from: "',
    }

    for pattern, replacement in dangerous_patterns.items():
        command = re.sub(pattern, replacement, command)
    return command
```

### Target Safety Check

```python
RISKY_PATTERNS = [
    r'rm\s+', r'del\s+', r'move\s+', r'copy\s+',
    r'pip\s+install', r'npm\s+install', r'cargo\s+install',
    r'git\s+(commit|push|pull)', r'docker\s+(build|run)',
    r'mkdir\s+-p', r'touch\s+'
]

def has_risky_commands(makefile_path: Path, target: str) -> bool:
    """Check if target executes risky commands."""
    commands = preview_makefile_execution(makefile_path, target)
    for command in commands:
        for pattern in RISKY_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return True
    return False
```

### Documentation Coverage Check

```python
def check_target_documentation(makefile_path: Path) -> dict:
    """Check which targets have help comments."""
    with open(makefile_path) as f:
        content = f.read()

    # Extract all targets
    targets = re.findall(r'^([a-zA-Z0-9_-]+):', content, re.MULTILINE)

    # Extract documented targets (with ## comments)
    documented = re.findall(r'^([a-zA-Z0-9_-]+):.*?##\s*(.+)$', content, re.MULTILINE)

    undocumented = set(targets) - set(doc[0] for doc in documented)

    return {
        'total_targets': len(targets),
        'documented_targets': len(documented),
        'undocumented_targets': list(undocumented),
        'coverage_ratio': len(documented) / len(targets) if targets else 0
    }
```
