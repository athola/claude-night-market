"""Shared sys.path setup for tests importing leyline's local ``src`` package.

pytest's ``pythonpath`` setting in pyproject.toml already exposes ``src/``
when running the full suite, but tests in this directory historically
inserted the path themselves before importing ``leyline.*`` modules. This
conftest centralizes that setup so individual test files can import
``leyline`` at the top of the file without triggering E402.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[3] / "src"
sys.path.insert(0, str(_SRC))
