"""Performance benchmarks for continuous improvement workflows.

Catches regressions and provides baselines. Marked with pytest.mark.benchmark
so they can run separately from the main suite.
"""

import json
import time

import pytest
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
        """Scan should complete in <100ms for typical plugin.

        Rationale: scanning ~18 local tmp files (10 commands, 5 skills,
        3 agents) is pure filesystem traversal with no I/O amplification.
        100ms is already 10-100x the observed runtime (~1-5ms); anything
        slower indicates a regression such as an accidental rglob over a
        large tree or a blocking network call.
        """
        self._create_plugin(tmp_path)
        auditor = PluginAuditor(tmp_path, dry_run=True)

        start = time.monotonic()
        auditor.scan_disk_files(tmp_path / "bench-plugin")
        duration = time.monotonic() - start

        assert duration < 0.1, f"scan_disk_files took {duration:.3f}s (expected <0.1s)"

    def test_audit_plugin_performance(self, tmp_path):
        """Full audit should complete in <200ms for typical plugin.

        Rationale: audit_plugin combines scan_disk_files, read_plugin_json,
        compare_registrations, and audit_skill_modules. All operations are
        local I/O on ~18 small tmp files. 200ms is a 20-100x safety margin
        over observed runtime (~5-10ms); exceeding it strongly signals an
        algorithmic regression (e.g., O(n^2) file scanning).
        """
        self._create_plugin(tmp_path)
        auditor = PluginAuditor(tmp_path, dry_run=True)

        start = time.monotonic()
        auditor.audit_plugin("bench-plugin")
        duration = time.monotonic() - start

        assert duration < 0.2, f"audit_plugin took {duration:.3f}s (expected <0.2s)"

    def test_large_plugin_performance(self, tmp_path):
        """Audit a large plugin (50 commands, 30 skills, 20 agents) in <1s.

        Rationale: 100 files is roughly 5x the typical plugin size. The
        algorithm is O(n) in file count, so the large-plugin budget is set
        to 5x the typical-plugin budget (0.2s * 5 = 1.0s), with a small
        extra cushion for filesystem overhead on slow CI disks.
        """
        self._create_plugin(tmp_path, n_commands=50, n_skills=30, n_agents=20)
        auditor = PluginAuditor(tmp_path, dry_run=True)

        start = time.monotonic()
        auditor.audit_plugin("bench-plugin")
        duration = time.monotonic() - start

        assert duration < 1.0, (
            f"Large plugin audit took {duration:.3f}s (expected <1.0s)"
        )

    def test_fix_plugin_performance(self, tmp_path):
        """Fix operation should complete in <100ms.

        Rationale: fix_plugin reads plugin.json, mutates a dict in memory,
        and writes one JSON file. Even on a slow disk this should take well
        under 50ms. 100ms gives a 2x safety margin for CI variance while
        still catching regressions like accidental full-rescan on fix.
        """
        self._create_plugin(tmp_path)
        auditor = PluginAuditor(tmp_path, dry_run=False)
        auditor.discrepancies["bench-plugin"] = {
            "missing": {"commands": ["./commands/new-cmd.md"]},
            "stale": {},
        }

        start = time.monotonic()
        auditor.fix_plugin("bench-plugin")
        duration = time.monotonic() - start

        assert duration < 0.1, f"fix_plugin took {duration:.3f}s (expected <0.1s)"

    def test_phase2_performance(self, tmp_path):
        """Phase 2 analysis should complete in <100ms.

        Rationale: PerformanceAnalyzer.analyze_plugin returns immediately
        when its log directory (~/.claude/skills/logs/) does not exist,
        which is always true in a tmp_path test environment. Even when logs
        are present the work is in-memory JSON parsing. 100ms is a generous
        budget; exceeding it likely means an unintended filesystem scan was
        introduced.
        """
        self._create_plugin(tmp_path)
        auditor = PluginAuditor(tmp_path, dry_run=True)

        start = time.monotonic()
        auditor.analyze_skill_performance("bench-plugin")
        duration = time.monotonic() - start

        assert duration < 0.1, f"Phase 2 took {duration:.3f}s (expected <0.1s)"

    def test_phase3_performance(self, tmp_path):
        """Phase 3 meta-evaluation should complete in <100ms.

        Rationale: MetaEvaluator.check_plugin reads SKILL.md files (each a
        few bytes in the fixture) and applies three simple regex patterns.
        With 5 skills in the fixture, total I/O is trivial. 100ms is a
        generous bound; exceeding it suggests a quadratic regex or an
        unintended recursive file walk was introduced.
        """
        self._create_plugin(tmp_path)
        auditor = PluginAuditor(tmp_path, dry_run=True)
        plugin_dir = tmp_path / "bench-plugin"

        start = time.monotonic()
        auditor.check_meta_evaluation("bench-plugin", plugin_dir)
        duration = time.monotonic() - start

        assert duration < 0.1, f"Phase 3 took {duration:.3f}s (expected <0.1s)"

    def test_compare_registrations_performance(self, tmp_path):
        """Registration comparison should complete in <50ms.

        Rationale: compare_registrations is pure set arithmetic on the
        pre-scanned results; no further disk I/O occurs unless a
        hooks.json is present (which this fixture does not create).
        50ms is already several orders of magnitude above the observed
        runtime (~0.1ms). Exceeding it means a disk operation was
        accidentally added to what must remain a CPU-only comparison.
        """
        plugin_dir = self._create_plugin(tmp_path)
        auditor = PluginAuditor(tmp_path, dry_run=True)
        on_disk = auditor.scan_disk_files(plugin_dir)
        plugin_json = auditor.read_plugin_json(plugin_dir)

        start = time.monotonic()
        auditor.compare_registrations(plugin_dir, on_disk, plugin_json)
        duration = time.monotonic() - start

        assert duration < 0.05, (
            f"compare_registrations took {duration:.3f}s (expected <0.05s)"
        )

    def test_full_pipeline_performance(self, tmp_path):
        """Full pipeline (audit + phase 2 + phase 3) should complete in <500ms.

        Rationale: this is the sum of audit_plugin (<0.2s), phase 2
        (<0.1s), and phase 3 (<0.1s) budgets, plus a 100ms cushion for
        Python startup variance and tmpfs overhead in CI environments.
        A regression in any single phase will push this composite test
        over its limit even if the individual test does not catch it first.
        """
        plugin_dir = self._create_plugin(tmp_path)
        auditor = PluginAuditor(tmp_path, dry_run=True)

        start = time.monotonic()
        auditor.audit_plugin("bench-plugin")
        auditor.analyze_skill_performance("bench-plugin")
        auditor.check_meta_evaluation("bench-plugin", plugin_dir)
        duration = time.monotonic() - start

        assert duration < 0.5, f"Full pipeline took {duration:.3f}s (expected <0.5s)"
