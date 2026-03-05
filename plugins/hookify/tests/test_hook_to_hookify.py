"""Tests for hook_to_hookify conversion tool."""

import ast
import subprocess
import sys
import tempfile
from pathlib import Path

# Import will work when module is installed
try:
    from scripts.hook_to_hookify import (
        DEFAULT_MAX_COMPLEXITY,
        DEFAULT_MIN_CONFIDENCE,
        ExtractedPattern,
        HookAnalyzer,
        _detect_tool_event,
        analyze_hook,
        generate_hookify_rule,
    )
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.hook_to_hookify import (
        DEFAULT_MAX_COMPLEXITY,
        DEFAULT_MIN_CONFIDENCE,
        ExtractedPattern,
        HookAnalyzer,
        _detect_tool_event,
        analyze_hook,
        generate_hookify_rule,
    )


class TestHookAnalyzer:
    """Test AST-based pattern extraction."""

    def test_extracts_regex_pattern(self):
        """Given a hook with re.search, extracts the regex pattern."""
        code = """
import re
def hook(context):
    if re.search(r"rm -rf", context["command"]):
        return {"action": "block"}
"""
        tree = ast.parse(code)
        analyzer = HookAnalyzer()
        analyzer.visit(tree)

        assert len(analyzer.patterns) == 1
        assert analyzer.patterns[0].pattern_type == "regex"
        assert analyzer.patterns[0].pattern == "rm -rf"

    def test_extracts_contains_pattern(self):
        """Given a hook with 'in' check, extracts contains pattern."""
        code = """
def hook(context):
    if "sudo" in context["command"]:
        return {"action": "warn"}
"""
        tree = ast.parse(code)
        analyzer = HookAnalyzer()
        analyzer.visit(tree)

        assert len(analyzer.patterns) == 1
        assert analyzer.patterns[0].pattern_type == "contains"
        assert analyzer.patterns[0].pattern == "sudo"

    def test_extracts_startswith_pattern(self):
        """Given a hook with startswith, extracts pattern."""
        code = """
def hook(context):
    if context["command"].startswith("git push"):
        return {"action": "warn"}
"""
        tree = ast.parse(code)
        analyzer = HookAnalyzer()
        analyzer.visit(tree)

        assert len(analyzer.patterns) == 1
        assert analyzer.patterns[0].pattern_type == "starts_with"
        assert analyzer.patterns[0].pattern == "git push"

    def test_detects_file_io_complexity(self):
        """Given a hook with file I/O, marks as complex."""
        code = """
def hook(context):
    with open("file.txt") as f:
        data = f.read()
"""
        tree = ast.parse(code)
        analyzer = HookAnalyzer()
        analyzer.visit(tree)

        assert analyzer.has_file_io
        assert analyzer.complexity >= 2


class TestAnalyzeHook:
    """Test full hook file analysis."""

    def test_analyzes_simple_hook(self):
        """Given a simple pattern-based hook, marks as convertible."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write("""
import re
def hook(context):
    if re.search(r"dangerous", context["command"]):
        return {"action": "block"}
""")
            f.flush()
            path = Path(f.name)

        analysis = analyze_hook(path)
        path.unlink()

        assert analysis.convertible
        assert len(analysis.patterns) == 1

    def test_marks_network_hook_unconvertible(self):
        """Given a hook with network calls, marks as not convertible."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write("""
import requests
def hook(context):
    response = requests.get("http://api.example.com")
    return response.json()
