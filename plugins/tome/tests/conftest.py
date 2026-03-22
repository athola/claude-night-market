"""Shared test fixtures for tome plugin."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from tome.models import (
    DomainClassification,
    Finding,
    ResearchSession,
)


@pytest.fixture
def tmp_session_dir(tmp_path: Path) -> Path:
    """Create a temporary .tome/sessions directory."""
    session_dir = tmp_path / ".tome" / "sessions"
    session_dir.mkdir(parents=True)
    return session_dir


@pytest.fixture
def sample_finding() -> Finding:
    """A single code-channel finding."""
    return Finding(
        source="github",
        channel="code",
        title="example/async-patterns",
        url="https://github.com/example/async-patterns",
        relevance=0.85,
        summary="Async patterns library with 1.2k stars",
        metadata={"stars": 1200, "language": "Python"},
    )


@pytest.fixture
def sample_findings() -> list[Finding]:
    """Mixed findings from multiple channels."""
    return [
        Finding(
            source="github",
            channel="code",
            title="example/async-patterns",
            url="https://github.com/example/async-patterns",
            relevance=0.85,
            summary="Async patterns library with 1.2k stars",
            metadata={"stars": 1200, "language": "Python"},
        ),
        Finding(
            source="hn",
            channel="discourse",
            title="Why async/await is better than callbacks",
            url="https://news.ycombinator.com/item?id=12345",
            relevance=0.72,
            summary="Discussion on async patterns, 200 points",
            metadata={"score": 200, "comments": 85},
        ),
        Finding(
            source="arxiv",
            channel="academic",
            title="A Survey of Asynchronous Programming Models",
            url="https://arxiv.org/abs/2301.12345",
            relevance=0.90,
            summary="Comprehensive survey of async models across languages",
            metadata={
                "authors": ["Smith, J.", "Doe, A."],
                "year": 2023,
                "citations": 45,
            },
        ),
    ]


@pytest.fixture
def sample_session(sample_findings: list[Finding]) -> ResearchSession:
    """A complete research session."""
    return ResearchSession(
        id="test-session-001",
        topic="async python patterns",
        domain="algorithm",
        triz_depth="medium",
        channels=["code", "discourse", "academic"],
        findings=sample_findings,
        status="complete",
        created_at=datetime(2026, 3, 20, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_classification() -> DomainClassification:
    """A domain classification result."""
    return DomainClassification(
        domain="algorithm",
        triz_depth="medium",
        channel_weights={"code": 0.3, "discourse": 0.3, "academic": 0.3, "triz": 0.1},
        confidence=0.82,
    )
