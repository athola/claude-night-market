"""Tests for markdown_wrap Nen Court validator (issue #406).

Feature: Lint markdown files for prose lines exceeding 80 characters.

As the Night Market vow enforcement system
I want a Nen Court validator that flags over-long prose lines
So that markdown wrap rules graduate from Soft to Nen Court enforcement.
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
    """Import markdown_wrap validator via importlib (standalone script)."""
    validators_path = Path(__file__).resolve().parents[3] / "validators"
    module_path = validators_path / "markdown_wrap.py"
    spec = importlib.util.spec_from_file_location("markdown_wrap", module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["markdown_wrap"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestLineClassification:
    """Feature: Identify which markdown lines are subject to the wrap rule.

    As the validator
    I want to classify each line by kind
    So that code blocks, tables, and URLs are not falsely flagged.
    """

    @pytest.mark.unit
    def test_classify_prose_line(self, validator_module):
        """A plain prose line is classified as 'prose'."""
        kind = validator_module.classify_line(
            "This is a sentence of prose.", in_code_block=False
        )
        assert kind == "prose"

    @pytest.mark.unit
    def test_classify_atx_heading(self, validator_module):
        """ATX headings are classified as 'heading' and skipped."""
        kind = validator_module.classify_line("# Heading One", in_code_block=False)
        assert kind == "heading"

    @pytest.mark.unit
    def test_classify_code_fence(self, validator_module):
        """Fenced code block markers are 'code-fence'."""
        kind = validator_module.classify_line("```python", in_code_block=False)
        assert kind == "code-fence"

    @pytest.mark.unit
    def test_classify_table_row(self, validator_module):
        """Table rows starting with | are 'table'."""
        kind = validator_module.classify_line(
            "| Column 1 | Column 2 |", in_code_block=False
        )
        assert kind == "table"

    @pytest.mark.unit
    def test_classify_inside_code_block(self, validator_module):
        """Any line inside a fenced block is 'code'."""
        kind = validator_module.classify_line(
            "def really_long_function_name_that_exceeds_the_eighty_character_budget():",
            in_code_block=True,
        )
        assert kind == "code"

    @pytest.mark.unit
    def test_classify_blank_line(self, validator_module):
        """Empty lines are 'blank'."""
        kind = validator_module.classify_line("", in_code_block=False)
        assert kind == "blank"

    @pytest.mark.unit
    def test_classify_list_item(self, validator_module):
        """List items are still subject to wrap (return 'prose')."""
        # Lists wrap at 80 chars too in this codebase's convention.
        kind = validator_module.classify_line(
            "- A list item with prose content", in_code_block=False
        )
        assert kind == "prose"


class TestExceedsBudget:
    """Feature: Detect prose lines exceeding 80 characters.

    As the validator
    I want to flag only lines that breach the budget
    So that violations are accurate and actionable.
    """

    @pytest.mark.unit
    def test_short_prose_passes(self, validator_module):
        """A 50-char prose line is not flagged."""
        line = "x" * 50
        assert validator_module.exceeds_budget(line, max_width=80) is False

    @pytest.mark.unit
    def test_exact_budget_passes(self, validator_module):
        """A 80-char line passes (boundary inclusive)."""
        line = "x" * 80
        assert validator_module.exceeds_budget(line, max_width=80) is False

    @pytest.mark.unit
    def test_over_budget_flagged(self, validator_module):
        """A 81-char line is flagged."""
        line = "x" * 81
        assert validator_module.exceeds_budget(line, max_width=80) is True

    @pytest.mark.unit
    def test_long_url_not_flagged(self, validator_module):
        """Lines that are mostly a URL get a pass (URLs cannot wrap)."""
        line = "See https://example.com/very/long/path/that/goes/on/and/on/" + "x" * 50
        # URL is unbreakable -> validator should not flag it.
        assert validator_module.exceeds_budget(line, max_width=80) is False

    @pytest.mark.unit
    def test_long_inline_code_not_flagged(self, validator_module):
        """Lines dominated by inline code (`...`) are not flagged."""
        line = "Use `" + "x" * 80 + "` to do the thing"
        assert validator_module.exceeds_budget(line, max_width=80) is False


class TestValidateText:
    """Feature: Validate a single markdown document.

    As the validator
    I want to scan a document and produce a verdict
    So that callers can integrate it into phase boundaries.
    """

    @pytest.mark.unit
    def test_clean_doc_returns_pass(self, validator_module):
        """A doc with all wrapped lines returns pass with no violations."""
        text = "Short line one.\n\nShort line two.\n"
        result = validator_module.validate_text(text, filename="ok.md")
        assert result["verdict"] == "pass"
        assert result["evidence"] == []

    @pytest.mark.unit
    def test_doc_with_long_line_returns_violation(self, validator_module):
        """A doc with one over-budget prose line returns violation with evidence."""
        long_line = "This is a sentence that intentionally goes on and on and on without wrapping anywhere."
        text = f"Short.\n{long_line}\nShort again.\n"
        result = validator_module.validate_text(text, filename="bad.md")
        assert result["verdict"] == "violation"
        assert len(result["evidence"]) == 1
        ev = result["evidence"][0]
        assert ev["file"] == "bad.md"
        assert ev["line"] == 2
        assert ev["length"] == len(long_line)

    @pytest.mark.unit
    def test_code_block_lines_not_flagged(self, validator_module):
        """Long lines inside fenced code blocks are not flagged."""
        text = (
            "Short prose.\n"
            "```python\n"
            "def f(): return 'x' * 200  # this is in code, do not flag\n"
            "```\n"
        )
        result = validator_module.validate_text(text, filename="code.md")
        assert result["verdict"] == "pass"

    @pytest.mark.unit
    def test_table_rows_not_flagged(self, validator_module):
        """Long table rows are not flagged (tables cannot wrap)."""
        text = (
            "Short.\n\n"
            "| Column header that is very long | Another long header column |\n"
            "|---|---|\n"
            "| value | another value |\n"
        )
        result = validator_module.validate_text(text, filename="tbl.md")
        assert result["verdict"] == "pass"

    @pytest.mark.unit
    def test_recommendation_is_present_on_violation(self, validator_module):
        """Violation verdict comes with a recommendation string."""
        text = "x" * 200 + "\n"
        result = validator_module.validate_text(text, filename="x.md")
        assert result["verdict"] == "violation"
        assert isinstance(result["recommendation"], str)
        assert "wrap" in result["recommendation"].lower()


class TestValidateFiles:
    """Feature: Validate a list of files on disk.

    As the validator
    I want to validate multiple files in one invocation
    So that the orchestrator can audit a whole branch in one call.
    """

    @pytest.mark.unit
    def test_validate_clean_file(self, validator_module, tmp_path):
        """A file with all-wrapped prose returns pass."""
        f = tmp_path / "ok.md"
        f.write_text("Short prose.\n\nMore short prose.\n")
        result = validator_module.validate_files([str(f)])
        assert result["verdict"] == "pass"
        assert result["evidence"] == []

    @pytest.mark.unit
    def test_validate_dirty_file(self, validator_module, tmp_path):
        """A file with one long prose line returns violation."""
        f = tmp_path / "bad.md"
        long = "This is a sentence that goes way over the eighty character budget and keeps going."
        f.write_text(f"Short.\n{long}\n")
        result = validator_module.validate_files([str(f)])
        assert result["verdict"] == "violation"
        assert len(result["evidence"]) == 1
        assert str(f) in result["evidence"][0]["file"]

    @pytest.mark.unit
    def test_validate_missing_file_inconclusive(self, validator_module, tmp_path):
        """A missing file produces inconclusive verdict."""
        result = validator_module.validate_files([str(tmp_path / "nope.md")])
        assert result["verdict"] == "inconclusive"
        assert any("not found" in str(ev).lower() for ev in result["evidence"])

    @pytest.mark.unit
    def test_validate_multiple_files_aggregates(self, validator_module, tmp_path):
        """Multiple files: verdict is violation if ANY file violates."""
        clean = tmp_path / "clean.md"
        clean.write_text("Short.\n")
        dirty = tmp_path / "dirty.md"
        dirty.write_text("x" * 200 + "\n")
        result = validator_module.validate_files([str(clean), str(dirty)])
        assert result["verdict"] == "violation"
        # Evidence cites the dirty file only.
        files_in_evidence = {ev["file"] for ev in result["evidence"]}
        assert str(dirty) in files_in_evidence
        assert str(clean) not in files_in_evidence


class TestCliEntry:
    """Feature: Validator runs as a standalone CLI script.

    As the orchestrator or developer
    I want to invoke the validator with stdin JSON and read stdout JSON
    So that integration with mission-orchestrator is uniform.
    """

    @pytest.mark.unit
    def test_main_reads_text_input(self, validator_module, capsys):
        """main() with {"text": "...", "filename": "x.md"} on stdin emits JSON verdict."""
        payload = json.dumps({"text": "Short.\n", "filename": "x.md"})
        with patch("sys.stdin", StringIO(payload)):
            with pytest.raises(SystemExit) as exc:
                validator_module.main()
        assert exc.value.code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["verdict"] == "pass"

    @pytest.mark.unit
    def test_main_reads_files_input(self, validator_module, capsys, tmp_path):
        """main() with {"files": [...]} returns aggregated verdict.

        A clean file should produce verdict=pass and exit code 0.
        """
        f = tmp_path / "doc.md"
        f.write_text("Short prose only.\n")
        payload = json.dumps({"files": [str(f)]})
        with patch("sys.stdin", StringIO(payload)):
            with pytest.raises(SystemExit) as exc:
                validator_module.main()
        assert exc.value.code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["verdict"] == "pass"

    @pytest.mark.unit
    def test_main_exit_code_violation_is_one(self, validator_module, capsys):
        """Violation verdict exits with code 1 (Nen Court contract: block phase)."""
        payload = json.dumps({"text": "x" * 200 + "\n", "filename": "bad.md"})
        with patch("sys.stdin", StringIO(payload)):
            with pytest.raises(SystemExit) as exc:
                validator_module.main()
        assert exc.value.code == 1

    @pytest.mark.unit
    def test_main_inconclusive_exit_code_two(self, validator_module, capsys, tmp_path):
        """Inconclusive verdict exits with code 2 (do not block, flag for review)."""
        payload = json.dumps({"files": [str(tmp_path / "missing.md")]})
        with patch("sys.stdin", StringIO(payload)):
            with pytest.raises(SystemExit) as exc:
                validator_module.main()
        assert exc.value.code == 2

    @pytest.mark.unit
    def test_main_malformed_input_inconclusive(self, validator_module, capsys):
        """Malformed JSON on stdin returns inconclusive (cannot crash orchestrator)."""
        with patch("sys.stdin", StringIO("not valid json")):
            with pytest.raises(SystemExit) as exc:
                validator_module.main()
        assert exc.value.code == 2
        out = json.loads(capsys.readouterr().out)
        assert out["verdict"] == "inconclusive"
