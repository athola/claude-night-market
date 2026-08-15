"""Tests for CLI scripts: extractor, challenge_engine, answer_evaluator,
progress_tracker.
"""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

import pytest
from answer_evaluator import main as answer_main
from challenge_engine import main as challenge_main
from extractor import main as extractor_main
from progress_tracker import main as progress_main

# ---------------------------------------------------------------------------
# Feature: extractor CLI
# ---------------------------------------------------------------------------


class TestExtractorCLI:
    """
    Feature: extractor.py CLI

    As a developer
    I want a CLI that extracts knowledge from a Python directory
    So that I can rebuild the knowledge base without running Claude
    """

    @pytest.mark.unit
    def test_prints_json_to_stdout(self, tmp_path: Path) -> None:
        """
        Scenario: Extract from directory, print JSON to stdout
        Given a directory with a Python source file
        When main() is called with no --output flag
        Then it exits 0 and prints a JSON array to stdout
        """
        src = tmp_path / "mymodule.py"
        src.write_text(
            'def calculate_discount(price):\n    """business rule."""\n    return price * 0.9\n'
        )

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exit_code = extractor_main([str(tmp_path)])

        assert exit_code == 0
        parsed = json.loads(buf.getvalue())
        assert isinstance(parsed, list)
        assert len(parsed) >= 1

    @pytest.mark.unit
    def test_saves_to_output_dir(self, tmp_path: Path) -> None:
        """
        Scenario: Extract and save to gauntlet dir
        Given a directory with a Python source file and an --output path
        When main() is called with --output
        Then knowledge.json is written to the output directory
        """
        src = tmp_path / "src"
        src.mkdir()
        (src / "module.py").write_text(
            'def validate(x):\n    """validate rule."""\n    return x > 0\n'
        )

        out = tmp_path / "gauntlet"
        exit_code = extractor_main([str(src), "--output", str(out)])

        assert exit_code == 0
        assert (out / "knowledge.json").exists()
        data = json.loads((out / "knowledge.json").read_text())
        assert isinstance(data, list)

    @pytest.mark.unit
    def test_text_format_output(self, tmp_path: Path) -> None:
        """
        Scenario: Text-format output
        Given a directory with a Python source file
        When main() is called with --format text
        Then stdout contains human-readable lines, not JSON
        """
        src = tmp_path / "mod.py"
        src.write_text('def my_func():\n    """do something."""\n    pass\n')

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exit_code = extractor_main([str(tmp_path), "--format", "text"])

        assert exit_code == 0
        assert "my_func" in buf.getvalue()

    @pytest.mark.unit
    def test_missing_target_dir_returns_error(self, tmp_path: Path) -> None:
        """
        Scenario: Non-existent target directory
        Given a path that does not exist
        When main() is called with that path
        Then it exits with a non-zero code
        """
        missing = tmp_path / "does_not_exist"
        exit_code = extractor_main([str(missing)])
        assert exit_code != 0


# ---------------------------------------------------------------------------
# Feature: challenge_engine CLI
# ---------------------------------------------------------------------------


class TestChallengeEngineCLI:
    """
    Feature: challenge_engine.py CLI

    As a developer
    I want a CLI that generates a challenge from the knowledge base
    So that pre-commit hooks and scripts can request challenges
    """

    @pytest.mark.unit
    def test_generates_challenge_json(self, tmp_path: Path) -> None:
        """
        Scenario: Generate a challenge from a populated knowledge base
        Given a gauntlet dir with knowledge.json containing one entry
        When main() is called
        Then it exits 0 and prints a JSON object with 'prompt' and 'type'
        """
        gauntlet_dir = tmp_path / ".gauntlet"
        gauntlet_dir.mkdir()
        entry = {
            "id": "abc123",
            "category": "business_logic",
            "module": "billing",
            "concept": "calculate_discount",
            "detail": "Applies a 10% discount to the price.",
            "difficulty": 2,
            "extracted_at": "2024-01-01T00:00:00+00:00",
            "source": "code",
            "related_files": [],
            "tags": ["billing"],
            "consumers": [],
        }
        (gauntlet_dir / "knowledge.json").write_text(json.dumps([entry]))

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exit_code = challenge_main(
                [str(gauntlet_dir), "--developer", "dev@example.com"]
            )

        assert exit_code == 0
        parsed = json.loads(buf.getvalue())
        assert "prompt" in parsed
        assert "type" in parsed

    @pytest.mark.unit
    def test_text_format_output(self, tmp_path: Path) -> None:
        """
        Scenario: Text format output
        Given a populated knowledge base
        When main() is called with --format text
        Then stdout contains the challenge prompt as plain text
        """
        gauntlet_dir = tmp_path / ".gauntlet"
        gauntlet_dir.mkdir()
        entry = {
            "id": "abc123",
            "category": "architecture",
            "module": "core",
            "concept": "EventBus",
            "detail": "Central message broker.",
            "difficulty": 3,
            "extracted_at": "2024-01-01T00:00:00+00:00",
            "source": "code",
            "related_files": [],
            "tags": ["arch"],
            "consumers": [],
        }
        (gauntlet_dir / "knowledge.json").write_text(json.dumps([entry]))

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exit_code = challenge_main([str(gauntlet_dir), "--format", "text"])

        assert exit_code == 0
        assert len(buf.getvalue()) > 0


