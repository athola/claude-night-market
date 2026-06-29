"""Shared test factory functions for tome plugin.

Import ``make_finding`` from here in any test module::

    from tests.factories import make_finding
"""

from __future__ import annotations

from typing import Any

from tome.models import Finding


def make_finding(relevance: float = 0.5, **overrides: Any) -> Finding:
    """Build a Finding for tests with sensible defaults.

    Covers both ranker-style calls (relevance + metadata) and
    merger-style calls (url + relevance). ``relevance`` stays positional
    because call sites pass it positionally; all other fields are keyword
    overrides merged over the defaults below.
    """
    fields: dict[str, Any] = {
        "source": "github",
        "channel": "code",
        "title": "Test Finding",
        "url": "https://example.com/f",
        "relevance": relevance,
        "summary": "A summary.",
        "metadata": {},
    }
    fields.update(overrides)
    return Finding(**fields)
