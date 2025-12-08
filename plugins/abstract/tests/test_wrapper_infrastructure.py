import pytest
from src.wrapper_base import SuperpowerWrapper

def test_wrapper_translates_parameters():
    wrapper = SuperpowerWrapper(
        source_plugin="abstract",
        source_command="test-skill",
        target_superpower="test-driven-development"
    )

    # Test parameter translation
    result = wrapper.translate_parameters({
        "skill-path": "skills/my-skill",
        "phase": "red"
    })

    assert result["target_under_test"] == "skills/my-skill"
    assert result["tdd_phase"] == "red"