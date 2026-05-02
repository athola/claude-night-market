"""Standard envelope shape for CLI scripts that emit JSON results.

Plugin scripts (test_generator, quality_checker, safe_replacer)
wrap their results in ``{"success": bool, ...}`` envelopes so
downstream tooling can detect success without parsing prose.
This module exposes that contract so future scripts cannot drift
on key names, ordering, or shape (D-13).
"""

from __future__ import annotations

from typing import Any


def success_envelope(data: Any) -> dict[str, Any]:
    """Wrap a successful CLI result for JSON emission.

    Returns ``{"success": True, "data": data}``.
    """
    return {"success": True, "data": data}


def error_envelope(message: str) -> dict[str, Any]:
    """Wrap a CLI error message for JSON emission.

    Returns ``{"success": False, "error": message}``.
    """
    return {"success": False, "error": message}
