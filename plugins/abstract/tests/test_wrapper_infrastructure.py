"""Test infrastructure for superpower wrapper functionality."""

import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from abstract.wrapper_base import SuperpowerWrapper


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


if __name__ == "__main__":
    try:
        test_wrapper_validation()
        test_parameter_validation()
        test_wrapper_translates_parameters()
    except Exception:
        import traceback

        traceback.print_exc()
        sys.exit(1)
