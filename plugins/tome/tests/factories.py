"""Shared test factory functions for tome plugin.

Import ``make_finding`` from here in any test module::

    from tests.factories import make_finding
"""

from __future__ import annotations

from typing import Any

from tome.models import Finding


def make_finding(
    relevance: float = 0.5,
    source: str = "github",
    channel: str = "code",
    metadata: dict[str, Any] | None = None,
    url: str = "https://example.com/f",
    title: str = "Test Finding",
    summary: str = "A summary.",
) -> Finding:
    """Build a Finding for tests with sensible defaults.

    Covers both ranker-style calls (relevance + metadata) and
    merger-style calls (url + relevance).
    """
    return Finding(
        source=source,
        channel=channel,
        title=title,
        url=url,
        relevance=relevance,
        summary=summary,
        metadata=metadata or {},
    )
