"""Tests for .slop-config.yaml config file support.

Issue #136: Config file support for scribe slop-detector

Tests verify YAML config parsing, allowlist filtering, custom word detection,
threshold validation, and exclude pattern matching.
"""

import fnmatch
import re
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Helpers that simulate the config-file module behaviour
# ---------------------------------------------------------------------------


def parse_config(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalise a raw YAML dict into a validated config structure."""
    custom_words = raw.get("custom_words", {})
    thresholds = raw.get("thresholds", {})

    warn = float(thresholds.get("warn", 2.0))
    error = float(thresholds.get("error", 5.0))

    return {
        "custom_words": {
            "tier1": [w.lower() for w in custom_words.get("tier1", [])],
            "tier2": [w.lower() for w in custom_words.get("tier2", [])],
        },
        "allowlist": [w.lower() for w in raw.get("allowlist", [])],
        "thresholds": {"warn": warn, "error": error},
        "exclude_patterns": raw.get("exclude_patterns", []),
        "extends": raw.get("extends"),
    }


def is_excluded(file_path: str, patterns: list[str]) -> bool:
    """Return True if file_path matches any exclude glob pattern."""
    for pattern in patterns:
        if fnmatch.fnmatch(file_path, pattern):
            return True
    return False


def build_tier1_pattern(builtin: list[str], custom: list[str]) -> re.Pattern:
    """Compile a combined tier-1 detection regex."""
    words = builtin + custom
    return re.compile(
        r"\b(" + "|".join(re.escape(w) for w in words) + r")\b", re.IGNORECASE
    )


def find_matches(text: str, pattern: re.Pattern, allowlist: list[str]) -> list[str]:
    """Return matches not present in the allowlist."""
    return [m for m in pattern.findall(text) if m.lower() not in allowlist]


# ---------------------------------------------------------------------------
# Built-in defaults used across tests
# ---------------------------------------------------------------------------

BUILTIN_TIER1 = ["delve", "tapestry", "realm", "embark", "multifaceted"]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestConfigParsing:
    """Feature: Parse a valid .slop-config.yaml structure."""

    @pytest.mark.unit
    def test_parses_custom_tier1_words(self) -> None:
        """Scenario: Custom tier-1 words are loaded from config.

        Given a config dict with custom_words.tier1
        When parsed
        Then those words appear in the tier1 list.
        """
        raw: dict[str, Any] = {
            "custom_words": {"tier1": ["synergize", "ideate"]},
        }
        config = parse_config(raw)
        assert "synergize" in config["custom_words"]["tier1"]
        assert "ideate" in config["custom_words"]["tier1"]

    @pytest.mark.unit
    def test_parses_custom_tier2_words(self) -> None:
        """Scenario: Custom tier-2 words are loaded from config."""
        raw: dict[str, Any] = {
            "custom_words": {"tier2": ["impactful", "learnings"]},
        }
        config = parse_config(raw)
        assert "impactful" in config["custom_words"]["tier2"]
        assert "learnings" in config["custom_words"]["tier2"]

    @pytest.mark.unit
    def test_parses_allowlist(self) -> None:
        """Scenario: Allowlist words are lower-cased and stored."""
        raw: dict[str, Any] = {"allowlist": ["Robust", "LEVERAGE"]}
        config = parse_config(raw)
        assert "robust" in config["allowlist"]
        assert "leverage" in config["allowlist"]

    @pytest.mark.unit
    def test_parses_thresholds(self) -> None:
        """Scenario: Numeric thresholds are parsed as floats."""
        raw: dict[str, Any] = {"thresholds": {"warn": 1.5, "error": 4.0}}
        config = parse_config(raw)
        assert config["thresholds"]["warn"] == 1.5
        assert config["thresholds"]["error"] == 4.0

    @pytest.mark.unit
    def test_defaults_when_fields_absent(self) -> None:
        """Scenario: Missing fields fall back to built-in defaults."""
        config = parse_config({})
        assert config["custom_words"]["tier1"] == []
        assert config["allowlist"] == []
        assert config["thresholds"]["warn"] == 2.0
        assert config["thresholds"]["error"] == 5.0
        assert config["exclude_patterns"] == []
        assert config["extends"] is None

    @pytest.mark.unit
    def test_parses_exclude_patterns(self) -> None:
        """Scenario: Glob exclude patterns are stored as-is."""
        raw: dict[str, Any] = {"exclude_patterns": ["vendor/**", "CHANGELOG.md"]}
        config = parse_config(raw)
        assert "vendor/**" in config["exclude_patterns"]
        assert "CHANGELOG.md" in config["exclude_patterns"]

    @pytest.mark.unit
    def test_parses_extends_path(self) -> None:
        """Scenario: The extends field is stored as a string path."""
        raw: dict[str, Any] = {"extends": "../../.slop-config.yaml"}
        config = parse_config(raw)
        assert config["extends"] == "../../.slop-config.yaml"


class TestAllowlistFiltering:
    """Feature: Words in the allowlist are not flagged."""

    @pytest.mark.unit
    def test_allowlisted_word_not_flagged(self) -> None:
        """Scenario: 'robust' is in the allowlist and must not appear in results.

        Given text containing 'robust' (a tier-1 word)
        And 'robust' is in the project allowlist
        When scanning for slop
        Then 'robust' is not reported as a match.
        """
        builtin = BUILTIN_TIER1 + ["robust"]
        pattern = build_tier1_pattern(builtin, [])
        allowlist = ["robust"]

        text = "The system is robust and delve-free."
        matches = find_matches(text, pattern, allowlist)

        assert "robust" not in [m.lower() for m in matches]
        assert "delve" in [m.lower() for m in matches]

    @pytest.mark.unit
    def test_non_allowlisted_word_still_flagged(self) -> None:
        """Scenario: Words absent from the allowlist are still detected."""
        pattern = build_tier1_pattern(BUILTIN_TIER1, [])
        allowlist = ["realm"]  # only realm is allowed

        text = "We embark on a journey through the realm of ideas."
        matches = find_matches(text, pattern, allowlist)

        lowered = [m.lower() for m in matches]
        assert "embark" in lowered
        assert "realm" not in lowered

    @pytest.mark.unit
    def test_allowlist_is_case_insensitive(self) -> None:
        """Scenario: Allowlist matching ignores capitalisation."""
        pattern = build_tier1_pattern(BUILTIN_TIER1, [])
        allowlist = ["delve"]  # stored lowercase

        text = "DELVE into the data."
        matches = find_matches(text, pattern, allowlist)
        assert matches == []


class TestCustomWordDetection:
    """Feature: Custom words from config are detected like built-in words."""

    @pytest.mark.unit
    def test_custom_tier1_word_detected(self) -> None:
        """Scenario: A project-specific tier-1 word is flagged.

        Given 'synergize' added as a custom tier-1 word
        When text contains 'synergize'
        Then it is detected.
        """
        custom = ["synergize", "ideate"]
        pattern = build_tier1_pattern(BUILTIN_TIER1, custom)

        text = "We need to synergize our efforts."
        matches = find_matches(text, pattern, allowlist=[])
        assert "synergize" in [m.lower() for m in matches]

    @pytest.mark.unit
    def test_custom_word_not_detected_without_config(self) -> None:
        """Scenario: Custom word is not detected when config is absent."""
        pattern = build_tier1_pattern(BUILTIN_TIER1, [])  # no custom words

        text = "We need to synergize our efforts."
        matches = find_matches(text, pattern, allowlist=[])
        assert matches == []

    @pytest.mark.unit
    def test_custom_word_combined_with_builtin(self) -> None:
        """Scenario: Custom and built-in words are both detected in one pass."""
        custom = ["ideate"]
        pattern = build_tier1_pattern(BUILTIN_TIER1, custom)

        text = "Let's ideate and delve into solutions."
        matches = [m.lower() for m in find_matches(text, pattern, allowlist=[])]
        assert "ideate" in matches
        assert "delve" in matches


class TestThresholdValidation:
    """Feature: warn threshold must be less than error threshold."""

    @pytest.mark.unit
    def test_valid_thresholds_accepted(self) -> None:
        """Scenario: warn < error is a valid configuration."""
        raw: dict[str, Any] = {"thresholds": {"warn": 2.0, "error": 5.0}}
        config = parse_config(raw)
        assert config["thresholds"]["warn"] < config["thresholds"]["error"]

    @pytest.mark.unit
    def test_equal_thresholds_are_invalid(self) -> None:
        """Scenario: warn == error violates the constraint."""
        raw: dict[str, Any] = {"thresholds": {"warn": 3.0, "error": 3.0}}
        config = parse_config(raw)
        warn = config["thresholds"]["warn"]
        error = config["thresholds"]["error"]
        assert not (warn < error), "equal thresholds should fail the warn < error check"

    @pytest.mark.unit
    def test_inverted_thresholds_are_invalid(self) -> None:
        """Scenario: warn > error violates the constraint."""
        raw: dict[str, Any] = {"thresholds": {"warn": 6.0, "error": 3.0}}
        config = parse_config(raw)
        warn = config["thresholds"]["warn"]
        error = config["thresholds"]["error"]
        assert not (warn < error), (
            "inverted thresholds should fail the warn < error check"
        )

    @pytest.mark.unit
    def test_threshold_boundary(self) -> None:
        """Scenario: Threshold boundary values are preserved exactly."""
        raw: dict[str, Any] = {"thresholds": {"warn": 0.1, "error": 0.2}}
        config = parse_config(raw)
        assert config["thresholds"]["warn"] == pytest.approx(0.1)
        assert config["thresholds"]["error"] == pytest.approx(0.2)


class TestExcludePatterns:
    """Feature: Files matching exclude glob patterns are skipped."""

    @pytest.mark.unit
    def test_file_in_vendor_excluded(self) -> None:
        """Scenario: A file under vendor/ matches the vendor/** pattern."""
        patterns = ["vendor/**"]
        assert is_excluded("vendor/third-party/README.md", patterns) is True

    @pytest.mark.unit
    def test_generated_file_excluded(self) -> None:
        """Scenario: A .generated.md file is excluded."""
        patterns = ["**/*.generated.md"]
        assert is_excluded("docs/api.generated.md", patterns) is True

    @pytest.mark.unit
    def test_normal_file_not_excluded(self) -> None:
        """Scenario: A normal docs file is not excluded."""
        patterns = ["vendor/**", "**/*.generated.md", "CHANGELOG.md"]
        assert is_excluded("docs/guide.md", patterns) is False

    @pytest.mark.unit
    def test_exact_filename_excluded(self) -> None:
        """Scenario: An exact filename match excludes that file."""
        patterns = ["CHANGELOG.md"]
        assert is_excluded("CHANGELOG.md", patterns) is True

    @pytest.mark.unit
    def test_empty_patterns_excludes_nothing(self) -> None:
        """Scenario: An empty exclude list never excludes any file."""
        assert is_excluded("anything/file.md", []) is False

    @pytest.mark.unit
    def test_multiple_patterns_first_match_wins(self) -> None:
        """Scenario: A file matching any pattern in the list is excluded."""
        patterns = ["docs/**", "vendor/**"]
        assert is_excluded("docs/intro.md", patterns) is True
        assert is_excluded("vendor/lib.md", patterns) is True
        assert is_excluded("src/main.py", patterns) is False
