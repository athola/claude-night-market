# ruff: noqa: D101,D102,D103,PLR2004,E501,S603
"""Cross-component workflow tests.

Each test pins an agreement between two sanctum components that one
workflow depends on: a command and the skill it loads, or a command and the
script it runs. Changing one side without the other fails here.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = PLUGIN_ROOT.parent
COMMANDS = PLUGIN_ROOT / "commands"
SKILLS = PLUGIN_ROOT / "skills"


def _commit_types(text: str, heading: str) -> list[str]:
    """Return the backticked commit types listed in the step named ``heading``."""
    step = re.search(rf"\*\*{heading}\*\*.*?(?=\n\d+[a-z]?\. \*\*)", text, re.DOTALL)
    assert step, f"step {heading!r} not found"
    return re.findall(r"`([a-z]+)`", step.group(0))


def _first_skill_loaded(command: Path) -> str:
    match = re.search(r"Run `Skill\(([a-z-]+:[a-z-]+)\)`", command.read_text())
    assert match, f"{command.name} loads no skill"
    return match.group(1)


class TestIntegrationWorkflows:
    def test_commit_command_and_skill_classify_with_the_same_types(self) -> None:
        """/commit-msg and the commit-messages skill classify with the same types.

        GIVEN the classify step in the command and in the skill
        WHEN their commit types are compared
        THEN both offer the same set, so the two routes produce the same prefixes
        """
        command_types = _commit_types(
            (COMMANDS / "commit-msg.md").read_text(), "Classify the change"
        )
        skill_types = _commit_types(
            (SKILLS / "commit-messages" / "SKILL.md").read_text(), "Classify"
        )
        assert set(command_types) == set(skill_types)
        assert {"feat", "fix", "docs", "refactor"} <= set(skill_types)

    def test_git_catchup_command_loads_existing_skills_in_order(self) -> None:
        """/git-catchup loads workspace review first, then a catchup skill that exists.

        GIVEN the git-catchup command
        WHEN its skill references are resolved
        THEN it starts with git-workspace-review and imbue's catchup skill is on disk
        """
        text = (COMMANDS / "git-catchup.md").read_text()
        loaded = re.findall(r"Run `Skill\(([a-z-]+):([a-z-]+)\)`", text)
        assert loaded[:2] == [
            ("sanctum", "git-workspace-review"),
            ("imbue", "catchup"),
        ]
        for plugin, skill in loaded:
            assert (PLUGINS_DIR / plugin / "skills" / skill / "SKILL.md").is_file()

    def test_update_versions_script_bumps_root_and_nested_manifests(
        self, tmp_path: Path
    ) -> None:
        """The script /update-version names bumps every manifest it says it supports.

        GIVEN a project with a root package.json and a nested plugin.json at 0.1.0
        WHEN update_versions.py runs with 0.1.1 against that root
        THEN both files carry 0.1.1 and nothing else in them changed
        """
        assert (
            "update_versions.py <version>"
            in (COMMANDS / "update-version.md").read_text()
        )
        package = tmp_path / "package.json"
        package.write_text('{"name": "demo", "version": "0.1.0"}\n')
        plugin = tmp_path / "plugins" / "demo" / ".claude-plugin" / "plugin.json"
        plugin.parent.mkdir(parents=True)
        plugin.write_text('{"name": "demo", "version": "0.1.0"}\n')

        result = subprocess.run(
            [
                sys.executable,
                str(PLUGIN_ROOT / "scripts" / "update_versions.py"),
                "0.1.1",
                "--root",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert json.loads(package.read_text()) == {"name": "demo", "version": "0.1.1"}
        assert json.loads(plugin.read_text()) == {"name": "demo", "version": "0.1.1"}

    def test_commit_path_docs_all_forbid_no_verify(self) -> None:
        """Every commit-path component tells a failing hook to be fixed, not skipped.

        GIVEN the commit command, the commit skill and the workspace review skill
        WHEN their rules are read
        THEN each one forbids --no-verify
        """
        for doc in (
            COMMANDS / "commit-msg.md",
            SKILLS / "commit-messages" / "SKILL.md",
            SKILLS / "git-workspace-review" / "SKILL.md",
        ):
            text = doc.read_text()
            assert re.search(r"(NEVER|Do not)[^.]*--no-verify", text), doc.name

    def test_tree_changing_commands_load_workspace_review_first(self) -> None:
        """Commands that change the tree capture workspace state before acting.

        GIVEN the commands that edit versions, docs or tests
        WHEN their first skill load is read
        THEN each loads git-workspace-review before anything else
        """
        for name in ("update-version.md", "update-docs.md", "update-tests.md"):
            assert (
                _first_skill_loaded(COMMANDS / name) == "sanctum:git-workspace-review"
            ), name
