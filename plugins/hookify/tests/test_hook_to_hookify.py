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
