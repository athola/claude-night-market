"""Shared sys.path setup for tests importing leyline hook modules.

Hook scripts live in ``hooks/`` (outside ``src/``) and are imported by
module name in tests, so this conftest exposes ``hooks/`` on sys.path for
tests in this directory before they import a hook module at the top of
the file.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
sys.path.insert(0, str(_HOOKS_DIR))
