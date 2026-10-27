#!/usr/bin/env python3
"""Deferred Capture - imbue plugin wrapper.

Delegates to the shared leyline deferred_capture module with
imbue-specific labels and context enrichment.
"""

from __future__ import annotations

import sys
from pathlib import Path

# The repo keeps plugins side by side, the install cache nests them by
# version: resolve leyline in either, falling back to the repo path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _vendored_leyline_sibling_plugins import (  # type: ignore[import-not-found]  # noqa: E402 - scripts dir on sys.path
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
