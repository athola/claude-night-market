"""Tests for url_detector hook."""

from __future__ import annotations

import io
import json
import os
import sys

import pytest

# Add hooks to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))

import url_detector
from url_detector import extract_urls


class TestExtractUrls:
    """Tests for URL extraction."""

    MULTIPLE_URL_COUNT = 2

    def test_no_urls(self) -> None:
        """Text without URLs should return empty list."""
        assert extract_urls("Hello world, no URLs here.") == []

    def test_http_url(self) -> None:
        """HTTP URLs should be extracted."""
        urls = extract_urls("Check out http://example.com for more.")
        assert "http://example.com" in urls

    def test_https_url(self) -> None:
        """HTTPS URLs should be extracted."""
        urls = extract_urls("See https://example.com/article for details.")
        assert len(urls) == 1
        assert "https://example.com/article" in urls[0]

    def test_multiple_urls(self) -> None:
        """Multiple URLs should be extracted."""
        text = "Visit https://one.com and https://two.com for info."
        urls = extract_urls(text)
        assert len(urls) == self.MULTIPLE_URL_COUNT

    def test_localhost_skipped(self) -> None:
        """Localhost URLs should be skipped."""
        urls = extract_urls("API at http://localhost:3000/api")
        assert len(urls) == 0

    def test_127_0_0_1_skipped(self) -> None:
        """127.0.0.1 URLs should be skipped."""
        urls = extract_urls("Server at http://127.0.0.1:8080")
        assert len(urls) == 0

    def test_image_urls_skipped(self) -> None:
        """Image URLs should be skipped."""
        urls = extract_urls("Image at https://example.com/photo.png")
        assert len(urls) == 0

    def test_video_urls_skipped(self) -> None:
        """Video URLs should be skipped."""
        urls = extract_urls("Video at https://example.com/video.mp4")
        assert len(urls) == 0

    def test_archive_urls_skipped(self) -> None:
        """Archive URLs should be skipped."""
        urls = extract_urls("Download https://example.com/file.zip")
        assert len(urls) == 0

    def test_pdf_urls_skipped(self) -> None:
        """PDF URLs should be skipped (special handling needed)."""
        urls = extract_urls("Paper at https://example.com/paper.pdf")
        assert len(urls) == 0

    def test_article_urls_extracted(self) -> None:
        """Article URLs should be extracted."""
        urls = extract_urls("Read https://blog.example.com/article-title")
        assert len(urls) == 1

    def test_fast_path_no_protocol(self) -> None:
        """Fast path: text without :// should return immediately."""
        # This should be very fast since no URLs possible
        urls = extract_urls("No protocol indicators here at all")
        assert urls == []

    def test_urls_in_markdown(self) -> None:
        """URLs in markdown links should be extracted."""
        text = "Check [this article](https://example.com/article) for more."
        urls = extract_urls(text)
        # Should extract but might include trailing )
        assert any("example.com/article" in url for url in urls)

    def test_complex_url_path(self) -> None:
        """Complex URL paths should be handled."""
        text = "See https://docs.example.com/v2/api/reference#section"
        urls = extract_urls(text)
        assert len(urls) == 1
        assert "docs.example.com" in urls[0]

    def test_claude_code_repo_url_skipped(self) -> None:
        """The Claude Code repo has local docs, so its URLs are not captured."""
        urls = extract_urls("See https://github.com/anthropics/claude-code/issues/1")
        assert urls == []

    def test_claude_code_repo_url_on_www_host_skipped(self) -> None:
        """www.github.com serves the same repo as github.com."""
        urls = extract_urls("See https://www.github.com/anthropics/claude-code")
        assert urls == []

    def test_claude_code_repo_url_with_git_suffix_skipped(self) -> None:
        """A clone URL names the same repo as the web URL."""
        urls = extract_urls("Clone https://github.com/anthropics/claude-code.git")
        assert urls == []

    def test_sibling_repo_sharing_claude_code_prefix_extracted(self) -> None:
        """A repo whose name extends claude-code is a different repo."""
        urls = extract_urls("See https://github.com/anthropics/claude-code-action")
        assert urls == ["https://github.com/anthropics/claude-code-action"]


