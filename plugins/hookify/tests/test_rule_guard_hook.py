"""The rule_guard hook is what makes an installed rule do anything.

Before it existed, ``install_rule.py`` wrote ``.claude/hookify.*.local.md``
files that nothing read back, so a "block" rule blocked nothing. These
tests drive the hook the way Claude Code does: a JSON payload on stdin,
a decision on stdout.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
HOOK = PLUGIN_ROOT / "hooks" / "rule_guard.py"
HOOKS_JSON = PLUGIN_ROOT / "hooks" / "hooks.json"

BLOCK_RULE = """---
name: test-block-frobnicate
enabled: true
event: bash
pattern: frobnicate\\s+--hard
action: block
---

frobnicate --hard is forbidden in this project.
"""

WARN_FILE_RULE = """---
name: test-warn-zzquux
enabled: true
event: file
action: warn
conditions:
  - field: file_path
    operator: ends_with
    pattern: .zzquux
---

zzquux files are generated; edit the source instead.
"""

PROMPT_RULE = """---
name: test-prompt-xyzzy
enabled: true
event: prompt
pattern: xyzzy-magic-word
action: block
---

That word is reserved.
"""


def _run(payload: dict, project_dir: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )


def _install(project_dir: Path, name: str, body: str) -> None:
    rules_dir = project_dir / ".claude"
    rules_dir.mkdir(exist_ok=True)
    (rules_dir / f"hookify.{name}.local.md").write_text(body)


class TestRegistration:
    def test_hooks_json_registers_the_guard_for_the_rule_events(self) -> None:
        manifest = json.loads(HOOKS_JSON.read_text())["hooks"]
        for event in ("PreToolUse", "UserPromptSubmit", "Stop"):
            commands = [
                hook["command"] for entry in manifest[event] for hook in entry["hooks"]
            ]
            assert any("rule_guard.py" in cmd for cmd in commands), event

    def test_a_file_outside_tests_constructs_the_engine(self) -> None:
        """The README promises a runtime; this is the one that exists."""
        source = HOOK.read_text()
        assert "RuleEngine(" in source
        assert "ConfigLoader(" in source


class TestBashRules:
    def test_block_rule_denies_matching_bash_command(self, tmp_path: Path) -> None:
        _install(tmp_path, "test-block-frobnicate", BLOCK_RULE)
        result = _run(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "frobnicate --hard ./x"},
            },
            tmp_path,
        )
        assert result.returncode == 0, result.stderr
        decision = json.loads(result.stdout)["hookSpecificOutput"]
        assert decision["permissionDecision"] == "deny"
        assert "test-block-frobnicate" in decision["permissionDecisionReason"]
        assert "forbidden" in decision["permissionDecisionReason"]

    def test_non_matching_bash_command_passes_through(self, tmp_path: Path) -> None:
        _install(tmp_path, "test-block-frobnicate", BLOCK_RULE)
        result = _run(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "frobnicate --soft ./x"},
            },
            tmp_path,
        )
        assert result.returncode == 0, result.stderr
        assert "permissionDecision" not in result.stdout


class TestFileRules:
    def test_warn_rule_surfaces_message_without_denying(self, tmp_path: Path) -> None:
        _install(tmp_path, "test-warn-zzquux", WARN_FILE_RULE)
        result = _run(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Write",
                "tool_input": {"file_path": "out/report.zzquux", "content": "hi"},
            },
            tmp_path,
        )
        assert result.returncode == 0, result.stderr
        out = json.loads(result.stdout)
        assert "permissionDecision" not in json.dumps(out)
        assert "test-warn-zzquux" in out["systemMessage"]

    def test_edit_tool_maps_new_string_to_new_text(self, tmp_path: Path) -> None:
        _install(
            tmp_path,
            "test-edit-body",
            "---\nname: test-edit-body\nenabled: true\nevent: file\n"
            "action: block\nconditions:\n  - field: new_text\n"
            "    operator: contains\n    pattern: ZZTOKENZZ\n---\n\nNo.\n",
        )
        result = _run(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": "a.txt",
                    "old_string": "x",
                    "new_string": "ZZTOKENZZ",
                },
            },
            tmp_path,
        )
        decision = json.loads(result.stdout)["hookSpecificOutput"]
        assert decision["permissionDecision"] == "deny"


class TestPromptRules:
    def test_block_rule_blocks_prompt(self, tmp_path: Path) -> None:
        _install(tmp_path, "test-prompt-xyzzy", PROMPT_RULE)
        result = _run(
            {"hook_event_name": "UserPromptSubmit", "prompt": "say xyzzy-magic-word"},
            tmp_path,
        )
        assert result.returncode == 0, result.stderr
        out = json.loads(result.stdout)
        assert out["decision"] == "block"
        assert "reserved" in out["reason"]


class TestStopRules:
    def test_block_rule_reads_transcript_tail(self, tmp_path: Path) -> None:
        transcript = tmp_path / "t.jsonl"
        transcript.write_text('{"type":"assistant","text":"QQSTOPTOKENQQ"}\n')
        _install(
            tmp_path,
            "test-stop",
            "---\nname: test-stop\nenabled: true\nevent: stop\naction: block\n"
            "pattern: QQSTOPTOKENQQ\n---\n\nNot done yet.\n",
        )
        result = _run(
            {
                "hook_event_name": "Stop",
                "transcript_path": str(transcript),
                "stop_hook_active": False,
            },
            tmp_path,
        )
        out = json.loads(result.stdout)
        assert out["decision"] == "block"

    def test_stop_hook_active_never_blocks_again(self, tmp_path: Path) -> None:
        transcript = tmp_path / "t.jsonl"
        transcript.write_text("QQSTOPTOKENQQ\n")
        _install(
            tmp_path,
            "test-stop",
            "---\nname: test-stop\nenabled: true\nevent: stop\naction: block\n"
            "pattern: QQSTOPTOKENQQ\n---\n\nNot done yet.\n",
        )
        result = _run(
            {
                "hook_event_name": "Stop",
                "transcript_path": str(transcript),
                "stop_hook_active": True,
            },
            tmp_path,
        )
        assert "block" not in result.stdout


class TestResilience:
    def test_malformed_payload_passes_through_with_stderr_signal(
        self, tmp_path: Path
    ) -> None:
        env = dict(os.environ)
        env["CLAUDE_PROJECT_DIR"] = str(tmp_path)
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not json {{{",
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0
        assert json.loads(result.stdout) == {}
        assert "rule_guard" in result.stderr

    def test_unrelated_tool_passes_through(self, tmp_path: Path) -> None:
        result = _run(
            {"hook_event_name": "PreToolUse", "tool_name": "Read", "tool_input": {}},
            tmp_path,
        )
        assert result.returncode == 0
        assert json.loads(result.stdout) == {}

    @pytest.mark.skipif(
        not Path("/usr/bin/python3").exists(), reason="no system python"
    )
    def test_runs_under_system_python(self, tmp_path: Path) -> None:
        """Hooks run with whatever python3 the shell finds; here that is 3.9."""
        _install(tmp_path, "test-block-frobnicate", BLOCK_RULE)
        env = dict(os.environ)
        env["CLAUDE_PROJECT_DIR"] = str(tmp_path)
        result = subprocess.run(
            ["/usr/bin/python3", str(HOOK)],
            input=json.dumps(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"command": "frobnicate --hard"},
                }
            ),
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        if "No module named 'yaml'" in result.stderr:
            pytest.skip("system python lacks pyyaml; the hook reported it")
        assert "deny" in result.stdout


class TestWithoutPyYAML:
    """Hooks run under the operator's python3, which may lack PyYAML.

    The loader reads rule frontmatter with a stdlib parser there, so a
    block rule still blocks. Before that, a missing PyYAML let every
    event through with one stderr line.
    """

    @staticmethod
    def _run_without_pyyaml(
        payload: dict, project_dir: Path
    ) -> subprocess.CompletedProcess[str]:
        block = project_dir / "blocker"
        block.mkdir()
        (block / "sitecustomize.py").write_text(
            'import sys\n\nsys.modules["yaml"] = None\n'
        )
        env = dict(os.environ)
        env["CLAUDE_PROJECT_DIR"] = str(project_dir)
        env["PYTHONPATH"] = str(block)
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
            check=False,
        )

    def test_non_matching_prompt_passes_without_pyyaml_or_a_traceback(
        self, tmp_path: Path
    ) -> None:
        """GIVEN an interpreter that cannot import PyYAML.

        WHEN a prompt no rule matches reaches the guard
        THEN the event passes and no traceback reaches stderr
        """
        result = self._run_without_pyyaml(
            {"hook_event_name": "UserPromptSubmit", "prompt": "hello there"},
            tmp_path,
        )

        assert result.returncode == 0, result.stderr
        assert "Traceback" not in result.stderr
        assert json.loads(result.stdout) == {}

    def test_block_rule_denies_force_push_without_pyyaml(self, tmp_path: Path) -> None:
        """GIVEN block-force-push installed and an interpreter without PyYAML.

        WHEN the session runs ``git push --force origin master``
        THEN the guard denies it

        Letting the event through with only a stderr line is a fail-open
        guard: the push ran and nothing in the session said why.
        """
        catalog_rule = (
            PLUGIN_ROOT
            / "skills"
            / "rule-catalog"
            / "rules"
            / "git"
            / "block-force-push.md"
        )
        _install(tmp_path, "block-force-push", catalog_rule.read_text())

        result = self._run_without_pyyaml(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "git push --force origin master"},
            },
            tmp_path,
        )

        assert result.returncode == 0, result.stderr
        decision = json.loads(result.stdout)["hookSpecificOutput"]
        assert decision["permissionDecision"] == "deny"

    def test_double_quoted_user_rule_still_denies_without_pyyaml(
        self, tmp_path: Path
    ) -> None:
        """GIVEN a hand-written block rule that double-quotes its pattern.

        WHEN the guard runs without PyYAML and the pattern matches
        THEN it denies, as it would with PyYAML
        """
        _install(
            tmp_path,
            "quoted-detonate",
            "---\n"
            "name: quoted-detonate\n"
            "enabled: true\n"
            "event: bash\n"
            "action: block\n"
            'pattern: "xyzzy\\\\s+detonate"\n'
            "---\n\nNo.\n",
        )

        result = self._run_without_pyyaml(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "echo xyzzy detonate"},
            },
            tmp_path,
        )

        assert result.returncode == 0, result.stderr
        decision = json.loads(result.stdout)["hookSpecificOutput"]
        assert decision["permissionDecision"] == "deny"

    def test_unreadable_user_rule_is_reported_not_dropped(self, tmp_path: Path) -> None:
        """GIVEN a user rule the loader cannot read (a block scalar).

        WHEN any event reaches the guard
        THEN the output names the skipped rule in a systemMessage

        A skipped block rule is a guard that stopped guarding. A log line
        on an exit-0 hook reaches nobody.
        """
        _install(
            tmp_path,
            "folded",
            "---\nname: folded\nenabled: true\nevent: bash\n"
            "action: block\npattern: |\n  rm -rf\n---\n\nNo.\n",
        )

        result = self._run_without_pyyaml(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "ls"},
            },
            tmp_path,
        )

        assert result.returncode == 0, result.stderr
        message = json.loads(result.stdout).get("systemMessage", "")
        assert "hookify.folded.local.md" in message

    def test_rules_still_run_when_pyyaml_is_available(self, tmp_path: Path) -> None:
        """GIVEN the ordinary interpreter with the dependency present.

        WHEN a blocking rule matches the prompt
        THEN the guard still denies, so the fallback changed nothing
        """
        _install(tmp_path, "test-prompt-xyzzy", PROMPT_RULE)

        result = _run(
            {"hook_event_name": "UserPromptSubmit", "prompt": "say xyzzy-magic-word"},
            tmp_path,
        )

        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["decision"] == "block"
