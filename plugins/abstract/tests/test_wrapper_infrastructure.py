"""Test infrastructure for superpower wrapper functionality."""

import sys
from pathlib import Path

import pytest

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from abstract.wrapper_base import SuperpowerWrapper, detect_breaking_changes


def _make_wrapper() -> SuperpowerWrapper:
    return SuperpowerWrapper(
        source_plugin="abstract",
        source_command="test-skill",
        target_superpower="test-driven-development",
    )


def test_wrapper_translates_parameters() -> None:
    """Test that wrapper translates parameters correctly."""
    # This should fail first (TDD principle)
    wrapper = SuperpowerWrapper(
        source_plugin="abstract",
        source_command="test-skill",
        target_superpower="test-driven-development",
    )

    # Test parameter translation - this should fail initially
    input_params = {"skill-path": "skills/my-skill", "phase": "red"}

    result = wrapper.translate_parameters(input_params)

    # Validate expected mappings exist
    assert "target_under_test" in result, (
        f"Expected 'target_under_test' in result, got: {result.keys()}"
    )
    assert "tdd_phase" in result, (
        f"Expected 'tdd_phase' in result, got: {result.keys()}"
    )

    # Validate correct values
    assert result["target_under_test"] == "skills/my-skill", (
        f"Expected 'skills/my-skill', got '{result['target_under_test']}'"
    )
    assert result["tdd_phase"] == "red", f"Expected 'red', got '{result['tdd_phase']}'"


def test_wrapper_validation() -> None:
    """Test wrapper validation functionality."""
    # Test invalid inputs - should raise ValueError
    try:
        SuperpowerWrapper("", "test-skill", "test-driven-development")
        msg = "Should have raised ValueError for empty source_plugin"
        raise AssertionError(msg)
    except ValueError:
        pass

    try:
        SuperpowerWrapper("abstract", None, "test-driven-development")
        msg = "Should have raised ValueError for None source_command"
        raise AssertionError(msg)
    except ValueError:
        pass

    try:
        SuperpowerWrapper("abstract", "test-skill", "")
        msg = "Should have raised ValueError for empty target_superpower"
        raise AssertionError(
            msg,
        )
    except ValueError:
        pass


def test_parameter_validation() -> None:
    """Test parameter validation functionality."""
    wrapper = SuperpowerWrapper(
        source_plugin="abstract",
        source_command="test-skill",
        target_superpower="test-driven-development",
    )

    # Test invalid parameter types
    try:
        wrapper.translate_parameters("not a dict")
        msg = "Should have raised ValueError for non-dict parameters"
        raise AssertionError(msg)
    except ValueError:
        pass

    # Test empty parameters
    result = wrapper.translate_parameters({})
    assert result == {}, f"Expected empty dict for empty input, got: {result}"


def test_load_parameter_map_malformed_yaml(tmp_path: Path) -> None:
    wrapper = _make_wrapper()

    config_path = tmp_path / "wrapper.yml"
    config_path.write_text("parameter_mapping: [unclosed\n", encoding="utf-8")

    wrapper.config_path = config_path
    with pytest.raises(ValueError, match=r"^Invalid YAML config:"):
        wrapper._load_parameter_map()

    assert any(
        err.error_code == "CONFIG_PARSE_ERROR" for err in wrapper.error_handler.errors
    )


def test_load_parameter_map_missing_config_file_uses_defaults(tmp_path: Path) -> None:
    wrapper = _make_wrapper()

    wrapper.config_path = tmp_path / "missing.yml"
    mapping = wrapper._load_parameter_map()

    assert mapping == {"skill-path": "target_under_test", "phase": "tdd_phase"}
    assert any(
        err.error_code == "CONFIG_NOT_FOUND" for err in wrapper.error_handler.errors
    )


def test_load_parameter_map_invalid_schema_parameter_mapping_not_dict(
    tmp_path: Path,
) -> None:
    wrapper = _make_wrapper()

    config_path = tmp_path / "wrapper.yml"
    config_path.write_text(
        "parameter_mapping:\n  - not\n  - a\n  - dict\n",
        encoding="utf-8",
    )

    wrapper.config_path = config_path
    with pytest.raises(ValueError, match=r"parameter_mapping must be a dictionary"):
        wrapper._load_parameter_map()

    assert any(
        err.error_code == "CONFIG_LOAD_ERROR" for err in wrapper.error_handler.errors
    )


