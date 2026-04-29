"""Tests for the skill_graph module.

Feature: Skill Graph Audit
    As a marketplace maintainer
    I want to inspect Skill() references across plugins
    So that I can detect hubs, orchestrators, isolates, and federations
    without manually maintaining docs/quality-gates.md.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from skill_graph import (  # noqa: E402 - import after sys.path mutation
    KNOWN_EXTERNAL_PLUGINS,
    SkillGraph,
    SkillNode,
    build_graph,
    classify_dangling_refs,
    detect_dangling_refs,
    detect_isolates,
    extract_skill_references,
    rank_hubs,
    rank_orchestrators,
)


class TestExtractSkillReferences:
    """Feature: Parse Skill() invocation references from skill markdown."""

    @pytest.mark.unit
    def test_extracts_qualified_reference(self, tmp_path: Path) -> None:
        """Scenario: Skill() with plugin:skill form is captured."""
        f = tmp_path / "SKILL.md"
        f.write_text(
            textwrap.dedent("""\
            ---
            name: example
            description: Example skill
            ---
            Use `Skill(scribe:slop-detector)` after writing prose.
            """)
        )

        refs = extract_skill_references(f)
        assert refs == {("scribe", "slop-detector")}

    @pytest.mark.unit
    def test_extracts_multiple_references(self, tmp_path: Path) -> None:
        """Scenario: Multiple references on different lines."""
        f = tmp_path / "SKILL.md"
        f.write_text(
            textwrap.dedent("""\
            ---
            name: orchestrator
            description: Orchestrator
            ---
            Run `Skill(imbue:proof-of-work)` to enforce evidence.
            Then `Skill(imbue:scope-guard)` for additive bias.
            And `Skill(scribe:slop-detector)` for prose hygiene.
            """)
        )

        refs = extract_skill_references(f)
        assert refs == {
            ("imbue", "proof-of-work"),
            ("imbue", "scope-guard"),
            ("scribe", "slop-detector"),
        }

    @pytest.mark.unit
    def test_ignores_unqualified_skill_calls(self, tmp_path: Path) -> None:
        """Scenario: Skill(name) without plugin: prefix is not counted as cross-plugin."""
        f = tmp_path / "SKILL.md"
        f.write_text(
            textwrap.dedent("""\
            ---
            name: example
            description: Example
            ---
            Use `Skill(some-name)` ambiguously.
            """)
        )

        refs = extract_skill_references(f)
        # Unqualified refs return None plugin component
        assert refs == {(None, "some-name")}

    @pytest.mark.unit
    def test_dedupes_within_file(self, tmp_path: Path) -> None:
        """Scenario: Same reference appearing multiple times counted once."""
        f = tmp_path / "SKILL.md"
        f.write_text(
            textwrap.dedent("""\
            ---
            name: example
            description: Example
            ---
            First `Skill(imbue:scope-guard)`.
            Second `Skill(imbue:scope-guard)` again.
            """)
        )

        refs = extract_skill_references(f)
        assert refs == {("imbue", "scope-guard")}


class TestBuildGraph:
    """Feature: Build directed graph from skill files in a marketplace tree."""

    @pytest.mark.unit
    def test_builds_nodes_for_each_skill(self, tmp_path: Path) -> None:
        """Scenario: Each SKILL.md becomes a node keyed by plugin:skill."""
        (tmp_path / "plugins" / "imbue" / "skills" / "scope-guard").mkdir(parents=True)
        (tmp_path / "plugins" / "scribe" / "skills" / "slop-detector").mkdir(
            parents=True
        )
        (
            tmp_path / "plugins" / "imbue" / "skills" / "scope-guard" / "SKILL.md"
        ).write_text("---\nname: scope-guard\ndescription: x\n---\nbody")
        (
            tmp_path / "plugins" / "scribe" / "skills" / "slop-detector" / "SKILL.md"
        ).write_text("---\nname: slop-detector\ndescription: x\n---\nbody")

        graph = build_graph(tmp_path / "plugins")
        assert "imbue:scope-guard" in graph.nodes
        assert "scribe:slop-detector" in graph.nodes
        assert graph.nodes["imbue:scope-guard"].plugin == "imbue"
        assert graph.nodes["imbue:scope-guard"].name == "scope-guard"

    @pytest.mark.unit
    def test_excludes_non_skill_markdown_at_other_depths(self, tmp_path: Path) -> None:
        """Scenario: Only files at plugins/<plugin>/skills/<name>/SKILL.md
        become nodes. Modular siblings, docs examples, and SKILL.md files at
        other depths must be ignored so the graph reflects real skills, not
        ancillary markdown that happens to share the SKILL.md filename or
        live near a skill.
        """
        skill_dir = tmp_path / "plugins" / "imbue" / "skills" / "scope-guard"
        skill_dir.mkdir(parents=True)
        # Real skill — should appear.
        (skill_dir / "SKILL.md").write_text(
            "---\nname: scope-guard\ndescription: x\n---\nbody"
        )
        # Modular sibling with Skill() refs — must NOT become a node.
        (skill_dir / "modules").mkdir()
        (skill_dir / "modules" / "extra.md").write_text(
            "---\nname: extra\ndescription: shared module\n---\n"
            "Mentions `Skill(scribe:slop-detector)` but is not itself a skill."
        )
        # Stray SKILL.md inside docs/ — wrong depth, must NOT become a node.
        docs_skill = tmp_path / "plugins" / "abstract" / "docs" / "examples" / "ignored"
        docs_skill.mkdir(parents=True)
        (docs_skill / "SKILL.md").write_text(
            "---\nname: ignored\ndescription: example only\n---\nbody"
        )
        # SKILL.md under plugins/<plugin>/scripts/ — wrong second segment.
        scripts_dir = tmp_path / "plugins" / "abstract" / "scripts" / "leak"
        scripts_dir.mkdir(parents=True)
        (scripts_dir / "SKILL.md").write_text(
            "---\nname: leak\ndescription: x\n---\nbody"
        )

        graph = build_graph(tmp_path / "plugins")

        assert "imbue:scope-guard" in graph.nodes
        assert "abstract:ignored" not in graph.nodes
        assert "abstract:leak" not in graph.nodes
        assert "imbue:extra" not in graph.nodes
        # Modular .md must not contribute edges either — extra.md mentions
        # scribe:slop-detector but slop-detector isn't even a defined node
        # here, and the edge must not exist regardless.
        assert ("imbue:extra", "scribe:slop-detector") not in graph.edges
        assert ("imbue:scope-guard", "scribe:slop-detector") not in graph.edges

    @pytest.mark.unit
    def test_builds_edges_from_skill_references(self, tmp_path: Path) -> None:
        """Scenario: Skill() references become directed edges."""
        (tmp_path / "plugins" / "imbue" / "skills" / "scope-guard").mkdir(parents=True)
        (tmp_path / "plugins" / "scribe" / "skills" / "slop-detector").mkdir(
            parents=True
        )
        (
            tmp_path / "plugins" / "imbue" / "skills" / "scope-guard" / "SKILL.md"
        ).write_text(
            "---\nname: scope-guard\ndescription: x\n---\nUse `Skill(scribe:slop-detector)`."
        )
        (
            tmp_path / "plugins" / "scribe" / "skills" / "slop-detector" / "SKILL.md"
        ).write_text("---\nname: slop-detector\ndescription: x\n---\nbody")

        graph = build_graph(tmp_path / "plugins")
        assert ("imbue:scope-guard", "scribe:slop-detector") in graph.edges


class TestRankings:
    """Feature: Surface hubs (high inbound) and orchestrators (high outbound)."""

    @pytest.mark.unit
    def test_rank_hubs_returns_inbound_descending(self, tmp_path: Path) -> None:
        """Scenario: Most-referenced skills appear first."""
        # Create one target referenced by 3 sources
        for plugin in ["a", "b", "c"]:
            (tmp_path / "plugins" / plugin / "skills" / "src").mkdir(parents=True)
            (tmp_path / "plugins" / plugin / "skills" / "src" / "SKILL.md").write_text(
                "---\nname: src\ndescription: x\n---\nUse `Skill(target:popular)`."
            )
        (tmp_path / "plugins" / "target" / "skills" / "popular").mkdir(parents=True)
        (
            tmp_path / "plugins" / "target" / "skills" / "popular" / "SKILL.md"
        ).write_text("---\nname: popular\ndescription: x\n---\nbody")

        graph = build_graph(tmp_path / "plugins")
        hubs = rank_hubs(graph, top_n=5)
        assert hubs[0][0] == "target:popular"
        assert hubs[0][1] == 3

    @pytest.mark.unit
    def test_rank_orchestrators_returns_outbound_descending(
        self, tmp_path: Path
    ) -> None:
        """Scenario: Skills with many outbound references appear first."""
        (tmp_path / "plugins" / "orch" / "skills" / "main").mkdir(parents=True)
        (tmp_path / "plugins" / "orch" / "skills" / "main" / "SKILL.md").write_text(
            "---\nname: main\ndescription: x\n---\n"
            "Run `Skill(a:one)`, `Skill(b:two)`, `Skill(c:three)`."
        )
        for plugin, name in [("a", "one"), ("b", "two"), ("c", "three")]:
            (tmp_path / "plugins" / plugin / "skills" / name).mkdir(parents=True)
            (tmp_path / "plugins" / plugin / "skills" / name / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: x\n---\nbody"
            )

        graph = build_graph(tmp_path / "plugins")
        orchs = rank_orchestrators(graph, top_n=5)
        assert orchs[0][0] == "orch:main"
        assert orchs[0][1] == 3


class TestDetectIsolates:
    """Feature: Detect skills with zero inbound and zero outbound references."""

    @pytest.mark.unit
    def test_detects_zero_degree_skill(self, tmp_path: Path) -> None:
        """Scenario: A skill with no references is reported as isolate."""
        (tmp_path / "plugins" / "lonely" / "skills" / "isolated").mkdir(parents=True)
        (
            tmp_path / "plugins" / "lonely" / "skills" / "isolated" / "SKILL.md"
        ).write_text(
            "---\nname: isolated\ndescription: x\n---\nbody with no Skill() refs"
        )
        (tmp_path / "plugins" / "connected" / "skills" / "src").mkdir(parents=True)
        (tmp_path / "plugins" / "connected" / "skills" / "src" / "SKILL.md").write_text(
            "---\nname: src\ndescription: x\n---\nUse `Skill(other:dst)`."
        )
        (tmp_path / "plugins" / "other" / "skills" / "dst").mkdir(parents=True)
        (tmp_path / "plugins" / "other" / "skills" / "dst" / "SKILL.md").write_text(
            "---\nname: dst\ndescription: x\n---\nbody"
        )

        graph = build_graph(tmp_path / "plugins")
        isolates = detect_isolates(graph)
        assert "lonely:isolated" in isolates
        assert "connected:src" not in isolates
        assert "other:dst" not in isolates

    @pytest.mark.unit
    def test_isolates_excludes_skills_with_only_outbound(self, tmp_path: Path) -> None:
        """Scenario: Pure orchestrator (only outbound) is not an isolate."""
        (tmp_path / "plugins" / "src" / "skills" / "orch").mkdir(parents=True)
        (tmp_path / "plugins" / "src" / "skills" / "orch" / "SKILL.md").write_text(
            "---\nname: orch\ndescription: x\n---\nUse `Skill(other:dst)`."
        )
        (tmp_path / "plugins" / "other" / "skills" / "dst").mkdir(parents=True)
        (tmp_path / "plugins" / "other" / "skills" / "dst" / "SKILL.md").write_text(
            "---\nname: dst\ndescription: x\n---\nbody"
        )

        graph = build_graph(tmp_path / "plugins")
        isolates = detect_isolates(graph)
        assert "src:orch" not in isolates


class TestClassifyDanglingRefs:
    """Feature: Classify dangling references into bug / external / placeholder."""

    def _make_graph_with_refs(self, tmp_path: Path, src_body: str) -> SkillGraph:
        (tmp_path / "plugins" / "src" / "skills" / "main").mkdir(parents=True)
        (tmp_path / "plugins" / "src" / "skills" / "main" / "SKILL.md").write_text(
            f"---\nname: main\ndescription: x\n---\n{src_body}"
        )
        return build_graph(tmp_path / "plugins")

    @pytest.mark.unit
    def test_external_plugin_ref_classified_as_external(self, tmp_path: Path) -> None:
        """Scenario: A reference to a known external plugin is not a bug."""
        graph = self._make_graph_with_refs(
            tmp_path, "Use `Skill(superpowers:brainstorming)`."
        )
        result = classify_dangling_refs(graph)
        assert ("src:main", "superpowers:brainstorming") in result["external"]
        assert result["bugs"] == []

    @pytest.mark.unit
    def test_placeholder_ref_classified_as_placeholder(self, tmp_path: Path) -> None:
        """Scenario: A NAME-suffixed reference is template documentation."""
        graph = self._make_graph_with_refs(
            tmp_path, "Use `Skill(archetypes:architecture-paradigm-NAME)`."
        )
        result = classify_dangling_refs(graph)
        assert (
            "src:main",
            "archetypes:architecture-paradigm-NAME",
        ) in result["placeholders"]
        assert result["bugs"] == []

    @pytest.mark.unit
    def test_unknown_internal_ref_classified_as_bug(self, tmp_path: Path) -> None:
        """Scenario: An internal-looking ref to a missing skill is a bug."""
        graph = self._make_graph_with_refs(
            tmp_path, "Use `Skill(imbue:nonexistent-skill)`."
        )
        result = classify_dangling_refs(graph)
        assert ("src:main", "imbue:nonexistent-skill") in result["bugs"]
        assert result["external"] == []

    @pytest.mark.unit
    def test_detect_dangling_refs_returns_only_bugs(self, tmp_path: Path) -> None:
        """Scenario: Wrapper helper filters out external + placeholder noise."""
        body = (
            "Use `Skill(superpowers:brainstorming)` and "
            "`Skill(archetypes:architecture-paradigm-NAME)` and "
            "`Skill(imbue:typo-skill)`."
        )
        graph = self._make_graph_with_refs(tmp_path, body)
        bugs = detect_dangling_refs(graph)
        assert bugs == [("src:main", "imbue:typo-skill")]

    @pytest.mark.unit
    def test_round_trip_fix_decrements_bug_count(self, tmp_path: Path) -> None:
        """Scenario: Removing one bug ref from source drops the count by 1.

        Encodes the audit's central round-trip claim documented in
        SKILL.md Verification: fixing a flagged ref must reduce the
        dangling-bug count. If a regex regression, stale-cache bug, or
        classification drift breaks the source-to-report round trip,
        this test fails before users act on a misleading report.
        """
        src_skill = tmp_path / "plugins" / "src" / "skills" / "main" / "SKILL.md"
        src_skill.parent.mkdir(parents=True)

        # GIVEN: source references two missing internal skills (both bugs)
        src_skill.write_text(
            "---\nname: main\ndescription: x\n---\n"
            "Use `Skill(imbue:typo-one)` and `Skill(imbue:typo-two)`."
        )
        initial_bugs = detect_dangling_refs(build_graph(tmp_path / "plugins"))
        assert len(initial_bugs) == 2

        # WHEN: one bug ref is removed from source and the graph is rebuilt
        src_skill.write_text(
            "---\nname: main\ndescription: x\n---\nUse `Skill(imbue:typo-two)`."
        )
        after_fix_bugs = detect_dangling_refs(build_graph(tmp_path / "plugins"))

        # THEN: the count drops by exactly 1 and the surviving ref is preserved
        assert len(after_fix_bugs) == len(initial_bugs) - 1
        assert after_fix_bugs == [("src:main", "imbue:typo-two")]

    @pytest.mark.unit
    def test_known_external_plugins_includes_superpowers(self) -> None:
        """Scenario: superpowers is recognised as an external ecosystem plugin."""
        assert "superpowers" in KNOWN_EXTERNAL_PLUGINS
        assert "elements-of-style" in KNOWN_EXTERNAL_PLUGINS


class TestSkillNode:
    """Feature: SkillNode dataclass holds metadata for graph reporting."""

    @pytest.mark.unit
    def test_node_has_plugin_and_name(self) -> None:
        """Scenario: Node carries identity components for reporting."""
        node = SkillNode(
            plugin="imbue",
            name="scope-guard",
            path=Path("plugins/imbue/skills/scope-guard/SKILL.md"),
            description="Pre-implementation scope control.",
        )
        assert node.plugin == "imbue"
        assert node.name == "scope-guard"
        assert str(node) == "imbue:scope-guard"
