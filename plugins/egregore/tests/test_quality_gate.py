"""Tests for quality gate orchestration logic."""

from __future__ import annotations

from pathlib import Path

from conventions import (
    Convention,
    Finding,
)

# ── Step routing tests ──────────────────────────────────


class TestConventionsForStep:
    """Feature: Convention filtering by pipeline step

    As the egregore orchestrator
    I want conventions filtered to the current step
    So that only relevant checks run at each stage
    """


# ── Verdict calculation tests ───────────────────────────


class TestCalculateVerdict:
    """Feature: Review verdict calculation

    As the egregore orchestrator
    I want clear verdicts from quality checks
    So that pipeline flow is deterministic
    """


# ── Quality config filtering tests ──────────────────────


class TestFilterSteps:
    """Feature: Per-work-item quality configuration

    As the egregore orchestrator
    I want to skip or select quality steps per work item
    So that the pipeline is configurable
    """

    ALL_STEPS = [
        "code-review",
        "unbloat",
        "code-refinement",
        "update-tests",
        "update-docs",
    ]


# ── Helpers ─────────────────────────────────────────────


def _make_conventions(ids: list[str]) -> list[Convention]:
    """Create minimal Convention objects for testing."""
    return [
        Convention(
            id=cid,
            name=f"conv-{cid}",
            description="test",
            check_type="grep",
            severity="blocking",
            enabled=True,
        )
        for cid in ids
    ]


def _make_finding(
    convention_id: str,
    severity: str = "blocking",
) -> Finding:
    """Create a minimal Finding for testing."""
    return Finding(
        convention_id=convention_id,
        convention_name=f"conv-{convention_id}",
        file=Path("test.py"),
        line=1,
        message="test finding",
        severity=severity,
    )
