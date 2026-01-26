#!/usr/bin/env python3
"""Simple tests for update_plugin_registrations.py script (no pytest)."""

import json
import sys
import tempfile
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from update_plugin_registrations import PluginAuditor


def test_scan_disk_files_finds_commands() -> None:
    """Test scanning for command files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create test structure
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "test-command.md").write_text("# Test")
        (commands_dir / "another-command.md").write_text("# Another")

        # Create module subdir (should be excluded)
        modules_dir = commands_dir / "test-modules"
        modules_dir.mkdir()
        (modules_dir / "module-file.md").write_text("# Module")

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor.scan_disk_files(tmp_path)

        assert len(result["commands"]) == 2, (
            f"Expected 2 commands, got {len(result['commands'])}"
        )
        assert "./commands/another-command.md" in result["commands"]
        assert "./commands/test-command.md" in result["commands"]
        assert "./commands/test-modules/module-file.md" not in result["commands"]
    print("✓ test_scan_disk_files_finds_commands passed")


def test_scan_disk_files_finds_skills() -> None:
    """Test scanning for skill directories with valid content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        # Skills need SKILL.md or root .md files to be recognized
        test_skill = skills_dir / "test-skill"
        test_skill.mkdir()
        (test_skill / "SKILL.md").write_text("# Test Skill")
        another_skill = skills_dir / "another-skill"
        another_skill.mkdir()
        (another_skill / "SKILL.md").write_text("# Another Skill")
        (skills_dir / "__pycache__").mkdir()  # Should be excluded

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor.scan_disk_files(tmp_path)

        assert len(result["skills"]) == 2, (
            f"Expected 2 skills, got {len(result['skills'])}"
        )
        assert "./skills/another-skill" in result["skills"]
        assert "./skills/test-skill" in result["skills"]
        assert "./skills/__pycache__" not in result["skills"]
    print("✓ test_scan_disk_files_finds_skills passed")


def test_compare_registrations_finds_missing() -> None:
    """Test detecting missing registrations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        on_disk = {
            "commands": ["./commands/cmd1.md", "./commands/cmd2.md"],
            "skills": [],
            "agents": [],
            "hooks": [],
        }
        in_json = {
            "commands": ["./commands/cmd1.md"],
            "skills": [],
            "agents": [],
            "hooks": [],
        }

        auditor = PluginAuditor(tmp_path, dry_run=True)
        discrepancies = auditor.compare_registrations("test", on_disk, in_json)

        assert "commands" in discrepancies["missing"]
        assert "./commands/cmd2.md" in discrepancies["missing"]["commands"]
    print("✓ test_compare_registrations_finds_missing passed")


def test_fix_plugin_adds_missing() -> None:
    """Test fixing adds missing registrations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create plugin structure
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()

        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir()

        plugin_json = config_dir / "plugin.json"
        plugin_json.write_text(
            json.dumps(
                {"name": "test-plugin", "commands": ["./commands/cmd1.md"]}, indent=2
            )
        )

        # Create auditor and simulate discrepancies
        auditor = PluginAuditor(tmp_path, dry_run=False)
        auditor.discrepancies["test-plugin"] = {
            "missing": {"commands": ["./commands/cmd2.md"]},
            "stale": {},
        }

        # Fix
        auditor.fix_plugin("test-plugin")

        # Verify
        with plugin_json.open() as f:
            data = json.load(f)

        assert len(data["commands"]) == 2
        assert "./commands/cmd1.md" in data["commands"]
        assert "./commands/cmd2.md" in data["commands"]
    print("✓ test_fix_plugin_adds_missing passed")


def test_scan_disk_files_excludes_cache_directories() -> None:
    """Test that cache/temp directories are properly excluded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create legitimate files
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "real-command.md").write_text("# Real")

        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        real_skill = skills_dir / "real-skill"
        real_skill.mkdir()
        (real_skill / "SKILL.md").write_text("# Real Skill")

        # Create cache directories that should be excluded
        # Python caches
        venv_cmd = commands_dir / ".venv"
        venv_cmd.mkdir()
        (venv_cmd / "fake-command.md").write_text("# Fake")

        pycache_skill = skills_dir / "__pycache__"
        pycache_skill.mkdir()

        # Node caches
        node_modules = skills_dir / "node_modules"
        node_modules.mkdir()

        # Rust caches
        target_skill = skills_dir / "target"
        target_skill.mkdir()

        auditor = PluginAuditor(tmp_path.parent, dry_run=True)
        result = auditor.scan_disk_files(tmp_path)

        # Should only find legitimate files
        assert len(result["commands"]) == 1, (
            f"Expected 1 command, got {len(result['commands'])}"
        )
        assert "./commands/real-command.md" in result["commands"]
        assert not any(".venv" in cmd for cmd in result["commands"]), (
            "Found .venv in commands"
        )

        assert len(result["skills"]) == 1, (
            f"Expected 1 skill, got {len(result['skills'])}"
        )
        assert "./skills/real-skill" in result["skills"]
        assert not any("__pycache__" in skill for skill in result["skills"]), (
            "Found __pycache__ in skills"
        )
        assert not any("node_modules" in skill for skill in result["skills"]), (
            "Found node_modules in skills"
        )
        assert not any("target" in skill for skill in result["skills"]), (
            "Found target in skills"
        )
    print("✓ test_scan_disk_files_excludes_cache_directories passed")


def main() -> None:
    """Run all tests."""
    print("Running update_plugin_registrations tests...\n")

    tests = [
        test_scan_disk_files_finds_commands,
        test_scan_disk_files_finds_skills,
        test_scan_disk_files_excludes_cache_directories,
        test_compare_registrations_finds_missing,
        test_fix_plugin_adds_missing,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Tests passed: {passed}/{len(tests)}")
    print(f"Tests failed: {failed}/{len(tests)}")
    print("=" * 50)

    if failed > 0:
        sys.exit(1)
    else:
        print("\n✓ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
