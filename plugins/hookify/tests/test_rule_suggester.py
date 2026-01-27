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

    def test_suggests_docker_rules(self):
        """Given Docker context, suggests Docker rules."""
        ctx = ProjectContext(has_docker=True)

        suggestions = suggest_rules(ctx)

        names = [s.name for s in suggestions]
        assert any("docker" in n for n in names)

    def test_suggests_javascript_rules(self):
        """Given JavaScript context, suggests npm-related rules."""
        ctx = ProjectContext(languages=["javascript"])

        suggestions = suggest_rules(ctx)

        names = [s.name for s in suggestions]
        assert any("npm" in n for n in names)


class TestDetectContextEdgeCases:
    """Test additional context detection scenarios."""

    def test_detects_rust_project(self):
        """Given Cargo.toml, detects Rust language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "Cargo.toml").touch()

            ctx = detect_context(path)

            assert "rust" in ctx.languages

    def test_detects_go_project(self):
        """Given go.mod, detects Go language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "go.mod").touch()

            ctx = detect_context(path)

            assert "go" in ctx.languages

    def test_detects_typescript(self):
        """Given package.json and tsconfig.json, detects TypeScript."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "package.json").touch()
            (path / "tsconfig.json").touch()

            ctx = detect_context(path)

            assert "javascript" in ctx.languages
            assert "typescript" in ctx.languages

    def test_detects_monorepo(self):
        """Given packages directory, detects monorepo type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "packages").mkdir()

            ctx = detect_context(path)

            assert ctx.project_type == "monorepo"

    def test_detects_ci(self):
        """Given .github/workflows, detects CI."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / ".github" / "workflows").mkdir(parents=True)

            ctx = detect_context(path)

            assert ctx.has_ci

    def test_detects_docker_compose(self):
        """Given docker-compose.yml, detects Docker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            (path / "docker-compose.yml").touch()

            ctx = detect_context(path)

            assert ctx.has_docker


class TestFormatSuggestions:
    """Test suggestion formatting."""

    def test_formats_as_text(self):
        """Given text format, returns markdown output."""
        from scripts.rule_suggester import RuleSuggestion, format_suggestions

        ctx = ProjectContext(has_git=True, languages=["python"])
        suggestions = [
            RuleSuggestion(
                name="test-rule",
                description="A test rule",
                relevance=0.9,
                reason="Testing",
                category="test",
                rule_template="---\nname: test\n---",
            )
        ]

        output = format_suggestions(suggestions, ctx, "text")

        assert "# Hookify Rule Suggestions" in output
        assert "test-rule" in output
        assert "90%" in output  # Relevance formatted as percentage

    def test_formats_as_json(self):
        """Given json format, returns valid JSON output."""
        import json

        from scripts.rule_suggester import RuleSuggestion, format_suggestions

        ctx = ProjectContext(has_git=True, languages=["python"])
        suggestions = [
            RuleSuggestion(
                name="test-rule",
                description="A test rule",
                relevance=0.9,
                reason="Testing",
                category="test",
                rule_template="---\nname: test\n---",
            )
        ]

        output = format_suggestions(suggestions, ctx, "json")

        # Should be valid JSON
        parsed = json.loads(output)
        assert "context" in parsed
        assert "suggestions" in parsed
        assert parsed["context"]["has_git"] is True
