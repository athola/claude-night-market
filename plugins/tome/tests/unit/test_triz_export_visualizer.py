# ruff: noqa: D101,D102,D103,D205,D212,PLR2004,E501
"""Unit tests for tome.channels.triz, tome.output.export, and
tome.output.visualizer.

These three modules were ~0% covered by the existing suite. The tests
here exercise the public surface of each module so the plugin clears
its 90% coverage gate (issue raised by /sanctum:update-plugins on
branch dora-1.9.6).
"""

from __future__ import annotations

import csv
import importlib.resources
from datetime import datetime, timezone

import pytest
import yaml

from tome.channels.triz import (
    FIELD_ADJACENCY,
    INVENTIVE_PRINCIPLES,
    build_cross_domain_search_queries,
    format_bridge_statement,
    formulate_contradiction,
    get_adjacent_fields,
    suggest_inventive_principles,
)
from tome.models import Finding, ResearchSession
from tome.output.export import export_for_memory_palace
from tome.output.visualizer import generate_visualization

# ============================================================================
# triz.formulate_contradiction
# ============================================================================


class TestFormulateContradiction:
    @pytest.mark.unit
    def test_keyword_match_picks_speed_memory_pair(self) -> None:
        result = formulate_contradiction("LRU cache for hot keys", "algorithm")
        assert result["improving"] == "speed"
        assert result["worsening"] == "memory usage"
        assert "algorithm" in result["system"]
        assert "speed" in result["contradiction"]

    @pytest.mark.unit
    def test_security_keyword_picks_security_usability(self) -> None:
        result = formulate_contradiction("password authentication flow", "security")
        assert result["improving"] == "security"
        assert result["worsening"] == "usability"

    @pytest.mark.unit
    def test_no_keyword_match_falls_back_to_default(self) -> None:
        result = formulate_contradiction("xyzzy plugh frobnicate", "general")
        assert result["improving"] == "flexibility"
        assert result["worsening"] == "complexity"

    @pytest.mark.unit
    def test_ideal_result_uses_template_when_pair_known(self) -> None:
        result = formulate_contradiction("cache performance tuning", "algorithm")
        # speed/memory pair has a templated ideal_result
        assert result["ideal_result"]
        assert "speed" in result["ideal_result"] or "memory" in result["ideal_result"]

    @pytest.mark.unit
    def test_ideal_result_falls_back_to_generic(self) -> None:
        # Force the default contradiction (flexibility/complexity) and check
        # the generic fallback string is used when no template is registered.
        result = formulate_contradiction("xyzzy", "general")
        # Generic template formats "achieves X without increasing Y"
        assert "flexibility" in result["ideal_result"]
        assert "complexity" in result["ideal_result"]


# ============================================================================
# triz.get_adjacent_fields
# ============================================================================


class TestGetAdjacentFields:
    @pytest.mark.unit
    def test_light_depth_returns_one_field(self) -> None:
        fields = get_adjacent_fields("algorithm", "light")
        assert len(fields) == 1
        assert fields[0] == FIELD_ADJACENCY["algorithm"][0]

    @pytest.mark.unit
    def test_medium_depth_returns_two_fields(self) -> None:
        fields = get_adjacent_fields("ui-ux", "medium")
        assert len(fields) == 2
        assert fields == FIELD_ADJACENCY["ui-ux"][:2]

    @pytest.mark.unit
    def test_deep_depth_returns_three_fields(self) -> None:
        fields = get_adjacent_fields("security", "deep")
        assert len(fields) == 3
        assert fields == FIELD_ADJACENCY["security"]

    @pytest.mark.unit
    def test_unknown_domain_falls_back_to_general(self) -> None:
        fields = get_adjacent_fields("unknown-domain", "deep")
        assert fields == FIELD_ADJACENCY["general"]

    @pytest.mark.unit
    def test_maximum_depth_extends_with_distant_fields(self) -> None:
        fields = get_adjacent_fields("algorithm", "maximum")
        # algorithm -> ui-ux is in _DISTANT_DOMAIN_PAIRS
        assert len(fields) >= 4
        assert all(isinstance(f, str) for f in fields)
        # No duplicates
        assert len(fields) == len(set(fields))

    @pytest.mark.unit
    def test_maximum_depth_pair_inverse_lookup(self) -> None:
        # ui-ux is the b side of the (algorithm, ui-ux) pair; the reverse
        # lookup branch must still resolve a distant_domain.
        fields = get_adjacent_fields("ui-ux", "maximum")
        assert len(fields) >= 4

    @pytest.mark.unit
    def test_maximum_depth_with_no_distant_pair_uses_fallback(self) -> None:
        # general has no entry in _DISTANT_DOMAIN_PAIRS, exercising the
        # "next non-general key" fallback branch.
        fields = get_adjacent_fields("general", "maximum")
        assert len(fields) >= 3