class TestQuietPathImports:
    """Feature: a prompt with no URL costs nothing but the regex.

    This hook is one of five on UserPromptSubmit, an event that blocks
    the turn and that telemetry showed timing out on roughly 16% of
    prompts. `shared.config` and `shared.deduplication` pull in
    memory_palace.paths and xxhash, about 100ms measured with
    `python -X importtime`, and neither is reachable until a URL has
    already been found. Its sibling `recall.py` pins the same contract
    for the same reason.
    """

    def test_shared_package_is_not_imported_at_module_scope(self) -> None:
        """Scenario: a promptless-of-URLs turn pays only for the regex."""
        import ast
        from pathlib import Path

        hook = Path(__file__).resolve().parents[2] / "hooks" / "url_detector.py"
        tree = ast.parse(hook.read_text())
        toplevel = {
            node.module
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module
        }
        toplevel |= {
            alias.name
            for node in tree.body
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        offenders = {
            name for name in toplevel if name.startswith(("shared", "memory_palace"))
        }
        assert not offenders, (
            f"imported at module scope, so every prompt pays for them: {offenders}"
        )


class TestMain:
    """Feature: the hook tells the session which pasted URLs are new.

    `get_config` and `is_known` are imported inside `main()`, so they are
    patched at their source modules. `is_known` reads the dedup index on
    disk, which is the external dependency here.
    """

    @staticmethod
    def _run(
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        stdin_text: str,
        *,
        known: frozenset[str] = frozenset(),
        enabled: bool = True,
    ) -> str:
        import shared.config
        import shared.deduplication

        monkeypatch.setattr(sys, "stdin", io.StringIO(stdin_text))
        monkeypatch.setattr(shared.config, "get_config", lambda: {"enabled": enabled})
        monkeypatch.setattr(shared.deduplication, "is_known", lambda url: url in known)
        with pytest.raises(SystemExit) as exit_info:
            url_detector.main()
        assert exit_info.value.code == 0
        return capsys.readouterr().out

    @staticmethod
    def _context(out: str) -> str:
        response = json.loads(out)
        assert response["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
        return response["hookSpecificOutput"]["additionalContext"]

    def test_invalid_json_exits_silently(self, monkeypatch, capsys) -> None:
        """Scenario: malformed stdin never blocks the prompt."""
        assert self._run(monkeypatch, capsys, "{not json") == ""

    def test_prompt_without_url_emits_nothing(self, monkeypatch, capsys) -> None:
        """Scenario: the fast path skips prompts with no URL marker."""
        out = self._run(monkeypatch, capsys, json.dumps({"prompt": "hello"}))
        assert out == ""

    def test_bare_www_without_scheme_emits_nothing(self, monkeypatch, capsys) -> None:
        """Scenario: `www.` passes the fast path, but only schemed URLs count."""
        out = self._run(
            monkeypatch, capsys, json.dumps({"prompt": "see www.example.com"})
        )
        assert out == ""

    def test_only_skipped_urls_emit_nothing(self, monkeypatch, capsys) -> None:
        """Scenario: localhost and media links are not knowledge sources."""
        prompt = "http://localhost:3000 and https://example.com/cat.png"
        out = self._run(monkeypatch, capsys, json.dumps({"prompt": prompt}))
        assert out == ""

    def test_disabled_config_emits_nothing(self, monkeypatch, capsys) -> None:
        """Scenario: a user who turned the plugin off gets no context."""
        out = self._run(
            monkeypatch,
            capsys,
            json.dumps({"prompt": "read https://example.com/post"}),
            enabled=False,
        )
        assert out == ""

    def test_new_url_is_flagged_for_intake(self, monkeypatch, capsys) -> None:
        """Scenario: an unindexed URL is listed for knowledge intake."""
        out = self._run(
            monkeypatch, capsys, json.dumps({"prompt": "https://example.com/post"})
        )
        context = self._context(out)
        assert "Detected 1 new URL(s)" in context
        assert "  - https://example.com/post" in context
        assert "already indexed" not in context

    def test_known_url_points_at_existing_knowledge(self, monkeypatch, capsys) -> None:
        """Scenario: an indexed URL is reported as already stored."""
        url = "https://example.com/post"
        out = self._run(
            monkeypatch,
            capsys,
            json.dumps({"prompt": url}),
            known=frozenset({url}),
        )
        context = self._context(out)
        assert "1 URL(s) already indexed" in context
        assert "new URL" not in context

    def test_mixed_urls_report_both_counts(self, monkeypatch, capsys) -> None:
        """Scenario: new and known URLs in one prompt are counted apart."""
        prompt = "https://a.example/one https://b.example/two"
        out = self._run(
            monkeypatch,
            capsys,
            json.dumps({"prompt": prompt}),
            known=frozenset({"https://b.example/two"}),
        )
        context = self._context(out)
        assert "Detected 1 new URL(s)" in context
        assert "1 URL(s) already indexed" in context

    def test_more_than_five_new_urls_are_truncated(self, monkeypatch, capsys) -> None:
        """Scenario: a long paste lists five URLs and counts the rest."""
        urls = [f"https://example.com/post-{n}" for n in range(7)]
        out = self._run(monkeypatch, capsys, json.dumps({"prompt": " ".join(urls)}))
        context = self._context(out)
        assert "Detected 7 new URL(s)" in context
        assert "  - https://example.com/post-4" in context
        assert "post-5" not in context
        assert "... and 2 more" in context
