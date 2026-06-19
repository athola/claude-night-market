"""Directory walker for the harden detector pipeline.

Walks a directory, applies the Python detectors to every ``*.py``
file, and returns the combined finding list. Skips conventional
vendored / generated paths so the report focuses on owned code.
"""

from __future__ import annotations

from pathlib import Path

from .detectors_python import scan_path
from .types import Finding

# Path components that mark code we do not own / do not want to flag.
# A path is skipped if any component matches one of these names.
_SKIP_COMPONENTS = frozenset(
    {
        "node_modules",
        "vendor",
        "dist",
        "build",
        ".venv",
        "venv",
        ".tox",
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        ".uv-cache",  # uv's local package cache
        "site-packages",
        ".eggs",
        "target",  # Rust build output
        ".cargo",  # Rust toolchain cache
    }
)


def _should_skip(path: Path) -> bool:
    return any(part in _SKIP_COMPONENTS for part in path.parts)


def scan_directory(root: Path) -> list[Finding]:
    """Recursively scan ``root`` for Python sources; return all findings."""
    root = Path(root)
    findings: list[Finding] = []
    for py_file in sorted(root.rglob("*.py")):
        if _should_skip(py_file):
            continue
        try:
            findings.extend(scan_path(py_file))
        except OSError as exc:
            # Unreadable file: an unscanned file is invisible to
            # --strict (which fires on HIGH+), so a permission-denied
            # path could hide a real finding. Surface it as an ADVISORY
            # (issue #575, B2) reusing the PYSX shape so the operator
            # sees the gap instead of a silent drop.
            findings.append(
                Finding(
                    id="PYSX",
                    severity="ADVISORY",
                    citation=None,
                    file=str(py_file),
                    line=0,
                    detection_signal=f"could not read file: {exc}",
                    proposal=None,
                )
            )
            continue
    return findings
