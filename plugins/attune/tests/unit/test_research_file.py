"""The research file is the only way findings reach the recommender (ADR-0025)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from attune_arch_init import load_research_file


def test_a_valid_file_returns_its_lists(tmp_path: Path) -> None:
    """Preferred and avoid come back as written."""
    path = tmp_path / "research.json"
    path.write_text(json.dumps({"preferred": ["hexagonal"], "avoid": ["layered"]}))
    assert load_research_file(path) == {
        "preferred": ["hexagonal"],
        "avoid": ["layered"],
    }


def test_an_unknown_key_is_refused(tmp_path: Path) -> None:
    """A misspelled key fails instead of being dropped.

    Silently ignored keys are how the matrix modifiers went unused.
    """
    path = tmp_path / "research.json"
    path.write_text(json.dumps({"preferred_paradigm": "hexagonal"}))
    with pytest.raises(ValueError, match="unknown research keys"):
        load_research_file(path)


def test_a_non_list_value_is_refused(tmp_path: Path) -> None:
    """Values must be lists of paradigm names."""
    path = tmp_path / "research.json"
    path.write_text(json.dumps({"avoid": "layered"}))
    with pytest.raises(ValueError, match="list of paradigm names"):
        load_research_file(path)


def test_an_unknown_paradigm_name_is_refused(tmp_path: Path) -> None:
    """A misspelled paradigm fails instead of becoming a phantom candidate.

    The ranker adds any name it is given, so "microservice" would be
    scored and could be recommended with no template or skill behind it.
    """
    path = tmp_path / "research.json"
    path.write_text(json.dumps({"avoid": ["microservice"]}))
    with pytest.raises(ValueError, match=r"unknown paradigms \['microservice'\]"):
        load_research_file(path)


def test_every_paradigm_the_matrix_names_is_accepted(tmp_path: Path) -> None:
    """The accepted vocabulary is the decision matrix's own."""
    names = [
        "layered",
        "functional-core",
        "hexagonal",
        "clean-architecture",
        "modular-monolith",
        "microservices",
        "event-driven",
        "cqrs-es",
        "pipes-filters",
    ]
    path = tmp_path / "research.json"
    path.write_text(json.dumps({"preferred": names}))
    assert load_research_file(path) == {"preferred": names}
