import os
import subprocess
import tempfile


def test_end_to_end_test_skill_migration():
    """Test that /test-skill wrapper works end-to-end"""
    # Create a test skill
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_path = os.path.join(tmpdir, "test-skill")
        os.makedirs(skill_path)

        with open(os.path.join(skill_path, "SKILL.md"), 'w') as f:
            f.write("""
---
name: test-skill
description: Test skill for migration validation
---
# Test Skill
This is a test skill.
""")

        # Run the wrapper
        result = subprocess.run([
            "python", "-c",
            f"""
from src.test_skill_wrapper import TestSkillWrapper
wrapper = TestSkillWrapper()
result = wrapper.execute({{
    'skill-path': '{skill_path}',
    'phase': 'red'
}})
print(result)
"""
        ], check=False, capture_output=True, text=True)

        assert result.returncode == 0
        assert "superpower_called" in result.stdout
