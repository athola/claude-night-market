"""Performance benchmarks for continuous improvement workflows.

Catches regressions and provides baselines. Marked with pytest.mark.benchmark
so they can run separately from the main suite.
"""

import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from update_plugin_registrations import PluginAuditor

# Mark all tests in this module as benchmarks
pytestmark = pytest.mark.benchmark


class TestAuditPerformance:
    """Benchmark plugin audit operations."""

    def _create_plugin(self, tmp_path, n_commands=10, n_skills=5, n_agents=3):
        """Helper to create a plugin with configurable size."""
        plugin_dir = tmp_path / "bench-plugin"
        plugin_dir.mkdir(exist_ok=True)

        commands_dir = plugin_dir / "commands"
        commands_dir.mkdir(exist_ok=True)
        for i in range(n_commands):
            (commands_dir / f"cmd-{i}.md").write_text(f"# Command {i}")

        skills_dir = plugin_dir / "skills"
        skills_dir.mkdir(exist_ok=True)
        for i in range(n_skills):
            skill = skills_dir / f"skill-{i}"
            skill.mkdir(exist_ok=True)
            (skill / "SKILL.md").write_text(f"---\nname: skill-{i}\n---\n# Skill {i}")

        agents_dir = plugin_dir / "agents"
        agents_dir.mkdir(exist_ok=True)
        for i in range(n_agents):
            (agents_dir / f"agent-{i}.md").write_text(f"# Agent {i}")

        config_dir = plugin_dir / ".claude-plugin"
        config_dir.mkdir(exist_ok=True)
        (config_dir / "plugin.json").write_text(
            json.dumps(
                {
                    "name": "bench-plugin",
                    "commands": [f"./commands/cmd-{i}.md" for i in range(n_commands)],
                    "skills": [f"./skills/skill-{i}" for i in range(n_skills)],
                    "agents": [f"./agents/agent-{i}.md" for i in range(n_agents)],
                },
                indent=2,
            )
        )

        return plugin_dir

    def test_scan_disk_files_performance(self, tmp_path):
        """Scan should complete in <1s for typical plugin."""
        self._create_plugin(tmp_path)
        auditor = PluginAuditor(tmp_path, dry_run=True)

        start = time.monotonic()
        auditor.scan_disk_files(tmp_path / "bench-plugin")
        duration = time.monotonic() - start

        assert duration < 1.0, f"scan_disk_files took {duration:.2f}s (expected <1s)"

    def test_audit_plugin_performance(self, tmp_path):
        """Full audit should complete in <2s for typical plugin."""
        self._create_plugin(tmp_path)
        auditor = PluginAuditor(tmp_path, dry_run=True)

        start = time.monotonic()
        auditor.audit_plugin("bench-plugin")
        duration = time.monotonic() - start

        assert duration < 2.0, f"audit_plugin took {duration:.2f}s (expected <2s)"

    def test_large_plugin_performance(self, tmp_path):
        """Audit a large plugin (50 commands, 30 skills, 20 agents) in <5s."""
        self._create_plugin(tmp_path, n_commands=50, n_skills=30, n_agents=20)
        auditor = PluginAuditor(tmp_path, dry_run=True)

        start = time.monotonic()
        auditor.audit_plugin("bench-plugin")
        duration = time.monotonic() - start

        assert duration < 5.0, f"Large plugin audit took {duration:.2f}s (expected <5s)"

    def test_fix_plugin_performance(self, tmp_path):
        """Fix operation should complete in <1s."""
        self._create_plugin(tmp_path)
        auditor = PluginAuditor(tmp_path, dry_run=False)
        auditor.discrepancies["bench-plugin"] = {
            "missing": {"commands": ["./commands/new-cmd.md"]},
            "stale": {},
        }

        start = time.monotonic()
        auditor.fix_plugin("bench-plugin")
        duration = time.monotonic() - start

        assert duration < 1.0, f"fix_plugin took {duration:.2f}s (expected <1s)"

    def test_phase2_performance(self, tmp_path):
        """Phase 2 analysis should complete in <5s."""
        self._create_plugin(tmp_path)
        auditor = PluginAuditor(tmp_path, dry_run=True)

        start = time.monotonic()
        auditor.analyze_skill_performance("bench-plugin")
        duration = time.monotonic() - start

        assert duration < 5.0, f"Phase 2 took {duration:.2f}s (expected <5s)"

    def test_phase3_performance(self, tmp_path):
        """Phase 3 meta-evaluation should complete in <5s."""
        self._create_plugin(tmp_path)
        auditor = PluginAuditor(tmp_path, dry_run=True)
        plugin_dir = tmp_path / "bench-plugin"

        start = time.monotonic()
        auditor.check_meta_evaluation("bench-plugin", plugin_dir)
        duration = time.monotonic() - start

        assert duration < 5.0, f"Phase 3 took {duration:.2f}s (expected <5s)"

    def test_compare_registrations_performance(self, tmp_path):
        """Registration comparison should complete in <1s."""
        plugin_dir = self._create_plugin(tmp_path)
        auditor = PluginAuditor(tmp_path, dry_run=True)
        on_disk = auditor.scan_disk_files(plugin_dir)
        plugin_json = auditor.read_plugin_json(plugin_dir)

        start = time.monotonic()
        auditor.compare_registrations(plugin_dir, on_disk, plugin_json)
        duration = time.monotonic() - start

        assert duration < 1.0, (
            f"compare_registrations took {duration:.2f}s (expected <1s)"
        )

    def test_full_pipeline_performance(self, tmp_path):
        """Full pipeline (audit + phase 2 + phase 3) should complete in <5s."""
        plugin_dir = self._create_plugin(tmp_path)
        auditor = PluginAuditor(tmp_path, dry_run=True)

        start = time.monotonic()
        auditor.audit_plugin("bench-plugin")
        auditor.analyze_skill_performance("bench-plugin")
        auditor.check_meta_evaluation("bench-plugin", plugin_dir)
        duration = time.monotonic() - start

        assert duration < 5.0, f"Full pipeline took {duration:.2f}s (expected <5s)"
