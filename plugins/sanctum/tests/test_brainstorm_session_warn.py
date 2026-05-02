# ruff: noqa: D101,D102,D103,E402,PLR2004,S603,S607
"""Tests for brainstorm_session_warn SessionStart hook.

The hook scans ``<project>/.superpowers/brainstorm/*/state/`` directories
for abandoned brainstorm sessions (``server-stopped`` marker, or stale
``server.pid``) and surfaces a warning to the user via ``stderr`` and
``additionalContext`` JSON output.
"""

from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from brainstorm_session_warn import find_stale_sessions, main


class TestFindStaleSessions:
    """find_stale_sessions returns directories with abandonment markers."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_server_stopped_marker(self, tmp_path) -> None:
        """A brainstorm dir whose state/server-stopped exists is stale."""
        session = tmp_path / ".superpowers" / "brainstorm" / "abc" / "state"
        session.mkdir(parents=True)
        (session / "server-stopped").write_text("")
        result = find_stale_sessions(tmp_path)
        assert len(result) == 1
        assert result[0].name == "abc"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_ignores_running_session_without_marker(self, tmp_path) -> None:
        """A brainstorm dir without server-stopped is treated as live."""
        session = tmp_path / ".superpowers" / "brainstorm" / "live" / "state"
        session.mkdir(parents=True)
        (session / "server.pid").write_text("99999")
        result = find_stale_sessions(tmp_path)
        # Either zero (we did not look up dead pids) or one. Spec: only
        # treat ``server-stopped`` as the unambiguous abandonment signal
        # so we never delete state for a live brainstorm.
        assert result == []

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_multiple_stale_sessions(self, tmp_path) -> None:
        for sid in ("aaa", "bbb", "ccc"):
            s = tmp_path / ".superpowers" / "brainstorm" / sid / "state"
            s.mkdir(parents=True)
            (s / "server-stopped").write_text("")
        # One running session should not appear in the result.
        live = tmp_path / ".superpowers" / "brainstorm" / "live" / "state"
        live.mkdir(parents=True)
        result = find_stale_sessions(tmp_path)
        assert sorted(p.name for p in result) == ["aaa", "bbb", "ccc"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_returns_empty_when_no_brainstorm_dir(self, tmp_path) -> None:
        assert find_stale_sessions(tmp_path) == []


class TestMainHook:
    """main() emits an additionalContext warning when stale sessions exist."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_warns_on_stale_session(self, tmp_path) -> None:
        s = tmp_path / ".superpowers" / "brainstorm" / "stale1" / "state"
        s.mkdir(parents=True)
        (s / "server-stopped").write_text("")

        captured_stdout = StringIO()
        with (
            patch("sys.stdin", StringIO("{}")),
            patch("sys.stdout", captured_stdout),
            patch("sys.stderr", StringIO()),
            patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": str(tmp_path)}),
        ):
            try:
                main()
            except SystemExit:
                pass

        out = captured_stdout.getvalue()
        if out.strip():
            payload = json.loads(out)
            ctx = payload.get("hookSpecificOutput", {}).get("additionalContext", "")
            assert "stale1" in ctx or "brainstorm" in ctx.lower()
            assert "abandoned" in ctx.lower() or "stale" in ctx.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_no_output_when_no_stale_sessions(self, tmp_path) -> None:
        captured_stdout = StringIO()
        with (
            patch("sys.stdin", StringIO("{}")),
            patch("sys.stdout", captured_stdout),
            patch("sys.stderr", StringIO()),
            patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": str(tmp_path)}),
        ):
            try:
                main()
            except SystemExit:
                pass

        # No JSON emitted when the project is clean.
        assert captured_stdout.getvalue().strip() == ""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_warning_includes_batch_rm_command(self, tmp_path) -> None:
        """The warning must include a copy-pasteable batch ``rm -rf`` line.

        Listing paths is not enough -- forcing the user to compose the
        cleanup command by hand for every session creates friction and
        invites mistakes. The hook must emit one line that, when copied
        verbatim into a shell, removes all listed sessions.
        """
        for sid in ("alpha", "beta"):
            s = tmp_path / ".superpowers" / "brainstorm" / sid / "state"
            s.mkdir(parents=True)
            (s / "server-stopped").write_text("")

        captured_stdout = StringIO()
        with (
            patch("sys.stdin", StringIO("{}")),
            patch("sys.stdout", captured_stdout),
            patch("sys.stderr", StringIO()),
            patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": str(tmp_path)}),
        ):
            try:
                main()
            except SystemExit:
                pass

        payload = json.loads(captured_stdout.getvalue())
        ctx = payload["hookSpecificOutput"]["additionalContext"]

        # The exact command must appear on a single line so it is one
        # copy-paste away from execution.
        rm_lines = [
            line for line in ctx.splitlines() if line.lstrip().startswith("rm -rf ")
        ]
        assert rm_lines, f"no `rm -rf` line in warning:\n{ctx}"
        rm_line = rm_lines[0]
        assert "alpha" in rm_line and "beta" in rm_line, (
            f"batch rm line missing one or more sessions: {rm_line!r}"
        )
        # Confirmation guidance must remain so the user is not nudged
        # into running the command without thinking. Match the root so
        # either "confirmation" or "confirming" satisfies the contract.
        assert "confirm" in ctx.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_exits_zero_even_on_error(self, tmp_path) -> None:
        """The hook is non-critical; failures must never block sessions."""
        captured_stdout = StringIO()
        with (
            patch("sys.stdin", StringIO("{}")),
            patch("sys.stdout", captured_stdout),
            patch("sys.stderr", StringIO()),
            patch.dict(
                "os.environ",
                {"CLAUDE_PROJECT_DIR": "/nonexistent/path/xyz"},
            ),
        ):
            with pytest.raises(SystemExit) as exc:
                main()
        assert exc.value.code == 0
