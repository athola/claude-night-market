"""Tests for context-aware rule suggester."""

import tempfile
from pathlib import Path

try:
    from scripts.rule_suggester import ProjectContext, detect_context, suggest_rules
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.rule_suggester import ProjectContext, detect_context, suggest_rules


class TestDetectContext:
    """Test project context detection."""

    def test_detects_python_project(self):
        """Given pyproject.toml, detects Python language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "pyproject.toml").touch()

            ctx = detect_context(path)

            assert "python" in ctx.languages

    def test_detects_git_repo(self):
        """Given .git directory, detects git."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / ".git").mkdir()

            ctx = detect_context(path)

            assert ctx.has_git

    def test_detects_docker(self):
        """Given Dockerfile, detects docker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "Dockerfile").touch()

            ctx = detect_context(path)

            assert ctx.has_docker

    def test_detects_javascript(self):
        """Given package.json, detects JavaScript."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "package.json").touch()

            ctx = detect_context(path)

            assert "javascript" in ctx.languages


class TestSuggestRules:
    """Test rule suggestion logic."""

    def test_suggests_git_rules_for_git_repo(self):
        """Given git context, suggests git-related rules."""
        ctx = ProjectContext(has_git=True)

        suggestions = suggest_rules(ctx)

        names = [s.name for s in suggestions]
        assert "block-force-push-main" in names

    def test_suggests_python_rules(self):
        """Given Python context, suggests Python rules."""
        ctx = ProjectContext(languages=["python"])

        suggestions = suggest_rules(ctx)

        names = [s.name for s in suggestions]
        assert any("pip" in n for n in names)

    def test_sorts_by_relevance(self):
        """Suggestions are sorted by relevance descending."""
        ctx = ProjectContext(has_git=True, languages=["python"])

        suggestions = suggest_rules(ctx)

        relevances = [s.relevance for s in suggestions]
        assert relevances == sorted(relevances, reverse=True)
