# ruff: noqa: D101,D102,D103,E402,PLR2004,S603,S607
"""Tests for brainstorm_session_warn SessionStart hook.

The hook scans ``<project>/.superpowers/brainstorm/*/state/`` directories
for abandoned brainstorm sessions (``server-stopped`` marker, or stale
``server.pid``) and surfaces a warning to the user via ``stderr`` and
``additionalContext`` JSON output.
"""

from __future__ import annotations

import json
import os
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from brainstorm_session_warn import _format_warning, find_stale_sessions, main


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
        # Hook MUST emit additionalContext when a stale session exists;
        # an empty stdout is a regression. C5 (PR #470 review) flagged
        # the prior `if out.strip():` guard as vacuous-pass.
        assert out.strip(), "main() must produce additionalContext on stale sessions"
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

        Listing paths is not enough: forcing the user to compose the
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


class TestErrorPaths:
    """The hook never blocks session start, and says why when it gives up."""

    @staticmethod
    def _run_main(stdin, project_dir: Path) -> tuple[int, str, str]:
        out, err = StringIO(), StringIO()
        with (
            patch("sys.stdin", stdin),
            patch("sys.stdout", out),
            patch("sys.stderr", err),
            patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": str(project_dir)}),
            pytest.raises(SystemExit) as exc,
        ):
            main()
        return exc.value.code, out.getvalue(), err.getvalue()

    @pytest.mark.unit
    def test_a_stray_file_beside_the_sessions_is_not_a_session(self, tmp_path) -> None:
        """GIVEN a plain file next to a stale session directory
        WHEN sessions are scanned
        THEN only the directory is reported.
        """
        root = tmp_path / ".superpowers" / "brainstorm"
        (root / "s1" / "state").mkdir(parents=True)
        (root / "s1" / "state" / "server-stopped").write_text("")
        (root / "notes.txt").write_text("not a session")

        assert find_stale_sessions(tmp_path) == [root / "s1"]

    @pytest.mark.unit
    def test_unreadable_stdin_exits_zero_with_a_breadcrumb(self, tmp_path) -> None:
        """GIVEN stdin that raises on read
        WHEN the hook runs
        THEN it exits 0, prints nothing to stdout, and names the cause on stderr.
        """

        class BrokenStdin:
            def read(self) -> str:
                raise OSError("bad fd")

        code, out, err = self._run_main(BrokenStdin(), tmp_path)

        assert code == 0
        assert out == ""
        assert "stdin read failed (bad fd)" in err

    @pytest.mark.unit
    @pytest.mark.skipif(
        hasattr(os, "geteuid") and os.geteuid() == 0,
        reason="root reads a mode-000 directory, so the scan cannot fail",
    )
    def test_unreadable_brainstorm_dir_exits_zero_with_a_breadcrumb(
        self, tmp_path
    ) -> None:
        """GIVEN a brainstorm directory the scan cannot list
        WHEN the hook runs
        THEN it exits 0, prints nothing to stdout, and reports the scan failure.
        """
        root = tmp_path / ".superpowers" / "brainstorm"
        root.mkdir(parents=True)
        root.chmod(0o000)
        try:
            code, out, err = self._run_main(StringIO("{}"), tmp_path)
        finally:
            root.chmod(0o755)

        assert code == 0
        assert out == ""
        assert "brainstorm_session_warn: scan failed" in err

    @pytest.mark.unit
    def test_session_outside_the_project_is_listed_by_absolute_path(
        self, tmp_path
    ) -> None:
        """GIVEN a stale session that is not under the project directory
        WHEN the warning is formatted
        THEN the bullet and the rm line carry its absolute path.
        """
        elsewhere = tmp_path / "elsewhere" / "s9"
        warning = _format_warning([elsewhere], tmp_path / "project")

        assert f"- `{elsewhere}`" in warning
        assert f"rm -rf {elsewhere}" in warning
