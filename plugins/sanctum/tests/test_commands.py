# ruff: noqa: D101,D102,D103,PLR2004,E501,S603,S607
"""Contract tests for Sanctum slash commands.

Commands are markdown instructions. These tests pin what each one tells
the model to run, the skills and scripts it relies on, and the rules it
states, so a command that drifts from the components it calls fails here.
"""

from __future__ import annotations

import fnmatch
import json
import re
import subprocess
from pathlib import Path

import update_versions

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = PLUGIN_ROOT.parent
COMMANDS = PLUGIN_ROOT / "commands"
SKILLS = PLUGIN_ROOT / "skills"


def _command(name: str) -> str:
    return (COMMANDS / f"{name}.md").read_text()


def _slash_target_exists(plugin: str, name: str) -> bool:
    """A slash name resolves to a command file or a skill directory."""
    root = PLUGINS_DIR / plugin
    return (root / "commands" / f"{name}.md").is_file() or (
        root / "skills" / name / "SKILL.md"
    ).is_file()


class TestCatchupCommand:
    def test_catchup_command_analyzes_diverged_branch(self) -> None:
        """Delta capture diffs from the merge base, so local-only commits count.

        Three dots compare HEAD with the merge base of the two branches. Two
        dots would also report every commit the base gained since the fork.
        """
        text = _command("git-catchup")
        assert "`git diff --stat ${BASE}...HEAD`" in text
        assert "`git diff --name-only ${BASE}...HEAD`" in text

    def test_catchup_command_identifies_the_upstream_branch(self) -> None:
        """Context confirmation resolves the upstream the branch tracks."""
        assert "`git rev-parse --abbrev-ref --symbolic-full-name @{u}`" in _command(
            "git-catchup"
        )

    def test_commit_msg_command_stops_before_classifying_when_nothing_is_staged(
        self,
    ) -> None:
        """The no-staged-changes stop comes before any classification step."""
        text = _command("commit-msg")
        stop = text.index("**If nothing is staged**, tell the user and stop.")
        assert stop < text.index("**Classify the change**")


class TestPRCommand:
    def test_pr_command_prepares_pull_request(self) -> None:
        """/prepare-pr runs four pre-flight updates, each of which resolves."""
        phase0 = (
            _command("prepare-pr").split("### Phase 0", 1)[1].split("### Phase 1", 1)[0]
        )
        updates = re.findall(r"^\s+/([a-z-]+):([a-z-]+)$", phase0, re.MULTILINE)
        assert updates == [
            ("sanctum", "update-docs"),
            ("abstract", "make-dogfood"),
            ("sanctum", "update-readme"),
            ("sanctum", "update-tests"),
        ]
        for plugin, name in updates:
            assert _slash_target_exists(plugin, name), f"/{plugin}:{name}"

    def test_pr_command_routes_reviewers_through_the_who_row(self) -> None:
        """The output's Who row names an out-of-band reviewer, not a reviewer list."""
        output = _command("prepare-pr").split("## Output Structure", 1)[1]
        who = re.search(r"^\| \*\*Who\*\* \|(.*)\|$", output, re.MULTILINE)
        assert who
        assert "out-of-band reviewer" in who.group(1)

    def test_update_docs_command_identifies_documentation_needs(self) -> None:
        """/update-docs captures the change context before editing docs."""
        text = _command("update-docs")
        loaded = re.findall(r"Run `Skill\(sanctum:([a-z-]+)\)`", text)
        assert loaded[:2] == ["git-workspace-review", "doc-updates"]
        for skill in loaded[:2]:
            assert (SKILLS / skill / "SKILL.md").is_file()

    def test_update_docs_command_documents_every_flag_in_its_usage(self) -> None:
        """Each flag in the usage line is explained under Arguments."""
        text = _command("update-docs")
        usage = re.search(r"^usage: (.*)$", text, re.MULTILINE)
        assert usage
        flags = re.findall(r"--[a-z-]+", usage.group(1))
        arguments = text.split("## Arguments", 1)[1].split("\n## ", 1)[0]
        assert flags
        for flag in flags:
            assert f"- `{flag}`" in arguments, flag

    def test_update_readme_command_modernizes_readme(self) -> None:
        """The update-readme skill captures context first and ships its modules."""
        text = (SKILLS / "update-readme" / "SKILL.md").read_text()
        assert "Run `Skill(sanctum:git-workspace-review)` first" in text
        modules = re.findall(r"^- (modules/[a-z-]+\.md)$", text, re.MULTILINE)
        assert modules
        for module in modules:
            assert (SKILLS / "update-readme" / module).is_file(), module

    def test_update_version_command_bumps_all_version_files(
        self, tmp_path: Path
    ) -> None:
        """The script finds every manifest type the command says it supports."""
        text = _command("update-version")
        supported = re.search(r"Supports ([a-z._, A-Z]+)\n", text)
        assert supported
        names = [name.strip() for name in supported.group(1).split(",")]
        for name in names:
            parent = tmp_path / name.replace(".", "_")
            if name in ("plugin.json", "metadata.json"):
                parent = parent / ".claude-plugin"
            parent.mkdir(parents=True)
            (parent / name).write_text('version = "1.0.0"\n')

        found = sorted(
            path.name for path in update_versions.find_version_files(tmp_path)
        )
        assert found == sorted(names)