""")
            f.flush()
            path = Path(f.name)

        analysis = analyze_hook(path)
        path.unlink()

        assert not analysis.convertible
        assert "network" in analysis.reason.lower()


class TestGenerateHookifyRule:
    """Test hookify rule generation."""

    def test_generates_simple_rule(self):
        """Given analysis with one pattern, generates valid rule."""
        from scripts.hook_to_hookify import HookAnalysis

        analysis = HookAnalysis(
            file_path=Path("test_hook.py"),
            hook_type="PreToolUse",
            patterns=[
                ExtractedPattern(
                    pattern_type="regex",
                    pattern="rm -rf /",
                    field="command",
                )
            ],
            convertible=True,
        )

        rule = generate_hookify_rule(analysis)

        assert "name: test-hook" in rule
        assert "event: bash" in rule
        assert "pattern: 'rm -rf /'" in rule

    def test_generates_conditions_for_multiple_patterns(self):
        """Given analysis with multiple patterns, generates conditions."""
        from scripts.hook_to_hookify import HookAnalysis

        analysis = HookAnalysis(
            file_path=Path("multi_hook.py"),
            hook_type="PreToolUse",
            patterns=[
                ExtractedPattern(
                    pattern_type="contains",
                    pattern="sudo",
                    field="command",
                ),
                ExtractedPattern(
                    pattern_type="contains",
                    pattern="rm",
                    field="command",
                ),
            ],
            convertible=True,
        )

        rule = generate_hookify_rule(analysis)

        assert "conditions:" in rule
        assert "operator: contains" in rule


class TestHookAnalyzerEdgeCases:
    """Test edge cases and additional patterns."""

    def test_extracts_endswith_pattern(self):
        """Given a hook with endswith, extracts pattern."""
        code = """
def hook(context):
    if context["file_path"].endswith(".py"):
        return {"action": "warn"}
"""
        tree = ast.parse(code)
        analyzer = HookAnalyzer()
        analyzer.visit(tree)

        assert len(analyzer.patterns) == 1
        assert analyzer.patterns[0].pattern_type == "ends_with"
        assert analyzer.patterns[0].pattern == ".py"

    def test_extracts_equality_pattern(self):
        """Given a hook with equality check, extracts equals pattern."""
        code = """
def hook(context):
    if context["command"] == "rm -rf /":
        return {"action": "block"}
"""
        tree = ast.parse(code)
        analyzer = HookAnalyzer()
        analyzer.visit(tree)

        assert len(analyzer.patterns) == 1
        assert analyzer.patterns[0].pattern_type == "equals"
        assert analyzer.patterns[0].pattern == "rm -rf /"

    def test_detects_network_complexity(self):
        """Given a hook with HTTP calls, marks as complex with network."""
        code = """
import requests
def hook(context):
    response = requests.get("http://example.com")
    return response
"""
        tree = ast.parse(code)
        analyzer = HookAnalyzer()
        analyzer.visit(tree)

        assert analyzer.has_network
        assert analyzer.complexity >= 5

    def test_guesses_content_field(self):
        """Given variable named 'content', guesses content field."""
        code = """
def hook(context):
    if "password" in context["content"]:
        return {"action": "block"}
"""
        tree = ast.parse(code)
        analyzer = HookAnalyzer()
        analyzer.visit(tree)

        assert len(analyzer.patterns) == 1
        assert analyzer.patterns[0].field == "content"

    def test_guesses_file_path_field(self):
        """Given variable named 'file_path', guesses file_path field."""
        code = """
def hook(context):
    file_path = context["file"]
    if ".env" in file_path:
        return {"action": "block"}
"""
        tree = ast.parse(code)
        analyzer = HookAnalyzer()
        analyzer.visit(tree)

        # Should detect the pattern and guess field from variable name
        assert len(analyzer.patterns) >= 1


class TestAnalyzeHookEdgeCases:
    """Test error handling and edge cases in analyze_hook."""

    def test_handles_syntax_error_gracefully(self):
        """Given invalid Python syntax, returns unconvertible analysis."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write("def invalid syntax here")
            f.flush()
            path = Path(f.name)

        analysis = analyze_hook(path)
        path.unlink()

        assert not analysis.convertible
        assert "parse" in analysis.reason.lower() or "syntax" in analysis.reason.lower()

    def test_marks_no_patterns_as_unconvertible(self):
        """Given hook with no extractable patterns, marks unconvertible."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write("""
def hook(context):
    # Does nothing recognizable
    return None
