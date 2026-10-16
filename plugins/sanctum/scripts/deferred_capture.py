#!/usr/bin/env python3
"""Deferred Capture - sanctum plugin (reference implementation).

Delegates to the shared leyline deferred_capture module with
the full label taxonomy.

Usage:
    python deferred_capture.py --title TITLE --source SOURCE
                               --context CONTEXT [options]
"""

from __future__ import annotations

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

CONFIG = PluginConfig(
    plugin_name="sanctum",
    label_colors={
        "deferred": "#7B61FF",
        "war-room": "#B60205",
        "brainstorm": "#1D76DB",
        "scope-guard": "#FBCA04",
        "feature-review": "#F9A825",
        "review": "#0E8A16",
        "regression": "#D73A4A",
        "egregore": "#5319E7",
    },
    source_help="Origin skill (e.g. war-room, brainstorm)",
)

if __name__ == "__main__":
    sys.exit(run_capture(CONFIG))
