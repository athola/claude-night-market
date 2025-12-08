#!/usr/bin/env python3
"""Test that all executable scripts have proper permissions (0755)."""

import os
import stat
from pathlib import Path

import pytest


def find_executable_scripts(root_dir: Path) -> list[Path]:
    """Find all executable Python scripts in the repository.

    Only includes files that have shebang lines (#!/usr/bin/env python3 or similar),
    indicating they are meant to be executed directly.

    Args:
        root_dir: Root directory to search

    Returns:
        List of paths to executable scripts

    """
    executable_scripts = []

    # Only check actual script directories, not library code
    script_patterns = [
        "scripts/*.py",
        "**/scripts/*.py",
        "**/tools/*",
        # Skip src/ - library modules shouldn't be executable even if they have shebangs
    ]

    for pattern in script_patterns:
        for file_path in root_dir.glob(pattern):
            # Skip hidden files and directories
            if any(part.startswith('.') for part in file_path.parts):
                continue

            # Skip .venv, test files, docs, and examples
            skip_patterns = ['.venv', 'test', 'docs/', 'examples/']
            if any(pattern in str(file_path) for pattern in skip_patterns):
                continue

            # Skip skill subdirectories since they have their own tooling
            if 'skills/' in str(file_path) and '/scripts/' not in str(file_path):
                continue

            # Only include files with shebang lines (meant to be executed directly)
            if file_path.is_file() and _has_shebang(file_path):
                executable_scripts.append(file_path)

    return executable_scripts


def _has_shebang(file_path: Path) -> bool:
    """Check if a file has a shebang line indicating it's meant to be executable.

    Args:
        file_path: Path to the file to check

    Returns:
        True if the file has a shebang line, False otherwise

    """
    try:
        with open(file_path, encoding='utf-8') as f:
            first_line = f.readline().strip()
            return first_line.startswith('#!') and 'python' in first_line.lower()
    except (UnicodeDecodeError, PermissionError, OSError):
        return False


def check_script_permissions(script_path: Path) -> bool:
    """Check if a script has proper permissions (0755).

    Args:
        script_path: Path to the script

    Returns:
        True if permissions are correct, False otherwise

    """
    st = os.stat(script_path)
    mode = stat.S_IMODE(st.st_mode)

    # Check for 0755 permissions (owner: rwx, group: r-x, other: r-x)
    expected_mode = 0o755
    return mode == expected_mode


def fix_script_permissions(script_path: Path) -> None:
    """Fix script permissions to 0755.

    Args:
        script_path: Path to the script

    """
    os.chmod(script_path, 0o755)  # noqa: S103


class TestScriptPermissions:
    """Test suite for script permissions."""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Get the repository root directory."""
        return Path(__file__).parent.parent

    @pytest.fixture
    def executable_scripts(self, repo_root: Path) -> list[Path]:
        """Get all executable scripts in the repository."""
        return find_executable_scripts(repo_root)

    def test_all_executables_have_shebang(self, executable_scripts: list[Path]) -> None:
        """Test that all executable scripts have proper shebang."""
        for script in executable_scripts:
            if script.suffix == '.py':
                with open(script, 'rb') as f:
                    first_line = f.readline().decode('utf-8', errors='ignore').strip()

                # Check for proper Python shebang
                assert first_line.startswith('#!'), f"{script}: Missing shebang"
                has_python = 'python' in first_line.lower()
                assert has_python, f"{script}: Invalid shebang: {first_line}"

    def test_executable_permissions(self, executable_scripts: list[Path]) -> None:
        """Test that all executable scripts have proper permissions (0755)."""
        permission_errors = []

        for script in executable_scripts:
            if not check_script_permissions(script):
                st = os.stat(script)
                mode = stat.S_IMODE(st.st_mode)
                permission_errors.append(
                    f"{script}: Invalid permissions {oct(mode)} (expected 0755)"
                )

        if permission_errors:
            # Provide helpful error message with fix command
            error_msg = "Found scripts with incorrect permissions:\n\n"
            error_msg += "\n".join(permission_errors)
            error_msg += "\n\nTo fix these permissions, run:\n"
            error_msg += "chmod 0755 " + " ".join(str(s) for s in executable_scripts)

            pytest.fail(error_msg)

    def test_tools_directory_permissions(self, repo_root: Path) -> None:
        """Test that tools in skills directories are executable."""
        tools_dir = repo_root / "skills" / "modular-skills" / "tools"

        if tools_dir.exists():
            for tool_path in tools_dir.iterdir():
                if tool_path.is_file() and not tool_path.name.startswith('.'):
                    is_exec = os.access(tool_path, os.X_OK)
                    assert is_exec, f"Tool not executable: {tool_path}"


if __name__ == "__main__":
    # Run tests directly for debugging
    import sys

    repo_root = Path(__file__).parent.parent
    scripts = find_executable_scripts(repo_root)

    print(f"Found {len(scripts)} executable scripts:")
    for script in sorted(scripts):
        print(f"  {script}")
        permissions_ok = check_script_permissions(script)
        status = "✓" if permissions_ok else "✗"
        print(f"    Permissions: {status}")

    # Fix permissions if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        print("\nFixing permissions...")
        for script in scripts:
            fix_script_permissions(script)
            print(f"  Fixed: {script}")
        print("\nDone!")
