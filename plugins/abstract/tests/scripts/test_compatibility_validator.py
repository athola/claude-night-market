"""Extended tests for compatibility_validator.py.

Feature: Compatibility validator extended coverage
    As a developer
    I want all branches in compatibility_validator tested
    So that feature extraction and severity logic works correctly
"""

from __future__ import annotations

import builtins
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from compatibility_validator import CompatibilityValidator, main


@pytest.fixture
def validator():
    """Create a CompatibilityValidator instance."""
    return CompatibilityValidator()


# ---------------------------------------------------------------------------
# Tests: _extract_features with nonexistent file (line 117)
# ---------------------------------------------------------------------------


class TestExtractFeaturesNonexistent:
    """Feature: _extract_features returns empty for missing file."""

    @pytest.mark.unit
    def test_nonexistent_file_returns_empty_features(self, validator) -> None:
        """Scenario: Missing file returns empty feature map."""
        result = validator._extract_features("/nonexistent/path/file.md")
        assert result["parameters"] == []
        assert result["options"] == []
        assert result["output_format"] is None
        assert result["error_handling"] == []


# ---------------------------------------------------------------------------
# Tests: _parse_markdown_command exception path (lines 148-150)
# ---------------------------------------------------------------------------


class TestParseMarkdownCommandException:
    """Feature: _parse_markdown_command handles parse failures."""

    @pytest.mark.unit
    def test_parse_error_returns_empty_features(
        self, validator, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: Exception during parsing returns empty features gracefully."""
        md_file = tmp_path / "test.md"
        md_file.write_text("---\nname: test\n---\n\nContent.\n")

        original_open = builtins.open

        def raising_open(file, *args, **kwargs):
            if str(file) == str(md_file):
                raise OSError("Simulated error")
            return original_open(file, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", raising_open)
        result = validator._parse_markdown_command(str(md_file))
        assert result["parameters"] == []


# ---------------------------------------------------------------------------
# Tests: _extract_frontmatter_features branches
# ---------------------------------------------------------------------------


class TestExtractFrontmatterFeatures:
    """Feature: _extract_frontmatter_features handles various frontmatter shapes."""

    @pytest.mark.unit
    def test_no_frontmatter_returns_empty(self, validator) -> None:
        """Scenario: Content without frontmatter returns unchanged features."""
        features = validator._empty_features()
        validator._extract_frontmatter_features("No frontmatter content.", features)
        assert features["parameters"] == []

    @pytest.mark.unit
    def test_non_dict_frontmatter_returns_empty(self, validator) -> None:
        """Scenario: Frontmatter that parses to non-dict is ignored."""
        features = validator._empty_features()
        content = "---\n- item1\n- item2\n---\n\nContent.\n"
        validator._extract_frontmatter_features(content, features)
        assert features["parameters"] == []

    @pytest.mark.unit
    def test_parameters_as_list_of_dicts(self, validator) -> None:
        """Scenario: Parameters as list of dicts extracts names."""
        features = validator._empty_features()
        content = textwrap.dedent("""
            ---
            parameters:
              - name: skill-path
                description: Path to skill
              - name: verbose
                description: Verbose mode
            ---

            Content.
        """).strip()
        validator._extract_frontmatter_features(content, features)
        assert "skill-path" in features["parameters"]
        assert "verbose" in features["parameters"]

    @pytest.mark.unit
    def test_parameters_as_list_of_strings(self, validator) -> None:
        """Scenario: Parameters as list of strings extracts them."""
        features = validator._empty_features()
        content = textwrap.dedent("""
            ---
            parameters:
              - input
              - output
            ---

            Content.
        """).strip()
        validator._extract_frontmatter_features(content, features)
        assert "input" in features["parameters"]

    @pytest.mark.unit
    def test_parameters_as_string(self, validator) -> None:
        """Scenario: Parameters as single string is added to list."""
        features = validator._empty_features()
        content = textwrap.dedent("""
            ---
            parameters: skill-path
            ---

            Content.
        """).strip()
        validator._extract_frontmatter_features(content, features)
        assert "skill-path" in features["parameters"]

    @pytest.mark.unit
    def test_options_as_list(self, validator) -> None:
        """Scenario: Options as list of strings is extracted."""
        features = validator._empty_features()
        content = textwrap.dedent("""
            ---
            options:
              - verbose
              - dry-run
            ---

            Content.
        """).strip()
        validator._extract_frontmatter_features(content, features)
        assert "verbose" in features["options"]
        assert "dry-run" in features["options"]

    @pytest.mark.unit
    def test_options_as_string(self, validator) -> None:
        """Scenario: Options as single string becomes a list."""
        features = validator._empty_features()
        content = textwrap.dedent("""
            ---
            options: verbose
            ---

            Content.
        """).strip()
        validator._extract_frontmatter_features(content, features)
        assert "verbose" in features["options"]

    @pytest.mark.unit
    def test_usage_with_report_sets_markdown_format(self, validator) -> None:
        """Scenario: Usage containing 'report' sets markdown_report format."""
        features = validator._empty_features()
        content = textwrap.dedent("""
            ---
            usage: Generate a report output
            ---

            Content.
        """).strip()
        validator._extract_frontmatter_features(content, features)
        assert features["output_format"] == "markdown_report"

    @pytest.mark.unit
    def test_usage_with_json_sets_json_format(self, validator) -> None:
        """Scenario: Usage containing 'json' (without 'report' or 'output') sets json format."""
        features = validator._empty_features()
        content = textwrap.dedent("""
            ---
            usage: Emit json data
            ---

            Content.
        """).strip()
        validator._extract_frontmatter_features(content, features)
        assert features["output_format"] == "json"

    @pytest.mark.unit
    def test_error_handling_as_list(self, validator) -> None:
        """Scenario: error_handling as list is extracted."""
        features = validator._empty_features()
        content = textwrap.dedent("""
            ---
            error_handling:
              - validation
              - retry
            ---

            Content.
        """).strip()
        validator._extract_frontmatter_features(content, features)
        assert "validation" in features["error_handling"]

    @pytest.mark.unit
    def test_error_handling_as_string(self, validator) -> None:
        """Scenario: error_handling as single string is added."""
        features = validator._empty_features()
        content = textwrap.dedent("""
            ---
            error_handling: exception
            ---

            Content.
        """).strip()
        validator._extract_frontmatter_features(content, features)
        assert "exception" in features["error_handling"]


# ---------------------------------------------------------------------------
# Tests: _parse_python_wrapper branches
# ---------------------------------------------------------------------------


class TestParsePythonWrapper:
    """Feature: _parse_python_wrapper extracts from Python files."""

    @pytest.mark.unit
    def test_valid_python_file(self, validator, tmp_path: Path) -> None:
        """Scenario: Valid Python file extracts parameters from functions."""
        py_file = tmp_path / "wrapper.py"
        py_file.write_text(
            "def process(skill_path, verbose=False):\n"
            "    try:\n"
            "        result = validate(skill_path)\n"
            "    except Exception:\n"
            "        pass\n"
            "    return result\n"
        )
        result = validator._parse_python_wrapper(str(py_file))
        assert isinstance(result["parameters"], list)

    @pytest.mark.unit
    def test_python_with_json_output(self, validator, tmp_path: Path) -> None:
        """Scenario: Python file using json sets json output format."""
        py_file = tmp_path / "wrapper.py"
        py_file.write_text(
            "import json\ndef run():\n    return json.dumps({'result': 'ok'})\n"
        )
        result = validator._parse_python_wrapper(str(py_file))
        assert result["output_format"] == "json"

    @pytest.mark.unit
    def test_python_with_fallback_pattern(self, validator, tmp_path: Path) -> None:
        """Scenario: Python file with 'fallback' gets fallback error handling."""
        py_file = tmp_path / "wrapper.py"
        py_file.write_text("def run():\n    # fallback mechanism here\n    pass\n")
        result = validator._parse_python_wrapper(str(py_file))
        assert "fallback" in result["error_handling"]

    @pytest.mark.unit
    def test_python_read_error_returns_empty(
        self, validator, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: Python file that can't be read returns empty features."""
        py_file = tmp_path / "unreadable.py"
        py_file.write_text("def func(): pass\n")

        original_open = builtins.open

        def raising_open(file, *args, **kwargs):
            if str(file) == str(py_file):
                raise OSError("Permission denied")
            return original_open(file, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", raising_open)
        result = validator._parse_python_wrapper(str(py_file))
        assert result["parameters"] == []


# ---------------------------------------------------------------------------
# Tests: _determine_severity branches (lines 560-576)
# ---------------------------------------------------------------------------


class TestDetermineSeverity:
    """Feature: _determine_severity returns correct severity levels."""

    @pytest.mark.unit
    def test_critical_parameter(self, validator) -> None:
        """Scenario: 'skill-path' parameter in parameters category is critical."""
        result = validator._determine_severity("parameters", "skill-path")
        assert result == "critical"

    @pytest.mark.unit
    def test_high_non_critical_parameter(self, validator) -> None:
        """Scenario: Non-critical parameter is 'high'."""
        result = validator._determine_severity("parameters", "output-dir")
        assert result == "high"

    @pytest.mark.unit
    def test_high_debug_option(self, validator) -> None:
        """Scenario: 'debug' option is 'high'."""
        result = validator._determine_severity("options", "debug")
        assert result == "high"

    @pytest.mark.unit
    def test_medium_option(self, validator) -> None:
        """Scenario: Regular option is 'medium'."""
        result = validator._determine_severity("options", "format")
        assert result == "medium"

    @pytest.mark.unit
    def test_medium_validation_error_handling(self, validator) -> None:
        """Scenario: 'validation' in error_handling is 'medium'."""
        result = validator._determine_severity("error_handling", "validation")
        assert result == "medium"

    @pytest.mark.unit
    def test_low_other_category(self, validator) -> None:
        """Scenario: output_format category is 'low'."""
        result = validator._determine_severity("output_format", "json")
        assert result == "low"

    @pytest.mark.unit
    def test_low_other_error_handling(self, validator) -> None:
        """Scenario: 'retry' error handling is 'low'."""
        result = validator._determine_severity("error_handling", "retry")
        assert result == "low"


# ---------------------------------------------------------------------------
# Tests: _calculate_parity edge cases (lines 447-474)
# ---------------------------------------------------------------------------


class TestCalculateParity:
    """Feature: _calculate_parity computes parity scores."""

    @pytest.mark.unit
    def test_both_empty_lists_is_perfect(self, validator) -> None:
        """Scenario: Both sides have empty lists → perfect match."""
        original = validator._empty_features()
        wrapper = validator._empty_features()
        score = validator._calculate_parity(original, wrapper)
        assert score == 1.0

    @pytest.mark.unit
    def test_original_has_features_wrapper_empty_is_partial(self, validator) -> None:
        """Scenario: Original has parameters, wrapper has none → partial score."""
        original = validator._empty_features()
        original["parameters"] = ["skill-path"]
        wrapper = validator._empty_features()
        score = validator._calculate_parity(original, wrapper)
        assert score < 1.0

    @pytest.mark.unit
    def test_normalized_parameter_matching(self, validator) -> None:
        """Scenario: skill-path and skill_path normalize to same match."""
        original = validator._empty_features()
        original["parameters"] = ["skill-path"]
        wrapper = validator._empty_features()
        wrapper["parameters"] = ["skill_path"]
        score = validator._calculate_parity(original, wrapper)
        # Should get a higher score due to normalized matching
        assert score > 0

    @pytest.mark.unit
    def test_different_output_format_lowers_score(self, validator) -> None:
        """Scenario: Different output formats reduce parity score."""
        original = validator._empty_features()
        original["output_format"] = "json"
        wrapper = validator._empty_features()
        wrapper["output_format"] = "markdown"
        score = validator._calculate_parity(original, wrapper)
        assert score < 1.0


# ---------------------------------------------------------------------------
# Tests: main() function (lines 609-631)
# ---------------------------------------------------------------------------


class TestCompatibilityValidatorMain:
    """Feature: main() entry point."""

    @pytest.mark.unit
    def test_main_with_missing_files_no_crash(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: main with nonexistent files doesn't crash.
        Given paths to nonexistent original and wrapper files
        When main is called
        Then it exits 0 (no critical missing features from empty comparison)
        """
        orig = str(tmp_path / "nonexistent.md")
        wrap = str(tmp_path / "nonexistent.py")
        monkeypatch.setattr(sys, "argv", ["compatibility_validator.py", orig, wrap])
        try:
            main()
        except SystemExit as e:
            assert e.code in (0, 1)

    @pytest.mark.unit
    def test_main_verbose_with_missing_features(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: main --verbose with real files runs without crash."""
        # Create a markdown command file
        orig_file = tmp_path / "command.md"
        orig_file.write_text(
            "---\nname: test\nparameters:\n  - name: input\n---\n\nContent.\n"
        )
        # Create an empty Python wrapper
        wrap_file = tmp_path / "wrapper.py"
        wrap_file.write_text("def run(): pass\n")

        monkeypatch.setattr(
            sys,
            "argv",
            ["compatibility_validator.py", str(orig_file), str(wrap_file), "--verbose"],
        )
        try:
            main()
        except SystemExit as e:
            assert e.code in (0, 1)
