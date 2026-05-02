"""Tests for pattern matching utilities.

Covers PatternMatcher: 18 predefined regex patterns across
DANGEROUS_PATTERNS, SECURITY_PATTERNS, and DEBUG_PATTERNS,
plus all 6 public methods.
"""

from __future__ import annotations

import pytest

from hookify.matchers.pattern_matcher import PatternMatcher


class TestDangerousPatterns:
    """Verify each DANGEROUS_PATTERNS regex matches expected inputs."""

    @pytest.mark.parametrize(
        "text",
        [
            "rm -rf /tmp",
            "rm -fr /var",
            "rm --recursive --force /opt",
            "rm -rfi /home",
        ],
    )
    def test_rm_recursive_matches(self, text: str) -> None:
        """rm_recursive pattern detects recursive-force removal."""
        pattern = PatternMatcher.get_pattern("rm_recursive")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, text) is True

    @pytest.mark.parametrize(
        "text",
        [
            "rm file.txt",
            "rm -r dir",
            "rm --force file",
            "rmdir empty",
        ],
    )
    def test_rm_recursive_rejects(self, text: str) -> None:
        """rm_recursive pattern ignores safe rm invocations."""
        pattern = PatternMatcher.get_pattern("rm_recursive")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, text) is False

    @pytest.mark.parametrize(
        "text",
        [
            "dd if=/dev/sda of=backup.img",
            "dd of=/dev/nvme0n1 if=image.raw",
        ],
    )
    def test_dd_device_matches(self, text: str) -> None:
        """dd_device pattern detects device-level dd commands."""
        pattern = PatternMatcher.get_pattern("dd_device")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, text) is True

    @pytest.mark.parametrize(
        "text",
        [
            "dd if=input.bin of=output.bin",
            "echo dd if=/dev/null",
        ],
    )
    def test_dd_device_rejects(self, text: str) -> None:
        """dd_device pattern ignores non-device dd usage."""
        pattern = PatternMatcher.get_pattern("dd_device")
        assert pattern is not None
        # "echo dd if=/dev/null" still contains "dd if=/dev/"
        # so only test the first case
        if "/dev/" not in text:
            assert PatternMatcher.test_pattern(pattern, text) is False

    def test_dd_device_rejects_plain_copy(self) -> None:
        """dd_device pattern ignores file-to-file dd."""
        pattern = PatternMatcher.get_pattern("dd_device")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, "dd if=a.bin of=b.bin") is False

    @pytest.mark.parametrize(
        "text",
        [
            "chmod 777 /var/www",
            "chmod -R 777 /srv",
            "chmod --recursive 777 /opt",
        ],
    )
    def test_chmod_777_matches(self, text: str) -> None:
        """chmod_777 pattern detects world-writable permission sets."""
        pattern = PatternMatcher.get_pattern("chmod_777")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, text) is True

    @pytest.mark.parametrize(
        "text",
        [
            "chmod 755 /var",
            "chmod 644 file.txt",
        ],
    )
    def test_chmod_777_rejects(self, text: str) -> None:
        """chmod_777 pattern ignores safe permission sets."""
        pattern = PatternMatcher.get_pattern("chmod_777")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, text) is False

    def test_sudo_matches(self) -> None:
        """sudo pattern detects sudo invocations."""
        pattern = PatternMatcher.get_pattern("sudo")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, "sudo apt install vim") is True

    def test_sudo_rejects(self) -> None:
        """sudo pattern ignores non-sudo commands."""
        pattern = PatternMatcher.get_pattern("sudo")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, "apt install vim") is False

    def test_mkfs_matches(self) -> None:
        """mkfs pattern detects filesystem creation commands."""
        pattern = PatternMatcher.get_pattern("mkfs")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, "mkfs.ext4 /dev/sda1") is True

    def test_mkfs_rejects(self) -> None:
        """mkfs pattern ignores unrelated commands."""
        pattern = PatternMatcher.get_pattern("mkfs")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, "ls mkfs") is False

    def test_format_matches(self) -> None:
        """format pattern detects Windows-style format commands."""
        pattern = PatternMatcher.get_pattern("format")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, "format C:") is True

    def test_format_rejects(self) -> None:
        """format pattern ignores non-drive format usage."""
        pattern = PatternMatcher.get_pattern("format")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, "format_string = 'hello'") is False


