"""Tests for the citation verifier.

The citation verifier re-reads each review finding's file:line and
confirms a verbatim anchor snippet matches the source. This is the
semantic complement to contract_validator (which checks structure).

Covers: VERIFIED on a resolving citation, FAILED on a bogus path, a
line out of range, an anchor mismatch, a path escaping the repo root,
a missing anchor; whitespace normalization; near-line window matching;
strictness modes; JSON and markdown finding inputs; CLI exit codes.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest
from scripts.citation_verifier import (
    Finding,
    VerificationReport,
    _findings_from_json,
    load_findings,
    main,
    parse_markdown_findings,
    verify_finding,
    verify_findings,
)

# --------------- fixtures ---------------


@pytest.fixture()
def source_repo(tmp_path: Path) -> Path:
    """A fake repo with one known source file to cite against."""
    src = tmp_path / "src"
    src.mkdir()
    # Line numbers are 1-indexed:
    #   1: import math
    #   2: (blank)
    #   3: def divide(a, b):
    #   4:     return a / b
    #   5: (blank)
    #   6: def mean(values):
    #   7:     return sum(values) / len(values)
    (src / "calc.py").write_text(
        textwrap.dedent("""\
            import math

            def divide(a, b):
                return a / b

            def mean(values):
                return sum(values) / len(values)
        """)
    )
    return tmp_path


def _finding(**overrides: object) -> dict:
    """A grounded finding dict aligned with conftest sample schema + anchor."""
    base = {
        "id": "F1",
        "title": "Division by zero unguarded",
        "severity": "High",
        "category": "Correctness",
        "file": "src/calc.py",
        "line": 4,
        "anchor": "return a / b",
        "evidence_refs": ["E1"],
        "recommendation": "Guard against b == 0.",
    }
    base.update(overrides)
    return base


# --------------- VERIFIED (grounded) ---------------


class TestVerifiedFindings:
    """Findings whose citation resolves and anchor matches the source."""

    def test_exact_line_anchor_verifies(self, source_repo: Path) -> None:
        result = verify_finding(Finding.from_dict(_finding()), source_repo)
        assert result.status == "VERIFIED"
        assert result.id == "F1"

    def test_whitespace_is_normalized(self, source_repo: Path) -> None:
        """Anchor with different surrounding/internal whitespace still matches."""
        f = _finding(anchor="return   a / b")
        result = verify_finding(Finding.from_dict(f), source_repo)
        assert result.status == "VERIFIED"

    def test_anchor_matches_within_window(self, source_repo: Path) -> None:
        """An off-by-one line still verifies within the default +/-2 window."""
        f = _finding(line=3, anchor="return a / b")  # actual text is on line 4
        result = verify_finding(Finding.from_dict(f), source_repo)
        assert result.status == "VERIFIED"

    def test_substring_anchor_verifies(self, source_repo: Path) -> None:
        """A verbatim substring of the cited line is sufficient."""
        f = _finding(line=7, anchor="sum(values) / len(values)")
        result = verify_finding(Finding.from_dict(f), source_repo)
        assert result.status == "VERIFIED"

    def test_report_passes_when_all_verified(self, source_repo: Path) -> None:
        report = verify_findings([_finding()], source_repo)
        assert isinstance(report, VerificationReport)
        assert report.passed is True
        assert report.verified_count == 1
        assert report.failed_count == 0

    def test_empty_findings_passes(self, source_repo: Path) -> None:
        """A clean review with zero findings is valid, not a failure."""
        report = verify_findings([], source_repo)
        assert report.passed is True
        assert report.verified_count == 0


# --------------- FAILED (hallucination guard) ---------------


class TestFailedFindings:
    """Each is a class of hallucinated or unresolvable citation."""

    def test_bogus_path_fails(self, source_repo: Path) -> None:
        f = _finding(file="src/does_not_exist.py")
        result = verify_finding(Finding.from_dict(f), source_repo)
        assert result.status == "FAILED"
        assert "not found" in result.reason.lower()

    def test_line_out_of_range_fails(self, source_repo: Path) -> None:
        f = _finding(line=999)
        result = verify_finding(Finding.from_dict(f), source_repo)
        assert result.status == "FAILED"
        assert "range" in result.reason.lower()

    def test_anchor_mismatch_fails(self, source_repo: Path) -> None:
        """Line exists but the quoted text was never there (hallucination).

        Subtly wrong: the source has ``a / b`` (float div); the anchor
        claims ``a // b`` (floor div). A grounded verifier must reject it.
        """
        f = _finding(anchor="return a // b")
        result = verify_finding(Finding.from_dict(f), source_repo)
        assert result.status == "FAILED"
        assert "anchor" in result.reason.lower()

    def test_missing_anchor_fails(self, source_repo: Path) -> None:
        """A finding with no anchor cannot be grounded."""
        f = _finding(anchor="")
        result = verify_finding(Finding.from_dict(f), source_repo)
        assert result.status == "FAILED"

    def test_path_escaping_repo_fails(self, source_repo: Path) -> None:
        """A path traversing outside the repo root is rejected."""
        f = _finding(file="../../../etc/passwd", anchor="root")
        result = verify_finding(Finding.from_dict(f), source_repo)
        assert result.status == "FAILED"
        assert "repo" in result.reason.lower() or "outside" in result.reason.lower()

    def test_report_fails_when_any_finding_fails(self, source_repo: Path) -> None:
        """One true + one false finding => report fails, statuses correct."""
        true_f = _finding(id="F1")
        false_f = _finding(id="F2", anchor="this text is not in the file")
        report = verify_findings([true_f, false_f], source_repo)
        assert report.passed is False
        assert report.verified_count == 1
        assert report.failed_count == 1
        failed_ids = {r.id for r in report.failures()}
        assert failed_ids == {"F2"}


# --------------- strictness ---------------


class TestStrictness:
    """Strictness mirrors the proof-of-work output-contract vocabulary."""

    def test_lenient_warns_but_passes(self, source_repo: Path) -> None:
        false_f = _finding(anchor="not in the file")
        report = verify_findings([false_f], source_repo, strictness="lenient")
        assert report.passed is True
        assert report.failed_count == 1  # still recorded, just not fatal

    def test_normal_fails_on_unresolved(self, source_repo: Path) -> None:
        false_f = _finding(anchor="not in the file")
        report = verify_findings([false_f], source_repo, strictness="normal")
        assert report.passed is False


# --------------- input parsing ---------------


class TestLoadFindings:
    """Findings load from a JSON list, a wrapped object, or markdown."""

    def test_load_json_list(self, source_repo: Path) -> None:
        path = source_repo / "findings.json"
        path.write_text(json.dumps([_finding()]))
        findings = load_findings(path)
        assert len(findings) == 1
        assert findings[0]["id"] == "F1"

    def test_load_wrapped_findings_object(self, source_repo: Path) -> None:
        """An object with a top-level 'findings' key is unwrapped."""
        path = source_repo / "report.json"
        path.write_text(json.dumps({"findings": [_finding(), _finding(id="F2")]}))
        findings = load_findings(path)
        assert len(findings) == 2

    def test_parse_markdown_finding_block(self) -> None:
        """The structured-output markdown block is parseable as a fallback."""
        md = textwrap.dedent("""\
            ## Issues

            ### [HIGH] Division by zero unguarded
            - **Location**: src/calc.py:4
            - **Anchor**: `return a / b`
            - **Category**: Correctness
            - **Evidence**: [E1]
            - **Recommendation**: Guard against b == 0.
        """)
        findings = parse_markdown_findings(md)
        assert len(findings) == 1
        assert findings[0]["file"] == "src/calc.py"
        assert findings[0]["line"] == 4
        assert findings[0]["anchor"] == "return a / b"

    def test_malformed_markdown_with_headings_raises(self, source_repo: Path) -> None:
        """A populated-but-malformed findings doc must not silently yield [].

        A document with finding headings but no parseable Location lines is a
        parse failure (e.g. a typo'd ``**Location**``), not an empty review.
        Silently returning [] would let every malformed citation escape the
        grounding guard and report PASS.
        """
        path = source_repo / "malformed.md"
        path.write_text(
            "### [HIGH] Division by zero unguarded\n"
            "- **Locaiton**: src/calc.py:4\n"  # typo: not a valid Location line
            "- **Anchor**: `return a / b`\n"
        )
        with pytest.raises(ValueError):
            load_findings(path)

    def test_genuinely_empty_markdown_returns_empty(self, source_repo: Path) -> None:
        """A doc with no finding headings is legitimately empty, not malformed."""
        path = source_repo / "empty.md"
        path.write_text("# Review\n\nNo findings to report.\n")
        assert load_findings(path) == []


# --------------- CLI ---------------


class TestCli:
    """End-to-end CLI exit codes: 0 verified, 1 failure, 2 parse/usage error."""

    def test_cli_exit_zero_on_verified(self, source_repo: Path) -> None:
        path = source_repo / "findings.json"
        path.write_text(json.dumps([_finding()]))
        code = main(["--findings", str(path), "--repo-root", str(source_repo)])
        assert code == 0

    def test_cli_exit_one_on_failure(self, source_repo: Path) -> None:
        path = source_repo / "findings.json"
        path.write_text(json.dumps([_finding(anchor="hallucinated text")]))
        code = main(["--findings", str(path), "--repo-root", str(source_repo)])
        assert code == 1

    def test_cli_exit_two_on_missing_file(self, source_repo: Path) -> None:
        code = main(
            [
                "--findings",
                str(source_repo / "nope.json"),
                "--repo-root",
                str(source_repo),
            ]
        )
        assert code == 2

    def test_cli_json_format(self, source_repo: Path, capsys) -> None:
        """--format json emits a machine-readable verdict with failures."""
        path = source_repo / "findings.json"
        path.write_text(json.dumps([_finding(id="BAD", anchor="nope")]))
        code = main(
            [
                "--findings",
                str(path),
                "--repo-root",
                str(source_repo),
                "--format",
                "json",
            ]
        )
        assert code == 1
        payload = json.loads(capsys.readouterr().out)
        assert payload["passed"] is False
        assert payload["failed_count"] == 1
        assert payload["failures"][0]["id"] == "BAD"

    def test_cli_exit_two_on_unparseable_json(self, source_repo: Path) -> None:
        """A .json file with invalid JSON is a parse error (exit 2)."""
        path = source_repo / "broken.json"
        path.write_text("{ this is not valid json ]")
        code = main(["--findings", str(path), "--repo-root", str(source_repo)])
        assert code == 2


# --------------- gap-closing unit tests ---------------


class TestEdgeCases:
    """Cover the defensive branches: bad line types, markdown loading."""

    def test_from_dict_non_integer_line_becomes_none(self) -> None:
        """A non-numeric line coerces to None and fails as 'no line'."""
        finding = Finding.from_dict(_finding(line="not-a-number"))
        assert finding.line is None

    def test_load_findings_from_markdown_file(self, source_repo: Path) -> None:
        """load_findings dispatches a .md file to the markdown parser."""
        path = source_repo / "findings.md"
        path.write_text(
            "### [HIGH] Title\n"
            "- **Location**: src/calc.py:4\n"
            "- **Anchor**: `return a / b`\n"
        )
        findings = load_findings(path)
        assert len(findings) == 1
        assert findings[0]["line"] == 4
        report = verify_findings(findings, source_repo)
        assert report.passed is True


# --------------- minimum anchor length (issue #569.1) ---------------


class TestMinAnchorLength:
    """A too-short anchor matches too easily and must not VERIFY.

    A 3-char anchor like ``def`` is a substring of countless lines, so it
    would VERIFY spuriously. Require a minimum number of non-space anchor
    characters before a substring match is trusted.
    """

    def test_three_char_anchor_does_not_verify(self, source_repo: Path) -> None:
        """The issue's example: ``def`` appears on line 3 but is too short."""
        f = _finding(line=3, anchor="def")
        result = verify_finding(Finding.from_dict(f), source_repo)
        assert result.status == "FAILED"
        assert "short" in result.reason.lower()

    def test_seven_char_anchor_does_not_verify(self, source_repo: Path) -> None:
        """Boundary: 7 non-space chars is still below the >=8 threshold."""
        # "return a" has 7 non-space characters and is a substring of line 4.
        f = _finding(line=4, anchor="return a")
        result = verify_finding(Finding.from_dict(f), source_repo)
        assert result.status == "FAILED"
        assert "short" in result.reason.lower()

    def test_eight_char_anchor_verifies(self, source_repo: Path) -> None:
        """Boundary: exactly 8 non-space chars is long enough to verify."""
        # "return a /" has 8 non-space characters and is on line 4.
        f = _finding(line=4, anchor="return a /")
        result = verify_finding(Finding.from_dict(f), source_repo)
        assert result.status == "VERIFIED"

    def test_long_real_anchor_still_verifies(self, source_repo: Path) -> None:
        """A normal multi-word anchor (>=8 non-space chars) is unaffected."""
        result = verify_finding(Finding.from_dict(_finding()), source_repo)
        assert result.status == "VERIFIED"


# --------------- coverage gaps (issue #569.4) ---------------


class TestStrictnessStrictPath:
    """The strict strictness value behaves like normal (fails on any miss)."""

    def test_strict_fails_on_unresolved(self, source_repo: Path) -> None:
        false_f = _finding(anchor="not anywhere in the file")
        report = verify_findings([false_f], source_repo, strictness="strict")
        assert report.passed is False
        assert report.failed_count == 1

    def test_strict_passes_when_all_verified(self, source_repo: Path) -> None:
        report = verify_findings([_finding()], source_repo, strictness="strict")
        assert report.passed is True
        assert report.failed_count == 0


class TestFindingsFromJson:
    """Normalization branches of _findings_from_json."""

    def test_bare_dict_is_wrapped_in_a_list(self) -> None:
        """A single finding object (no 'findings' key) becomes a 1-item list."""
        single = {"id": "F1", "file": "src/calc.py", "line": 4, "anchor": "x"}
        assert _findings_from_json(single) == [single]

    def test_non_list_findings_value_raises(self) -> None:
        """A 'findings' key that is not a list is a malformed document."""
        with pytest.raises(json.JSONDecodeError):
            _findings_from_json({"findings": {"id": "F1"}})

    def test_scalar_json_raises(self) -> None:
        """A bare scalar (neither list nor dict) is an unexpected shape."""
        with pytest.raises(json.JSONDecodeError):
            _findings_from_json(42)


class TestUnknownSuffixFallback:
    """load_findings on an unknown suffix tries JSON, then markdown."""

    def test_unknown_suffix_parses_json(self, source_repo: Path) -> None:
        path = source_repo / "findings.txt"
        path.write_text(json.dumps([_finding()]))
        findings = load_findings(path)
        assert len(findings) == 1
        assert findings[0]["id"] == "F1"

    def test_unknown_suffix_falls_back_to_markdown(self, source_repo: Path) -> None:
        path = source_repo / "findings.txt"
        path.write_text(
            "### [HIGH] Title\n"
            "- **Location**: src/calc.py:4\n"
            "- **Anchor**: `return a / b`\n"
        )
        findings = load_findings(path)
        assert len(findings) == 1
        assert findings[0]["line"] == 4
