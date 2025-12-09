#!/usr/bin/env python3
"""Entry point for the Minister project tracker CLI."""

from __future__ import annotations

import sys
from pathlib import Path


def _bootstrap_path() -> None:
    plugin_root = Path(__file__).resolve().parent.parent
    src_path = plugin_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


_bootstrap_path()

from minister.project_tracker import (  # noqa: E402
    run_cli,
)

if __name__ == "__main__":
    raise SystemExit(run_cli())
