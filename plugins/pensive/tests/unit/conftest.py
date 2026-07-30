"""Shared sys.path setup for tests/unit.

Some hook tests import modules that live outside the ``pensive`` package
(the plugin's own ``hooks/`` directory and the sibling ``gauntlet`` plugin's
``src/`` tree). Performing the path insertion here, before pytest collects
any test module, lets those modules be imported at the top of a test file
instead of after runtime path setup.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
_GAUNTLET_SRC = Path(__file__).resolve().parents[3] / "gauntlet" / "src"
sys.path.insert(0, str(_HOOKS_DIR))
sys.path.insert(0, str(_GAUNTLET_SRC))