# ---------------------------------------------------------------------------
# Feature: answer_evaluator CLI
# ---------------------------------------------------------------------------


class TestAnswerEvaluatorCLI:
    """
    Feature: answer_evaluator.py CLI

    As a developer
    I want a CLI that scores an answer against a challenge
    So that pre-commit hooks can evaluate responses automatically
    """

    @pytest.mark.unit
    def test_pass_result_for_correct_letter(self, tmp_path: Path) -> None:
        """
        Scenario: Correct multiple-choice answer
        Given a multiple_choice challenge JSON where the answer is 'A'
        When main() is called with answer 'A'
        Then it exits 0 and prints result 'pass'
        """
        challenge = {
            "id": "ch-001",
            "type": "multiple_choice",
            "knowledge_entry_id": "abc123",
            "difficulty": 2,
            "prompt": "What is X?",
            "context": "some context",
            "answer": "A",
            "options": ["correct", "wrong1", "wrong2", "wrong3"],
            "hints": [],
            "scope_files": [],
        }
        challenge_file = tmp_path / "challenge.json"
        challenge_file.write_text(json.dumps(challenge))

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exit_code = answer_main([str(challenge_file), "A"])

        assert exit_code == 0
        assert "pass" in buf.getvalue()

    @pytest.mark.unit
    def test_fail_result_for_wrong_letter(self, tmp_path: Path) -> None:
        """
        Scenario: Incorrect multiple-choice answer
        Given a multiple_choice challenge with answer 'A'
        When main() is called with answer 'C'
        Then the output contains 'fail'
        """
        challenge = {
            "id": "ch-002",
            "type": "multiple_choice",
            "knowledge_entry_id": "abc123",
            "difficulty": 2,
            "prompt": "What is X?",
            "context": "some context",
            "answer": "A",
            "options": ["correct", "wrong1", "wrong2", "wrong3"],
            "hints": [],
            "scope_files": [],
        }
        challenge_file = tmp_path / "challenge.json"
        challenge_file.write_text(json.dumps(challenge))

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exit_code = answer_main([str(challenge_file), "C"])

        assert exit_code == 0
        assert "fail" in buf.getvalue()


# ---------------------------------------------------------------------------
# Feature: progress_tracker CLI
# ---------------------------------------------------------------------------


class TestProgressTrackerCLI:
    """
    Feature: progress_tracker.py CLI

    As a developer
    I want a CLI that shows my challenge progress stats
    So that I can track my learning without opening a chat session
    """

    @pytest.mark.unit
    def test_shows_stats_for_new_developer(self, tmp_path: Path) -> None:
        """
        Scenario: Fresh developer with no history
        Given a gauntlet dir with no progress files
        When main() is called for a developer
        Then it exits 0 and prints stats (accuracy = 0)
        """
        gauntlet_dir = tmp_path / ".gauntlet"
        gauntlet_dir.mkdir()

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exit_code = progress_main(
                [str(gauntlet_dir), "--developer", "dev@example.com"]
            )

        assert exit_code == 0
        assert "0" in buf.getvalue()

    @pytest.mark.unit
    def test_shows_stats_for_developer_with_history(self, tmp_path: Path) -> None:
        """
        Scenario: Developer with existing progress
        Given a gauntlet dir with a progress JSON file
        When main() is called for that developer
        Then it exits 0 and output reflects recorded history
        """
        gauntlet_dir = tmp_path / ".gauntlet"
        gauntlet_dir.mkdir()
        progress_dir = gauntlet_dir / "progress"
        progress_dir.mkdir()

        progress_data = {
            "developer_id": "dev@example.com",
            "history": [
                {
                    "challenge_id": "ch-001",
                    "knowledge_entry_id": "abc123",
                    "challenge_type": "multiple_choice",
                    "category": "business_logic",
                    "difficulty": 2,
                    "result": "pass",
                    "answered_at": "2024-01-01T00:00:00+00:00",
                }
            ],
            "last_seen": {},
            "streak": 1,
        }
        (progress_dir / "dev_example.com.json").write_text(json.dumps(progress_data))

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exit_code = progress_main(
                [str(gauntlet_dir), "--developer", "dev@example.com"]
            )

        assert exit_code == 0
        assert "1" in buf.getvalue()

    @pytest.mark.unit
    def test_json_format_output(self, tmp_path: Path) -> None:
        """
        Scenario: JSON format output
        Given a gauntlet dir
        When main() is called with --format json
        Then stdout is valid JSON
        """
        gauntlet_dir = tmp_path / ".gauntlet"
        gauntlet_dir.mkdir()

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exit_code = progress_main(
                [
                    str(gauntlet_dir),
                    "--developer",
                    "dev@example.com",
                    "--format",
                    "json",
                ]
            )

        assert exit_code == 0
        parsed = json.loads(buf.getvalue())
        assert "developer_id" in parsed or "accuracy" in parsed