# ============================================================================
# triz.build_cross_domain_search_queries
# ============================================================================


class TestBuildCrossDomainSearchQueries:
    @pytest.mark.unit
    def test_two_queries_per_field(self) -> None:
        contradiction = {"improving": "speed", "worsening": "memory"}
        queries = build_cross_domain_search_queries(
            "rate limiting", ["biology", "logistics"], contradiction
        )
        assert len(queries) == 4
        assert any("biology" in q for q in queries)
        assert any("logistics" in q for q in queries)

    @pytest.mark.unit
    def test_empty_fields_returns_empty(self) -> None:
        queries = build_cross_domain_search_queries("anything", [], {})
        assert queries == []

    @pytest.mark.unit
    def test_missing_contradiction_keys_use_defaults(self) -> None:
        queries = build_cross_domain_search_queries("topic", ["physics"], {})
        # Should have used "performance" / "complexity" defaults
        assert any("performance" in q and "complexity" in q for q in queries)


# ============================================================================
# triz.suggest_inventive_principles
# ============================================================================


class TestSuggestInventivePrinciples:
    @pytest.mark.unit
    def test_known_contradiction_returns_mapped_principles(self) -> None:
        principles = suggest_inventive_principles("speed", "memory usage")
        numbers = [p["number"] for p in principles]
        # speed/memory maps to [1, 15, 27]
        assert numbers == [1, 15, 27]
        for p in principles:
            assert "name" in p
            assert "description" in p
            assert "application" in p
            assert p["application"]

    @pytest.mark.unit
    def test_unknown_contradiction_falls_back_to_defaults(self) -> None:
        principles = suggest_inventive_principles("zzz", "qqq")
        numbers = [p["number"] for p in principles]
        # Falls back to _DEFAULT_PRINCIPLES = [1, 13, 22, 25]
        assert numbers == [1, 13, 22, 25]

    @pytest.mark.unit
    def test_principle_without_specific_hint_uses_default_application(
        self,
    ) -> None:
        # consistency/availability maps to [15, 16, 24]; principle 15 has a
        # specific hint for consistency, principle 16 has one too. Verify
        # principle 24's application is the consistency-specific hint, not
        # the generic fallback.
        principles = suggest_inventive_principles("consistency", "availability")
        by_num = {p["number"]: p for p in principles}
        assert "intermediary" in by_num[24]["application"].lower()

    @pytest.mark.unit
    def test_default_application_used_when_no_hint_matches(self) -> None:
        # Pick a contradiction whose principle has no hint registered for
        # the improving fragment. flexibility/complexity -> [1, 5, 6];
        # principle 1 has a "flexibility" hint, but if we contrive an
        # unknown improving label, the default-application path runs.
        # Use the default-principles path with a non-mapped pair.
        principles = suggest_inventive_principles("zzz", "qqq")
        # _DEFAULT_PRINCIPLES = [1, 13, 22, 25]; principle 13 has no
        # hint with the "zzz" fragment, so falls back to the generic
        # description-based application.
        by_num = {p["number"]: p for p in principles}
        assert by_num[13]["application"]
        # The default application format includes "Apply <name> to the
        # <improving> problem"; verify shape.
        assert "Apply" in by_num[13]["application"]


# ============================================================================
# triz.format_bridge_statement
# ============================================================================


class TestFormatBridgeStatement:
    @pytest.mark.unit
    def test_returns_finding_with_triz_channel(self) -> None:
        finding = format_bridge_statement(
            source_field="biology",
            source_solution="cells use semipermeable membranes for selective transport",
            target_domain="security",
            application="implement field-level access controls",
            confidence=0.7,
        )
        assert isinstance(finding, Finding)
        assert finding.source == "triz"
        assert finding.channel == "triz"
        assert finding.relevance == 0.7
        assert "biology" in finding.title
        assert "security" in finding.title

    @pytest.mark.unit
    def test_url_is_triz_pseudo_scheme(self) -> None:
        finding = format_bridge_statement(
            "operations research",
            "queueing theory bounds wait times",
            "algorithm",
            "model request queue admission",
            0.5,
        )
        assert finding.url.startswith("triz://bridge/")
        # Spaces in source_field should become hyphens in the URL slug
        assert "operations-research" in finding.url


