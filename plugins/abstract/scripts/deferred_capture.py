#!/usr/bin/env python3
"""Deferred Capture - abstract plugin wrapper.

Delegates to the shared leyline deferred_capture module with
abstract-specific labels and context enrichment.
"""

from __future__ import annotations

import sys
from pathlib import Path

_LEYLINE_SRC = Path(__file__).resolve().parents[2] / "leyline" / "src"
sys.path.insert(0, str(_LEYLINE_SRC))

from leyline.deferred_capture import (  # type: ignore[import-not-found]  # noqa: E402
    PluginConfig,
    run_capture,
)


def _enrich(source: str, context: str) -> str:
    if source == "regression":
        return f"{context}\n\nNote: this label applies to skill regression detection."
    return context


CONFIG = PluginConfig(
    plugin_name="abstract",
    label_colors={
        "deferred": "#7B61FF",
        "regression": "#D73A4A",
    },
    enrich_context=_enrich,
    source_help="Origin skill (e.g. regression)",
)

if __name__ == "__main__":
    sys.exit(run_capture(CONFIG))
