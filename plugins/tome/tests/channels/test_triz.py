"""
Feature: TRIZ cross-domain analysis engine

As a research pipeline
I want to apply TRIZ methodology to surface cross-domain solutions
So that agents can find non-obvious analogies from other fields
"""

from __future__ import annotations

import pytest
from tome.channels.triz import (
    build_cross_domain_search_queries,
    format_bridge_statement,
    formulate_contradiction,
    get_adjacent_fields,
    suggest_inventive_principles,
)
from tome.models import Finding


class TestContradictionFormulation:
    """
    Feature: TRIZ contradiction formulation from topic strings

    As a TRIZ analyst
    I want to extract the core technical contradiction from a topic
    So that I can map it to inventive principles and adjacent fields
    """

    @pytest.mark.unit
    def test_returns_dict_with_all_required_keys(self) -> None:
        """
        Scenario: formulate_contradiction returns all expected keys
        Given any topic and domain
        When formulate_contradiction is called
        Then the result contains system, improving, worsening,
             ideal_result, and contradiction
        """
        result = formulate_contradiction("distributed cache", "algorithm")

        required_keys = {
            "system",
            "improving",
            "worsening",
            "ideal_result",
            "contradiction",
        }
        assert required_keys.issubset(result.keys())

    @pytest.mark.unit
    def test_all_values_are_strings(self) -> None:
        """
        Scenario: All values in the contradiction dict are strings
        Given a topic
        When formulate_contradiction is called
        Then every value in the returned dict is a non-empty string
        """
        result = formulate_contradiction("cache performance", "algorithm")

        for key, value in result.items():
            assert isinstance(value, str), f"Key {key!r} has non-string value"
            assert value.strip() != "", f"Key {key!r} has empty value"

    @pytest.mark.unit
    def test_cache_performance_yields_speed_memory_contradiction(self) -> None:
        """
        Scenario: Cache-related topic maps to speed vs memory contradiction
        Given the topic "cache performance"
        When formulate_contradiction is called
        Then the improving parameter relates to speed and worsening to memory
        """
        result = formulate_contradiction("cache performance", "algorithm")

        improving = result["improving"].lower()
        worsening = result["worsening"].lower()
        assert any(word in improving for word in ("speed", "performance", "throughput"))
        assert any(word in worsening for word in ("memory", "storage", "space"))

    @pytest.mark.unit
    def test_api_security_yields_security_usability_contradiction(self) -> None:
        """
        Scenario: Security-related topic maps to security vs usability contradiction
        Given the topic "API security"
        When formulate_contradiction is called
        Then the improving parameter relates to security and worsening to usability
        """
        result = formulate_contradiction("API security", "security")

        improving = result["improving"].lower()
        worsening = result["worsening"].lower()
        assert "security" in improving
        assert any(
            word in worsening for word in ("usability", "accessibility", "experience")
        )

    @pytest.mark.unit
    def test_unknown_topic_defaults_to_flexibility_complexity(self) -> None:
        """
        Scenario: Unrecognised topic falls back to flexibility/complexity
        Given a topic with no known contradiction keywords
        When formulate_contradiction is called
        Then the improving parameter relates to flexibility
             and worsening to complexity
        """
        result = formulate_contradiction("xyzzy plugh foo bar", "general")

        improving = result["improving"].lower()
        worsening = result["worsening"].lower()
        assert "flexibility" in improving
        assert "complexity" in worsening

    @pytest.mark.unit
    def test_contradiction_string_follows_improving_worsens_format(self) -> None:
        """
        Scenario: The contradiction key follows the standard TRIZ phrasing
        Given any topic
        When formulate_contradiction is called
        Then the contradiction value contains "Improving" and "worsens"
        """
        result = formulate_contradiction("database latency", "algorithm")

        assert "Improving" in result["contradiction"]
        assert "worsens" in result["contradiction"]

    @pytest.mark.unit
    def test_ideal_result_contains_improving_and_worsening(self) -> None:
        """
        Scenario: ideal_result references both sides of the contradiction
        Given a topic yielding a specific contradiction
        When formulate_contradiction is called
        Then the ideal_result mentions both the improving and worsening params
        """
        result = formulate_contradiction("cache performance", "algorithm")

        ideal = result["ideal_result"].lower()
        improving = result["improving"].lower()
        worsening = result["worsening"].lower()
        # At least one token from each side must appear in the ideal result
        assert any(word in ideal for word in improving.split())
        assert any(word in ideal for word in worsening.split())


