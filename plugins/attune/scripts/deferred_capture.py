#!/usr/bin/env python3
"""Deferred Capture - attune plugin wrapper.

Delegates to the shared leyline deferred_capture module with
attune-specific labels and context enrichment.
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


def _enrich(source: str, context: str) -> str:
    if source == "war-room":
        session_dir = os.environ.get("STRATEGEION_SESSION_DIR", "")
        if session_dir:
            return f"{context}\n\nStrategeion session: {session_dir}"
    return context


CONFIG = PluginConfig(
    plugin_name="attune",
    label_colors={
        "deferred": "#7B61FF",
        "war-room": "#B60205",
        "brainstorm": "#1D76DB",
    },
    enrich_context=_enrich,
    source_help="Origin skill (e.g. war-room, brainstorm)",
)

if __name__ == "__main__":
    sys.exit(run_capture(CONFIG))
