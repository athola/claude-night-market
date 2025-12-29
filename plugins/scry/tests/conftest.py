"""Pytest configuration for scry plugin tests."""

import shutil
import subprocess
from pathlib import Path

import pytest

# Plugin root directory
PLUGIN_ROOT = Path(__file__).parent.parent


@pytest.fixture
def plugin_root() -> Path:
    """Return the plugin root directory."""
    return PLUGIN_ROOT


@pytest.fixture
def skills_dir(plugin_root: Path) -> Path:
    """Return the skills directory."""
    return plugin_root / "skills"


@pytest.fixture
def commands_dir(plugin_root: Path) -> Path:
    """Return the commands directory."""
    return plugin_root / "commands"


@pytest.fixture
def scripts_dir(plugin_root: Path) -> Path:
    """Return the scripts directory."""
    return plugin_root / "scripts"


@pytest.fixture
def has_ffmpeg() -> bool:
    """Check if ffmpeg is available."""
    return shutil.which("ffmpeg") is not None


@pytest.fixture
def has_vhs() -> bool:
    """Check if vhs is available."""
    return shutil.which("vhs") is not None


@pytest.fixture
def has_playwright() -> bool:
    """Check if playwright is available."""
    try:
        result = subprocess.run(
            ["npx", "playwright", "--version"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        # npx or playwright took too long to respond
        return False
    except FileNotFoundError:
        # npx command not found (Node.js not installed)
        return False
    except OSError as e:
        # Other OS-level errors (permissions, etc.)
        import warnings

        warnings.warn(f"Playwright check failed with OSError: {e}", stacklevel=2)
        return False