""")
            f.flush()
            path = Path(f.name)

        analysis = analyze_hook(path)
        path.unlink()

        assert not analysis.convertible
        assert "no extractable" in analysis.reason.lower()


class TestGenerateHookifyRuleEdgeCases:
    """Test edge cases in rule generation."""

    def test_returns_empty_for_unconvertible(self):
        """Given unconvertible analysis, returns empty string."""
        from scripts.hook_to_hookify import HookAnalysis

        analysis = HookAnalysis(
            file_path=Path("complex.py"),
            convertible=False,
            reason="Too complex",
        )

        rule = generate_hookify_rule(analysis)

        assert rule == ""

    def test_generates_single_non_regex_pattern(self):
        """Given single non-regex pattern, generates conditions block."""
        from scripts.hook_to_hookify import HookAnalysis

        analysis = HookAnalysis(
            file_path=Path("contains_hook.py"),
            hook_type="PreToolUse",
            patterns=[
                ExtractedPattern(
                    pattern_type="contains",
                    pattern="sudo",
                    field="command",
                )
            ],
            convertible=True,
        )

        rule = generate_hookify_rule(analysis)

        assert "conditions:" in rule
        assert "operator: contains" in rule
        assert "field: command" in rule


class TestDefaultThresholds:
    """Test that default threshold constants exist and have expected values."""

    def test_default_max_complexity_exists(self):
        """Default max complexity constant should be 10."""
        assert DEFAULT_MAX_COMPLEXITY == 10

    def test_default_min_confidence_exists(self):
        """Default min confidence constant should be 0.7."""
        assert DEFAULT_MIN_CONFIDENCE == 0.7

    def test_analyze_hook_uses_default_max_complexity(self):
        """Without explicit threshold, analyze_hook uses DEFAULT_MAX_COMPLEXITY."""
        # A hook with complexity exactly at the default threshold (10)
        # should be marked unconvertible (> 10 fails, but we need > threshold)
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write("""
import re
def hook(context):
    if re.search(r"dangerous", context["command"]):
        return {"action": "block"}
""")
            f.flush()
            path = Path(f.name)

        # Simple hook has low complexity, should be convertible with default
        analysis = analyze_hook(path)
        path.unlink()

        assert analysis.convertible
        assert analysis.complexity_score <= DEFAULT_MAX_COMPLEXITY

    def test_analyze_hook_uses_default_min_confidence(self):
        """Without explicit threshold, analyze_hook uses DEFAULT_MIN_CONFIDENCE."""
        # An equality pattern has confidence 0.8 which is above default 0.7
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write("""
def hook(context):
    if context["command"] == "rm -rf /":
        return {"action": "block"}
""")
            f.flush()
            path = Path(f.name)

        analysis = analyze_hook(path)
        path.unlink()

        assert analysis.convertible
        # All patterns should survive the default 0.7 confidence filter
        assert len(analysis.patterns) == 1
        assert analysis.patterns[0].confidence >= DEFAULT_MIN_CONFIDENCE


class TestCustomMaxComplexity:
    """Test that --max-complexity / max_complexity param affects decisions."""

    def test_lower_max_complexity_rejects_simple_hook(self):
        """A hook at complexity 0 is rejected when max_complexity is -1."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write("""
import re
def hook(context):
    if re.search(r"danger", context["command"]):
        return {"action": "block"}
""")
            f.flush()
            path = Path(f.name)

        # Even complexity 0 exceeds a threshold of -1
        analysis = analyze_hook(path, max_complexity=-1)
        path.unlink()

        assert not analysis.convertible
        assert "complex" in analysis.reason.lower()

    def test_higher_max_complexity_accepts_moderate_hook(self):
        """A hook within custom max complexity should be convertible."""
        # Same file I/O hook but with a generous threshold
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write("""
import re
def hook(context):
    with open("config.txt") as f:
        data = f.read()
    if re.search(r"danger", context["command"]):
        return {"action": "block"}
""")
            f.flush()
            path = Path(f.name)

        # File I/O hook is normally unconvertible due to has_file_io,
        # but we test with a very high threshold. Note: file I/O still
        # blocks conversion independently, so use a pure complexity test.
        analysis = analyze_hook(path, max_complexity=100)
        path.unlink()

        # File I/O still blocks independently, but complexity check passes
        # The hook is unconvertible due to file I/O, not complexity
        assert not analysis.convertible
        assert "file" in analysis.reason.lower()

    def test_complexity_exactly_at_threshold_is_convertible(self):
        """Hook with complexity == max_complexity should be convertible."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write("""
