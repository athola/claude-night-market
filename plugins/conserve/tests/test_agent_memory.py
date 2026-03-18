"""Tests for three-tier agent memory and session routing.

Tests hot/warm/cold memory management, triage protocol,
and session routing decisions.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from scripts.agent_memory import (
    MemoryManager,
    RoutingDecision,
    decide_session_routing,
)

# --------------- memory tiers ---------------


class TestMemoryTiers:
    """Feature: Three-tier agent memory hierarchy.

    As a long-running agent
    I want tiered memory (hot/warm/cold)
    So that my context stays lean and prioritized.
    """

    @pytest.mark.unit
    def test_init_creates_directory_structure(self, tmp_path: Path) -> None:
        """Given an agent directory, init creates memory tiers."""
        mm = MemoryManager(tmp_path / "agent-x")
        mm.init()

        assert (tmp_path / "agent-x" / "memory.md").exists()
        assert (tmp_path / "agent-x" / "topics").is_dir()
        assert (tmp_path / "agent-x" / "archive").is_dir()

    @pytest.mark.unit
    def test_hot_tier_line_count(self, tmp_path: Path) -> None:
        """Given a hot-tier file, report its line count."""
        mm = MemoryManager(tmp_path / "agent-x")
        mm.init()
        hot = tmp_path / "agent-x" / "memory.md"
        hot.write_text("line1\nline2\nline3\n")
        assert mm.hot_tier_line_count() == 3

    @pytest.mark.unit
    def test_hot_tier_over_limit(self, tmp_path: Path) -> None:
        """Given hot tier over 200 lines, flag as over limit."""
        mm = MemoryManager(tmp_path / "agent-x")
        mm.init()
        hot = tmp_path / "agent-x" / "memory.md"
        hot.write_text("\n".join(f"line {i}" for i in range(250)))
        assert mm.is_hot_tier_over_limit() is True

    @pytest.mark.unit
    def test_hot_tier_under_limit(self, tmp_path: Path) -> None:
        """Given hot tier under 200 lines, not over limit."""
        mm = MemoryManager(tmp_path / "agent-x")
        mm.init()
        hot = tmp_path / "agent-x" / "memory.md"
        hot.write_text("short content\n")
        assert mm.is_hot_tier_over_limit() is False

    @pytest.mark.unit
    def test_add_warm_topic(self, tmp_path: Path) -> None:
        """Given a topic, write it to the warm tier."""
        mm = MemoryManager(tmp_path / "agent-x")
        mm.init()
        mm.write_warm_topic("validation-patterns", "Content about validation.")
        topic = tmp_path / "agent-x" / "topics" / "validation-patterns.md"
        assert topic.exists()
        assert "Content about validation" in topic.read_text()

    @pytest.mark.unit
    def test_archive_to_cold(self, tmp_path: Path) -> None:
        """Given content, archive it to the cold tier."""
        mm = MemoryManager(tmp_path / "agent-x")
        mm.init()
        mm.archive_to_cold("2026-03", "Historical summary for March.")
        archive = tmp_path / "agent-x" / "archive" / "2026-03.md"
        assert archive.exists()
        assert "Historical summary" in archive.read_text()

    @pytest.mark.unit
    def test_list_warm_topics(self, tmp_path: Path) -> None:
        """Given multiple warm topics, list them."""
        mm = MemoryManager(tmp_path / "agent-x")
        mm.init()
        mm.write_warm_topic("a-topic", "Content A")
        mm.write_warm_topic("b-topic", "Content B")
        topics = mm.list_warm_topics()
        assert "a-topic" in topics
        assert "b-topic" in topics


# --------------- session routing ---------------


class TestSessionRouting:
    """Feature: Route work to subagents or dedicated sessions.

    As a coordinator
    I want complexity-based routing
    So that simple work uses subagents and complex work
    uses dedicated sessions.
    """

    @pytest.mark.unit
    def test_simple_task_routes_to_subagent(self) -> None:
        """Given 2 files in 1 area, route to subagent."""
        decision = decide_session_routing(
            files=["plugins/imbue/a.py", "plugins/imbue/b.py"],
            areas=["plugins/imbue"],
        )
        assert decision == RoutingDecision.SUBAGENT

    @pytest.mark.unit
    def test_complex_task_routes_to_dedicated(self) -> None:
        """Given files in 4+ areas, route to dedicated sessions."""
        decision = decide_session_routing(
            files=[
                "plugins/imbue/a.py",
                "plugins/conserve/b.py",
                "plugins/pensive/c.py",
                "plugins/sanctum/d.py",
            ],
            areas=[
                "plugins/imbue",
                "plugins/conserve",
                "plugins/pensive",
                "plugins/sanctum",
            ],
        )
        assert decision == RoutingDecision.DEDICATED_SESSION

    @pytest.mark.unit
    def test_medium_task_routes_to_subagent(self) -> None:
        """Given 3 areas, still routes to subagent (threshold is 4)."""
        decision = decide_session_routing(
            files=["a.py", "b.py", "c.py"],
            areas=["plugins/a", "plugins/b", "plugins/c"],
        )
        assert decision == RoutingDecision.SUBAGENT

    @pytest.mark.unit
    def test_codebase_wide_routes_to_sequential(self) -> None:
        """Given codebase_wide flag, route to sequential."""
        decision = decide_session_routing(
            files=[],
            areas=[],
            codebase_wide=True,
        )
        assert decision == RoutingDecision.SEQUENTIAL
