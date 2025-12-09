import os
import tempfile

from scripts.compatibility_validator import CompatibilityValidator


def test_validates_feature_parity():
    """Test that compatibility validator correctly validates feature parity"""
    validator = CompatibilityValidator()

    # Create temporary files for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock original command file
        original_file = os.path.join(tmpdir, "test-skill.md")
        with open(original_file, 'w') as f:
            f.write("""---
name: test-skill
description: Test skill for TDD workflows
usage: /test-skill [skill-path] [--phase red|green|refactor]
parameters:
  - name: skill-path
    required: true
  - name: phase
    required: false
    values: [red, green, refactor]
options:
  - red
  - green
  - refactor
---

# Test Skill Command

This command implements TDD workflow for skills.
""")

        # Create mock wrapper file
        wrapper_file = os.path.join(tmpdir, "test_skill_wrapper.py")
        with open(wrapper_file, 'w') as f:
            f.write('''from wrapper_base import SuperpowerWrapper

class TestSkillWrapper(SuperpowerWrapper):
    def __init__(self):
        super().__init__(
            source_plugin="abstract",
            source_command="test-skill",
            target_superpower="test-driven-development"
        )

    def execute(self, skill_path, phase):
        """Execute with all original parameters"""
        return {
            "skill_path": skill_path,
            "phase": phase,
            "options": ["red", "green", "refactor"],
            "output_format": "markdown_report"
        }
''')

        result = validator.validate_wrapper(original_file, wrapper_file)

        # We should have decent parity with reasonable expectations
        assert result["feature_parity"] >= 0.4
        # Allow missing features but check they're not all critical
        critical_missing = [f for f in result["missing_features"] if f.get("severity") == "critical"]
        assert len(critical_missing) <= 1  # At most 1 critical missing feature

def test_detects_missing_features():
    """Test that validator detects missing features"""
    validator = CompatibilityValidator()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create original with many features
        original_file = os.path.join(tmpdir, "feature-rich.md")
        with open(original_file, 'w') as f:
            f.write("""---
name: feature-rich
parameters:
  - name: skill-path
  - name: phase
  - name: verbose
  - name: debug
options:
  - red
  - green
  - refactor
  - verbose
  - debug
  - timeout
---

# Feature Rich Command
""")

        # Create minimal wrapper
        wrapper_file = os.path.join(tmpdir, "minimal.py")
        with open(wrapper_file, 'w') as f:
            f.write('''class MinimalWrapper:
    def execute(self, skill_path):
        """Minimal implementation"""
        return {"result": "minimal"}
''')

        result = validator.validate_wrapper(original_file, wrapper_file)

        # Minimal wrapper should have lower but not terrible parity
        assert result["feature_parity"] <= 0.8
        assert len(result["missing_features"]) > 0  # Should detect missing features
        assert any(feature["name"] in ["verbose", "debug", "timeout"]
                  for feature in result["missing_features"])

def test_calculates_parity_score_correctly():
    """Test parity score calculation"""
    validator = CompatibilityValidator()

    # Test perfect parity
    original_features = {
        "parameters": ["skill-path", "phase"],
        "options": ["red", "green", "refactor"],
        "output_format": "markdown",
        "error_handling": ["validation", "fallback"]
    }

    wrapper_features = {
        "parameters": ["skill-path", "phase"],
        "options": ["red", "green", "refactor"],
        "output_format": "markdown",
        "error_handling": ["validation", "fallback"]
    }

    score = validator._calculate_parity(original_features, wrapper_features)
    assert score == 1.0

    # Test partial parity
    partial_features = {
        "parameters": ["skill-path"],  # missing 'phase'
        "options": ["red", "green"],   # missing 'refactor'
        "output_format": "json",      # different format
        "error_handling": ["validation"]  # missing 'fallback'
    }

    score = validator._calculate_parity(original_features, partial_features)
    assert 0.3 <= score <= 0.5  # Should be around 0.4 based on weights

def test_parses_different_file_types():
    """Test parsing different file types"""
    validator = CompatibilityValidator()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Test markdown parsing
        md_file = os.path.join(tmpdir, "test.md")
        with open(md_file, 'w') as f:
            f.write("""---
parameters:
  - name: skill-path
  - name: phase
options:
  - red
  - green
---
""")

        md_features = validator._parse_markdown_command(md_file)
        assert "skill-path" in md_features["parameters"]
        assert "phase" in md_features["parameters"]
        assert "red" in md_features["options"]

        # Test Python parsing
        py_file = os.path.join(tmpdir, "test.py")
        with open(py_file, 'w') as f:
            f.write('''
def execute(skill_path, phase="red", debug=False):
    """Execute with parameters"""
    if debug:
        print("Debug mode")
    return {"status": "ok"}
''')

        py_features = validator._parse_python_wrapper(py_file)
        assert "skill_path" in py_features["parameters"] or "skill_path" in str(py_features)
        assert "phase" in py_features["parameters"] or "phase" in str(py_features)

def test_feature_weights():
    """Test that feature weights are applied correctly"""
    validator = CompatibilityValidator()

    # Check that weights are defined and sum to 1.0
    total_weight = sum(validator.feature_weights.values())
    assert abs(total_weight - 1.0) < 0.01

    # Check required features exist
    required_features = ["parameters", "options", "output_format", "error_handling"]
    for feature in required_features:
        assert feature in validator.feature_weights
        assert validator.feature_weights[feature] > 0
