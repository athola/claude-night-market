"""CLI entrypoint for ``python -m context_scanner``."""

from __future__ import annotations

import sys

from .cli import main

sys.exit(main())
