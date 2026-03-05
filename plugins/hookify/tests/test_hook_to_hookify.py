"""Tests for hook_to_hookify conversion tool."""

import tempfile
from pathlib import Path

# Import will work when module is installed
try:
    from scripts.hook_to_hookify import (
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
        import ast

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
        import ast

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
        import ast

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
        import ast

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
        import ast

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
        import ast

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
        import ast

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
        import ast

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
        import ast

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
