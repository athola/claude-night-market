#!/usr/bin/env python3
"""Deferred Capture - egregore plugin wrapper.

Delegates to the shared leyline deferred_capture module with
egregore-specific labels and context enrichment.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_LEYLINE_SRC = Path(__file__).resolve().parents[2] / "leyline" / "src"
sys.path.insert(0, str(_LEYLINE_SRC))

try:
    from leyline.deferred_capture import (  # type: ignore[import-not-found]  # noqa: E402
        PluginConfig,
        run_capture,
    )
except ImportError:
    print(
        "ERROR: leyline plugin not found. Install leyline for deferred capture support.",
        file=sys.stderr,
    )
    sys.exit(1)


def _enrich(_source: str, context: str) -> str:
    step = os.environ.get("EGREGORE_STEP", "")
    if step:
        return f"{context}\n\nEgregore pipeline step: {step}"
    return context


CONFIG = PluginConfig(
    plugin_name="egregore",
    label_colors={
        "deferred": "#7B61FF",
        "egregore": "#5319E7",
    },
    enrich_context=_enrich,
    source_help="Origin skill (e.g. egregore)",
)

if __name__ == "__main__":
    sys.exit(run_capture(CONFIG))
