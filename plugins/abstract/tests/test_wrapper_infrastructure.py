"""Test infrastructure for superpower wrapper functionality."""

import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from abstract.wrapper_base import SuperpowerWrapper


def test_wrapper_translates_parameters():
    """Test that wrapper translates parameters correctly."""
    print("🧪 Running wrapper parameter translation test...")

    # This should fail first (TDD principle)
    wrapper = SuperpowerWrapper(
        source_plugin="abstract",
        source_command="test-skill",
        target_superpower="test-driven-development"
    )

    print("✅ Wrapper created successfully")

    # Test parameter translation - this should fail initially
    input_params = {
        "skill-path": "skills/my-skill",
        "phase": "red"
    }

    print(f"🔍 Translating parameters: {input_params}")
    result = wrapper.translate_parameters(input_params)
    print(f"📝 Translation result: {result}")

    # Validate expected mappings exist
    assert "target_under_test" in result, f"Expected 'target_under_test' in result, got: {result.keys()}"
    assert "tdd_phase" in result, f"Expected 'tdd_phase' in result, got: {result.keys()}"

    # Validate correct values
    assert result["target_under_test"] == "skills/my-skill", f"Expected 'skills/my-skill', got '{result['target_under_test']}'"
    assert result["tdd_phase"] == "red", f"Expected 'red', got '{result['tdd_phase']}'"

    print("✅ All assertions passed!")


def test_wrapper_validation():
    """Test wrapper validation functionality."""
    print("🧪 Running wrapper validation test...")

    # Test invalid inputs - should raise ValueError
    try:
        wrapper = SuperpowerWrapper("", "test-skill", "test-driven-development")
        assert False, "Should have raised ValueError for empty source_plugin"
    except ValueError as e:
        print(f"✅ Correctly caught invalid source_plugin: {e}")

    try:
        wrapper = SuperpowerWrapper("abstract", None, "test-driven-development")
        assert False, "Should have raised ValueError for None source_command"
    except ValueError as e:
        print(f"✅ Correctly caught invalid source_command: {e}")

    try:
        wrapper = SuperpowerWrapper("abstract", "test-skill", "")
        assert False, "Should have raised ValueError for empty target_superpower"
    except ValueError as e:
        print(f"✅ Correctly caught invalid target_superpower: {e}")

    print("✅ Validation tests passed!")


def test_parameter_validation():
    """Test parameter validation functionality."""
    print("🧪 Running parameter validation test...")

    wrapper = SuperpowerWrapper(
        source_plugin="abstract",
        source_command="test-skill",
        target_superpower="test-driven-development"
    )

    # Test invalid parameter types
    try:
        wrapper.translate_parameters("not a dict")
        assert False, "Should have raised ValueError for non-dict parameters"
    except ValueError as e:
        print(f"✅ Correctly caught invalid parameter type: {e}")

    # Test empty parameters
    result = wrapper.translate_parameters({})
    assert result == {}, f"Expected empty dict for empty input, got: {result}"
    print("✅ Empty parameters handled correctly")

    print("✅ Parameter validation tests passed!")


if __name__ == "__main__":
    print("🚀 Running wrapper infrastructure tests...")

    try:
        test_wrapper_validation()
        test_parameter_validation()
        test_wrapper_translates_parameters()
        print("\n🎉 All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)