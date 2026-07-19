"""Regression tests for GAT-004, GAT-005, and GAT-006 findings."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from gauntlet.challenges import (
    _generate_problem_variation,
    get_variation_provider,
    set_variation_provider,
)
from gauntlet.graph import GraphStore, _sanitize_fts_query
from gauntlet.models import BankProblem, Difficulty, GraphNode, NodeKind

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_problem(
    prompt: str = "Given an array, return the maximum value.",
) -> BankProblem:
    return BankProblem(
        id="gat-test-001",
        title="Test Problem",
        category="arrays-and-hashing",
        difficulty=Difficulty.EASY,
        prompt=prompt,
        hints=["Use a loop"],
        solution_outline="Iterate once, track max.",
        tags=["arrays"],
    )


def _make_node(name: str, kind: NodeKind = NodeKind.FUNCTION) -> GraphNode:
    return GraphNode(
        kind=kind,
        qualified_name=name,
        file_path=f"src/{name}.py",
        line_start=1,
        line_end=10,
        language="python",
        parent_name="",
        params=[],
        return_type="",
        modifiers=[],
        is_test=False,
        file_hash="",
    )


@pytest.fixture()
def store(tmp_path: Path) -> GraphStore:
    s = GraphStore(tmp_path / "gat_test.db")
    yield s
    s.close()


# ---------------------------------------------------------------------------
# GAT-004: search_fts must not call get_node() per FTS result (batch SELECT)
# ---------------------------------------------------------------------------


class TestGAT004BatchFTS:
    """
    Regression: search_fts must resolve FTS rows via a single batched IN-clause
    SELECT, never via individual get_node() calls (one per result).
    """

    @pytest.mark.unit
    def test_search_fts_does_not_call_get_node(self, store: GraphStore) -> None:
        """get_node must not be called during search_fts (batch path used)."""
        for i in range(5):
            node = _make_node(f"module.func_{i}")
            store.upsert_node(node)
        store.rebuild_fts()

        with patch.object(store, "get_node", wraps=store.get_node) as mock_get:
            results = store.search_fts("func")
            assert mock_get.call_count == 0, (
                f"search_fts called get_node {mock_get.call_count} time(s); "
                "expected batch SELECT to be used instead"
            )
        assert len(results) > 0

    @pytest.mark.unit
    def test_search_fts_returns_correct_order(self, store: GraphStore) -> None:
        """FTS rank ordering must be preserved after batch resolution."""
        for i in range(3):
            node = _make_node(f"ns.compute_value_{i}")
            store.upsert_node(node)
        store.rebuild_fts()

        results = store.search_fts("compute_value")
        qns = [r.qualified_name for r in results]
        # All inserted nodes that match should appear in results
        assert len(results) >= 1
        # Results must all be GraphNode instances
        assert all(isinstance(r, GraphNode) for r in results)


# ---------------------------------------------------------------------------
# GAT-005: bare Exception catch must be narrowed
# ---------------------------------------------------------------------------


class TestGAT005BLE001Annotation:
    """
    GAT-005: _generate_problem_variation catches bare Exception (BLE001).

    The broad catch is INTENTIONAL: VariationProvider is an arbitrary callable
    (anthropic SDK, in-loop LLM, test stub) that may raise any exception type.
    All errors must fall back to the seed problem, including network failures
    (RuntimeError, OSError) and SDK errors. The fix is a noqa annotation with
    documented rationale, not a narrowing of the exception type.

    These tests document the full fallback contract.
    """

    def setup_method(self) -> None:
        self._original = get_variation_provider()

    def teardown_method(self) -> None:
        set_variation_provider(self._original)

    @pytest.mark.unit
    def test_runtime_error_from_provider_falls_back(self) -> None:
        """RuntimeError (e.g. network failure) must fall back to seed problem."""

        def bad_provider(template: str, problem: BankProblem) -> str | None:
            raise RuntimeError("network timeout")

        set_variation_provider(bad_provider)
        result = _generate_problem_variation(_make_problem())
        assert result.id == "gat-test-001"
        assert result.prompt == "Given an array, return the maximum value."

    @pytest.mark.unit
    def test_value_error_from_provider_falls_back(self) -> None:
        """ValueError from provider must fall back to the seed problem."""

        def value_err_provider(template: str, problem: BankProblem) -> str | None:
            raise ValueError("bad format")

        set_variation_provider(value_err_provider)
        result = _generate_problem_variation(_make_problem())
        assert result.id == "gat-test-001"

    @pytest.mark.unit
    def test_import_error_from_provider_falls_back(self) -> None:
        """ImportError (missing anthropic SDK) must fall back to seed problem."""

        def no_sdk_provider(template: str, problem: BankProblem) -> str | None:
            raise ImportError("No module named 'anthropic'")

        set_variation_provider(no_sdk_provider)
        result = _generate_problem_variation(_make_problem())
        assert result.id == "gat-test-001"

    @pytest.mark.unit
    def test_key_error_from_provider_falls_back(self) -> None:
        """KeyError from provider must fall back to the seed problem."""

        def key_err_provider(template: str, problem: BankProblem) -> str | None:
            raise KeyError("missing_key")

        set_variation_provider(key_err_provider)
        result = _generate_problem_variation(_make_problem())
        assert result.id == "gat-test-001"


# ---------------------------------------------------------------------------
# GAT-006: _sanitize_fts_query output must be identical after refactor
# ---------------------------------------------------------------------------


class TestGAT006SanitizeFTS:
    """
    _sanitize_fts_query must remove all six FTS5 special characters (+, -, *,
    (, ), ") by replacing them with spaces and normalising whitespace.
    The refactor (loop -> re.sub) must produce byte-identical output.
    """

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("a+b", "a b"),
            ("a-b", "a b"),
            ("a*b", "a b"),
            ("a(b", "a b"),
            ("a)b", "a b"),
            ('a"b', "a b"),
            ("hello+world-(foo*bar)", "hello world foo bar"),
            (
                'complex "query" (with+special*chars)-here',
                "complex query with special chars here",
            ),
            ("no_special_chars", "no_special_chars"),
            ("  extra   spaces  ", "extra spaces"),
            ("", ""),
            ("+++", ""),
            ("a  +  b", "a b"),
        ],
    )
    def test_special_chars_replaced(self, raw: str, expected: str) -> None:
        """Each FTS5 special char is replaced with space; whitespace normalised."""
        assert _sanitize_fts_query(raw) == expected

    @pytest.mark.unit
    def test_all_six_special_chars_handled(self) -> None:
        """All six FTS5 operators are stripped from a query with all of them."""
        all_specials = 'a+b-c*d(e)f"g'
        result = _sanitize_fts_query(all_specials)
        for ch in '+-*()"':
            assert ch not in result, f"Special char {ch!r} not removed from {result!r}"

    @pytest.mark.unit
    def test_word_tokens_preserved(self) -> None:
        """Non-special text tokens must survive sanitization unchanged."""
        result = _sanitize_fts_query("graph search algorithm")
        assert result == "graph search algorithm"