class TestAdjacentFields:
    """
    Feature: Adjacent field lookup by domain and TRIZ depth

    As a research agent
    I want to retrieve cross-domain fields calibrated to search depth
    So that I query proportionally many external disciplines
    """

    @pytest.mark.unit
    def test_light_depth_returns_one_field(self) -> None:
        """
        Scenario: light depth yields exactly 1 adjacent field
        Given domain "algorithm" and depth "light"
        When get_adjacent_fields is called
        Then exactly 1 field is returned
        """
        fields = get_adjacent_fields("algorithm", "light")

        assert len(fields) == 1

    @pytest.mark.unit
    def test_medium_depth_returns_two_fields(self) -> None:
        """
        Scenario: medium depth yields exactly 2 adjacent fields
        Given domain "algorithm" and depth "medium"
        When get_adjacent_fields is called
        Then exactly 2 fields are returned
        """
        fields = get_adjacent_fields("algorithm", "medium")

        assert len(fields) == 2

    @pytest.mark.unit
    def test_deep_depth_returns_three_fields(self) -> None:
        """
        Scenario: deep depth yields exactly 3 adjacent fields
        Given domain "algorithm" and depth "deep"
        When get_adjacent_fields is called
        Then exactly 3 fields are returned
        """
        fields = get_adjacent_fields("algorithm", "deep")

        assert len(fields) == 3

    @pytest.mark.unit
    def test_maximum_depth_returns_more_than_three_fields(self) -> None:
        """
        Scenario: maximum depth includes distant fields beyond the primary 3
        Given domain "algorithm" and depth "maximum"
        When get_adjacent_fields is called
        Then more than 3 fields are returned
        """
        fields = get_adjacent_fields("algorithm", "maximum")

        assert len(fields) > 3

    @pytest.mark.unit
    def test_all_returned_fields_are_strings(self) -> None:
        """
        Scenario: Every adjacent field entry is a plain string
        Given any domain and depth
        When get_adjacent_fields is called
        Then every element in the returned list is a string
        """
        for depth in ("light", "medium", "deep", "maximum"):
            fields = get_adjacent_fields("algorithm", depth)
            for f in fields:
                assert isinstance(f, str), (
                    f"depth={depth!r} returned non-string field: {f!r}"
                )

    @pytest.mark.unit
    def test_algorithm_domain_includes_operations_research(self) -> None:
        """
        Scenario: algorithm domain has operations research as its first adjacent field
        Given domain "algorithm" and depth "light"
        When get_adjacent_fields is called
        Then "operations research" is among the returned fields
        """
        fields = get_adjacent_fields("algorithm", "light")

        assert "operations research" in fields

    @pytest.mark.unit
    def test_unknown_domain_falls_back_to_general(self) -> None:
        """
        Scenario: Unrecognised domain falls back to the "general" adjacency list
        Given domain "unknown-domain" and depth "medium"
        When get_adjacent_fields is called
        Then 2 fields are returned without raising
        """
        fields = get_adjacent_fields("unknown-domain", "medium")

        assert len(fields) == 2
        assert all(isinstance(f, str) for f in fields)

    @pytest.mark.unit
    def test_maximum_depth_has_no_duplicates(self) -> None:
        """
        Scenario: maximum depth does not repeat the same field twice
        Given domain "ui-ux" and depth "maximum"
        When get_adjacent_fields is called
        Then all returned fields are unique
        """
        fields = get_adjacent_fields("ui-ux", "maximum")

        assert len(fields) == len(set(fields))

    @pytest.mark.unit
    def test_maximum_depth_domain_not_in_distant_pairs_still_works(self) -> None:
        """
        Scenario: Domain absent from the distant-pairs table falls back
                  to picking any other known domain for distant fields
        Given domain "architecture" which has no explicit distant-pair entry
        And depth "maximum"
        When get_adjacent_fields is called
        Then more than 3 fields are returned and all are strings
        """
        fields = get_adjacent_fields("architecture", "maximum")

        assert len(fields) > 3
        assert all(isinstance(f, str) for f in fields)
        assert len(fields) == len(set(fields))