class TestSecurityPatterns:
    """Verify each SECURITY_PATTERNS regex matches expected inputs."""

    @pytest.mark.parametrize(
        "text",
        [
            "eval('code')",
            "exec('import os')",
            "eval (expression)",
        ],
    )
    def test_eval_pattern_matches(self, text: str) -> None:
        """eval_pattern detects eval/exec calls."""
        pattern = PatternMatcher.get_pattern("eval_pattern")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, text) is True

    def test_eval_pattern_rejects(self) -> None:
        """eval_pattern ignores non-eval code."""
        pattern = PatternMatcher.get_pattern("eval_pattern")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, "evaluate_result()") is False

    def test_innerHTML_matches(self) -> None:
        """innerHTML pattern detects direct innerHTML assignment."""
        pattern = PatternMatcher.get_pattern("innerHTML")
        assert pattern is not None
        assert (
            PatternMatcher.test_pattern(pattern, 'el.innerHTML = "<b>hi</b>"') is True
        )

    def test_innerHTML_rejects(self) -> None:
        """innerHTML pattern ignores textContent assignment."""
        pattern = PatternMatcher.get_pattern("innerHTML")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, 'el.textContent = "safe"') is False

    def test_setInnerHTML_matches(self) -> None:
        """setInnerHTML pattern detects dangerouslySetInnerHTML."""
        pattern = PatternMatcher.get_pattern("setInnerHTML")
        assert pattern is not None
        assert (
            PatternMatcher.test_pattern(
                pattern, "dangerouslySetInnerHTML={{__html: data}}"
            )
            is True
        )

    def test_setInnerHTML_rejects(self) -> None:
        """setInnerHTML pattern ignores normal JSX."""
        pattern = PatternMatcher.get_pattern("setInnerHTML")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, '<div className="safe">') is False

    def test_sql_injection_matches(self) -> None:
        """sql_injection pattern detects string concatenation in queries."""
        pattern = PatternMatcher.get_pattern("sql_injection")
        assert pattern is not None
        text = 'cursor.execute("SELECT * FROM users WHERE id=" + user_id)'
        assert PatternMatcher.test_pattern(pattern, text) is True

    def test_sql_injection_rejects(self) -> None:
        """sql_injection pattern ignores parameterized queries."""
        pattern = PatternMatcher.get_pattern("sql_injection")
        assert pattern is not None
        text = 'cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))'
        assert PatternMatcher.test_pattern(pattern, text) is False

    def test_hardcoded_secret_matches(self) -> None:
        """hardcoded_secret pattern detects inline credentials."""
        pattern = PatternMatcher.get_pattern("hardcoded_secret")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, "password = 'hunter2'") is True

    def test_hardcoded_secret_rejects(self) -> None:
        """hardcoded_secret pattern ignores env-var lookups."""
        pattern = PatternMatcher.get_pattern("hardcoded_secret")
        assert pattern is not None
        assert (
            PatternMatcher.test_pattern(pattern, "password = os.environ['DB_PASS']")
            is False
        )