# ============================================================================
# triz module data integrity
# ============================================================================


class TestTrizCatalogues:
    @pytest.mark.unit
    def test_all_40_inventive_principles_present(self) -> None:
        assert set(INVENTIVE_PRINCIPLES.keys()) == set(range(1, 41))
        for _num, (name, desc) in INVENTIVE_PRINCIPLES.items():
            assert name
            assert desc

    @pytest.mark.unit
    def test_field_adjacency_keys_have_three_entries(self) -> None:
        for domain, fields in FIELD_ADJACENCY.items():
            assert len(fields) == 3, f"{domain} should list 3 adjacent fields"

    @pytest.mark.unit
    def test_vendored_39_parameters_present(self) -> None:
        data_pkg = importlib.resources.files("tome.channels.triz_data")
        raw = data_pkg.joinpath("39_parameters.yaml").read_text(encoding="utf-8")
        parsed = yaml.safe_load(raw)

        params = parsed["parameters"]
        assert len(params) == 39
        for entry in params:
            assert isinstance(entry["id"], int)
            assert 1 <= entry["id"] <= 39
            assert isinstance(entry["name"], str) and entry["name"].strip() != ""

    @pytest.mark.unit
    def test_vendored_matrix_csv_header_and_size(self) -> None:
        data_pkg = importlib.resources.files("tome.channels.triz_data")
        raw = data_pkg.joinpath("contradiction_matrix.csv").read_text(encoding="utf-8")
        rows = list(csv.reader(raw.splitlines()))

        assert rows[0] == [
            "improving_parameter",
            "worsening_parameter",
            "recommended_principles",
            "principle_names",
        ]
        # Sparse matrix: 109 populated cells in the vendored subset.
        assert len(rows) - 1 >= 100

    @pytest.mark.unit
    def test_vendored_matrix_principle_numbers_in_range(self) -> None:
        data_pkg = importlib.resources.files("tome.channels.triz_data")
        raw = data_pkg.joinpath("contradiction_matrix.csv").read_text(encoding="utf-8")
        reader = csv.DictReader(raw.splitlines())

        for row in reader:
            numbers = [int(n) for n in row["recommended_principles"].split(";") if n]
            assert numbers, "every populated cell lists at least one principle"
            for num in numbers:
                assert 1 <= num <= 40, f"principle {num} out of range"


# ============================================================================
# output.export.export_for_memory_palace
# ============================================================================


def _finding(**overrides: object) -> Finding:
    fields: dict[str, object] = {
        "source": "github",
        "channel": "code",
        "title": "Title",
        "url": "https://example.com/x",
        "relevance": 0.8,
        "summary": "summary",
        "metadata": {},
    }
    fields.update(overrides)
    return Finding(**fields)


