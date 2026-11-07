"""The error tome raises when memory-palace's graph backend is absent.

memory-palace is a declared runtime dependency of tome's graph features.
The rest of tome runs without it, and a feature that needs the backend
raises this rather than degrading to a silent no-op.
"""

from __future__ import annotations


class GraphBackendUnavailable(RuntimeError):
    """Raised when no knowledge-graph backend can be loaded."""
