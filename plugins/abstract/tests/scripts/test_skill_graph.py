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
    VALID_ROLES,
    SkillGraph,
    SkillNode,
    build_graph,
    classify_by_role,
    classify_dangling_refs,
    detect_dangling_refs,
    detect_isolates,
    detect_uncalled_libraries,
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


class TestFrontmatterDependencies:
    """Feature: Frontmatter `dependencies:` and `modules:` arrays count as
    skill references.

    Background: The 2026-04-25 orphan audit had a measurement bug -- it only
    saw inline `Skill(plugin:name)` calls and missed skills loaded via
    frontmatter dependency arrays. This produced ~85 false-positive orphans.
    The taxonomy in docs/skill-integration-guide.md formalises the entry
    paths a skill can have; the audit must recognise all of them.
    """

    @pytest.mark.unit
    def test_qualified_dependency_creates_edge(self, tmp_path: Path) -> None:
        """Scenario: `dependencies: [tome:code-search]` is an edge to that skill."""
        (tmp_path / "plugins" / "tome" / "skills" / "research").mkdir(parents=True)
        (tmp_path / "plugins" / "tome" / "skills" / "research" / "SKILL.md").write_text(
            textwrap.dedent("""\
                ---
                name: research
                description: Multi-source research.
                dependencies:
                  - tome:code-search
                  - tome:discourse
                ---
                Body without inline Skill() calls.
                """)
        )
        (tmp_path / "plugins" / "tome" / "skills" / "code-search").mkdir(parents=True)
        (
            tmp_path / "plugins" / "tome" / "skills" / "code-search" / "SKILL.md"
        ).write_text("---\nname: code-search\ndescription: x\n---\nbody")
        (tmp_path / "plugins" / "tome" / "skills" / "discourse").mkdir(parents=True)
        (
            tmp_path / "plugins" / "tome" / "skills" / "discourse" / "SKILL.md"
        ).write_text("---\nname: discourse\ndescription: x\n---\nbody")

        graph = build_graph(tmp_path / "plugins")

        assert ("tome:research", "tome:code-search") in graph.edges
        assert ("tome:research", "tome:discourse") in graph.edges

    @pytest.mark.unit
    def test_bare_dependency_resolves_to_same_plugin(self, tmp_path: Path) -> None:
        """Scenario: `dependencies: [hexagonal]` in archetypes resolves to
        archetypes:hexagonal. The architecture-paradigms hub uses bare-name
        deps for sibling paradigm skills.
        """
        (
            tmp_path / "plugins" / "archetypes" / "skills" / "architecture-paradigms"
        ).mkdir(parents=True)
        (
            tmp_path
            / "plugins"
            / "archetypes"
            / "skills"
            / "architecture-paradigms"
            / "SKILL.md"
        ).write_text(
            textwrap.dedent("""\
                ---
                name: architecture-paradigms
                description: Paradigm router.
                dependencies:
                  - architecture-paradigm-hexagonal
                  - architecture-paradigm-microservices
                ---
                Body.
                """)
        )
        (
            tmp_path
            / "plugins"
            / "archetypes"
            / "skills"
            / "architecture-paradigm-hexagonal"
        ).mkdir(parents=True)
        (
            tmp_path
            / "plugins"
            / "archetypes"
            / "skills"
            / "architecture-paradigm-hexagonal"
            / "SKILL.md"
        ).write_text(
            "---\nname: architecture-paradigm-hexagonal\ndescription: x\n---\nbody"
        )
        (
            tmp_path
            / "plugins"
            / "archetypes"
            / "skills"
            / "architecture-paradigm-microservices"
        ).mkdir(parents=True)
        (
            tmp_path
            / "plugins"
            / "archetypes"
            / "skills"
            / "architecture-paradigm-microservices"
            / "SKILL.md"
        ).write_text(
            "---\nname: architecture-paradigm-microservices\ndescription: x\n---\nbody"
        )

        graph = build_graph(tmp_path / "plugins")

        assert (
            "archetypes:architecture-paradigms",
            "archetypes:architecture-paradigm-hexagonal",
        ) in graph.edges
        assert (
            "archetypes:architecture-paradigms",
            "archetypes:architecture-paradigm-microservices",
        ) in graph.edges

    @pytest.mark.unit
    def test_bare_names_in_modules_array_treated_as_local_files(
        self, tmp_path: Path
    ) -> None:
        """Scenario: `modules: [tdd-methodology]` is a local module file
        basename (resolves to ``modules/tdd-methodology.md``), NOT a
        same-plugin skill reference.

        This distinguishes `modules:` (composition of one skill from
        local files) from `dependencies:` (sibling skill loads). Without
        this distinction, the audit produces hundreds of false-positive
        dangling-bug findings against module-heavy skills like
        abstract:skill-authoring.
        """
        (tmp_path / "plugins" / "abstract" / "skills" / "skill-authoring").mkdir(
            parents=True
        )
        (
            tmp_path
            / "plugins"
            / "abstract"
            / "skills"
            / "skill-authoring"
            / "SKILL.md"
        ).write_text(
            textwrap.dedent("""\
                ---
                name: skill-authoring
                description: Skill authoring guide.
                modules:
                  - tdd-methodology
                  - persuasion-principles
                ---
                Body.
                """)
        )

        graph = build_graph(tmp_path / "plugins")

        # Bare names in modules: must NOT produce phantom edges.
        assert (
            "abstract:skill-authoring",
            "abstract:tdd-methodology",
        ) not in graph.edges
        assert (
            "abstract:skill-authoring",
            "abstract:persuasion-principles",
        ) not in graph.edges

    @pytest.mark.unit
    def test_qualified_entry_in_modules_still_creates_edge(
        self, tmp_path: Path
    ) -> None:
        """Scenario: `modules: [other-plugin:helper]` is a fully-qualified
        cross-plugin reference and SHOULD produce an edge.

        The bare-name suppression only applies to ambiguous entries; an
        explicit `plugin:name` form is unambiguous and authoritative.
        """
        (tmp_path / "plugins" / "src" / "skills" / "main").mkdir(parents=True)
        (tmp_path / "plugins" / "src" / "skills" / "main" / "SKILL.md").write_text(
            textwrap.dedent("""\
                ---
                name: main
                description: x
                modules:
                  - other:helper
                ---
                Body.
                """)
        )
        (tmp_path / "plugins" / "other" / "skills" / "helper").mkdir(parents=True)
        (tmp_path / "plugins" / "other" / "skills" / "helper" / "SKILL.md").write_text(
            "---\nname: helper\ndescription: x\n---\nbody"
        )

        graph = build_graph(tmp_path / "plugins")
        assert ("src:main", "other:helper") in graph.edges

    @pytest.mark.unit
    def test_modules_array_with_local_paths_is_ignored(self, tmp_path: Path) -> None:
        """Scenario: `modules: [modules/usage.md]` is a local file, not a
        skill reference. It must NOT produce an edge to a phantom
        `<plugin>:modules/usage.md` node.
        """
        (tmp_path / "plugins" / "abstract" / "skills" / "skill-graph-audit").mkdir(
            parents=True
        )
        (
            tmp_path
            / "plugins"
            / "abstract"
            / "skills"
            / "skill-graph-audit"
            / "SKILL.md"
        ).write_text(
            textwrap.dedent("""\
                ---
                name: skill-graph-audit
                description: Map Skill refs.
                modules:
                  - modules/usage.md
                  - modules/interpretation.md
                ---
                Body.
                """)
        )

        graph = build_graph(tmp_path / "plugins")

        # No phantom edges to file-path entries.
        for _src, dst in graph.edges:
            assert "/" not in dst, f"file path leaked into edges: {dst}"
            assert not dst.endswith(".md"), f"file path leaked into edges: {dst}"

    @pytest.mark.unit
    def test_dep_to_unknown_plugin_classified_external(self, tmp_path: Path) -> None:
        """Scenario: Frontmatter dep to a known-external plugin is treated
        the same as an inline Skill() ref to that plugin -- external,
        not a bug.
        """
        (tmp_path / "plugins" / "src" / "skills" / "main").mkdir(parents=True)
        (tmp_path / "plugins" / "src" / "skills" / "main" / "SKILL.md").write_text(
            textwrap.dedent("""\
                ---
                name: main
                description: x
                dependencies:
                  - superpowers:brainstorming
                ---
                Body.
                """)
        )

        graph = build_graph(tmp_path / "plugins")
        result = classify_dangling_refs(graph)

        assert ("src:main", "superpowers:brainstorming") in result["external"]
        assert result["bugs"] == []


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

    @pytest.mark.unit
    def test_node_role_defaults_to_empty(self) -> None:
        """Scenario: Legacy nodes without role: have empty role, not None."""
        node = SkillNode(
            plugin="imbue",
            name="scope-guard",
            path=Path("/tmp/SKILL.md"),
        )
        assert node.role == ""

    @pytest.mark.unit
    def test_node_carries_role_when_set(self) -> None:
        """Scenario: role= constructor argument is preserved."""
        node = SkillNode(
            plugin="scribe",
            name="slop-detector",
            path=Path("/tmp/SKILL.md"),
            role="library",
        )
        assert node.role == "library"