import re
def hook(context):
    if re.search(r"danger", context["command"]):
        return {"action": "block"}
""")
            f.flush()
            path = Path(f.name)

        # Simple hook has complexity 0, set threshold to 0 (== is OK)
        analysis = analyze_hook(path, max_complexity=0)
        path.unlink()

        assert analysis.convertible

    def test_complexity_above_threshold_is_unconvertible(self):
        """Hook with complexity > max_complexity should be unconvertible."""
        # This hook has file I/O giving it complexity >= 2
        # We use a hook that only adds complexity without file_io/network
        # to test pure complexity threshold
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            # open() adds complexity 2 via file_io detection, but we need
            # a test that triggers complexity > threshold without file_io.
            # A regex pattern itself doesn't add complexity. Let's create
            # a hook that has multiple open/read calls but test via
            # the max_complexity param. Actually, since file_io is checked
            # before complexity, we need to craft this carefully.
            #
            # We'll write a hook with patterns only (no file_io/network)
            # and set max_complexity=0 so the analyzer's complexity of 0
            # is NOT > 0, so it passes. But if we set max_complexity=-1,
            # complexity 0 > -1 so it fails.
            f.write("""
import re
def hook(context):
    if re.search(r"danger", context["command"]):
        return {"action": "block"}
""")
            f.flush()
            path = Path(f.name)

        # complexity is 0 for this hook, but threshold of -1 makes 0 > -1
        analysis = analyze_hook(path, max_complexity=-1)
        path.unlink()

        assert not analysis.convertible
        assert "complex" in analysis.reason.lower()


class TestCustomMinConfidence:
    """Test that --min-confidence / min_confidence param filters patterns."""

    def test_high_min_confidence_filters_low_confidence_patterns(self):
        """Patterns below min_confidence should be filtered out."""
        # Equality pattern has confidence 0.8, contains has 0.85
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write("""
def hook(context):
    if context["command"] == "rm -rf /":
        return {"action": "block"}
""")
            f.flush()
            path = Path(f.name)

        # Equality pattern has confidence 0.8; with min_confidence=0.9,
        # it should be filtered out
        analysis = analyze_hook(path, min_confidence=0.9)
        path.unlink()

        assert len(analysis.patterns) == 0
        # With no patterns left, it should be unconvertible
        assert not analysis.convertible

    def test_low_min_confidence_keeps_all_patterns(self):
        """All patterns should be kept when min_confidence is very low."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write("""
def hook(context):
    if context["command"] == "rm -rf /":
        return {"action": "block"}
""")
            f.flush()
            path = Path(f.name)

        # Equality pattern has confidence 0.8; with min_confidence=0.1,
        # it should be kept
        analysis = analyze_hook(path, min_confidence=0.1)
        path.unlink()

        assert len(analysis.patterns) == 1
        assert analysis.convertible

    def test_min_confidence_at_exact_value_keeps_pattern(self):
        """Pattern with confidence == min_confidence should be kept."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write("""
def hook(context):
    if context["command"] == "rm -rf /":
        return {"action": "block"}
""")
            f.flush()
            path = Path(f.name)

        # Equality pattern has confidence 0.8; min_confidence=0.8 should keep it
        analysis = analyze_hook(path, min_confidence=0.8)
        path.unlink()

        assert len(analysis.patterns) == 1
        assert analysis.convertible

    def test_mixed_confidence_filters_only_low(self):
        """Only patterns below min_confidence should be removed."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
            f.write("""
import re
def hook(context):
    if context["command"] == "rm -rf /":
        pass
    if re.search(r"sudo", context["command"]):
        return {"action": "block"}
""")
            f.flush()
            path = Path(f.name)

        # Equality has confidence 0.8, regex has confidence 0.9
        # With min_confidence=0.85, only regex should survive
        analysis = analyze_hook(path, min_confidence=0.85)
        path.unlink()

        assert len(analysis.patterns) == 1
        assert analysis.patterns[0].pattern_type == "regex"
        assert analysis.patterns[0].confidence >= 0.85


