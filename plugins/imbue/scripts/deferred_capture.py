#!/usr/bin/env python3
"""Deferred Capture - imbue plugin wrapper.

Delegates to the shared leyline deferred_capture module with
imbue-specific labels and context enrichment.
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
    if source == "scope-guard":
        return f"{context}\n\nNote: worthiness scoring applies to this item."
    return context


CONFIG = PluginConfig(
    plugin_name="imbue",
    label_colors={
        "deferred": "#7B61FF",
        "scope-guard": "#FBCA04",
        "feature-review": "#F9A825",
    },
    enrich_context=_enrich,
    source_help="Origin skill (e.g. scope-guard, feature-review)",
)

if __name__ == "__main__":
    sys.exit(run_capture(CONFIG))
