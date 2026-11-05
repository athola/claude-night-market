"""The modules the homeostatic hook imports must load without PyYAML.

The hook runs under the operator's bare python3. It imports these inside
a try/except ImportError, so a yaml import anywhere in their chain did
not crash: it switched the improvement trend and memory off with no sign.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
BLOCK_YAML = (
    "import sys\n"
    "class _Block:\n"
    "    def find_spec(self, name, path=None, target=None):\n"
    "        if name == 'yaml' or name.startswith('yaml.'):\n"
    "            raise ImportError('yaml blocked')\n"
    "sys.meta_path.insert(0, _Block())\n"
    f"sys.path.insert(0, {str(SRC)!r})\n"
)


@pytest.mark.parametrize(
    "module",
    [
        "abstract.improvement_queue",
        "abstract.improvement_memory",
        "abstract.performance_tracker",
    ],
)
def test_module_imports_with_yaml_blocked(module: str) -> None:
    result = subprocess.run(
        [sys.executable, "-c", BLOCK_YAML + f"import {module}\n"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