class TestCrossDomainQueries:
    """
    Feature: Cross-domain WebSearch query construction

    As a research agent
    I want ready-made search queries for each adjacent field
    So that I can issue WebSearch calls without extra logic
    """

    @pytest.mark.unit
    def test_builds_at_least_one_query_per_field(self) -> None:
        """
        Scenario: At least one query is generated for each adjacent field
        Given 2 adjacent fields and a contradiction
        When build_cross_domain_search_queries is called
        Then at least 2 queries are returned (one per field minimum)
        """
        adjacent_fields = ["operations research", "physics"]
        contradiction = {
            "improving": "speed",
            "worsening": "memory",
            "system": "cache",
            "ideal_result": "...",
            "contradiction": "Improving speed worsens memory",
        }

        queries = build_cross_domain_search_queries(
            "cache performance", adjacent_fields, contradiction
        )

        assert len(queries) >= len(adjacent_fields)

    @pytest.mark.unit
    def test_queries_contain_field_name(self) -> None:
        """
        Scenario: Each query references the adjacent field it targets
        Given adjacent fields ["genetics"]
        When build_cross_domain_search_queries is called
        Then at least one returned query contains "genetics"
        """
        adjacent_fields = ["genetics"]
        contradiction = {
            "improving": "speed",
            "worsening": "memory",
            "system": "sorting",
            "ideal_result": "...",
            "contradiction": "Improving speed worsens memory",
        }

        queries = build_cross_domain_search_queries(
            "sorting algorithm", adjacent_fields, contradiction
        )

        assert any("genetics" in q.lower() for q in queries)

    @pytest.mark.unit
    def test_queries_reference_the_contradiction(self) -> None:
        """
        Scenario: Queries embed contradiction terms for targeted search
        Given a contradiction with improving="speed" and worsening="memory"
        When build_cross_domain_search_queries is called
        Then at least one query contains "speed" or "memory"
        """
        adjacent_fields = ["logistics"]
        contradiction = {
            "improving": "speed",
            "worsening": "memory",
            "system": "cache",
            "ideal_result": "...",
            "contradiction": "Improving speed worsens memory",
        }

        queries = build_cross_domain_search_queries(
            "cache design", adjacent_fields, contradiction
        )

        contradiction_terms = {"speed", "memory"}
        assert any(
            any(term in q.lower() for term in contradiction_terms) for q in queries
        )

    @pytest.mark.unit
    def test_all_queries_are_strings(self) -> None:
        """
        Scenario: Every returned query is a plain string
        Given valid inputs
        When build_cross_domain_search_queries is called
        Then every element in the result is a string
        """
        adjacent_fields = ["ecology", "materials science"]
        contradiction = {
            "improving": "consistency",
            "worsening": "availability",
            "system": "database",
            "ideal_result": "...",
            "contradiction": "Improving consistency worsens availability",
        }

        queries = build_cross_domain_search_queries(
            "distributed database", adjacent_fields, contradiction
        )

        assert all(isinstance(q, str) for q in queries)

    @pytest.mark.unit
    def test_empty_adjacent_fields_returns_empty_list(self) -> None:
        """
        Scenario: No adjacent fields means no queries
        Given an empty adjacent_fields list
        When build_cross_domain_search_queries is called
        Then an empty list is returned
        """
        contradiction = {
            "improving": "speed",
            "worsening": "memory",
            "system": "cache",
            "ideal_result": "...",
            "contradiction": "Improving speed worsens memory",
        }

        queries = build_cross_domain_search_queries("cache", [], contradiction)

        assert queries == []