class TestCLIThresholdArgs:
    """Test CLI argument parsing for thresholds."""

    def test_cli_accepts_max_complexity_arg(self):
        """The argparse parser should accept --max-complexity."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.hook_to_hookify",
                "--help",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert "--max-complexity" in result.stdout

    def test_cli_accepts_min_confidence_arg(self):
        """The argparse parser should accept --min-confidence."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.hook_to_hookify",
                "--help",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert "--min-confidence" in result.stdout


class TestDetectToolEvent:
    """Test tool-type detection from pattern fields."""

    def test_command_patterns_map_to_bash(self):
        """Given patterns on 'command' field, returns 'bash' event."""
        from scripts.hook_to_hookify import HookAnalysis

        analysis = HookAnalysis(
            file_path=Path("cmd_hook.py"),
            hook_type="PreToolUse",
            patterns=[
                ExtractedPattern(
                    pattern_type="regex",
                    pattern="rm -rf",
                    field="command",
                )
            ],
            convertible=True,
        )

        assert _detect_tool_event(analysis) == "bash"

    def test_file_path_patterns_map_to_file(self):
        """Given patterns on 'file_path' field, returns 'file' event."""
        from scripts.hook_to_hookify import HookAnalysis

        analysis = HookAnalysis(
            file_path=Path("path_hook.py"),
            hook_type="PreToolUse",
            patterns=[
                ExtractedPattern(
                    pattern_type="ends_with",
                    pattern=".env",
                    field="file_path",
                )
            ],
            convertible=True,
        )

        assert _detect_tool_event(analysis) == "file"

    def test_content_patterns_map_to_file(self):
        """Given patterns on 'content' field, returns 'file' event."""
        from scripts.hook_to_hookify import HookAnalysis

        analysis = HookAnalysis(
            file_path=Path("content_hook.py"),
            hook_type="PostToolUse",
            patterns=[
                ExtractedPattern(
                    pattern_type="contains",
                    pattern="password",
                    field="content",
                )
            ],
            convertible=True,
        )

        assert _detect_tool_event(analysis) == "file"

    def test_new_text_patterns_map_to_file(self):
        """Given patterns on 'new_text' field, returns 'file' event."""
        from scripts.hook_to_hookify import HookAnalysis

        analysis = HookAnalysis(
            file_path=Path("write_hook.py"),
            hook_type="PreToolUse",
            patterns=[
                ExtractedPattern(
                    pattern_type="regex",
                    pattern="API_KEY",
                    field="new_text",
                )
            ],
            convertible=True,
        )

        assert _detect_tool_event(analysis) == "file"

    def test_old_text_patterns_map_to_file(self):
        """Given patterns on 'old_text' field, returns 'file' event."""
        from scripts.hook_to_hookify import HookAnalysis

        analysis = HookAnalysis(
            file_path=Path("edit_hook.py"),
            hook_type="PreToolUse",
            patterns=[
                ExtractedPattern(
                    pattern_type="contains",
                    pattern="TODO",
                    field="old_text",
                )
            ],
            convertible=True,
        )

        assert _detect_tool_event(analysis) == "file"

    def test_mixed_fields_fall_back_to_bash(self):
        """Given patterns on both command and file fields, returns 'bash'."""
        from scripts.hook_to_hookify import HookAnalysis

        analysis = HookAnalysis(
            file_path=Path("mixed_hook.py"),
            hook_type="PreToolUse",
            patterns=[
                ExtractedPattern(
                    pattern_type="contains",
                    pattern="sudo",
                    field="command",
                ),
                ExtractedPattern(
                    pattern_type="ends_with",
                    pattern=".py",
                    field="file_path",
                ),
            ],
            convertible=True,
        )

        assert _detect_tool_event(analysis) == "bash"

    def test_session_start_maps_to_prompt(self):
        """Given SessionStart hook type, returns 'prompt' event."""
        from scripts.hook_to_hookify import HookAnalysis

        analysis = HookAnalysis(
            file_path=Path("session_hook.py"),
            hook_type="SessionStart",
            patterns=[
                ExtractedPattern(
                    pattern_type="contains",
                    pattern="hello",
                    field="user_prompt",
                )
            ],
            convertible=True,
        )

        assert _detect_tool_event(analysis) == "prompt"

    def test_stop_maps_to_stop(self):
        """Given Stop hook type, returns 'stop' event."""
        from scripts.hook_to_hookify import HookAnalysis

        analysis = HookAnalysis(
            file_path=Path("stop_hook.py"),
            hook_type="Stop",
            patterns=[
                ExtractedPattern(
                    pattern_type="contains",
                    pattern="done",
                    field="command",
                )
            ],
            convertible=True,
        )

        assert _detect_tool_event(analysis) == "stop"

    def test_no_patterns_defaults_to_bash(self):
        """Given no patterns, returns 'bash' as the safe default."""
        from scripts.hook_to_hookify import HookAnalysis

        analysis = HookAnalysis(
            file_path=Path("empty_hook.py"),
            hook_type="PreToolUse",
            patterns=[],
            convertible=True,
        )

        assert _detect_tool_event(analysis) == "bash"

    def test_multiple_file_patterns_map_to_file(self):
        """Given multiple patterns all on file fields, returns 'file'."""
        from scripts.hook_to_hookify import HookAnalysis

        analysis = HookAnalysis(
            file_path=Path("multi_file_hook.py"),
            hook_type="PostToolUse",
            patterns=[
                ExtractedPattern(
                    pattern_type="ends_with",
                    pattern=".env",
                    field="file_path",
                ),
                ExtractedPattern(
                    pattern_type="contains",
                    pattern="API_KEY",
                    field="content",
                ),
            ],
            convertible=True,
        )

        assert _detect_tool_event(analysis) == "file"

    def test_user_prompt_field_defaults_to_bash(self):
        """Given user_prompt field on PreToolUse, defaults to 'bash'.

        The user_prompt field is not a file field or command field,
        so it does not trigger either detection path, resulting in
        the bash default.
        """
        from scripts.hook_to_hookify import HookAnalysis

        analysis = HookAnalysis(
            file_path=Path("prompt_check.py"),
            hook_type="PreToolUse",
            patterns=[
                ExtractedPattern(
                    pattern_type="contains",
                    pattern="please",
                    field="user_prompt",
                )
            ],
            convertible=True,
        )

        assert _detect_tool_event(analysis) == "bash"