class TestUpdateDocsDirectoryRules:
    """Test that /update-docs covers all documentation directories."""

    @staticmethod
    def _rules() -> list[tuple[str, str, int]]:
        """Read (location, style, max file lines) rows from the command's table."""
        table = _command("update-docs").split("## Directory-Specific Style Rules", 1)[1]
        rows = re.findall(
            r"^\| (`[^`]+`|Other) \| ([^|]+) \| (\d+) lines \|", table, re.MULTILINE
        )
        return [
            (loc.strip("`"), style.strip(), int(lines)) for loc, style, lines in rows
        ]

    def _get_ruleset(self, file_path: str) -> tuple[str, int]:
        """Pick the first documented row whose location matches ``file_path``."""
        for location, style, max_lines in self._rules():
            if location == "Other":
                return style, max_lines
            pattern = location if "*" in location else f"{location}*"
            if fnmatch.fnmatchcase(file_path, pattern) and (
                "*" not in location or file_path.count("/") == location.count("/")
            ):
                return style, max_lines
        raise AssertionError(f"no row for {file_path}")

    def test_docs_directory_uses_strict_rules(self) -> None:
        assert self._get_ruleset("docs/api-overview.md") == ("Strict reference", 500)

    def test_book_directory_uses_lenient_rules(self) -> None:
        assert self._get_ruleset("book/src/tutorials/getting-started.md") == (
            "Technical book",
            1000,
        )

    def test_wiki_directory_uses_wiki_rules(self) -> None:
        assert self._get_ruleset("wiki/architecture/adr-001.md") == (
            "Wiki reference",
            500,
        )

    def test_plugin_readme_uses_summary_rules(self) -> None:
        assert self._get_ruleset("plugins/sanctum/README.md") == ("Plugin summary", 300)

    def test_plugin_nested_file_uses_default_rules(self) -> None:
        # Non-README files in plugins should use default (strict) rules
        assert self._get_ruleset("plugins/sanctum/docs/internal.md") == (
            "Default strict",
            500,
        )

    def test_unknown_directory_defaults_to_strict(self) -> None:
        assert self._get_ruleset("random/unknown/file.md") == ("Default strict", 500)

    def test_shell_audit_uses_the_same_limits_as_the_table(self) -> None:
        """The find/awk audit block enforces the limits the table documents."""
        text = _command("update-docs")
        assert (
            "find docs/ -name '*.md' -exec wc -l {} \\; 2>/dev/null | awk '$1 > 500'"
            in text
        )
        assert (
            "find book/ -name '*.md' -exec wc -l {} \\; 2>/dev/null | awk '$1 > 1000'"
            in text
        )
        assert '[ "$lines" -gt 300 ]' in text


class TestCreateTagConfigDriven:
    """Test that /create-tag uses config-driven post-tag submissions."""

    REQUIRED_SUBMISSION_KEYS = {"name", "script"}

    def _load_tag_submissions(self, repo_root: str) -> dict | None:
        """Load tag-submissions.json from repo root, or None if absent."""
        config_path = Path(repo_root) / "tag-submissions.json"
        if not config_path.exists():
            return None
        return json.loads(config_path.read_text())

    def _validate_submission_entry(self, entry: dict) -> list[str]:
        """Return list of validation errors for a submission entry."""
        errors = []
        missing = self.REQUIRED_SUBMISSION_KEYS - set(entry.keys())
        if missing:
            errors.append(f"Missing required keys: {missing}")
        if "script" in entry and not isinstance(entry["script"], str):
            errors.append("script must be a string path")
        return errors

    def test_tag_submissions_json_exists_in_repo(self) -> None:
        """Config file exists at repo root for this project."""
        repo_root = Path(__file__).resolve().parents[3]
        config = self._load_tag_submissions(str(repo_root))
        assert config is not None, "tag-submissions.json should exist in repo root"

    def test_tag_submissions_has_submissions_key(self) -> None:
        """Config must have a 'submissions' list."""
        repo_root = Path(__file__).resolve().parents[3]
        config = self._load_tag_submissions(str(repo_root))
        assert config is not None
        assert "submissions" in config
        assert isinstance(config["submissions"], list)
        assert len(config["submissions"]) > 0

    def test_each_submission_has_required_keys(self) -> None:
        """Each submission entry must have name and script."""
        repo_root = Path(__file__).resolve().parents[3]
        config = self._load_tag_submissions(str(repo_root))
        assert config is not None
        for entry in config["submissions"]:
            errors = self._validate_submission_entry(entry)
            assert not errors, f"Entry {entry.get('name', '?')}: {errors}"

    def test_submission_scripts_exist_on_disk(self) -> None:
        """Referenced scripts must exist in the repo."""
        repo_root = Path(__file__).resolve().parents[3]
        config = self._load_tag_submissions(str(repo_root))
        assert config is not None
        for entry in config["submissions"]:
            script_path = repo_root / entry["script"]
            assert script_path.exists(), f"Script not found: {entry['script']}"

    def test_create_tag_command_references_config(self) -> None:
        """The create-tag command must reference tag-submissions.json."""
        repo_root = Path(__file__).resolve().parents[3]
        cmd_path = repo_root / "plugins" / "sanctum" / "commands" / "create-tag.md"
        content = cmd_path.read_text()
        assert "tag-submissions.json" in content

    def test_missing_config_gracefully_skips(self, tmp_path: Path) -> None:
        """Without a config, the documented step reports the skip and exits 0.

        GIVEN a repository root with no tag-submissions.json
        WHEN the create-tag post-tag block runs there
        THEN it prints the skip notice, runs nothing, and succeeds
        """
        text = (PLUGIN_ROOT / "commands" / "create-tag.md").read_text()
        block = re.search(r"```bash\n(# Check for config\n.*?)```", text, re.DOTALL)
        assert block
        # The model fills the <version> placeholder before running the block.
        script = block.group(1).replace("<version>", "1.2.3")

        result = subprocess.run(
            ["bash", "-c", script],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert result.stdout == (
            "No tag-submissions.json found, skipping post-tag submissions\n"
        )
