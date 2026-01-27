"""Tests for hook_to_hookify conversion tool."""

import tempfile
from pathlib import Path

# Import will work when module is installed
try:
    from scripts.hook_to_hookify import (
        ExtractedPattern,
        HookAnalyzer,
        analyze_hook,
        generate_hookify_rule,
    )
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.hook_to_hookify import (
        ExtractedPattern,
        HookAnalyzer,
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
