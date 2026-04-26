"""Tests for the DSA problem bank loader, filter, and conversion."""

from __future__ import annotations

import pytest
import yaml
from gauntlet.models import BankProblem, ChallengeType, Difficulty
from gauntlet.problem_bank import (
    bank_problem_to_challenge,
    filter_problems,
    load_bank,
    load_manifest,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sample_problem(**overrides: object) -> dict:
    """Return a minimal valid problem dict with optional overrides."""
    base: dict = {
        "id": "two-sum",
        "title": "Two Sum",
        "category": "arrays-and-hashing",
        "difficulty": "easy",
        "prompt": (
            "Given an array of integers, return indices"
            " of two numbers that add up to a target."
        ),
        "hints": ["Use a hash map."],
        "solution_outline": "Store complement in a dict while iterating.",
        "tags": ["hash-map", "array"],
        "neetcode_id": "two-sum",
        "challenge_type": "explain_why",
    }
    base.update(overrides)
    return base


def _write_yaml(path, data):
    """Write *data* as YAML to *path*."""
    with open(path, "w") as f:
        yaml.safe_dump(data, f)


# ---------------------------------------------------------------------------
# Feature: Difficulty enum
# ---------------------------------------------------------------------------


class TestDifficulty:
    """
    Feature: Difficulty enum for DSA problem tiers

    As a gauntlet engine
    I want difficulty levels that map to numeric scores
    So that bank problems integrate with the existing 1-5 scale
    """

    @pytest.mark.unit
    def test_string_representation(self):
        """
        Scenario: Difficulty renders as its value string
        Given a Difficulty enum member
        When converted to string
        Then it equals the raw value
        """
        assert str(Difficulty.EASY) == "easy"
        assert str(Difficulty.EXTRA_HARD) == "extra_hard"

    @pytest.mark.unit
    def test_to_numeric_mapping(self):
        """
        Scenario: Each difficulty maps to a 1-4 integer
        Given all four difficulty tiers
        When to_numeric() is called
        Then easy=1, medium=2, hard=3, extra_hard=4
        """
        assert Difficulty.EASY.to_numeric() == 1
        assert Difficulty.MEDIUM.to_numeric() == 2
        assert Difficulty.HARD.to_numeric() == 3
        assert Difficulty.EXTRA_HARD.to_numeric() == 4

    @pytest.mark.unit
    def test_invalid_difficulty_raises(self):
        """
        Scenario: Invalid difficulty string is rejected
        Given a string that is not a valid difficulty
        When used to construct a Difficulty
        Then a ValueError is raised
        """
        with pytest.raises(ValueError):
            Difficulty("nightmare")


# ---------------------------------------------------------------------------
# Feature: BankProblem serialization
# ---------------------------------------------------------------------------


class TestBankProblemSerialization:
    """
    Feature: BankProblem round-trip serialization

    As a problem bank maintainer
    I want to_dict / from_dict to be lossless
    So that problems survive YAML serialization
    """

    @pytest.mark.unit
    def test_round_trip(self):
        """
        Scenario: to_dict then from_dict reproduces the same object
        Given a BankProblem with all fields populated
        When serialized and deserialized
        Then every field matches
        """
        original = BankProblem(
            id="two-sum",
            title="Two Sum",
            category="arrays-and-hashing",
            difficulty=Difficulty.EASY,
            prompt="Find two numbers that add up to target.",
            hints=["Use a hash map."],
            solution_outline="Dict lookup for complement.",
            tags=["hash-map", "array"],
            neetcode_id="two-sum",
            challenge_type="explain_why",
        )
        restored = BankProblem.from_dict(original.to_dict())

        assert restored.id == original.id
        assert restored.title == original.title
        assert restored.category == original.category
        assert restored.difficulty == original.difficulty
        assert restored.prompt == original.prompt
        assert restored.hints == original.hints
        assert restored.solution_outline == original.solution_outline
        assert restored.tags == original.tags
        assert restored.neetcode_id == original.neetcode_id
        assert restored.challenge_type == original.challenge_type

    @pytest.mark.unit
    def test_from_dict_defaults(self):
        """
        Scenario: Optional fields fall back to defaults
        Given a dict with only required fields
        When deserialized
        Then optional fields use their defaults
        """
        minimal = {
            "id": "x",
            "title": "X",
            "category": "trees",
            "difficulty": "hard",
            "prompt": "Do something.",
        }
        problem = BankProblem.from_dict(minimal)

        assert problem.hints == []
        assert problem.solution_outline == ""
        assert problem.tags == []
        assert problem.neetcode_id == ""
        assert problem.challenge_type == "explain_why"


# ---------------------------------------------------------------------------
# Feature: load_bank
# ---------------------------------------------------------------------------


class TestLoadBank:
    """
    Feature: Loading problems from YAML files

    As the gauntlet engine
    I want to load all problems from a directory of YAML files
    So that the problem bank is populated at startup
    """

    @pytest.mark.unit
    def test_loads_problems_from_yaml(self, tmp_path):
        """
        Scenario: Valid YAML files produce BankProblem instances
        Given a directory with one YAML file containing two problems
        When load_bank is called
        Then two BankProblem instances are returned
        """
        _write_yaml(
            tmp_path / "arrays.yaml",
            {
                "category": "arrays-and-hashing",
                "problems": [
                    _sample_problem(id="p1", title="Problem 1"),
                    _sample_problem(id="p2", title="Problem 2"),
                ],
            },
        )
        problems = load_bank(tmp_path)

        assert len(problems) == 2
        assert problems[0].id == "p1"
        assert problems[1].id == "p2"

    @pytest.mark.unit
    def test_inherits_file_level_category(self, tmp_path):
        """
        Scenario: Per-problem category is inherited from file metadata
        Given a YAML file with file-level category but no per-problem category
        When load_bank is called
        Then each problem inherits the file-level category
        """
        problem_data = _sample_problem(id="p1")
        del problem_data["category"]
        _write_yaml(
            tmp_path / "trees.yaml",
            {"category": "trees", "problems": [problem_data]},
        )
        problems = load_bank(tmp_path)

        assert len(problems) == 1
        assert problems[0].category == "trees"

    @pytest.mark.unit
    def test_skips_underscore_prefixed_files(self, tmp_path):
        """
        Scenario: Files starting with '_' are ignored
        Given a _manifest.yaml and a regular YAML file
        When load_bank is called
        Then only the regular file's problems are loaded
        """
        _write_yaml(tmp_path / "_manifest.yaml", {"version": "1.0"})
        _write_yaml(
            tmp_path / "stack.yaml",
            {"problems": [_sample_problem(id="s1", category="stack")]},
        )
        problems = load_bank(tmp_path)

        assert len(problems) == 1
        assert problems[0].id == "s1"

    @pytest.mark.unit
    def test_skips_empty_files(self, tmp_path):
        """
        Scenario: YAML files with no 'problems' key are skipped
        Given an empty YAML file
        When load_bank is called
        Then no problems are returned
        """
        _write_yaml(tmp_path / "empty.yaml", {})
        problems = load_bank(tmp_path)

        assert problems == []

    @pytest.mark.unit
    def test_skips_files_without_problems_key(self, tmp_path):
        """
        Scenario: YAML files with unrelated content are skipped
        Given a YAML file with data but no 'problems' key
        When load_bank is called
        Then no problems are returned
        """
        _write_yaml(tmp_path / "meta.yaml", {"version": "2.0", "author": "test"})
        problems = load_bank(tmp_path)

        assert problems == []

    @pytest.mark.unit
    def test_loads_sorted_by_filename(self, tmp_path):
        """
        Scenario: Problems are loaded in filename-sorted order
        Given two YAML files named 'b.yaml' and 'a.yaml'
        When load_bank is called
        Then problems from 'a.yaml' come first
        """
        _write_yaml(
            tmp_path / "b.yaml",
            {"problems": [_sample_problem(id="b1", category="graphs")]},
        )
        _write_yaml(
            tmp_path / "a.yaml",
            {"problems": [_sample_problem(id="a1", category="trees")]},
        )
        problems = load_bank(tmp_path)

        assert problems[0].id == "a1"
        assert problems[1].id == "b1"

    @pytest.mark.unit
    def test_empty_directory(self, tmp_path):
        """
        Scenario: Empty directory returns empty list
        Given a directory with no YAML files
        When load_bank is called
        Then an empty list is returned
        """
        problems = load_bank(tmp_path)
        assert problems == []


# ---------------------------------------------------------------------------
# Feature: filter_problems
# ---------------------------------------------------------------------------


class TestFilterProblems:
    """
    Feature: Filtering problems by category, difficulty, and tags

    As a gauntlet engine
    I want to filter the problem bank by various criteria
    So that sessions can target specific skill areas
    """

    @pytest.fixture()
    def bank(self):
        """Return a small bank of three problems across categories."""
        return [
            BankProblem(
                id="p1",
                title="Two Sum",
                category="arrays-and-hashing",
                difficulty=Difficulty.EASY,
                prompt="...",
                tags=["hash-map", "array"],
            ),
            BankProblem(
                id="p2",
                title="Valid Parentheses",
                category="stack",
                difficulty=Difficulty.EASY,
                prompt="...",
                tags=["stack"],
            ),
            BankProblem(
                id="p3",
                title="Merge K Lists",
                category="heap-priority-queue",
                difficulty=Difficulty.HARD,
                prompt="...",
                tags=["heap", "linked-list"],
            ),
        ]

    @pytest.mark.unit
    def test_filter_by_category(self, bank):
        """
        Scenario: Filtering by category returns matching problems
        Given a bank with problems in different categories
        When filtered by 'stack'
        Then only the stack problem is returned
        """
        result = filter_problems(bank, category="stack")

        assert len(result) == 1
        assert result[0].id == "p2"

    @pytest.mark.unit
    def test_filter_by_difficulty(self, bank):
        """
        Scenario: Filtering by difficulty returns matching problems
        Given a bank with easy and hard problems
        When filtered by EASY
        Then two easy problems are returned
        """
        result = filter_problems(bank, difficulty=Difficulty.EASY)

        assert len(result) == 2
        assert all(p.difficulty == Difficulty.EASY for p in result)

    @pytest.mark.unit
    def test_filter_by_tags(self, bank):
        """
        Scenario: Filtering by tags returns problems with any matching tag
        Given a bank with tagged problems
        When filtered by ['heap']
        Then only the heap problem is returned
        """
        result = filter_problems(bank, tags=["heap"])

        assert len(result) == 1
        assert result[0].id == "p3"

    @pytest.mark.unit
    def test_filter_combined(self, bank):
        """
        Scenario: Multiple filters are combined with AND logic
        Given a bank with various problems
        When filtered by category='arrays-and-hashing' AND difficulty=EASY
        Then only the matching problem is returned
        """
        result = filter_problems(
            bank, category="arrays-and-hashing", difficulty=Difficulty.EASY
        )

        assert len(result) == 1
        assert result[0].id == "p1"

    @pytest.mark.unit
    def test_filter_no_match(self, bank):
        """
        Scenario: Filters that match nothing return empty list
        Given a bank with problems
        When filtered by a non-existent category
        Then an empty list is returned
        """
        result = filter_problems(bank, category="nonexistent")

        assert result == []

    @pytest.mark.unit
    def test_filter_none_returns_all(self, bank):
        """
        Scenario: No filters returns all problems
        Given a bank with three problems
        When filter_problems is called with no criteria
        Then all three problems are returned
        """
        result = filter_problems(bank)

        assert len(result) == 3


# ---------------------------------------------------------------------------
# Feature: bank_problem_to_challenge
# ---------------------------------------------------------------------------


class TestBankProblemToChallenge:
    """
    Feature: Converting BankProblems to Challenges

    As the gauntlet engine
    I want to convert bank problems into Challenge objects
    So that they integrate with spaced-repetition scoring
    """

    @pytest.mark.unit
    def test_converts_basic_fields(self):
        """
        Scenario: A BankProblem becomes a Challenge with correct fields
        Given a BankProblem with all fields set
        When converted to a Challenge
        Then prompt, hints, answer, and context are mapped correctly
        """
        problem = BankProblem(
            id="two-sum",
            title="Two Sum",
            category="arrays-and-hashing",
            difficulty=Difficulty.EASY,
            prompt="Find two numbers that add up to target.",
            hints=["Use a hash map."],
            solution_outline="Dict lookup for complement.",
            tags=["hash-map"],
            challenge_type="explain_why",
        )
        challenge = bank_problem_to_challenge(problem)

        assert challenge.prompt == problem.prompt
        assert challenge.hints == problem.hints
        assert challenge.answer == problem.solution_outline
        assert challenge.context == "Two Sum [arrays-and-hashing]"

    @pytest.mark.unit
    def test_difficulty_maps_to_numeric(self):
        """
        Scenario: Difficulty enum maps to 1-4 scale on Challenge
        Given a HARD BankProblem
        When converted to a Challenge
        Then challenge.difficulty is 3
        """
        problem = BankProblem(
            id="merge-k",
            title="Merge K Lists",
            category="heap-priority-queue",
            difficulty=Difficulty.HARD,
            prompt="Merge k sorted linked lists.",
        )
        challenge = bank_problem_to_challenge(problem)

        assert challenge.difficulty == 3

    @pytest.mark.unit
    def test_challenge_id_prefixed_with_bank(self):
        """
        Scenario: Challenge ID starts with 'bank-' prefix
        Given a BankProblem
        When converted to a Challenge
        Then the Challenge id starts with 'bank-'
        """
        problem = BankProblem(
            id="x",
            title="X",
            category="trees",
            difficulty=Difficulty.MEDIUM,
            prompt="...",
        )
        challenge = bank_problem_to_challenge(problem)

        assert challenge.id.startswith("bank-")

    @pytest.mark.unit
    def test_knowledge_entry_id_prefixed_with_bank(self):
        """
        Scenario: Knowledge entry ID encodes the bank problem ID
        Given a BankProblem with id 'two-sum'
        When converted to a Challenge
        Then knowledge_entry_id is 'bank:two-sum'
        """
        problem = BankProblem(
            id="two-sum",
            title="Two Sum",
            category="arrays-and-hashing",
            difficulty=Difficulty.EASY,
            prompt="...",
        )
        challenge = bank_problem_to_challenge(problem)

        assert challenge.knowledge_entry_id == "bank:two-sum"

    @pytest.mark.unit
    def test_challenge_type_mapping(self):
        """
        Scenario: Valid challenge_type maps to ChallengeType enum
        Given a BankProblem with challenge_type='trace'
        When converted to a Challenge
        Then the Challenge type is ChallengeType.TRACE
        """
        problem = BankProblem(
            id="x",
            title="X",
            category="trees",
            difficulty=Difficulty.MEDIUM,
            prompt="...",
            challenge_type="trace",
        )
        challenge = bank_problem_to_challenge(problem)

        assert challenge.type == ChallengeType.TRACE

    @pytest.mark.unit
    def test_invalid_challenge_type_defaults_to_explain_why(self):
        """
        Scenario: Unknown challenge_type falls back to explain_why
        Given a BankProblem with an unrecognized challenge_type
        When converted to a Challenge
        Then ChallengeType.EXPLAIN_WHY is used
        """
        problem = BankProblem(
            id="x",
            title="X",
            category="trees",
            difficulty=Difficulty.MEDIUM,
            prompt="...",
            challenge_type="invalid_type",
        )
        challenge = bank_problem_to_challenge(problem)

        assert challenge.type == ChallengeType.EXPLAIN_WHY

    @pytest.mark.unit
    def test_scope_files_empty(self):
        """
        Scenario: Bank problems have no scope files
        Given a BankProblem (standalone, not tied to codebase files)
        When converted to a Challenge
        Then scope_files is an empty list
        """
        problem = BankProblem(
            id="x",
            title="X",
            category="trees",
            difficulty=Difficulty.EASY,
            prompt="...",
        )
        challenge = bank_problem_to_challenge(problem)

        assert challenge.scope_files == []


# ---------------------------------------------------------------------------
# Feature: load_manifest
# ---------------------------------------------------------------------------


class TestLoadManifest:
    """
    Feature: Loading the problem bank manifest

    As a gauntlet engine
    I want to load category metadata from _manifest.yaml
    So that the UI can display category information
    """

    @pytest.mark.unit
    def test_loads_manifest(self, tmp_path):
        """
        Scenario: Valid manifest file is loaded
        Given a _manifest.yaml with version and categories
        When load_manifest is called
        Then the returned dict contains version and categories
        """
        manifest_data = {
            "version": "1.0",
            "categories": [
                {"id": "trees", "name": "Trees", "neetcode_count": 15},
            ],
        }
        _write_yaml(tmp_path / "_manifest.yaml", manifest_data)
        result = load_manifest(tmp_path)

        assert result["version"] == "1.0"
        assert len(result["categories"]) == 1
        assert result["categories"][0]["id"] == "trees"

    @pytest.mark.unit
    def test_missing_manifest_returns_empty_dict(self, tmp_path):
        """
        Scenario: Missing manifest file returns empty dict
        Given a directory with no _manifest.yaml
        When load_manifest is called
        Then an empty dict is returned
        """
        result = load_manifest(tmp_path)

        assert result == {}

    @pytest.mark.unit
    def test_empty_manifest_returns_empty_dict(self, tmp_path):
        """
        Scenario: Empty manifest file returns empty dict
        Given an empty _manifest.yaml
        When load_manifest is called
        Then an empty dict is returned
        """
        (tmp_path / "_manifest.yaml").write_text("")
        result = load_manifest(tmp_path)

        assert result == {}


# ---------------------------------------------------------------------------
# Feature: generate_bank_challenge integration
# ---------------------------------------------------------------------------


class TestGenerateBankChallenge:
    """
    Feature: Challenge generation via challenges.py integration

    As the gauntlet engine
    I want generate_bank_challenge to delegate to problem_bank
    So that the public API stays in challenges.py
    """

    @pytest.mark.unit
    def test_generate_bank_challenge_returns_challenge(self):
        """
        Scenario: generate_bank_challenge produces a valid Challenge
        Given a BankProblem
        When generate_bank_challenge is called
        Then a Challenge object is returned with the correct prompt
        """
        from unittest.mock import patch

        from gauntlet.challenges import generate_bank_challenge

        problem = BankProblem(
            id="valid-parens",
            title="Valid Parentheses",
            category="stack",
            difficulty=Difficulty.EASY,
            prompt="Determine if input string has valid brackets.",
            hints=["Use a stack."],
            solution_outline="Push opens, pop on close, check match.",
        )

        with patch(
            "gauntlet.challenges._generate_problem_variation",
            return_value=problem,
        ):
            challenge = generate_bank_challenge(problem)

        assert challenge.prompt == problem.prompt
        assert challenge.id.startswith("bank-")
        assert challenge.difficulty == 1
