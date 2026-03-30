#!/usr/bin/env python3
"""Deferred Capture - pensive plugin wrapper.

Delegates to the shared leyline deferred_capture module with
pensive-specific labels and context enrichment.
"""

from __future__ import annotations

import sys
from pathlib import Path

_LEYLINE_SRC = Path(__file__).resolve().parents[2] / "leyline" / "src"
sys.path.insert(0, str(_LEYLINE_SRC))

try:
    from leyline.deferred_capture import (
        PluginConfig,
        run_capture,
    )
except ImportError:
    print(
        "ERROR: leyline not found. Install leyline for deferred capture support.",
        file=sys.stderr,
    )
    sys.exit(1)


def _enrich(source: str, context: str) -> str:
    if source == "review":
        return f"{context}\n\nNote: this label applies to code/PR review findings."
    return context


CONFIG = PluginConfig(
    plugin_name="pensive",
    label_colors={
        "deferred": "#7B61FF",
        "review": "#0E8A16",
    },
    enrich_context=_enrich,
    source_help="Origin skill (e.g. review)",
)

if __name__ == "__main__":
    sys.exit(run_capture(CONFIG))