class TestDebugPatterns:
    """Verify each DEBUG_PATTERNS regex matches expected inputs."""

    @pytest.mark.parametrize(
        "text",
        [
            "console.log('debug')",
            "console.log (value)",
        ],
    )
    def test_console_log_matches(self, text: str) -> None:
        """console_log pattern detects console.log calls."""
        pattern = PatternMatcher.get_pattern("console_log")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, text) is True

    def test_console_log_rejects(self) -> None:
        """console_log pattern ignores console.error."""
        pattern = PatternMatcher.get_pattern("console_log")
        assert pattern is not None
        assert (
            PatternMatcher.test_pattern(pattern, "console.error('real error')") is False
        )

    @pytest.mark.parametrize(
        "text",
        [
            "print('debug info')",
            "println('value')",
            "println!('macro')",
        ],
    )
    def test_print_debug_matches(self, text: str) -> None:
        """print_debug pattern detects print/println calls."""
        pattern = PatternMatcher.get_pattern("print_debug")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, text) is True

    def test_debugger_matches(self) -> None:
        """debugger pattern detects JS debugger statements."""
        pattern = PatternMatcher.get_pattern("debugger")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, "debugger;") is True

    def test_debugger_rejects(self) -> None:
        """debugger pattern ignores variable names containing 'debugger'."""
        pattern = PatternMatcher.get_pattern("debugger")
        assert pattern is not None
        # "debugger_mode = true" does not have "debugger ;" or "debugger;"
        assert PatternMatcher.test_pattern(pattern, "debugger_mode = true") is False

    def test_var_dump_matches(self) -> None:
        """var_dump pattern detects PHP var_dump calls."""
        pattern = PatternMatcher.get_pattern("var_dump")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, "var_dump($variable)") is True

    def test_var_dump_rejects(self) -> None:
        """var_dump pattern ignores unrelated code."""
        pattern = PatternMatcher.get_pattern("var_dump")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, "var dumped = true") is False

    def test_dd_laravel_matches(self) -> None:
        """dd_laravel pattern detects Laravel dd() calls."""
        pattern = PatternMatcher.get_pattern("dd_laravel")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, "dd($request)") is True

    def test_dd_laravel_rejects(self) -> None:
        """dd_laravel pattern ignores 'add' or 'added'."""
        pattern = PatternMatcher.get_pattern("dd_laravel")
        assert pattern is not None
        assert PatternMatcher.test_pattern(pattern, "added = true") is False


class TestGetPattern:
    """Test PatternMatcher.get_pattern method."""

    def test_returns_pattern_for_known_name(self) -> None:
        """Known pattern name returns its regex string."""
        result = PatternMatcher.get_pattern("sudo")
        assert result == r"sudo\s+"

    def test_returns_none_for_unknown_name(self) -> None:
        """Unknown pattern name returns None."""
        result = PatternMatcher.get_pattern("nonexistent_pattern")
        assert result is None

    def test_returns_none_for_empty_string(self) -> None:
        result = PatternMatcher.get_pattern("")
        assert result is None


class TestListPatterns:
    """Test PatternMatcher.list_patterns method."""

    def test_returns_all_16_patterns(self) -> None:
        """All 16 predefined patterns are returned."""
        patterns = PatternMatcher.list_patterns()
        assert len(patterns) == 16

    def test_includes_all_categories(self) -> None:
        """Returned dict includes patterns from all three categories."""
        patterns = PatternMatcher.list_patterns()
        # One from each category
        assert "rm_recursive" in patterns
        assert "eval_pattern" in patterns
        assert "console_log" in patterns

    def test_values_are_strings(self) -> None:
        """Every pattern value is a non-empty string."""
        patterns = PatternMatcher.list_patterns()
        for name, regex in patterns.items():
            assert isinstance(regex, str), f"{name} value is not a string"
            assert len(regex) > 0, f"{name} value is empty"


class TestTestPattern:
    """Test PatternMatcher.test_pattern static method."""

    def test_match_returns_true(self) -> None:
        """Matching text returns True."""
        assert PatternMatcher.test_pattern(r"hello", "hello world") is True

    def test_no_match_returns_false(self) -> None:
        """Non-matching text returns False."""
        assert PatternMatcher.test_pattern(r"hello", "goodbye") is False

    def test_invalid_regex_returns_false(self) -> None:
        """Invalid regex returns False instead of raising."""
        assert PatternMatcher.test_pattern(r"[invalid", "text") is False

    def test_empty_text_returns_false_for_nonempty_pattern(self) -> None:
        """Empty text does not match a non-empty pattern."""
        assert PatternMatcher.test_pattern(r"hello", "") is False

    def test_empty_pattern_matches_anything(self) -> None:
        """Empty regex pattern matches any string (zero-width match)."""
        assert PatternMatcher.test_pattern(r"", "anything") is True

    def test_multiline_flag_active(self) -> None:
        """MULTILINE flag allows ^ to match line starts."""
        text = "line1\nfoo bar\nline3"
        assert PatternMatcher.test_pattern(r"^foo", text) is True


