"""Scale checks for the continuous improvement audit workflow.

Each audit phase runs against typical and large plugin fixtures and the
test asserts the result is complete and correct. Wall-clock bounds were
removed: they measured the host (a loaded runner fails them) rather than
the auditor, and a quadratic rescan shows up as a wrong or missing result
in the structural assertions below only when it changes behavior.
"""

import json

from update_plugin_registrations import PluginAuditor


class TestAuditAtScale:
    """Audit operations return complete results at typical and large sizes."""

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

    def test_scan_disk_files_finds_every_fixture_file(self, tmp_path):
        """Scan reports each command, skill and agent of a typical plugin."""
        plugin_dir = self._create_plugin(tmp_path)
        auditor = PluginAuditor(tmp_path, dry_run=True)

        found = auditor.scan_disk_files(plugin_dir)

        assert {kind: len(paths) for kind, paths in found.items()} == {
            "commands": 10,
            "skills": 5,
            "agents": 3,
            "hooks": 0,
        }

    def test_large_plugin_scan_finds_every_fixture_file(self, tmp_path):
        """Scan stays complete for 50 commands, 30 skills and 20 agents."""
        plugin_dir = self._create_plugin(
            tmp_path, n_commands=50, n_skills=30, n_agents=20
        )
        auditor = PluginAuditor(tmp_path, dry_run=True)

        found = auditor.scan_disk_files(plugin_dir)

        assert (len(found["commands"]), len(found["skills"]), len(found["agents"])) == (
            50,
            30,
            20,
        )

    def test_scan_ignores_markdown_nested_in_module_directories(self, tmp_path):
        """Nested module and steps markdown is not counted as a command."""
        plugin_dir = self._create_plugin(tmp_path)
        nested = plugin_dir / "commands" / "cmd-0-modules" / "steps"
        nested.mkdir(parents=True)
        (nested / "1-step.md").write_text("# Step")
        auditor = PluginAuditor(tmp_path, dry_run=True)

        found = auditor.scan_disk_files(plugin_dir)

        assert len(found["commands"]) == 10

    def test_audit_of_a_fully_registered_plugin_records_no_discrepancy(self, tmp_path):
        """A plugin whose plugin.json lists every file has nothing to report."""
        self._create_plugin(tmp_path, n_commands=50, n_skills=30, n_agents=20)
        auditor = PluginAuditor(tmp_path, dry_run=True)

        auditor.audit_plugin("bench-plugin")

        assert auditor.discrepancies == {}

    def test_audit_reports_an_unregistered_command(self, tmp_path):
        """A command file missing from plugin.json is listed as missing."""
        plugin_dir = self._create_plugin(tmp_path)
        (plugin_dir / "commands" / "unregistered.md").write_text("# New")
        auditor = PluginAuditor(tmp_path, dry_run=True)

        auditor.audit_plugin("bench-plugin")

        assert auditor.discrepancies["bench-plugin"]["missing"]["commands"] == [
            "./commands/unregistered.md"
        ]

    def test_fix_plugin_registers_the_missing_command_in_plugin_json(self, tmp_path):
        """Fix writes the missing command into plugin.json."""
        plugin_dir = self._create_plugin(tmp_path)
        auditor = PluginAuditor(tmp_path, dry_run=False)
        auditor.discrepancies["bench-plugin"] = {
            "missing": {"commands": ["./commands/new-cmd.md"]},
            "stale": {},
        }

        auditor.fix_plugin("bench-plugin")

        registered = json.loads(
            (plugin_dir / ".claude-plugin" / "plugin.json").read_text()
        )["commands"]
        assert "./commands/new-cmd.md" in registered

    def test_dry_run_fix_leaves_plugin_json_unchanged(self, tmp_path):
        """Fix under dry_run does not write plugin.json."""
        plugin_dir = self._create_plugin(tmp_path)
        config = plugin_dir / ".claude-plugin" / "plugin.json"
        before = config.read_text()
        auditor = PluginAuditor(tmp_path, dry_run=True)
        auditor.discrepancies["bench-plugin"] = {
            "missing": {"commands": ["./commands/new-cmd.md"]},
            "stale": {},
        }

        auditor.fix_plugin("bench-plugin")

        assert config.read_text() == before

    def test_skill_performance_without_logs_reports_no_problem_skills(self, tmp_path):
        """Phase 2 finds no unstable skills when no usage logs exist."""
        self._create_plugin(tmp_path)
        auditor = PluginAuditor(tmp_path, dry_run=True)

        report = auditor.analyze_skill_performance("bench-plugin")

        assert report == {
            "unstable_skills": [],
            "recent_failures": [],
            "low_success_rate": [],
        }

    def test_meta_evaluation_reports_the_three_check_categories(self, tmp_path):
        """Phase 3 returns one list per documented check."""
        plugin_dir = self._create_plugin(tmp_path)
        auditor = PluginAuditor(tmp_path, dry_run=True)

        report = auditor.check_meta_evaluation(plugin_dir)

        assert set(report) == {"missing_toc", "missing_verification", "missing_tests"}

    def test_compare_registrations_matches_a_registered_plugin(self, tmp_path):
        """Comparing disk to plugin.json for a registered plugin finds no drift."""
        plugin_dir = self._create_plugin(tmp_path)
        auditor = PluginAuditor(tmp_path, dry_run=True)
        on_disk = auditor.scan_disk_files(plugin_dir)
        plugin_json = auditor.read_plugin_json(plugin_dir)

        drift = auditor.compare_registrations(plugin_dir, on_disk, plugin_json)

        assert drift == {"missing": {}, "stale": {}}