class TestInventivePrinciples:
    """
    Feature: TRIZ inventive principle suggestion

    As a TRIZ analyst
    I want to retrieve the most applicable inventive principles
    So that engineers can explore structured solution patterns
    """

    @pytest.mark.unit
    def test_returns_three_to_five_principles(self) -> None:
        """
        Scenario: Suggestion always returns 3-5 principles
        Given any valid improving/worsening pair
        When suggest_inventive_principles is called
        Then between 3 and 5 principles are returned
        """
        principles = suggest_inventive_principles("speed", "memory")

        assert 3 <= len(principles) <= 5

    @pytest.mark.unit
    def test_each_principle_has_required_keys(self) -> None:
        """
        Scenario: Every principle dict has all four required keys
        Given the speed/memory contradiction
        When suggest_inventive_principles is called
        Then every returned dict has number, name, description, application
        """
        principles = suggest_inventive_principles("speed", "memory")

        required = {"number", "name", "description", "application"}
        for i, p in enumerate(principles):
            assert required.issubset(p.keys()), (
                f"Principle at index {i} is missing keys: {required - set(p.keys())}"
            )

    @pytest.mark.unit
    def test_speed_memory_contradiction_includes_segmentation(self) -> None:
        """
        Scenario: Segmentation (#1) appears for speed vs memory
        Given improving="speed" and worsening="memory"
        When suggest_inventive_principles is called
        Then principle #1 (Segmentation) is in the returned list
        """
        principles = suggest_inventive_principles("speed", "memory")

        numbers = [p["number"] for p in principles]
        assert 1 in numbers, f"Segmentation (#1) not found in {numbers}"

    @pytest.mark.unit
    def test_default_contradiction_returns_valid_principles(self) -> None:
        """
        Scenario: An unrecognised contradiction uses the default mapping
        Given improving="xyzzy" and worsening="plugh"
        When suggest_inventive_principles is called
        Then 3-5 valid principles are returned without raising
        """
        principles = suggest_inventive_principles("xyzzy", "plugh")

        assert 3 <= len(principles) <= 5
        for p in principles:
            assert isinstance(p["number"], int)
            assert isinstance(p["name"], str)
            assert isinstance(p["description"], str)
            assert isinstance(p["application"], str)

    @pytest.mark.unit
    def test_principle_numbers_are_valid_triz_numbers(self) -> None:
        """
        Scenario: All returned principle numbers are in the 1-40 range
        Given any contradiction
        When suggest_inventive_principles is called
        Then every principle number is between 1 and 40 inclusive
        """
        for improving, worsening in [
            ("speed", "memory"),
            ("flexibility", "complexity"),
            ("security", "usability"),
            ("throughput", "latency"),
        ]:
            principles = suggest_inventive_principles(improving, worsening)
            for p in principles:
                assert 1 <= p["number"] <= 40, (
                    f"Number {p['number']} out of TRIZ range for {improving}/{worsening}"
                )

    @pytest.mark.unit
    def test_application_field_is_non_empty_string(self) -> None:
        """
        Scenario: The application field is always a meaningful string
        Given any contradiction
        When suggest_inventive_principles is called
        Then every application value is a non-empty string
        """
        principles = suggest_inventive_principles("consistency", "availability")

        for p in principles:
            assert isinstance(p["application"], str)
            assert p["application"].strip() != ""