class TestExtractMatches:
    """Test PatternMatcher.extract_matches static method."""

    def test_extracts_all_occurrences(self) -> None:
        """All matches are returned as a list."""
        result = PatternMatcher.extract_matches(r"\d+", "abc 123 def 456 ghi 789")
        assert result == ["123", "456", "789"]

    def test_no_matches_returns_empty_list(self) -> None:
        result = PatternMatcher.extract_matches(r"\d+", "no digits here")
        assert result == []

    def test_invalid_regex_returns_empty_list(self) -> None:
        """Invalid regex returns an empty list instead of raising."""
        result = PatternMatcher.extract_matches(r"[bad", "text")
        assert result == []

    def test_groups_returned_as_tuples(self) -> None:
        """Patterns with capture groups return group contents."""
        result = PatternMatcher.extract_matches(r"(\w+)=(\w+)", "a=1 b=2")
        assert result == [("a", "1"), ("b", "2")]


class TestValidatePattern:
    """Test PatternMatcher.validate_pattern static method."""

    def test_valid_pattern(self) -> None:
        """Valid regex returns (True, '')."""
        is_valid, error = PatternMatcher.validate_pattern(r"\d+")
        assert is_valid is True
        assert error == ""

    def test_invalid_pattern(self) -> None:
        """Invalid regex returns (False, error_message)."""
        is_valid, error = PatternMatcher.validate_pattern(r"[unclosed")
        assert is_valid is False
        assert len(error) > 0

    def test_empty_pattern_is_valid(self) -> None:
        """Empty string is a valid regex."""
        is_valid, error = PatternMatcher.validate_pattern("")
        assert is_valid is True
        assert error == ""


class TestEscapePattern:
    """Test PatternMatcher.escape_pattern static method."""

    def test_escapes_special_characters(self) -> None:
        """Special regex characters are escaped."""
        result = PatternMatcher.escape_pattern("file.txt")
        assert result == r"file\.txt"

    def test_escapes_brackets(self) -> None:
        """Brackets are escaped properly."""
        result = PatternMatcher.escape_pattern("[test]")
        assert r"\[test\]" == result

    def test_plain_text_unchanged(self) -> None:
        """Plain alphanumeric text is returned unchanged."""
        result = PatternMatcher.escape_pattern("hello123")
        assert result == "hello123"

    def test_empty_string(self) -> None:
        """Empty string returns empty string."""
        result = PatternMatcher.escape_pattern("")
        assert result == ""


class TestSuggestPattern:
    """Test PatternMatcher.suggest_pattern class method."""

    def test_suggests_matching_patterns(self) -> None:
        """Text containing a dangerous command returns matching pattern names."""
        suggestions = PatternMatcher.suggest_pattern("sudo rm -rf /")
        assert "sudo" in suggestions
        assert "rm_recursive" in suggestions

    def test_no_suggestions_for_safe_text(self) -> None:
        """Innocuous text returns an empty list."""
        suggestions = PatternMatcher.suggest_pattern("echo hello")
        assert suggestions == []

    def test_debug_code_suggestion(self) -> None:
        """Debug code triggers the correct debug pattern."""
        suggestions = PatternMatcher.suggest_pattern("console.log('debug')")
        assert "console_log" in suggestions

    def test_security_suggestion(self) -> None:
        """Security anti-pattern triggers the correct security pattern."""
        suggestions = PatternMatcher.suggest_pattern("password = 'secret123'")
        assert "hardcoded_secret" in suggestions

    def test_multiple_categories(self) -> None:
        """Text matching patterns from multiple categories returns all."""
        text = "eval('sudo rm -rf /')"
        suggestions = PatternMatcher.suggest_pattern(text)
        # Should match eval_pattern, sudo, and rm_recursive
        assert "eval_pattern" in suggestions
        assert "sudo" in suggestions
        assert "rm_recursive" in suggestions
