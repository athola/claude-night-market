"""Test attune plugin structure and basic functionality."""

import json
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).parent.parent


def test_plugin_json_exists():
    """Verify plugin.json exists and is valid."""
    plugin_json = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
    assert plugin_json.exists(), "plugin.json not found"

    with open(plugin_json) as f:
        data = json.load(f)

    assert data["name"] == "attune"
    assert data["version"] == "1.2.0"
    assert "commands" in data
    assert "skills" in data
    assert len(data["keywords"]) > 0


def test_metadata_json_exists():
    """Verify metadata.json exists and is valid."""
    metadata_json = PLUGIN_ROOT / ".claude-plugin" / "metadata.json"
    assert metadata_json.exists(), "metadata.json not found"

    with open(metadata_json) as f:
        data = json.load(f)

    assert data["name"] == "attune"
    assert data["version"] == "1.2.0"


def test_commands_exist():
    """Verify all registered commands have corresponding files."""
    plugin_json = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"

    with open(plugin_json) as f:
        data = json.load(f)

    for command in data["commands"]:
        command_path = PLUGIN_ROOT / command
        assert command_path.exists(), f"Command file not found: {command}"


def test_skills_exist():
    """Verify all registered skills have corresponding files."""
    plugin_json = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"

    with open(plugin_json) as f:
        data = json.load(f)

    for skill in data["skills"]:
        skill_path = PLUGIN_ROOT / skill
        if skill_path.suffix == ".md":
            # Single-file skill
            assert skill_path.exists(), f"Skill file not found: {skill}"
        else:
            # Directory skill with SKILL.md
            skill_file = skill_path / "SKILL.md"
            assert skill_file.exists(), f"SKILL.md not found in {skill}"


def test_python_templates_exist():
    """Verify Python templates are present."""
    templates_dir = PLUGIN_ROOT / "templates" / "python"
    assert templates_dir.exists(), "Python templates directory not found"

    required_templates = [
        ".gitignore.template",
        "pyproject.toml.template",
        "Makefile.template",
        ".pre-commit-config.yaml.template",
        "workflows/test.yml.template",
        "workflows/lint.yml.template",
        "workflows/typecheck.yml.template",
    ]

    for template in required_templates:
        template_path = templates_dir / template
        assert template_path.exists(), f"Template not found: {template}"


def test_scripts_exist():
    """Verify Python scripts are present."""
    scripts_dir = PLUGIN_ROOT / "scripts"
    assert scripts_dir.exists(), "Scripts directory not found"

    required_scripts = [
        "attune_init.py",
        "template_engine.py",
        "project_detector.py",
    ]

    for script in required_scripts:
        script_path = scripts_dir / script
        assert script_path.exists(), f"Script not found: {script}"


def test_init_script_executable():
    """Verify init script is executable."""
    init_script = PLUGIN_ROOT / "scripts" / "attune_init.py"
    assert init_script.exists(), "attune_init.py not found"

    # Check if file has execute permissions
    import stat

    st = init_script.stat()
    assert st.st_mode & stat.S_IXUSR, "attune_init.py is not executable"


def test_readme_exists():
    """Verify README.md exists."""
    readme = PLUGIN_ROOT / "README.md"
    assert readme.exists(), "README.md not found"

    content = readme.read_text()
    assert "# Attune" in content
    assert "Quick Start" in content


def test_brainstorm_doc_exists():
    """Verify brainstorming document exists."""
    brainstorm = PLUGIN_ROOT / "docs" / "brainstorm-attune-plugin.md"
    assert brainstorm.exists(), "Brainstorming document not found"

    content = brainstorm.read_text()
    assert "Problem Statement" in content
    assert "Recommended Approach" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