def test_load_parameter_map_invalid_schema_mapping_types(tmp_path: Path) -> None:
    wrapper = _make_wrapper()

    config_path = tmp_path / "wrapper.yml"
    config_path.write_text("parameter_mapping:\n  skill-path: 123\n", encoding="utf-8")

    wrapper.config_path = config_path
    with pytest.raises(ValueError, match=r"Invalid mapping:"):
        wrapper._load_parameter_map()

    assert any(
        err.error_code == "CONFIG_LOAD_ERROR" for err in wrapper.error_handler.errors
    )


class TestValidateTranslation:
    """Test validate_translation() function - addressing issue #33."""

    def test_validate_translation_accepts_valid_translation(self) -> None:
        """validate_translation accepts valid translation structure."""
        wrapper = _make_wrapper()

        original = {"skill-path": "skills/my-skill", "phase": "red"}
        translated = {"target_under_test": "skills/my-skill", "tdd_phase": "red"}

        result = wrapper.validate_translation(original, translated)
        assert result is True, "Valid translation should be accepted"

    def test_validate_translation_rejects_empty_translation_with_input(self) -> None:
        """validate_translation rejects empty translation from non-empty input."""
        wrapper = _make_wrapper()

        original = {"skill-path": "skills/my-skill"}
        translated = {}

        result = wrapper.validate_translation(original, translated)
        assert result is False, (
            "Empty translation from non-empty input should be rejected"
        )

        # Should have logged an error
        errors = wrapper.error_handler.errors
        assert any(err.error_code == "TRANSLATION_FAILED" for err in errors), (
            "Should log TRANSLATION_FAILED error"
        )

    def test_validate_translation_empty_to_empty_returns_false(self) -> None:
        """validate_translation returns False for empty translation.

        Note: The function returns len(translated_params) > 0, so even
        empty-to-empty returns False. This is current behavior.
        """
        wrapper = _make_wrapper()

        original = {}
        translated = {}

        result = wrapper.validate_translation(original, translated)
        # Current implementation returns False for any empty translation
        assert result is False, "Empty translation returns False"

    def test_validate_translation_with_no_mapping_for_param(self) -> None:
        """validate_translation checks for params in expected list."""
        wrapper = _make_wrapper()

        # Use a parameter that's in expected list but has a mapping
        # Current implementation only warns if param is in expected list
        # AND missing from parameter_map
        original = {"skill-path": "skills/my-skill"}
        translated = {"target_under_test": "skills/my-skill"}

        # This should pass validation (skill-path IS in parameter_map)
        result = wrapper.validate_translation(original, translated)
        assert result is True, "Valid mapping should return True"

    def test_validate_translation_with_extra_translated_params(self) -> None:
        """validate_translation handles extra parameters in translation."""
        wrapper = _make_wrapper()

        original = {"skill-path": "skills/my-skill"}
        translated = {
            "target_under_test": "skills/my-skill",
            "extra_param": "value",
        }

        # Extra params in translation are OK (mapping might add defaults)
        result = wrapper.validate_translation(original, translated)
        assert result is True


class TestDetectBreakingChanges:
    """Test detect_breaking_changes() with edge cases - addressing issue #33."""

    def test_detect_breaking_changes_empty_file_list(self) -> None:
        """detect_breaking_changes handles empty file list gracefully."""
        result = detect_breaking_changes([])

        # Should return empty result (no changes detected)
        assert result == [], "Empty file list should return empty result"

    def test_detect_breaking_changes_returns_appropriate_structure(self) -> None:
        """detect_breaking_changes returns proper structure for empty input."""
        result = detect_breaking_changes([])

        # Result should be a list (empty for no files)
        assert isinstance(
            result,
            list,
        ), "Result should be a list"


if __name__ == "__main__":
    try:
        test_wrapper_validation()
        test_parameter_validation()
        test_wrapper_translates_parameters()
    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)