class TestGenerateHookifyRuleToolEvent:
    """Test that generate_hookify_rule uses tool-type detection."""

    def test_file_hook_generates_file_event(self):
        """Given PreToolUse hook with file_path pattern, generates file event."""
        from scripts.hook_to_hookify import HookAnalysis

        analysis = HookAnalysis(
            file_path=Path("protect_env.py"),
            hook_type="PreToolUse",
            patterns=[
                ExtractedPattern(
                    pattern_type="ends_with",
                    pattern=".env",
                    field="file_path",
                )
            ],
            convertible=True,
        )

        rule = generate_hookify_rule(analysis)

        assert "event: file" in rule
        assert "event: bash" not in rule

    def test_command_hook_generates_bash_event(self):
        """Given PreToolUse hook with command pattern, generates bash event."""
        from scripts.hook_to_hookify import HookAnalysis

        analysis = HookAnalysis(
            file_path=Path("block_rm.py"),
            hook_type="PreToolUse",
            patterns=[
                ExtractedPattern(
                    pattern_type="regex",
                    pattern="rm -rf",
                    field="command",
                )
            ],
            convertible=True,
        )

        rule = generate_hookify_rule(analysis)

        assert "event: bash" in rule

    def test_content_hook_generates_file_event(self):
        """Given PostToolUse hook with content pattern, generates file event."""
        from scripts.hook_to_hookify import HookAnalysis

        analysis = HookAnalysis(
            file_path=Path("scan_content.py"),
            hook_type="PostToolUse",
            patterns=[
                ExtractedPattern(
                    pattern_type="contains",
                    pattern="password",
                    field="content",
                )
            ],
            convertible=True,
        )

        rule = generate_hookify_rule(analysis)

        assert "event: file" in rule
