import pytest
from src.test_skill_wrapper import TestSkillWrapper

def test_test_skill_invokes_tdd_superpower():
    wrapper = TestSkillWrapper()

    # Mock the superpower call
    result = wrapper.execute({
        "skill-path": "skills/analyzing-logs",
        "phase": "red"
    })

    assert result["superpower_called"] == "test-driven-development"
    assert result["phase_executed"] == "red"