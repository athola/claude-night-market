"""Entry point: ``python -m pensive.harden``."""

from __future__ import annotations

import sys

from .cli import run_cli

if __name__ == "__main__":
    sys.exit(run_cli())
