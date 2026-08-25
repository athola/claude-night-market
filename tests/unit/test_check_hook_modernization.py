# ruff: noqa: D101,D102,D103,D205,D212,PLR2004,E501,E402,I001
"""Tests for hook modernization checker.

Validates detection of outdated hook patterns against
the Claude Code SDK specification.
"""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from check_hook_modernization import (
    AuditResult,
    Finding,
    check_hooks_json_config,
    check_python_source,
    format_json,
    format_text,
    get_hook_event_types,
    main,
    run_audit,
)


# ============================================================================
# check_python_source: PostToolUse invalid decisions
# ============================================================================


class TestPostToolUseInvalidDecision:
    """Feature: Detect invalid decision values in PostToolUse hooks."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_allow_decision(self) -> None:
        """
        Given a PostToolUse hook returning {"decision": "ALLOW"},
        When the source is checked,
        Then it should report an error for invalid decision value.
        """
        source = textwrap.dedent("""
            import json, sys
            def main():
                try:
                    data = json.load(sys.stdin)
                except json.JSONDecodeError:
                    pass
                print(json.dumps({"decision": "ALLOW"}))
        """)
        findings = check_python_source(
            source, "test-plugin", "hook.py", ["PostToolUse"]
        )
        errors = [f for f in findings if f.pattern == "invalid-post-decision"]
        assert len(errors) == 1
        assert errors[0].severity == "error"
        assert "ALLOW" in errors[0].message

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_approve_decision(self) -> None:
        """
        Given a PostToolUse hook returning {"decision": "approve"},
        When the source is checked,
        Then it should report an error.
        """
        source = 'print(json.dumps({"decision": "approve"}))'
        findings = check_python_source(source, "test", "hook.py", ["PostToolUse"])
        errors = [f for f in findings if f.pattern == "invalid-post-decision"]
        assert len(errors) >= 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_block_decision(self) -> None:
        """
        Given a PostToolUse hook returning {"decision": "block"},
        When the source is checked,
        Then it should NOT report an invalid decision error.
        """
        source = textwrap.dedent("""
            import json, sys
            def main():
                try:
                    data = json.load(sys.stdin)
                except json.JSONDecodeError:
                    pass
                print(json.dumps({"decision": "block"}))
        """)
        findings = check_python_source(source, "test", "hook.py", ["PostToolUse"])
        errors = [f for f in findings if f.pattern == "invalid-post-decision"]
        assert len(errors) == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_empty_response(self) -> None:
        """
        Given a PostToolUse hook returning {},
        When the source is checked,
        Then it should NOT report a decision error.
        """
        source = textwrap.dedent("""
            import json, sys
            def main():
                try:
                    data = json.load(sys.stdin)
                except json.JSONDecodeError:
                    pass
                print(json.dumps({}))
        """)
        findings = check_python_source(source, "test", "hook.py", ["PostToolUse"])
        errors = [f for f in findings if f.pattern == "invalid-post-decision"]
        assert len(errors) == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skips_non_post_tool_use(self) -> None:
        """
        Given a PreToolUse hook returning {"decision": "ALLOW"},
        When the source is checked with event_types=["PreToolUse"],
        Then it should NOT report a PostToolUse decision error.
        """
        source = 'print(json.dumps({"decision": "ALLOW"}))'
        findings = check_python_source(source, "test", "hook.py", ["PreToolUse"])
        errors = [f for f in findings if f.pattern == "invalid-post-decision"]
        assert len(errors) == 0


# ============================================================================
# check_python_source: PreToolUse output forms
# ============================================================================


class TestPreToolUseOutputForms:
    """Feature: Both legacy and hookSpecificOutput PreToolUse forms are valid.

    The Claude Code SDK supports two output schemas for PreToolUse hooks:
    - Legacy: {"decision": "block"|"approve", "reason": "..."}
    - Modern: {"hookSpecificOutput": {"hookEventName": "PreToolUse",
              "permissionDecision": "allow"|"deny"|"ask",
              "permissionDecisionReason": "..."}}

    Neither form is deprecated. The scanner must not flag either.
    See issue #517 for the diagnosis history.
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_legacy_decision_reason_form_is_not_flagged(self) -> None:
        """
        Given a PreToolUse hook using top-level {"decision", "reason"},
        When the source is checked,
        Then it should NOT warn about a deprecated form.
        """
        source = textwrap.dedent("""
            import json, sys
            def main():
                try:
                    data = json.load(sys.stdin)
                except json.JSONDecodeError:
                    pass
                result = {"decision": "block", "reason": "blocked"}
                print(json.dumps(result))
        """)
        findings = check_python_source(source, "test", "hook.py", ["PreToolUse"])
        deprecated = [f for f in findings if f.pattern == "deprecated-pre-decision"]
        assert deprecated == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_hookSpecificOutput_form_is_not_flagged(self) -> None:
        """
        Given a PreToolUse hook using hookSpecificOutput.permissionDecision,
        When the source is checked,
        Then it should NOT warn about deprecated fields.
        """
        source = textwrap.dedent("""
            import json, sys
            def main():
                try:
                    data = json.load(sys.stdin)
                except json.JSONDecodeError:
                    pass
                result = {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "allow",
                    }
                }
                print(json.dumps(result))
        """)
        findings = check_python_source(source, "test", "hook.py", ["PreToolUse"])
        deprecated = [f for f in findings if f.pattern == "deprecated-pre-decision"]
        assert deprecated == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_additionalContext_form_is_not_flagged(self) -> None:
        """
        Given a PreToolUse hook using {"additionalContext": "..."},
        When the source is checked,
        Then it should NOT warn (this is the shadow-mode advisory form).
        """
        source = textwrap.dedent("""
            import json, sys
            def main():
                try:
                    data = json.load(sys.stdin)
                except json.JSONDecodeError:
                    pass
                result = {"additionalContext": "advisory"}
                print(json.dumps(result))
        """)
        findings = check_python_source(source, "test", "hook.py", ["PreToolUse"])
        deprecated = [f for f in findings if f.pattern == "deprecated-pre-decision"]
        assert deprecated == []


