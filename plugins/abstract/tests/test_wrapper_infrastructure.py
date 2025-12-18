"""Test infrastructure for superpower wrapper functionality."""

import sys
from pathlib import Path

import pytest

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from abstract.wrapper_base import SuperpowerWrapper


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
    assert (
        "target_under_test" in result
    ), f"Expected 'target_under_test' in result, got: {result.keys()}"
    assert (
        "tdd_phase" in result
    ), f"Expected 'tdd_phase' in result, got: {result.keys()}"

    # Validate correct values
    assert (
        result["target_under_test"] == "skills/my-skill"
    ), f"Expected 'skills/my-skill', got '{result['target_under_test']}'"
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


if __name__ == "__main__":
    try:
        test_wrapper_validation()
        test_parameter_validation()
        test_wrapper_translates_parameters()
    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)
