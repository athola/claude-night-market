"""Tests for the post_learnings_stop Stop hook.

Feature: Post learnings to GitHub Discussions on session stop

As an ecosystem maintainer
I want learnings posted to Discussions at session end
So that improvement data is captured automatically.
"""

from __future__ import annotations

import importlib.util
import io
import sys
from pathlib import Path

import pytest

# Load the hook module dynamically
_HOOK_PATH = Path(__file__).parents[3] / "hooks" / "post_learnings_stop.py"
_spec = importlib.util.spec_from_file_location("post_learnings_stop", _HOOK_PATH)
assert _spec is not None
assert _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
sys.modules["post_learnings_stop"] = _mod
_spec.loader.exec_module(_mod)


class _BrokenStdin:
    """Stdin whose read() fails the way a closed pipe does."""

    def read(self) -> str:
        raise OSError("stdin closed")


@pytest.fixture
def pipeline_calls(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Arm the hook so that reaching the pipeline is observable.

    The stdin block is a swallow, so "did not raise" passes whether the
    hook carried on or bailed out. Recording the two posting calls turns
    the question into one the test can see. Both recorders stand in for
    network calls, which is the boundary; everything between stdin and
    them runs for real.
    """
    calls: list[str] = []
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    skills_dir = tmp_path / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "LEARNINGS.md").write_text("**Skills Analyzed**: 5\n")
    monkeypatch.setattr(_mod, "_HAS_SCRIPTS", True)
    monkeypatch.setattr(_mod, "_HAS_INSIGHT_ENGINE", False)
    monkeypatch.setattr(_mod, "_promote", lambda: calls.append("promote"))
    monkeypatch.setattr(_mod, "_post_learnings", lambda: calls.append("post"))
    return calls


class TestStdinHandling:
    """Feature: Hook protocol stdin consumption

    As a Stop hook
    I want to safely consume and parse JSON from stdin
    So that malformed input never crashes the session.
    """

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "stdin",
        [
            io.StringIO('{"event": "stop"}'),
            io.StringIO("{not valid json!!!"),
            io.StringIO(""),
            _BrokenStdin(),
        ],
        ids=["valid-json", "malformed-json", "empty", "closed-pipe"],
    )
    def test_stdin_shape_does_not_stop_the_pipeline(
        self,
        stdin: object,
        pipeline_calls: list[str],
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,
    ) -> None:
        """Given: stdin in any of the four shapes a Stop hook may receive
        When: main() runs with the posting pipeline armed
        Then: promote and post-learnings both run, in that order

        The point of swallowing a stdin error is that the rest of the
        hook still happens. Asserting only that nothing raised would
        also pass if the hook returned at the first sign of trouble,
        which is the regression worth catching.
        """
        monkeypatch.setattr("sys.stdin", stdin)

        assert _mod.main() is None

        assert pipeline_calls == ["promote", "post"]
        assert capsys.readouterr().err == ""

    @pytest.mark.unit
    def test_missing_scripts_skips_the_pipeline(
        self, pipeline_calls: list[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Given: the posting scripts failed to import
        When: main() runs on well-formed stdin
        Then: neither posting call is made

        The negative half of the test above: it fails if the pipeline
        runs unconditionally rather than because stdin was handled.
        """
        monkeypatch.setattr("sys.stdin", io.StringIO('{"event": "stop"}'))
        monkeypatch.setattr(_mod, "_HAS_SCRIPTS", False)

        assert _mod.main() is None

        assert pipeline_calls == []


class TestLearningsContentCheck:
    """Feature: Skip posting when no content exists

    As a Stop hook
    I want to skip posting when LEARNINGS.md is empty
    So that empty summaries are not created.
    """

    @pytest.mark.unit
    def test_skips_when_no_learnings_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: LEARNINGS.md does not exist
        Given no LEARNINGS.md file
        When _learnings_have_content() is called
        Then it returns False.
        """
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        assert _mod._learnings_have_content() is False

    @pytest.mark.unit
    def test_skips_when_learnings_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: LEARNINGS.md has zero skills analyzed
        Given LEARNINGS.md with "Skills Analyzed: 0"
        When _learnings_have_content() is called
        Then it returns False.
        """
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        skills_dir = tmp_path / ".claude" / "skills"
        skills_dir.mkdir(parents=True)
        (skills_dir / "LEARNINGS.md").write_text("**Skills Analyzed**: 0\n")
        assert _mod._learnings_have_content() is False

    @pytest.mark.unit
    def test_detects_content(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: LEARNINGS.md has real content
        Given LEARNINGS.md with analyzed skills
        When _learnings_have_content() is called
        Then it returns True.
        """
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        skills_dir = tmp_path / ".claude" / "skills"
        skills_dir.mkdir(parents=True)
        (skills_dir / "LEARNINGS.md").write_text(
            "**Skills Analyzed**: 5\n\n## Findings\n..."
        )
        assert _mod._learnings_have_content() is True