# ============================================================================
# check_python_source: missing error handling
# ============================================================================


class TestMissingErrorHandling:
    """Feature: Detect hooks that read stdin without error handling."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_missing_try_except(self) -> None:
        """
        Given a hook that reads sys.stdin without try/except,
        When the source is checked,
        Then it should warn about missing error handling.
        """
        source = textwrap.dedent("""
            import json, sys
            def main():
                data = json.load(sys.stdin)
                print(json.dumps({}))
        """)
        findings = check_python_source(source, "test", "hook.py", ["PostToolUse"])
        missing = [f for f in findings if f.pattern == "missing-stdin-error-handling"]
        assert len(missing) == 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_proper_error_handling(self) -> None:
        """
        Given a hook with try/except JSONDecodeError,
        When the source is checked,
        Then it should NOT warn.
        """
        source = textwrap.dedent("""
            import json, sys
            def main():
                try:
                    data = json.load(sys.stdin)
                except json.JSONDecodeError:
                    data = {}
                print(json.dumps({}))
        """)
        findings = check_python_source(source, "test", "hook.py", ["PostToolUse"])
        missing = [f for f in findings if f.pattern == "missing-stdin-error-handling"]
        assert len(missing) == 0


# ============================================================================
# get_hook_event_types
# ============================================================================


class TestGetHookEventTypes:
    """Feature: Parse hooks.json to map scripts to event types."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_maps_scripts_to_events(self, tmp_path) -> None:
        """
        Given a hooks.json with PostToolUse and PreToolUse entries,
        When parsed,
        Then each script should map to its event types.
        """
        hooks_json = tmp_path / "hooks.json"
        hooks_json.write_text(
            json.dumps(
                {
                    "hooks": {
                        "PostToolUse": [
                            {
                                "matcher": "Bash",
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "python3 ${PLUGIN}/hooks/sanitize.py",
                                    }
                                ],
                            }
                        ],
                        "PreToolUse": [
                            {
                                "matcher": "Write",
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "python3 ${PLUGIN}/hooks/guard.py",
                                    }
                                ],
                            }
                        ],
                    }
                }
            )
        )
        result = get_hook_event_types(hooks_json)
        assert "sanitize.py" in result
        assert "PostToolUse" in result["sanitize.py"]
        assert "guard.py" in result
        assert "PreToolUse" in result["guard.py"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_missing_file(self, tmp_path) -> None:
        """
        Given a nonexistent hooks.json path,
        When parsed,
        Then it should return an empty dict.
        """
        result = get_hook_event_types(tmp_path / "nope.json")
        assert result == {}


# ============================================================================
# run_audit: integration with filesystem
# ============================================================================


class TestRunAudit:
    """Feature: Full audit across a mock plugin tree."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_finds_issues_in_mock_plugin(self, tmp_path) -> None:
        """
        Given a plugin with a PostToolUse hook using "ALLOW",
        When run_audit scans the tree,
        Then it should find the invalid decision error.
        """
        # Set up mock plugin structure
        plugin = tmp_path / "plugins" / "bad-plugin" / "hooks"
        plugin.mkdir(parents=True)

        hooks_json = plugin / "hooks.json"
        hooks_json.write_text(
            json.dumps(
                {
                    "hooks": {
                        "PostToolUse": [
                            {
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "python3 hooks/bad_hook.py",
                                    }
                                ],
                            }
                        ],
                    }
                }
            )
        )

        bad_hook = plugin / "bad_hook.py"
        bad_hook.write_text(
            textwrap.dedent("""
            import json, sys
            def main():
                data = json.load(sys.stdin)
                print(json.dumps({"decision": "ALLOW"}))
        """)
        )

        result = run_audit(tmp_path)
        assert result.error_count >= 1
        patterns = [f.pattern for f in result.findings]
        assert "invalid-post-decision" in patterns

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_clean_plugin_has_no_errors(self, tmp_path) -> None:
        """
        Given a plugin with properly formatted hooks,
        When run_audit scans the tree,
        Then it should find zero errors.
        """
        plugin = tmp_path / "plugins" / "good-plugin" / "hooks"
        plugin.mkdir(parents=True)

        hooks_json = plugin / "hooks.json"
        hooks_json.write_text(
            json.dumps(
                {
                    "hooks": {
                        "PostToolUse": [
                            {
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "python3 hooks/good_hook.py",
                                    }
                                ],
                            }
                        ],
                    }
                }
            )
        )

        good_hook = plugin / "good_hook.py"
        good_hook.write_text(
            textwrap.dedent("""
            import json, sys
            def main():
                try:
                    data = json.load(sys.stdin)
                except json.JSONDecodeError:
                    return
                print(json.dumps({}))
        """)
        )

        result = run_audit(tmp_path)
        assert result.error_count == 0


# ============================================================================
# Output formatting
# ============================================================================


class TestOutputFormatting:
    """Feature: Format findings as text or JSON."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_text_format_no_findings(self) -> None:
        """Given no findings, text output says no issues."""
        result = AuditResult(findings=[])
        text = format_text(result)
        assert "No modernization issues" in text

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_text_format_with_findings(self) -> None:
        """Given findings, text output includes severity and count."""
        result = AuditResult(
            findings=[
                Finding("p", "f.py", "test", "error", "bad thing"),
            ]
        )
        text = format_text(result)
        assert "ERROR" in text
        assert "1 errors" in text

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_json_format(self) -> None:
        """Given findings, JSON output is parseable with correct structure."""
        result = AuditResult(
            findings=[
                Finding("p", "f.py", "test", "warning", "minor issue"),
            ]
        )
        parsed = json.loads(format_json(result))
        assert parsed["success"] is True
        assert parsed["warnings"] == 1
        assert len(parsed["findings"]) == 1
        assert parsed["findings"][0]["plugin"] == "p"


# ============================================================================
# main() CLI
# ============================================================================


class TestMainCLI:
    """Feature: CLI entry point handles arguments correctly."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_json_flag_returns_0(self, tmp_path) -> None:
        """
        Given --json flag,
        When main() runs (even with errors),
        Then it should return 0 (JSON mode never fails).
        """
        # Empty tree = no findings
        (tmp_path / "plugins").mkdir()
        code = main(["--json", "--root", str(tmp_path)])
        assert code == 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_text_mode_returns_1_on_errors(self, tmp_path) -> None:
        """
        Given a plugin with errors,
        When main() runs in text mode,
        Then it should return 1.
        """
        plugin = tmp_path / "plugins" / "bad" / "hooks"
        plugin.mkdir(parents=True)
        (plugin / "hooks.json").write_text(
            json.dumps(
                {
                    "hooks": {
                        "PostToolUse": [
                            {
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "hooks/h.py",
                                    }
                                ],
                            }
                        ],
                    }
                }
            )
        )
        (plugin / "h.py").write_text(
            'import json\nprint(json.dumps({"decision": "ALLOW"}))'
        )

        code = main(["--root", str(tmp_path)])
        assert code == 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_text_mode_returns_0_when_clean(self, tmp_path) -> None:
        """
        Given a clean tree,
        When main() runs,
        Then it should return 0.
        """
        (tmp_path / "plugins").mkdir()
        code = main(["--root", str(tmp_path)])
        assert code == 0


# ============================================================================
# Silent-drop surfacing (issue #575, B1)
# ============================================================================


class TestSilentDropSurfacing:
    """Feature: 'could not check' must not become 'checked, fine'.

    Three swallow points used to convert an unverifiable file into a
    silent pass inside a CI gate: a malformed hooks.json, a Python
    source that fails to parse, and an unreadable hook file. Each must
    now surface an error Finding so the exit-1 path catches it.
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_syntax_error_source_emits_error_finding(self) -> None:
        """
        Given a PostToolUse hook whose source does not parse,
        When the source is checked,
        Then an error Finding is emitted (not a silent return).
        """
        source = "def (oops this is not python:\n    print('x')\n"
        findings = check_python_source(source, "test", "hook.py", ["PostToolUse"])
        errors = [f for f in findings if f.severity == "error"]
        assert len(errors) >= 1
        assert any("pars" in f.message.lower() for f in errors)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_malformed_hooks_json_emits_error_finding(self, tmp_path) -> None:
        """
        Given a plugin whose hooks.json is not valid JSON,
        When run_audit scans the tree,
        Then an error Finding is emitted rather than skipping checks.
        """
        plugin = tmp_path / "plugins" / "broken" / "hooks"
        plugin.mkdir(parents=True)
        (plugin / "hooks.json").write_text("{ this is not json ]")
        (plugin / "hook.py").write_text("import json\nprint('{}')\n")

        result = run_audit(tmp_path)
        assert result.error_count >= 1
        assert any("hooks.json" in f.file for f in result.findings)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_malformed_hooks_json_makes_main_return_1(self, tmp_path) -> None:
        """
        Given a malformed hooks.json,
        When main() runs in text mode,
        Then it returns 1 (the CI gate fails, not silently passes).
        """
        plugin = tmp_path / "plugins" / "broken" / "hooks"
        plugin.mkdir(parents=True)
        (plugin / "hooks.json").write_text("{ nope")
        (plugin / "hook.py").write_text("import json\nprint('{}')\n")

        code = main(["--root", str(tmp_path)])
        assert code == 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_unreadable_source_emits_error_finding(self, tmp_path) -> None:
        """
        Given a hook path that cannot be read (a directory named *.py),
        When run_audit scans the tree,
        Then an error Finding is emitted rather than a silent continue.
        """
        plugin = tmp_path / "plugins" / "weird" / "hooks"
        plugin.mkdir(parents=True)
        (plugin / "hooks.json").write_text(
            json.dumps(
                {
                    "hooks": {
                        "PostToolUse": [
                            {
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "hooks/unreadable.py",
                                    }
                                ],
                            }
                        ],
                    }
                }
            )
        )
        # A directory whose name ends in .py: glob matches it, but
        # read_text() raises IsADirectoryError (an OSError subclass).
        (plugin / "unreadable.py").mkdir()

        result = run_audit(tmp_path)
        assert result.error_count >= 1
        assert any("unreadable.py" in f.file for f in result.findings)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_get_hook_event_types_propagates_malformed_json(self, tmp_path) -> None:
        """
        Given a malformed hooks.json,
        When get_hook_event_types parses it,
        Then it raises (malformed != empty) rather than returning {}.
        """
        bad = tmp_path / "hooks.json"
        bad.write_text("{ not json")
        with pytest.raises(json.JSONDecodeError):
            get_hook_event_types(bad)


