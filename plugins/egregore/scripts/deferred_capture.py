#!/usr/bin/env python3
"""Deferred Capture - egregore plugin wrapper.

Delegates to the shared leyline deferred_capture module with
egregore-specific labels and context enrichment.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# The repo keeps plugins side by side, the install cache nests them by
# version: resolve leyline in either, falling back to the repo path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _vendored_leyline_sibling_plugins import (  # noqa: E402 - after sys.path setup
    add_sibling_src_to_path,
)

add_sibling_src_to_path(__file__, "leyline")

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