# ---------------------------------------------------------------------------
# Feature: progress_tracker CLI --record
# ---------------------------------------------------------------------------


class TestProgressTrackerRecordCLI:
    """
    Feature: progress_tracker.py --record

    As a reviewing agent outside the challenge loop
    I want to persist an answer record from the CLI
    So that comprehension probes raised during PR review steer the same
    adaptive selector that gauntlet challenges use
    """

    @staticmethod
    def _record(**overrides: object) -> str:
        payload = {
            "challenge_id": "pr-1234-h1",
            "knowledge_entry_id": "pr:1234:src/foo.py:42",
            "challenge_type": "explain_why",
            "category": "data_flow",
            "difficulty": 3,
            "result": "partial",
        }
        payload.update(overrides)
        return json.dumps(payload)

    @pytest.mark.unit
    def test_records_answer_for_new_developer(self, tmp_path: Path) -> None:
        """
        Scenario: Record a probe result with no prior history
        Given a gauntlet dir with no progress files
        When main() is called with --record and a valid answer payload
        Then it exits 0 and the record is persisted to the progress file
        """
        gauntlet_dir = tmp_path / ".gauntlet"
        gauntlet_dir.mkdir()

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exit_code = progress_main(
                [
                    str(gauntlet_dir),
                    "--developer",
                    "dev@example.com",
                    "--record",
                    self._record(),
                ]
            )

        assert exit_code == 0
        saved = json.loads(
            (gauntlet_dir / "progress" / "dev_example.com.json").read_text()
        )
        assert len(saved["history"]) == 1
        assert saved["history"][0]["category"] == "data_flow"
        assert saved["history"][0]["knowledge_entry_id"] == "pr:1234:src/foo.py:42"

    @pytest.mark.unit
    def test_recorded_answer_is_visible_to_stats(self, tmp_path: Path) -> None:
        """
        Scenario: A recorded probe feeds the shared progress store
        Given a probe result recorded via --record
        When main() is called again in stats mode
        Then the stats reflect the recorded answer
        """
        gauntlet_dir = tmp_path / ".gauntlet"
        gauntlet_dir.mkdir()
        args = [str(gauntlet_dir), "--developer", "dev@example.com"]

        with contextlib.redirect_stdout(io.StringIO()):
            assert progress_main([*args, "--record", self._record(result="pass")]) == 0

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exit_code = progress_main([*args, "--format", "json"])

        assert exit_code == 0
        stats = json.loads(buf.getvalue())
        assert stats["total_challenges"] == 1

    @pytest.mark.unit
    def test_records_without_a_knowledge_base(self, tmp_path: Path) -> None:
        """
        Scenario: Graceful degradation when no knowledge base exists
        Given a gauntlet dir with no knowledge.json
        When a PR-sourced probe is recorded
        Then it still exits 0 and persists
        """
        gauntlet_dir = tmp_path / ".gauntlet"
        gauntlet_dir.mkdir()
        assert not (gauntlet_dir / "knowledge.json").exists()

        with contextlib.redirect_stdout(io.StringIO()):
            exit_code = progress_main(
                [
                    str(gauntlet_dir),
                    "--developer",
                    "d@e.com",
                    "--record",
                    self._record(),
                ]
            )

        assert exit_code == 0

    @pytest.mark.unit
    def test_rejects_malformed_record_json(self, tmp_path: Path) -> None:
        """
        Scenario: Malformed payload
        Given a --record value that is not valid JSON
        When main() is called
        Then it exits non-zero rather than writing a partial record
        """
        gauntlet_dir = tmp_path / ".gauntlet"
        gauntlet_dir.mkdir()

        with contextlib.redirect_stderr(io.StringIO()):
            exit_code = progress_main(
                [str(gauntlet_dir), "--developer", "d@e.com", "--record", "{not json"]
            )

        assert exit_code != 0
        assert not (gauntlet_dir / "progress" / "d_e.com.json").exists()

    @pytest.mark.unit
    def test_rejects_out_of_range_difficulty(self, tmp_path: Path) -> None:
        """
        Scenario: Difficulty outside the 1-4 scale
        Given a --record payload with difficulty 9
        When main() is called
        Then it exits non-zero and nothing is persisted
        """
        gauntlet_dir = tmp_path / ".gauntlet"
        gauntlet_dir.mkdir()

        with contextlib.redirect_stderr(io.StringIO()):
            exit_code = progress_main(
                [
                    str(gauntlet_dir),
                    "--developer",
                    "d@e.com",
                    "--record",
                    self._record(difficulty=9),
                ]
            )

        assert exit_code != 0
        assert not (gauntlet_dir / "progress" / "d_e.com.json").exists()
