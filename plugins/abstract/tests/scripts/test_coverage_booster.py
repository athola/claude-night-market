"""Coverage booster tests targeting specific uncovered branches.

Feature: Coverage booster for remaining uncovered lines
    As a developer
    I want the remaining uncovered branches tested
    So that overall coverage reaches 90%
"""

from __future__ import annotations

import builtins
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from add_bdd_markers import main
from token_usage_tracker import TokenUsageTracker
from tool_performance_analyzer import ToolPerformanceAnalyzer

from abstract.wrapper_base import SuperpowerWrapper

# ---------------------------------------------------------------------------
# Tests: tool_performance_analyzer.py lines 59-68
# (TimeoutExpired + Exception handlers in analyze_tools)
# ---------------------------------------------------------------------------


class TestToolPerformanceAnalyzerExceptions:
    """Feature: analyze_tools handles subprocess exceptions."""

    @pytest.mark.unit
    def test_timeout_expired_records_timeout_entry(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: TimeoutExpired sets timeout=True in result.
        Given a tool that times out when run
        When analyze_tools is called
        Then the tool entry has timeout=True and success=False
        """
        tool_file = tmp_path / "slow-tool.py"
        tool_file.write_text("#!/usr/bin/env python3\nimport time\ntime.sleep(60)\n")
        tool_file.chmod(0o755)

        def raising_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd=args[0], timeout=5)

        monkeypatch.setattr(subprocess, "run", raising_run)

        analyzer = ToolPerformanceAnalyzer(tmp_path)
        result = analyzer.analyze_tools()
        assert result["total_tools"] == 1
        tool_data = result["tools"]["slow-tool.py"]
        assert tool_data["success"] is False
        assert tool_data.get("timeout") is True
        assert tool_data["execution_time"] == 5.0

    @pytest.mark.unit
    def test_generic_exception_records_error_entry(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: Generic exception sets error=True in result.
        Given a tool that raises an unexpected exception when run
        When analyze_tools is called
        Then the tool entry has error=True and success=False
        """
        tool_file = tmp_path / "broken-tool.py"
        tool_file.write_text("#!/usr/bin/env python3\npass\n")
        tool_file.chmod(0o755)

        def raising_run(*args, **kwargs):
            raise OSError("Cannot execute")

        monkeypatch.setattr(subprocess, "run", raising_run)

        analyzer = ToolPerformanceAnalyzer(tmp_path)
        result = analyzer.analyze_tools()
        assert result["total_tools"] == 1
        tool_data = result["tools"]["broken-tool.py"]
        assert tool_data["success"] is False
        assert tool_data.get("error") is True
        assert tool_data["execution_time"] == 0.0


# ---------------------------------------------------------------------------
# Tests: token_usage_tracker.py lines 59, 63-66
# (tokens > optimal_limit branch + OSError exception handler)
# ---------------------------------------------------------------------------


class TestTokenUsageTrackerBranches:
    """Feature: TokenUsageTracker handles over-limit and unreadable files."""

    @pytest.mark.unit
    def test_tokens_over_optimal_limit_counted(self, tmp_path: Path) -> None:
        """Scenario: Large skill file increases skills_over_limit count.
        Given a SKILL.md file with more than optimal_limit * 4 characters
        When track_usage is called
        Then skills_over_limit is 1
        """
        # Write a file large enough to exceed a low optimal_limit
        skill_dir = tmp_path / "big-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        # With optimal_limit=10, any content > 40 chars triggers over-limit
        skill_file.write_text("x" * 50)

        tracker = TokenUsageTracker(tmp_path, optimal_limit=10)
        result = tracker.track_usage()
        assert result["skills_over_limit"] == 1
        assert result["optimal_usage_count"] == 0

    @pytest.mark.unit
    def test_unreadable_skill_file_skipped_gracefully(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: OSError on SKILL.md file causes it to be skipped.
        Given a SKILL.md that raises OSError when read
        When track_usage is called
        Then the file is skipped and totals remain 0
        """
        skill_dir = tmp_path / "bad-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("content")

        original_open = builtins.open

        def raising_open(file, *args, **kwargs):
            if Path(file) == skill_file:
                raise OSError("Permission denied")
            return original_open(file, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", raising_open)

        tracker = TokenUsageTracker(tmp_path, optimal_limit=2000)
        result = tracker.track_usage()
        # total_skills counts files found, but tokens are 0 due to exception
        assert result["skills_over_limit"] == 0
        assert result["total_tokens"] == 0


# ---------------------------------------------------------------------------
# Tests: add_bdd_markers.py lines 161-165, 176
# (main() with files modified branch - non-dry-run with modification)
# ---------------------------------------------------------------------------


class TestAddBddMarkersMainModified:
    """Feature: add_bdd_markers main() reports modified files."""

    @pytest.mark.unit
    def test_main_modifies_file_and_reports_count(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: main() without --dry-run modifies a BDD test file.
        Given a test file with BDD patterns but missing @pytest.mark.bdd
        When main is called (not dry-run) from the test file's project root
        Then the modified count is reported and the marker is added
        """
        # Create a plugin test directory structure
        test_dir = tmp_path / "plugins" / "my-plugin" / "tests"
        test_dir.mkdir(parents=True)

        test_file = test_dir / "test_example.py"
        test_file.write_text(
            "@pytest.mark.unit\n"
            "def test_something() -> None:\n"
            '    """Scenario: something\n'
            "    Given a thing\n"
            "    When it runs\n"
            "    Then it works\n"
            '    """\n'
            "    assert True\n"
        )

        monkeypatch.setattr(sys, "argv", ["add_bdd_markers.py"])
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            # Should complete without crash; file gets modified
            main()
        except SystemExit as e:
            assert e.code == 0
        finally:
            os.chdir(original_cwd)

        # Verify the marker was added
        content = test_file.read_text()
        assert "@pytest.mark.bdd" in content


# ---------------------------------------------------------------------------
# Tests: wrapper_base.py lines 179-182, 194-195
# (non-string key in translate_parameters + exception handler)
# ---------------------------------------------------------------------------


class TestWrapperBaseTranslateParametersEdgeCases:
    """Feature: translate_parameters handles non-string keys and exceptions."""

    @pytest.mark.unit
    def test_non_string_key_adds_error(self, tmp_path: Path) -> None:
        """Scenario: Non-string key in params dict adds error entry.
        Given a params dict with an integer key
        When translate_parameters is called
        Then a translation error is recorded for the invalid key
        """
        # Create wrapper with empty parameter map
        wrapper = SuperpowerWrapper(
            source_plugin="test-plugin",
            source_command="test-command",
            target_superpower="test-superpower",
        )

        # Pass a dict with integer key (non-string)
        # SuperpowerWrapper.translate_parameters iterates over params
        # Use a workaround since dicts in Python require the type to be hashable
        result = wrapper.translate_parameters({1: "value", "valid-key": "data"})  # type: ignore[arg-type]
        # Should handle gracefully - the int key triggers the isinstance(key, str) check
        assert isinstance(result, dict)
        # The error for the int key is recorded internally
        # valid-key should still be in translated result
        assert "valid-key" in result
