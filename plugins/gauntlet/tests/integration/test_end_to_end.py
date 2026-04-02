"""End-to-end integration tests for the gauntlet plugin."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from gauntlet.challenges import generate_challenge, select_challenge_type
from gauntlet.extraction import extract_from_file
from gauntlet.knowledge_store import KnowledgeStore
from gauntlet.models import DeveloperProgress
from gauntlet.progress import ProgressTracker
from gauntlet.query import get_context_for_files, query_knowledge
from gauntlet.scoring import evaluate_answer

# ---------------------------------------------------------------------------
# Feature: Full challenge loop
# ---------------------------------------------------------------------------


class TestFullChallengeLoop:
    """
    Feature: End-to-end challenge loop

    As a developer using gauntlet
    I want to go from code extraction through challenge evaluation to
    progress recording in a single flow
    So that every component integrates correctly
    """

    @pytest.mark.integration
    def test_extract_challenge_evaluate_record(self, tmp_path: Path) -> None:
        """
        Scenario: Full loop from file extraction to recorded answer
        Given a Python source file with a documented function
        When extract_from_file, KnowledgeStore.save, generate_challenge,
             evaluate_answer, and ProgressTracker.record_answer are called
             in sequence
        Then the progress history contains exactly one answer record with
             a valid result
        """
        # Arrange: write a Python source file
        src = tmp_path / "billing.py"
        src.write_text(
            textwrap.dedent(
                """\
                from __future__ import annotations


                def calculate_discount(price: float, tier: str) -> float:
                    \"\"\"Calculate business discount based on customer tier.

                    Business rules:
                    - Gold tier receives a 20 percent discount.
                    - Standard tier receives no discount.
                    \"\"\"
                    if tier == "gold":
                        return price * 0.80
                    return price
                """
            )
        )

        # Act 1: extract
        entries = extract_from_file(src)
        assert len(entries) >= 1, "Expected at least one entry from extraction"

        # Act 2: save to knowledge store
        gauntlet_dir = tmp_path / ".gauntlet"
        store = KnowledgeStore(gauntlet_dir)
        store.save(entries)
        assert (gauntlet_dir / "knowledge.json").exists()

        # Act 3: generate a challenge
        entry = entries[0]
        challenge = generate_challenge(entry, "multiple_choice")
        assert challenge.prompt
        assert challenge.answer

        # Act 4: evaluate an answer (use the correct answer)
        result = evaluate_answer(challenge, challenge.answer)
        assert result in ("pass", "partial", "fail")

        # Act 5: record the answer
        tracker = ProgressTracker(gauntlet_dir)
        progress = DeveloperProgress(developer_id="dev@example.com")
        tracker.record_answer(
            progress=progress,
            challenge_id=challenge.id,
            knowledge_entry_id=entry.id,
            challenge_type=challenge.type,
            category=entry.category,
            difficulty=entry.difficulty,
            result=result,
        )

        # Assert: progress was persisted and has one record
        loaded = tracker.get_or_create("dev@example.com")
        assert len(loaded.history) == 1
        assert loaded.history[0].result in ("pass", "partial", "fail")

    @pytest.mark.integration
    def test_adaptive_selection_after_multiple_answers(self, tmp_path: Path) -> None:
        """
        Scenario: Adaptive type selection shifts after repeated correct answers
        Given a developer with a streak of 3 correct multiple_choice answers
        When select_challenge_type is called
        Then multiple_choice gets lower weight and other types have higher
             relative weight (the returned type may vary, but selection
             completes without error)
        """
        # Arrange: build progress with 3 passing multiple_choice answers
        gauntlet_dir = tmp_path / ".gauntlet"
        tracker = ProgressTracker(gauntlet_dir)
        progress = DeveloperProgress(developer_id="dev@example.com")

        src = tmp_path / "mod.py"
        src.write_text('def do_thing():\n    """architecture pattern."""\n    pass\n')
        entries = extract_from_file(src)
        assert entries

        store = KnowledgeStore(gauntlet_dir)
        store.save(entries)

        for _ in range(3):
            challenge = generate_challenge(entries[0], "multiple_choice")
            tracker.record_answer(
                progress=progress,
                challenge_id=challenge.id,
                knowledge_entry_id=entries[0].id,
                challenge_type="multiple_choice",
                category=entries[0].category,
                difficulty=entries[0].difficulty,
                result="pass",
            )

        # Act: select a challenge type
        selected = select_challenge_type(progress)

        # Assert: a valid type is returned
        valid_types = {
            "multiple_choice",
            "code_completion",
            "trace",
            "explain_why",
            "spot_bug",
            "dependency_map",
        }
        assert selected in valid_types


# ---------------------------------------------------------------------------
# Feature: Query API after extraction
# ---------------------------------------------------------------------------


class TestQueryAPIAfterExtraction:
    """
    Feature: Query API integration

    As an agent consuming gauntlet knowledge
    I want to extract a codebase, store the results, then query them
    So that downstream tools get accurate, filtered knowledge
    """

    @pytest.mark.integration
    def test_extract_store_query_returns_matching_entries(self, tmp_path: Path) -> None:
        """
        Scenario: Query by module name after extraction and store
        Given a Python file extracted and saved to the knowledge store
        When query_knowledge is called with the module name as a file filter
        Then the returned entries include the extracted concept
        """
        # Arrange: write and extract a source file
        src = tmp_path / "payments.py"
        src.write_text(
            textwrap.dedent(
                """\
                from __future__ import annotations


                def process_payment(amount: float) -> bool:
                    \"\"\"Process a payment transaction.

                    Validates the amount and calls the payment gateway.
                    Returns True on success.
                    \"\"\"
                    if amount <= 0:
                        return False
                    return True
                """
            )
        )

        entries = extract_from_file(src)
        gauntlet_dir = tmp_path / ".gauntlet"
        store = KnowledgeStore(gauntlet_dir)
        store.save(entries)

        # Act: query by module name
        results = query_knowledge(gauntlet_dir, files=["payments"])
        assert len(results) >= 1
        concepts = [e.concept for e in results]
        assert "process_payment" in concepts

    @pytest.mark.integration
    def test_get_context_for_files_returns_markdown(self, tmp_path: Path) -> None:
        """
        Scenario: get_context_for_files produces markdown summary
        Given knowledge entries saved for a module
        When get_context_for_files is called with that module name
        Then the output is a non-empty markdown string containing the concept
        """
        # Arrange
        src = tmp_path / "auth.py"
        src.write_text(
            textwrap.dedent(
                """\
                from __future__ import annotations


                def verify_token(token: str) -> bool:
                    \"\"\"Verify a JWT token for authentication.

                    Checks signature, expiry, and issuer claims.
                    \"\"\"
                    return bool(token)
                """
            )
        )

        entries = extract_from_file(src)
        gauntlet_dir = tmp_path / ".gauntlet"
        store = KnowledgeStore(gauntlet_dir)
        store.save(entries)

        # Act
        context = get_context_for_files(gauntlet_dir, files=["auth"])

        # Assert
        assert "## Gauntlet Knowledge Context" in context
        assert "verify_token" in context

    @pytest.mark.integration
    def test_query_with_no_matching_files_returns_empty(self, tmp_path: Path) -> None:
        """
        Scenario: Query for files not in knowledge base returns empty list
        Given a knowledge base with entries for 'payments'
        When query_knowledge is called with files=['nonexistent']
        Then an empty list is returned
        """
        # Arrange
        src = tmp_path / "payments.py"
        src.write_text('def pay():\n    """business logic payment."""\n    pass\n')
        entries = extract_from_file(src)
        gauntlet_dir = tmp_path / ".gauntlet"
        KnowledgeStore(gauntlet_dir).save(entries)

        # Act
        results = query_knowledge(gauntlet_dir, files=["nonexistent_module"])

        # Assert
        assert results == []
