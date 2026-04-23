"""Tests for proof_of_work Nen Court validator (issue #406).

Feature: Verify agent output contains evidence references.

As the Night Market vow enforcement system
I want a Nen Court validator that audits proof-of-work claims
So that "should work" assertions without evidence are flagged.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def validator_module():
    """Import proof_of_work validator via importlib."""
    validators_path = Path(__file__).resolve().parents[3] / "validators"
    module_path = validators_path / "proof_of_work.py"
    spec = importlib.util.spec_from_file_location("proof_of_work", module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["proof_of_work"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestEvidenceRefDetection:
    """Feature: Detect [E1], [E2] style evidence references."""

    @pytest.mark.unit
    def test_finds_e1_reference(self, validator_module):
        """A text containing [E1] yields an evidence ref."""
        refs = validator_module.find_evidence_refs("Tested with foo [E1] -- passes.")
        assert "E1" in refs

    @pytest.mark.unit
    def test_finds_multiple_refs(self, validator_module):
        """Multiple [E1]..[E5] refs are all collected."""
        refs = validator_module.find_evidence_refs("Saw [E1] and [E2] then later [E5].")
        assert refs == {"E1", "E2", "E5"}

    @pytest.mark.unit
    def test_ignores_partial_matches(self, validator_module):
        """[Edge] or [Equals] are NOT evidence refs."""
        refs = validator_module.find_evidence_refs("[Edge case] vs [Equals 1]")
        assert refs == set()

    @pytest.mark.unit
    def test_handles_empty_text(self, validator_module):
        """Empty input yields empty set."""
        assert validator_module.find_evidence_refs("") == set()


class TestUnsupportedClaimDetection:
    """Feature: Flag forbidden 'should work' style language without evidence."""

    @pytest.mark.unit
    def test_should_work_without_evidence_flagged(self, validator_module):
        """Phrase 'should work' with no [Ex] in same paragraph is flagged."""
        text = "The fix is straightforward and should work in production."
        claims = validator_module.find_unsupported_claims(text)
        assert any("should work" in c.lower() for c in claims)

    @pytest.mark.unit
    def test_looks_correct_without_evidence_flagged(self, validator_module):
        """'looks correct' without evidence is flagged."""
        claims = validator_module.find_unsupported_claims(
            "The implementation looks correct to me."
        )
        assert any("looks correct" in c.lower() for c in claims)

    @pytest.mark.unit
    def test_should_work_with_evidence_passes(self, validator_module):
        """When 'should work' is paired with an [E1] ref, no flag."""
        text = "The fix should work [E1] -- tested with the failing case."
        claims = validator_module.find_unsupported_claims(text)
        assert claims == []

    @pytest.mark.unit
    def test_normal_descriptive_text_passes(self, validator_module):
        """Plain descriptive text with no claim phrases produces no flags."""
        text = "The function reads a file and returns its contents."
        assert validator_module.find_unsupported_claims(text) == []


class TestStatusDetection:
    """Feature: Extract PASS/FAIL/BLOCKED status from output."""

    @pytest.mark.unit
    def test_status_pass(self, validator_module):
        """Text containing 'Status: PASS' yields 'pass' status."""
        assert validator_module.extract_status("Status: PASS") == "pass"

    @pytest.mark.unit
    def test_status_fail(self, validator_module):
        """Text containing 'Status: FAIL' yields 'fail'."""
        assert validator_module.extract_status("Status: FAIL") == "fail"

    @pytest.mark.unit
    def test_status_blocked(self, validator_module):
        """Text containing 'Status: BLOCKED' yields 'blocked'."""
        assert validator_module.extract_status("Status: BLOCKED") == "blocked"

    @pytest.mark.unit
    def test_status_missing_returns_none(self, validator_module):
        """No status line -> None."""
        assert validator_module.extract_status("Hello world") is None


class TestValidateOutput:
    """Feature: Validate a complete agent output document.

    As the validator
    I want to combine evidence-ref checks, unsupported-claim checks,
    and status checks into a single verdict.
    """

    @pytest.mark.unit
    def test_complete_evidence_passes(self, validator_module):
        """Output with min_evidence refs and no unsupported claims passes."""
        text = (
            "Implemented the fix.  Verified with test_foo [E1] and "
            "test_bar [E2].  Status: PASS.\n"
        )
        result = validator_module.validate_output(text, min_evidence=2)
        assert result["verdict"] == "pass"

    @pytest.mark.unit
    def test_too_few_refs_violates(self, validator_module):
        """Below min_evidence threshold -> violation."""
        text = "Did the thing [E1].  Status: PASS."
        result = validator_module.validate_output(text, min_evidence=3)
        assert result["verdict"] == "violation"
        assert any("evidence" in str(ev).lower() for ev in result["evidence"])

    @pytest.mark.unit
    def test_unsupported_claim_violates(self, validator_module):
        """An unsupported 'should work' claim violates regardless of refs."""
        text = (
            "Did stuff [E1] [E2] [E3].  This new approach should work.  Status: PASS."
        )
        result = validator_module.validate_output(text, min_evidence=3)
        assert result["verdict"] == "violation"
        assert any("should work" in str(ev).lower() for ev in result["evidence"])

    @pytest.mark.unit
    def test_no_status_inconclusive(self, validator_module):
        """Missing status line yields inconclusive."""
        text = "Did stuff [E1] [E2] [E3]."
        result = validator_module.validate_output(text, min_evidence=3)
        assert result["verdict"] == "inconclusive"

    @pytest.mark.unit
    def test_explicit_fail_status_passes_validator(self, validator_module):
        """A FAIL status is honest reporting, validator returns pass.

        The validator audits proof-of-work compliance, not whether the
        underlying work succeeded.  An honest FAIL with evidence is
        better than a dishonest PASS without evidence.
        """
        text = "Tried fix [E1] [E2] [E3], regression in test_x. Status: FAIL."
        result = validator_module.validate_output(text, min_evidence=3)
        assert result["verdict"] == "pass"


class TestCliEntry:
    """Feature: Validator runs as a standalone CLI script."""

    @pytest.mark.unit
    def test_main_with_text_input(self, validator_module, capsys):
        payload = json.dumps(
            {
                "text": "Did work [E1] [E2] [E3]. Status: PASS.",
                "min_evidence": 3,
            }
        )
        with patch("sys.stdin", StringIO(payload)):
            with pytest.raises(SystemExit) as exc:
                validator_module.main()
        assert exc.value.code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["verdict"] == "pass"

    @pytest.mark.unit
    def test_main_violation_exit_one(self, validator_module, capsys):
        payload = json.dumps({"text": "Should work just fine.", "min_evidence": 1})
        with patch("sys.stdin", StringIO(payload)):
            with pytest.raises(SystemExit) as exc:
                validator_module.main()
        assert exc.value.code == 1

    @pytest.mark.unit
    def test_main_inconclusive_exit_two(self, validator_module, capsys):
        payload = json.dumps({"text": "Did stuff [E1] [E2]", "min_evidence": 1})
        with patch("sys.stdin", StringIO(payload)):
            with pytest.raises(SystemExit) as exc:
                validator_module.main()
        assert exc.value.code == 2

    @pytest.mark.unit
    def test_main_malformed_input_inconclusive(self, validator_module, capsys):
        with patch("sys.stdin", StringIO("not json")):
            with pytest.raises(SystemExit) as exc:
                validator_module.main()
        assert exc.value.code == 2