class TestBridgeStatement:
    """
    Feature: TRIZ cross-domain bridge Finding construction

    As a synthesis engine
    I want a structured Finding representing an analogical bridge
    So that the report can present cross-domain mappings clearly
    """

    @pytest.mark.unit
    def test_returns_a_finding_instance(self) -> None:
        """
        Scenario: format_bridge_statement always returns a Finding
        Given valid source and target information
        When format_bridge_statement is called
        Then a Finding object is returned
        """
        result = format_bridge_statement(
            source_field="ecology",
            source_solution="species use niche partitioning to reduce competition",
            target_domain="algorithm",
            application="partition key space to reduce cache contention",
            confidence=0.75,
        )

        assert isinstance(result, Finding)

    @pytest.mark.unit
    def test_source_and_channel_are_triz(self) -> None:
        """
        Scenario: The Finding is tagged as a TRIZ finding
        Given any bridge inputs
        When format_bridge_statement is called
        Then source="triz" and channel="triz"
        """
        finding = format_bridge_statement(
            source_field="immunology",
            source_solution="adaptive immune response uses memory cells",
            target_domain="security",
            application="use threat-memory tokens to accelerate re-auth",
            confidence=0.6,
        )

        assert finding.source == "triz"
        assert finding.channel == "triz"

    @pytest.mark.unit
    def test_title_includes_source_and_target_fields(self) -> None:
        """
        Scenario: Title reflects the bridge direction
        Given source_field="ecology" and target_domain="algorithm"
        When format_bridge_statement is called
        Then the title contains both "ecology" and "algorithm"
        """
        finding = format_bridge_statement(
            source_field="ecology",
            source_solution="predator-prey cycles",
            target_domain="algorithm",
            application="adaptive backoff",
            confidence=0.5,
        )

        assert "ecology" in finding.title.lower()
        assert "algorithm" in finding.title.lower()

    @pytest.mark.unit
    def test_summary_includes_source_solution_and_application(self) -> None:
        """
        Scenario: Summary captures both sides of the bridge
        Given source_solution and application strings
        When format_bridge_statement is called
        Then the summary contains substrings from both
        """
        finding = format_bridge_statement(
            source_field="logistics",
            source_solution="just-in-time delivery",
            target_domain="devops",
            application="on-demand resource provisioning",
            confidence=0.8,
        )

        assert "just-in-time" in finding.summary.lower()
        assert "on-demand" in finding.summary.lower()

    @pytest.mark.unit
    def test_metadata_includes_bridge_confidence(self) -> None:
        """
        Scenario: Metadata carries bridge_confidence for downstream filtering
        Given confidence=0.82
        When format_bridge_statement is called
        Then metadata["bridge_confidence"] == 0.82
        """
        finding = format_bridge_statement(
            source_field="physics",
            source_solution="resonance amplification",
            target_domain="ui-ux",
            application="feedback loops in interaction design",
            confidence=0.82,
        )

        assert "bridge_confidence" in finding.metadata
        assert finding.metadata["bridge_confidence"] == pytest.approx(0.82)

    @pytest.mark.unit
    def test_metadata_includes_source_and_target_fields(self) -> None:
        """
        Scenario: Metadata records both field names for provenance
        Given source_field="genetics" and target_domain="data-structure"
        When format_bridge_statement is called
        Then metadata has source_field and target_field keys
        """
        finding = format_bridge_statement(
            source_field="genetics",
            source_solution="crossover recombination",
            target_domain="data-structure",
            application="tree rotation strategies",
            confidence=0.65,
        )

        assert finding.metadata["source_field"] == "genetics"
        assert finding.metadata["target_field"] == "data-structure"

    @pytest.mark.unit
    def test_relevance_equals_confidence(self) -> None:
        """
        Scenario: Finding relevance is set to the bridge confidence value
        Given confidence=0.72
        When format_bridge_statement is called
        Then finding.relevance == 0.72
        """
        finding = format_bridge_statement(
            source_field="supply chain",
            source_solution="kanban pull systems",
            target_domain="devops",
            application="pull-based CI pipelines",
            confidence=0.72,
        )

        assert finding.relevance == pytest.approx(0.72)

    @pytest.mark.unit
    def test_url_is_a_string(self) -> None:
        """
        Scenario: The url field is always a string (may be empty or synthetic)
        Given any bridge inputs
        When format_bridge_statement is called
        Then finding.url is a string
        """
        finding = format_bridge_statement(
            source_field="architecture",
            source_solution="load-bearing arches",
            target_domain="data-structure",
            application="balanced tree invariants",
            confidence=0.55,
        )

        assert isinstance(finding.url, str)