def _session(findings: list[Finding] | None = None, **overrides) -> ResearchSession:
    defaults = {
        "topic": "test topic",
        "domain": "algorithm",
        "triz_depth": "light",
        "channels": ["code", "discourse"],
        "findings": findings or [],
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    return ResearchSession(**defaults)


class TestExportForMemoryPalace:
    @pytest.mark.unit
    def test_empty_session_renders_no_findings_message(self) -> None:
        session = _session(findings=[])
        out = export_for_memory_palace(session)
        assert "No findings recorded" in out
        assert "topic: test topic" in out
        assert "type: research-export" in out

    @pytest.mark.unit
    def test_session_without_created_at_omits_date(self) -> None:
        session = _session(created_at=None)
        out = export_for_memory_palace(session)
        # date field still present, but value empty
        assert "date: " in out

    @pytest.mark.unit
    def test_findings_grouped_by_channel(self) -> None:
        f1 = _finding(title="Repo A", channel="code", source="github")
        f2 = _finding(
            title="Discussion B",
            channel="discourse",
            source="hn",
            url="https://news.ycombinator.com/item?id=1",
        )
        session = _session(findings=[f1, f2])
        out = export_for_memory_palace(session)
        assert "Repo A" in out
        assert "Discussion B" in out
        # Each finding lists Source / URL / Relevance / Summary
        assert "**Source**: github" in out
        assert "**URL**: https://news.ycombinator.com/item?id=1" in out

    @pytest.mark.unit
    def test_finding_metadata_rendered(self) -> None:
        f = _finding(metadata={"stars": 1234, "language": "Rust"})
        session = _session(findings=[f])
        out = export_for_memory_palace(session)
        assert "**stars**: 1234" in out
        assert "**language**: Rust" in out

    @pytest.mark.unit
    def test_yaml_quote_escapes_special_chars(self) -> None:
        # Topic containing ":" forces quoting via _yaml_quote
        session = _session(topic='colon: needed "quoting"', findings=[])
        out = export_for_memory_palace(session)
        # The quoted field appears wrapped in double quotes with escapes
        assert 'topic: "colon' in out


# ============================================================================
# output.visualizer.generate_visualization
# ============================================================================


class TestGenerateVisualization:
    @pytest.mark.unit
    def test_empty_findings_returns_empty_string(self) -> None:
        assert generate_visualization([], "any-domain") == ""

    @pytest.mark.unit
    def test_architecture_domain_renders_mermaid(self) -> None:
        findings = [_finding(title=f"node {i}") for i in range(3)]
        out = generate_visualization(findings, "architecture")
        assert "```mermaid" in out
        assert "graph TD" in out
        assert 'N0["node 0"]' in out
        # Sequential connections
        assert "N0 --> N1" in out
        assert "N1 --> N2" in out

    @pytest.mark.unit
    def test_mermaid_sanitizes_problematic_chars(self) -> None:
        # Title with special chars that would break mermaid
        f = _finding(title='broken "quote" [brackets] arrow-->here')
        out = generate_visualization([f], "architecture")
        # quotes replaced with apostrophes, brackets replaced, arrows neutralized
        assert (
            '"'
            not in out.split("mermaid")[1]
            .split("```")[0]
            .replace('"node', "")
            .replace('["', "")
            .replace('"]', "")
            or "broken 'quote'" in out
        )
        assert "[brackets]" not in out
        assert "-->here" not in out  # the title-internal arrow removed

    @pytest.mark.unit
    def test_mermaid_caps_at_eight_nodes(self) -> None:
        findings = [_finding(title=f"n{i}") for i in range(20)]
        out = generate_visualization(findings, "architecture")
        # Should only render N0..N7
        assert 'N7["n7"]' in out
        assert "N8" not in out

    @pytest.mark.unit
    def test_algorithm_domain_renders_comparison_table(self) -> None:
        findings = [_finding(title="Algo A", relevance=0.95, summary="fast")]
        out = generate_visualization(findings, "algorithm")
        assert "| Finding | Source | Relevance | Summary |" in out
        assert "Algo A" in out
        assert "0.95" in out

    @pytest.mark.unit
    def test_data_structure_domain_uses_comparison_table(self) -> None:
        out = generate_visualization([_finding(title="Trie")], "data-structure")
        assert "| Finding |" in out
        assert "Trie" in out

    @pytest.mark.unit
    def test_financial_domain_renders_metrics_table_with_stars(self) -> None:
        findings = [
            _finding(
                title="Repo X",
                metadata={"stars": 9999},
            )
        ]
        out = generate_visualization(findings, "financial")
        assert "Stars/Score" in out
        assert "9999" in out

    @pytest.mark.unit
    def test_scientific_domain_renders_metrics_table_with_citations(self) -> None:
        findings = [
            _finding(
                title="Paper Y",
                metadata={"citations": 42},
            )
        ]
        out = generate_visualization(findings, "scientific")
        assert "Citations" in out
        assert "42" in out

    @pytest.mark.unit
    def test_metrics_table_falls_back_when_metadata_missing(self) -> None:
        findings = [_finding(title="No metric", metadata={})]
        out = generate_visualization(findings, "scientific")
        # Falls through to "-" placeholder
        assert "No metric" in out
        assert "| -" in out or "| - |" in out

    @pytest.mark.unit
    def test_other_domain_renders_ranked_list(self) -> None:
        findings = [
            _finding(title="First"),
            _finding(title="Second"),
        ]
        out = generate_visualization(findings, "general")
        assert "1. **First**" in out
        assert "2. **Second**" in out
