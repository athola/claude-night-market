"""Tests for context-aware rule suggester."""

import json
import tempfile
from pathlib import Path

try:
    from scripts.rule_suggester import (
        RULE_TEMPLATES,
        ProjectContext,
        RuleSuggestion,
        detect_context,
        format_suggestions,
        suggest_rules,
    )
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.rule_suggester import (
        RULE_TEMPLATES,
        ProjectContext,
        RuleSuggestion,
        detect_context,
        format_suggestions,
        suggest_rules,
    )


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


class TestNewLanguageTemplates:
    """Test TypeScript, Go, and Rust rule suggestions."""

    # TypeScript

    def test_suggests_typescript_rules_for_typescript_project(self):
        """Given TypeScript context, suggests TypeScript rules."""
        ctx = ProjectContext(languages=["typescript"])

        suggestions = suggest_rules(ctx)

        names = [s.name for s in suggestions]
        assert "block-npm-audit-bypass" in names

    def test_typescript_warn_no_lockfile(self):
        """Given TypeScript context, includes warn-no-lockfile rule."""
        ctx = ProjectContext(languages=["typescript"])

        suggestions = suggest_rules(ctx)

        names = [s.name for s in suggestions]
        assert "warn-no-lockfile" in names

    def test_typescript_block_any_type(self):
        """Given TypeScript context, includes block-any-type rule."""
        ctx = ProjectContext(languages=["typescript"])

        suggestions = suggest_rules(ctx)

        names = [s.name for s in suggestions]
        assert "block-any-type" in names

    def test_typescript_templates_have_required_fields(self):
        """All TypeScript templates have the required RuleSuggestion fields."""
        for template in RULE_TEMPLATES["typescript"]:
            assert template.name, "name must not be empty"
            assert template.description, "description must not be empty"
            assert 0.0 <= template.relevance <= 1.0, "relevance must be in [0, 1]"
            assert template.reason, "reason must not be empty"
            assert template.category in (
                "security",
                "quality",
                "workflow",
            ), f"unexpected category: {template.category}"
            assert template.rule_template, "rule_template must not be empty"

    # Go

    def test_suggests_go_rules_for_go_project(self):
        """Given Go context, suggests Go rules."""
        ctx = ProjectContext(languages=["go"])

        suggestions = suggest_rules(ctx)

        names = [s.name for s in suggestions]
        assert "block-go-vet-bypass" in names

    def test_go_warn_no_mod_tidy(self):
        """Given Go context, includes warn-no-mod-tidy rule."""
        ctx = ProjectContext(languages=["go"])

        suggestions = suggest_rules(ctx)

        names = [s.name for s in suggestions]
        assert "warn-no-mod-tidy" in names

    def test_go_block_unsafe_import(self):
        """Given Go context, includes block-unsafe-import rule."""
        ctx = ProjectContext(languages=["go"])

        suggestions = suggest_rules(ctx)

        names = [s.name for s in suggestions]
        assert "block-unsafe-import" in names

    def test_go_templates_have_required_fields(self):
        """All Go templates have the required RuleSuggestion fields."""
        for template in RULE_TEMPLATES["go"]:
            assert template.name, "name must not be empty"
            assert template.description, "description must not be empty"
            assert 0.0 <= template.relevance <= 1.0, "relevance must be in [0, 1]"
            assert template.reason, "reason must not be empty"
            assert template.category in (
                "security",
                "quality",
                "workflow",
            ), f"unexpected category: {template.category}"
            assert template.rule_template, "rule_template must not be empty"

    # Rust

    def test_suggests_rust_rules_for_rust_project(self):
        """Given Rust context, suggests Rust rules."""
        ctx = ProjectContext(languages=["rust"])

        suggestions = suggest_rules(ctx)

        names = [s.name for s in suggestions]
        assert "block-clippy-bypass" in names

    def test_rust_warn_no_audit(self):
        """Given Rust context, includes warn-no-audit rule."""
        ctx = ProjectContext(languages=["rust"])

        suggestions = suggest_rules(ctx)

        names = [s.name for s in suggestions]
        assert "warn-no-audit" in names

    def test_rust_block_unsafe_without_comment(self):
        """Given Rust context, includes block-unsafe-without-comment rule."""
        ctx = ProjectContext(languages=["rust"])

        suggestions = suggest_rules(ctx)

        names = [s.name for s in suggestions]
        assert "block-unsafe-without-comment" in names

    def test_rust_templates_have_required_fields(self):
        """All Rust templates have the required RuleSuggestion fields."""
        for template in RULE_TEMPLATES["rust"]:
            assert template.name, "name must not be empty"
            assert template.description, "description must not be empty"
            assert 0.0 <= template.relevance <= 1.0, "relevance must be in [0, 1]"
            assert template.reason, "reason must not be empty"
            assert template.category in (
                "security",
                "quality",
                "workflow",
            ), f"unexpected category: {template.category}"
            assert template.rule_template, "rule_template must not be empty"

    # Cross-language

    def test_no_cross_language_bleed(self):
        """Go rules are not returned for a Python-only project."""
        ctx = ProjectContext(languages=["python"])

        suggestions = suggest_rules(ctx)

        names = [s.name for s in suggestions]
        assert "block-go-vet-bypass" not in names
        assert "block-clippy-bypass" not in names
        assert "block-any-type" not in names


class TestFormatSuggestions:
    """Test suggestion formatting."""

    def test_formats_as_text(self):
        """Given text format, returns markdown output."""
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