class TestRoleAwareClassification:
    """Feature: Role-aware audit classification per the taxonomy in
    docs/skill-integration-guide.md#skill-role-taxonomy.

    Each role has different expectations:
    - `entrypoint` skills are user-invoked; zero inbound is normal.
    - `library` skills exist to be loaded; zero inbound is a smell
      (genuinely uncalled).
    - `hook-target` skills are invoked by hooks; the audit cannot see
      that path, so zero inbound is normal.
    - Unset roles fall back to legacy isolate detection.
    """

    @pytest.mark.unit
    def test_valid_roles_constant(self) -> None:
        """Scenario: The taxonomy's three roles are exposed as a constant."""
        assert VALID_ROLES == {"entrypoint", "library", "hook-target"}

    @pytest.mark.unit
    def test_role_parsed_from_frontmatter(self, tmp_path: Path) -> None:
        """Scenario: A skill declaring role: library has node.role set."""
        (tmp_path / "plugins" / "scribe" / "skills" / "slop-detector").mkdir(
            parents=True
        )
        (
            tmp_path / "plugins" / "scribe" / "skills" / "slop-detector" / "SKILL.md"
        ).write_text(
            textwrap.dedent("""\
                ---
                name: slop-detector
                description: Detect AI slop.
                role: library
                ---
                Body.
                """)
        )

        graph = build_graph(tmp_path / "plugins")
        assert graph.nodes["scribe:slop-detector"].role == "library"

    @pytest.mark.unit
    def test_invalid_role_value_silently_dropped(self, tmp_path: Path) -> None:
        """Scenario: An unknown role: value is treated as unset rather than error.

        The audit must remain robust to typos and to future role additions
        that haven't reached the validator yet.
        """
        (tmp_path / "plugins" / "x" / "skills" / "y").mkdir(parents=True)
        (tmp_path / "plugins" / "x" / "skills" / "y" / "SKILL.md").write_text(
            textwrap.dedent("""\
                ---
                name: y
                description: x
                role: not-a-real-role
                ---
                Body.
                """)
        )
        graph = build_graph(tmp_path / "plugins")
        assert graph.nodes["x:y"].role == ""

    @pytest.mark.unit
    def test_library_with_zero_inbound_is_uncalled_not_isolate(
        self, tmp_path: Path
    ) -> None:
        """Scenario: role: library with zero inbound goes into
        uncalled_libraries, NOT isolates.

        The original audit's measurement bug flagged genuine libraries as
        orphans. With role: declared, the audit can place them in a
        dedicated bin that signals "potentially dead library" without
        conflating with truly-dangling skills.
        """
        (tmp_path / "plugins" / "lib" / "skills" / "uncalled").mkdir(parents=True)
        (tmp_path / "plugins" / "lib" / "skills" / "uncalled" / "SKILL.md").write_text(
            textwrap.dedent("""\
                ---
                name: uncalled
                description: A library no one calls yet.
                role: library
                ---
                Body.
                """)
        )

        graph = build_graph(tmp_path / "plugins")
        isolates = detect_isolates(graph)
        uncalled = detect_uncalled_libraries(graph)

        assert "lib:uncalled" not in isolates
        assert "lib:uncalled" in uncalled

    @pytest.mark.unit
    def test_entrypoint_with_zero_inbound_is_neither_isolate_nor_uncalled(
        self, tmp_path: Path
    ) -> None:
        """Scenario: role: entrypoint skills are user-invoked; zero inbound
        is the normal case, not a defect.
        """
        (tmp_path / "plugins" / "p" / "skills" / "user-facing").mkdir(parents=True)
        (tmp_path / "plugins" / "p" / "skills" / "user-facing" / "SKILL.md").write_text(
            textwrap.dedent("""\
                ---
                name: user-facing
                description: User invokes via slash command.
                role: entrypoint
                ---
                Body.
                """)
        )

        graph = build_graph(tmp_path / "plugins")
        assert "p:user-facing" not in detect_isolates(graph)
        assert "p:user-facing" not in detect_uncalled_libraries(graph)

    @pytest.mark.unit
    def test_hook_target_with_zero_inbound_is_neither(self, tmp_path: Path) -> None:
        """Scenario: role: hook-target skills are invoked by hooks; the
        audit cannot see that path, so zero inbound is normal.
        """
        (tmp_path / "plugins" / "p" / "skills" / "hookable").mkdir(parents=True)
        (tmp_path / "plugins" / "p" / "skills" / "hookable" / "SKILL.md").write_text(
            textwrap.dedent("""\
                ---
                name: hookable
                description: Read by a PreToolUse hook.
                role: hook-target
                ---
                Body.
                """)
        )

        graph = build_graph(tmp_path / "plugins")
        assert "p:hookable" not in detect_isolates(graph)
        assert "p:hookable" not in detect_uncalled_libraries(graph)

    @pytest.mark.unit
    def test_unset_role_falls_back_to_legacy_isolate_detection(
        self, tmp_path: Path
    ) -> None:
        """Scenario: Skills without role: keep the legacy zero-degree rule.

        Backward compatibility: existing skills predate the convention
        and must not be silently reclassified.
        """
        (tmp_path / "plugins" / "p" / "skills" / "legacy").mkdir(parents=True)
        (tmp_path / "plugins" / "p" / "skills" / "legacy" / "SKILL.md").write_text(
            "---\nname: legacy\ndescription: x\n---\nbody"
        )

        graph = build_graph(tmp_path / "plugins")
        assert "p:legacy" in detect_isolates(graph)

    @pytest.mark.unit
    def test_classify_by_role_bins_skills(self, tmp_path: Path) -> None:
        """Scenario: classify_by_role returns a dict keyed by role with
        skills in each bin, plus an `unset` bin for legacy skills.
        """
        for role_value, skill_name in [
            ("entrypoint", "ep"),
            ("library", "lib"),
            ("hook-target", "ht"),
            ("", "legacy"),
        ]:
            (tmp_path / "plugins" / "p" / "skills" / skill_name).mkdir(parents=True)
            fm_extra = f"role: {role_value}\n" if role_value else ""
            (
                tmp_path / "plugins" / "p" / "skills" / skill_name / "SKILL.md"
            ).write_text(
                f"---\nname: {skill_name}\ndescription: x\n{fm_extra}---\nbody"
            )

        graph = build_graph(tmp_path / "plugins")
        bins = classify_by_role(graph)

        assert bins["entrypoint"] == ["p:ep"]
        assert bins["library"] == ["p:lib"]
        assert bins["hook-target"] == ["p:ht"]
        assert bins["unset"] == ["p:legacy"]
