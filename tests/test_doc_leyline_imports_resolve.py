"""Every ``from leyline... import`` shown in a tracked doc must import.

leyline is the library other plugins are told to build on, and its skills
taught imports of modules that never existed (``leyline.auth``,
``leyline.usage_logger``). A reader who copies one fails at import time.
"""

from __future__ import annotations

import importlib
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
IMPORT_LINE = re.compile(r"^\s*from (leyline(?:\.\w+)*) import ([\w, ()]+)")


def _unresolved() -> list[str]:
    sys.path.insert(0, str(REPO_ROOT / "plugins" / "leyline" / "src"))
    docs = subprocess.run(
        ["git", "ls-files", "*.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert docs, "git ls-files found no markdown; the sweep would pass vacuously"
    problems = []
    for doc in docs:
        text = (REPO_ROOT / doc).read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), 1):
            match = IMPORT_LINE.match(line)
            if not match:
                continue
            names = [n.strip(" ()") for n in match.group(2).split(",")]
            try:
                module = importlib.import_module(match.group(1))
            except ModuleNotFoundError:
                problems.append(f"{doc}:{number}: no module {match.group(1)}")
                continue
            missing = [n for n in names if n and not hasattr(module, n)]
            if missing:
                problems.append(f"{doc}:{number}: {match.group(1)} lacks {missing}")
    return problems


def test_every_documented_leyline_import_resolves() -> None:
    assert _unresolved() == []
