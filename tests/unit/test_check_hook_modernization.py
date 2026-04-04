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
    check_python_source,
    format_json,
    format_text,
    get_hook_event_types,
    main,
    run_audit,
)


# ============================================================================
# check_python_source — PostToolUse invalid decisions
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
# check_python_source — PreToolUse deprecated fields
# ============================================================================


class TestPreToolUseDeprecatedFields:
    """Feature: Detect deprecated decision/reason in PreToolUse hooks."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_deprecated_decision_field(self) -> None:
        """
        Given a PreToolUse hook using top-level "decision" field,
        When the source is checked,
        Then it should warn about deprecated usage.
        """
        source = textwrap.dedent("""
            import json, sys
            def main():
                try:
                    data = json.load(sys.stdin)
                except json.JSONDecodeError:
                    pass
                result = {"decision": "approve", "reason": "safe file"}
                print(json.dumps(result))
        """)
        findings = check_python_source(source, "test", "hook.py", ["PreToolUse"])
        deprecated = [f for f in findings if f.pattern == "deprecated-pre-decision"]
        assert len(deprecated) >= 1

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_allows_hookSpecificOutput_usage(self) -> None:
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
                        "permissionDecision": "allow",
                    }
                }
                print(json.dumps(result))
        """)
        findings = check_python_source(source, "test", "hook.py", ["PreToolUse"])
        deprecated = [f for f in findings if f.pattern == "deprecated-pre-decision"]
        assert len(deprecated) == 0


# ============================================================================
# check_python_source — missing error handling
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
# run_audit — integration with filesystem
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
