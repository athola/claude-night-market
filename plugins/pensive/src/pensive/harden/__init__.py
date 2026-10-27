"""Active security hardening: Python detector MVP.

This package backs the /harden command. The `pensive:harden` skill
documents the contract; this module implements a starter set of
AST-based detectors that emit Findings the skill can render into
its report.

Public API:

- ``Finding``, ``Severity``, ``Citation`` from ``.types``
- ``scan_source(source, *, file=...)`` and ``scan_path(path)`` from
  ``.detectors_python``
- ``scan_directory(path)`` from ``.scanner``
- ``run_cli(argv)`` from ``.cli`` (also wired as
  ``python -m pensive.harden``)
"""

from __future__ import annotations

from .cli import run_cli
from .detectors_python import scan_path, scan_source
from .scanner import scan_directory
from .types import Citation, Finding, Severity

__all__ = [
    "Citation",
    "Finding",
    "Severity",
    "run_cli",
    "scan_directory",
    "scan_path",
    "scan_source",
]