# ============================================================================
# check_hooks_json_config: `if` placement (measured on CLI 2.1.245)
# ============================================================================


class TestMisplacedIfCondition:
    """Feature: Detect an `if` condition the harness will silently ignore.

    Measured on CLI 2.1.245: an `if` key on the matcher-group object is
    dropped, so the hook fires on every matching tool call. The same key
    inside the hook entry suppresses the spawn. A misplaced key produces
    a config that reads as gated and behaves as ungated, with no error.
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_flags_if_on_matcher_group(self):
        config = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "if": "Bash(git commit*)",
                        "hooks": [{"type": "command", "command": "gate.py"}],
                    }
                ]
            }
        }
        findings = check_hooks_json_config(config, "gauntlet")
        assert [f.pattern for f in findings] == ["misplaced-if-condition"]
        assert findings[0].severity == "error"
        assert "hook entry" in findings[0].message

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_accepts_if_inside_hook_entry(self):
        config = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "gate.py",
                                "if": "Bash(git commit*)",
                            }
                        ],
                    }
                ]
            }
        }
        assert check_hooks_json_config(config, "gauntlet") == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_accepts_group_with_no_if(self):
        config = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [{"type": "command", "command": "x.py"}],
                    }
                ]
            }
        }
        assert check_hooks_json_config(config, "pensive") == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reports_every_misplaced_group(self):
        group = {
            "matcher": "Bash",
            "if": "Bash(git commit*)",
            "hooks": [{"type": "command", "command": "x.py"}],
        }
        config = {"hooks": {"PreToolUse": [dict(group)], "PostToolUse": [dict(group)]}}
        findings = check_hooks_json_config(config, "gauntlet")
        assert len(findings) == 2
        assert {f.file for f in findings} == {"hooks.json"}


class TestShippedHooksJsonPlacement:
    """Feature: no shipped hooks.json carries a silently-ignored `if`."""

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_no_plugin_ships_a_misplaced_if(self):
        repo_root = Path(__file__).resolve().parents[2]
        offenders = []
        for hooks_json in sorted(repo_root.glob("plugins/*/hooks/hooks.json")):
            config = json.loads(hooks_json.read_text())
            plugin = hooks_json.parts[-3]
            offenders.extend(
                f"{plugin}: {f.message}"
                for f in check_hooks_json_config(config, plugin)
            )
        assert offenders == []


class TestNonStringIfCondition:
    """Feature: an array-valued `if` is a silent kill switch.

    Measured on CLI 2.1.245: an entry whose `if` is a list is never
    spawned, even when one element of the list matches the command.
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_flags_array_valued_if(self):
        config = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "gate.py",
                                "if": ["Bash(git commit*)", "Bash(pip install*)"],
                            }
                        ],
                    }
                ]
            }
        }
        findings = check_hooks_json_config(config, "imbue")
        assert [f.pattern for f in findings] == ["non-string-if-condition"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_accepts_string_if(self):
        config = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "gate.py",
                                "if": "Bash(git commit*)",
                            }
                        ],
                    }
                ]
            }
        }
        assert check_hooks_json_config(config, "imbue") == []
