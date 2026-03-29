"""Tests for compatibility validator."""

from scripts.compatibility_validator import CompatibilityValidator


def test_validate_wrapper_with_matching_features(tmp_path) -> None:
    """Test validator passes when wrapper matches command features."""
    command = tmp_path / "command.md"
    wrapper = tmp_path / "wrapper.py"

    command.write_text(
        """---
name: test-command
parameters:
  - skill-path
  - command
options:
  - verbose
  - debug
usage: "JSON"
---
This command performs validation checks.
""",
    )
    wrapper.write_text(
        """def run(skill_path, command, verbose=False, debug=False):
    options = ["--verbose", "--debug"]
    output = {"format": "json"}
    try:
        validate(command)
    except Exception:
        return {"status": "error", **output}
    return {"status": "ok", **output}
""",
    )

    validator = CompatibilityValidator()
    result = validator.validate_wrapper(str(command), str(wrapper))

    assert result["validation_passed"] is True
    assert result["feature_parity"] == 1.0
    assert result["missing_features"] == []


def test_validate_wrapper_flags_missing_critical_parameter(tmp_path) -> None:
    """Test validator flags missing critical parameters."""
    command = tmp_path / "command.md"
    wrapper = tmp_path / "wrapper.py"

    command.write_text(
        """---
name: test-command
parameters:
  - skill-path
  - command
usage: "JSON output"
---
""",
    )
    wrapper.write_text(
        """def run(command):
    return {"format": "json"}
""",
    )

    validator = CompatibilityValidator()
    result = validator.validate_wrapper(str(command), str(wrapper))

    assert result["validation_passed"] is False
    assert any(
        feature["category"] == "parameters"
        and feature["name"] == "skill-path"
        and feature["severity"] == "critical"
        for feature in result["missing_features"]
    )
