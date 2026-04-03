"""Skrills binary fallback for Python hooks and scripts.

Usage in hooks:
    from skrills_fallback import try_skrills

    result = try_skrills(["validate", "--skill-dir", "./plugins"])
    if result is not None:
        # skrills handled it; result is CompletedProcess
        sys.exit(result.returncode)
    else:
        # Fall back to Python implementation
        ...
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def find_skrills() -> str | None:
    """Find skrills binary. Returns path or None."""
    # 1. Plugin bin/ directory (v2.1.91+ makes this available)
    plugin_bin = Path(__file__).parent / "skrills"
    if plugin_bin.is_file() and os.access(plugin_bin, os.X_OK):
        return str(plugin_bin)

    # 2. PATH lookup
    found = shutil.which("skrills")
    if found:
        return found

    return None


def try_skrills(
    args: list[str],
    timeout: int = 10,
    capture: bool = True,
) -> subprocess.CompletedProcess | None:
    """Try running skrills with given args. Returns None if not available."""
    binary = find_skrills()
    if binary is None:
        return None

    try:
        return subprocess.run(
            [binary, *args],
            capture_output=capture,
            text=True,
            timeout=timeout,
        )
    except (FileNotFoundError, PermissionError, subprocess.TimeoutExpired):
        return None
