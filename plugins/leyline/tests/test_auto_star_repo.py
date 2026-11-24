"""Tests for auto-star-repo.sh safety guarantees.

Feature: Opt-in star on session start (issue #1054)

    As a user who likes these plugins
    I want to tick one plugin option and have the repo starred once
    So that nothing asks me for a star, and nothing stars without my say

    CRITICAL SAFETY INVARIANTS:
    - Nothing happens unless the user set leyline's star_repo option
    - The script must NEVER unstar (no DELETE calls)
    - It stars at most once per machine: a marker stops every later run
    - The model is never told to ask for a star
    - CLAUDE_NIGHT_MARKET_NO_STAR_PROMPT=1 overrides the option
"""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
from pathlib import Path

import pytest

HOOK_PATH = Path(__file__).parent.parent / "hooks" / "auto-star-repo.sh"


@pytest.fixture
def hook_source() -> str:
    """Load the auto-star hook source code."""
    return HOOK_PATH.read_text()


def _non_comment_lines(source: str) -> list[str]:
    """Return non-comment, non-empty lines from shell source."""
    return [
        line.strip()
        for line in source.split("\n")
        if line.strip() and not line.strip().startswith("#")
    ]


def _strip_heredocs(source: str) -> str:
    """Remove heredoc blocks (<<'PROMPT' ... PROMPT) from source."""
    return re.sub(
        r"cat <<'PROMPT'.*?^PROMPT$",
        "",
        source,
        flags=re.DOTALL | re.MULTILINE,
    )


def _extract_function(source: str, name: str) -> str | None:
    """Extract a shell function body by name."""
    match = re.search(rf"{name}\(\)\s*\{{(.+?)\n\}}", source, re.DOTALL)
    return match.group(1) if match else None


class TestCheckPathNeverStars:
    """CRITICAL: The check functions must only READ status, never write."""

    @pytest.mark.unit
    def test_check_gh_has_no_put(self, hook_source: str) -> None:
        """
        GIVEN the check_gh function
        WHEN scanning for PUT operations
        THEN none exist (check_gh only reads status).
        """
        body = _extract_function(hook_source, "check_gh")
        assert body is not None, "check_gh function must exist"
        assert "-X PUT" not in body, "SAFETY: check_gh must not PUT"

    @pytest.mark.unit
    def test_check_curl_has_no_put(self, hook_source: str) -> None:
        """
        GIVEN the check_curl function
        WHEN scanning for PUT operations
        THEN none exist (check_curl only reads status).
        """
        body = _extract_function(hook_source, "check_curl")
        assert body is not None, "check_curl function must exist"
        assert "-X PUT" not in body, "SAFETY: check_curl must not PUT"

    @pytest.mark.unit
    def test_no_delete_anywhere(self, hook_source: str) -> None:
        """
        GIVEN the full hook script
        WHEN scanning for DELETE operations
        THEN none exist anywhere.
        """
        assert "-X DELETE" not in hook_source, (
            "SAFETY VIOLATION: -X DELETE found in hook"
        )


class TestStarMode:
    """Verify --star flag enables starring via gh or curl."""

    @pytest.mark.unit
    def test_star_flag_is_supported(self, hook_source: str) -> None:
        """
        GIVEN the hook script
        WHEN called with --star
        THEN it attempts to star the repo.
        """
        assert '"--star"' in hook_source, "Script must support --star flag"

    @pytest.mark.unit
    def test_do_star_gh_uses_put(self, hook_source: str) -> None:
        """
        GIVEN the do_star_gh function
        WHEN starring the repo
        THEN it uses PUT to the starred API endpoint.
        """
        body = _extract_function(hook_source, "do_star_gh")
        assert body is not None, "do_star_gh function must exist"
        assert "-X PUT" in body, "do_star_gh must PUT to star"
        assert "/user/starred/" in body, "do_star_gh must target starred API"

    @pytest.mark.unit
    def test_do_star_curl_uses_put(self, hook_source: str) -> None:
        """
        GIVEN the do_star_curl function
        WHEN starring the repo
        THEN it uses PUT with Bearer auth.
        """
        body = _extract_function(hook_source, "do_star_curl")
        assert body is not None, "do_star_curl function must exist"
        assert "-X PUT" in body, "do_star_curl must PUT to star"
        assert "Authorization: Bearer" in body, "do_star_curl must use Bearer auth"

    @pytest.mark.unit
    def test_star_mode_exits_before_check(self, hook_source: str) -> None:
        """
        GIVEN the --star code path
        WHEN starring is requested
        THEN it exits before reaching the check/prompt logic.
        """
        main = _extract_function(hook_source, "main")
        assert main is not None, "main function must exist"
        star_idx = main.find('"--star")')
        check_gh_idx = main.find("check_gh")
        assert star_idx != -1, "main must dispatch the --star arm"
        assert check_gh_idx != -1, "main must call check_gh"
        star_arm = main[star_idx : main.find(";;", star_idx)]
        assert "exit 0" in star_arm, "--star arm must exit"
        assert star_idx < check_gh_idx, "--star path must exit before check functions"


class TestTargetRepo:
    """Verify the script targets the correct repository."""

    @pytest.mark.unit
    def test_targets_athola_claude_night_market(self, hook_source: str) -> None:
        """
        GIVEN the hook script
        WHEN checking the target repo
        THEN it targets athola/claude-night-market.
        """
        assert 'OWNER="athola"' in hook_source
        assert 'REPO="claude-night-market"' in hook_source


class TestJsonOutputStructure:
    """Feature: Hook outputs valid SessionStart JSON.

    As a Claude Code hook
    I want to emit structured hookSpecificOutput JSON
    So that the harness can parse session context reliably
    """

    @pytest.mark.unit
    def test_emit_empty_helper_exists(self, hook_source: str) -> None:
        """Scenario: _emit_empty helper is defined.

        Given the hook script
        When checking for _emit_empty
        Then it exists and outputs hookSpecificOutput JSON.
        """
        assert "_emit_empty()" in hook_source, "_emit_empty helper must be defined"

    @pytest.mark.unit
    def test_emit_empty_outputs_session_start(self, hook_source: str) -> None:
        """Scenario: _emit_empty produces SessionStart event.

        Given the _emit_empty function
        When checking its output
        Then it contains hookEventName SessionStart.
        """
        body = _extract_function(hook_source, "_emit_empty")
        assert body is not None, "_emit_empty function must exist"
        assert "hookSpecificOutput" in body
        assert "SessionStart" in body

    @pytest.mark.unit
    def test_not_starred_outputs_hook_json(self, hook_source: str) -> None:
        """Scenario: not_starred branch outputs hookSpecificOutput JSON.

        Given the not_starred code path
        When examining its output
        Then it uses hookSpecificOutput JSON format.
        """
        assert "hookSpecificOutput" in hook_source

    @pytest.mark.unit
    def test_opt_out_calls_emit_empty(self, hook_source: str) -> None:
        """Scenario: Opt-out path uses _emit_empty.

        Given CLAUDE_NIGHT_MARKET_NO_STAR_PROMPT=1
        When the opt-out triggers
        Then it calls _emit_empty (not bare exit 0).
        """
        lines = hook_source.split("\n")
        checks = [
            i
            for i, line in enumerate(lines)
            # The runtime branch (case "${...}" in), not comments or usage
            if "CLAUDE_NIGHT_MARKET_NO_STAR_PROMPT" in line
            and line.strip().startswith(("if", "case"))
        ]
        assert checks, "Script must branch on CLAUDE_NIGHT_MARKET_NO_STAR_PROMPT"
        block = "\n".join(lines[checks[0] : checks[0] + 5])
        assert "_emit_empty" in block, "Opt-out path must call _emit_empty"


class TestStarPromptOptOut:
    """Verify the opt-out mechanism works."""

    @pytest.mark.unit
    def test_opt_out_env_var_exits_before_checks(self, hook_source: str) -> None:
        """
        GIVEN the hook script
        WHEN CLAUDE_NIGHT_MARKET_NO_STAR_PROMPT=1 is set
        THEN the script exits before the check_gh/check_curl calls.

        Note: opt-out is after the --star path intentionally,
        since --star is only called after explicit user consent.
        """
        main = _extract_function(hook_source, "main")
        assert main is not None, "main function must exist"
        opt_out_idx = main.find("CLAUDE_NIGHT_MARKET_NO_STAR_PROMPT")
        check_gh_idx = main.find("check_gh")
        assert opt_out_idx != -1, "Script must check CLAUDE_NIGHT_MARKET_NO_STAR_PROMPT"
        assert check_gh_idx != -1, "main must call check_gh"
        assert opt_out_idx < check_gh_idx, "Opt-out must come before check functions"


class TestStatusChecks:
    """Verify both code paths check status correctly."""

    @pytest.mark.unit
    def test_gh_path_checks_status(self, hook_source: str) -> None:
        """
        GIVEN the check_gh function
        WHEN examining its logic
        THEN it detects both starred and not-starred states.
        """
        body = _extract_function(hook_source, "check_gh")
        assert body is not None, "check_gh function must exist"
        assert "/user/starred/" in body
        assert '"204"' in body, "check_gh must detect starred (204)"
        assert '"404"' in body, "check_gh must detect not starred (404)"

    @pytest.mark.unit
    def test_curl_path_checks_status(self, hook_source: str) -> None:
        """
        GIVEN the check_curl function
        WHEN examining its logic
        THEN it detects both starred and not-starred states.
        """
        body = _extract_function(hook_source, "check_curl")
        assert body is not None, "check_curl function must exist"
        assert "http_code" in body
        assert '"204"' in body, "check_curl must detect starred (204)"
        assert '"404"' in body, "check_curl must detect not starred (404)"


class TestCurlFallback:
    """Verify curl fallback is properly implemented."""

    @pytest.mark.unit
    def test_curl_checks_availability(self, hook_source: str) -> None:
        assert "command -v curl" in hook_source

    @pytest.mark.unit
    def test_curl_requires_token(self, hook_source: str) -> None:
        assert "GITHUB_TOKEN" in hook_source
        assert "GH_TOKEN" in hook_source

    @pytest.mark.unit
    def test_curl_uses_bearer_auth(self, hook_source: str) -> None:
        assert "Authorization: Bearer" in hook_source

    @pytest.mark.unit
    def test_gh_tried_before_curl(self, hook_source: str) -> None:
        main_section = hook_source[hook_source.rfind("# --- Main") :]
        gh_pos = main_section.find("check_gh")
        curl_pos = main_section.find("check_curl")
        assert gh_pos < curl_pos


class TestFailSafety:
    """Verify the script fails silently on errors."""

    @pytest.mark.unit
    def test_gh_guard_checks_cli(self, hook_source: str) -> None:
        assert "command -v gh" in hook_source

    @pytest.mark.unit
    def test_gh_guard_checks_auth(self, hook_source: str) -> None:
        assert "gh auth status" in hook_source

    @pytest.mark.unit
    def test_main_flow_handles_all_failures(self, hook_source: str) -> None:
        assert "exit 0" in hook_source

    @pytest.mark.unit
    def test_script_is_executable(self) -> None:
        mode = os.stat(HOOK_PATH).st_mode
        assert mode & stat.S_IXUSR

    @pytest.mark.unit
    def test_script_has_bash_shebang(self, hook_source: str) -> None:
        assert hook_source.startswith("#!/usr/bin/env bash")

    @pytest.mark.unit
    def test_script_uses_strict_mode(self, hook_source: str) -> None:
        assert "set -euo pipefail" in hook_source


class TestXtraceKeepsTheTokenOut:
    """`-x` traces the script, and the curl calls carry a bearer token.

    Both curl paths run with the caller's stderr sent to /dev/null, which
    hides a trace on stderr but not one BASH_XTRACEFD sends elsewhere, and
    not curl's argv from ps. So the token never lands in a traced word or
    in argv: it reaches curl on stdin (#1305).
    """

    @pytest.mark.unit
    @pytest.mark.parametrize("args", [["-x"], ["-x", "--star"]])
    def test_trace_never_prints_the_token(
        self, tmp_path: Path, args: list[str]
    ) -> None:
        import subprocess  # noqa: PLC0415 - only this class runs the script

        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        fake_curl = bin_dir / "curl"
        fake_curl.write_text("#!/bin/sh\nprintf 404\n")
        fake_curl.chmod(0o755)
        env = {
            "HOME": str(tmp_path),
            "PATH": f"{bin_dir}:/usr/bin:/bin",
            "GH_TOKEN": "sekrit-token-123",
            # Opted in, so the check path reaches curl with the token.
            "CLAUDE_PLUGIN_OPTION_STAR_REPO": "true",
            "XDG_STATE_HOME": str(tmp_path / "state"),
        }

        run = subprocess.run(
            ["bash", str(HOOK_PATH), *args],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        assert "+ " in run.stderr, "xtrace did not run"
        assert "sekrit-token-123" not in run.stderr
        assert "sekrit-token-123" not in run.stdout

    @staticmethod
    def _run_recording_curl(
        tmp_path: Path,
        args: list[str],
        extra_env: dict[str, str],
        pass_fds: tuple[int, ...] = (),
    ) -> subprocess.CompletedProcess[str]:
        """Run the hook with a curl that records its argv and stdin."""
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        (bin_dir / "gh").write_text("#!/bin/sh\nexit 1\n")
        (bin_dir / "curl").write_text(
            "#!/bin/sh\n"
            f"printf '%s\\n' \"$@\" >>'{tmp_path}/curl.argv'\n"
            f"cat >>'{tmp_path}/curl.stdin'\n"
            "printf 404\n"
        )
        for shim in bin_dir.iterdir():
            shim.chmod(0o755)
        env = {
            "HOME": str(tmp_path),
            "PATH": f"{bin_dir}:/usr/bin:/bin",
            "GH_TOKEN": "sekrit-token-123",
            "CLAUDE_PLUGIN_OPTION_STAR_REPO": "true",
            "XDG_STATE_HOME": str(tmp_path / "state"),
            **extra_env,
        }
        return subprocess.run(
            ["bash", str(HOOK_PATH), *args],
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            pass_fds=pass_fds,
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("args", [["-x"], ["-x", "--star"]])
    def test_trace_sent_to_its_own_fd_never_prints_the_token(
        self, tmp_path: Path, args: list[str]
    ) -> None:
        """
        GIVEN BASH_XTRACEFD pointing the trace at a file, as one does to
              keep it apart from the script's output
        WHEN the hook runs with -x and a token in GH_TOKEN
        THEN the trace never holds the token: the call sites' 2>/dev/null
             does not reach a trace on another fd (#1305).
        """
        trace = tmp_path / "trace.log"
        with trace.open("w") as trace_file:
            fd = trace_file.fileno()
            self._run_recording_curl(
                tmp_path, args, {"BASH_XTRACEFD": str(fd)}, pass_fds=(fd,)
            )

        text = trace.read_text()
        assert "curl" in text, "the trace never reached a curl call"
        assert "sekrit-token-123" not in text

    @pytest.mark.unit
    def test_token_reaches_curl_on_stdin_not_in_its_argv(self, tmp_path: Path) -> None:
        """
        GIVEN a token in GH_TOKEN and gh logged out
        WHEN the hook checks and stars through curl
        THEN the Authorization header reaches curl on stdin, and the token
             is never in curl's argv, where ps shows it to every local user.
        """
        self._run_recording_curl(tmp_path, [], {})

        argv = (tmp_path / "curl.argv").read_text()
        stdin = (tmp_path / "curl.stdin").read_text()
        assert "sekrit-token-123" not in argv
        assert stdin.count("Authorization: Bearer sekrit-token-123") == 2


def _run_with_shims(
    tmp_path: Path, shims: dict[str, str], args: list[str]
) -> subprocess.CompletedProcess[str]:
    """Run the hook with *shims* (name to /bin/sh body) first on PATH.

    CLAUDE_PLUGIN_ROOT is left unset, as it is when a user runs --star
    from their own shell.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, body in shims.items():
        shim = bin_dir / name
        shim.write_text(f"#!/bin/sh\n{body}\n")
        shim.chmod(0o755)
    env = {
        "HOME": str(tmp_path),
        "PATH": f"{bin_dir}:/usr/bin:/bin",
        "GH_TOKEN": "token-without-star-scope",
    }
    return subprocess.run(
        ["bash", str(HOOK_PATH), *args],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


# A curl that answers every request with 403: like the real one, it exits
# 22 only when asked to fail on HTTP errors.
_CURL_403 = (
    'for arg in "$@"; do case "$arg" in -f|-fsS|--fail) exit 22 ;; esac; done\n'
    "printf 403\nexit 0"
)
_GH_LOGGED_OUT = "exit 1"


class TestStarFailureIsReported:
    """--star must not report success when no method starred the repo."""

    @pytest.mark.unit
    def test_star_exits_nonzero_when_every_method_fails(self, tmp_path: Path) -> None:
        """
        GIVEN gh logged out and a token the API answers with 403
        WHEN --star runs
        THEN it exits nonzero and logs an error the model can relay.
        """
        run = _run_with_shims(
            tmp_path, {"gh": _GH_LOGGED_OUT, "curl": _CURL_403}, ["--star"]
        )

        assert run.returncode != 0
        assert "[ERROR]" in run.stderr

    @pytest.mark.unit
    def test_star_exits_zero_when_the_put_succeeds(self, tmp_path: Path) -> None:
        """
        GIVEN gh logged out and a curl whose PUT succeeds
        WHEN --star runs
        THEN it exits 0.
        """
        run = _run_with_shims(
            tmp_path, {"gh": _GH_LOGGED_OUT, "curl": "exit 0"}, ["--star"]
        )

        assert run.returncode == 0, run.stderr


# gh that logs each call to $GH_CALLS. STARRED=1 answers the status check
# with 204, otherwise 404. PUT_EXIT sets how the PUT exits.
_GH_LOGGING = """echo "$*" >> "$GH_CALLS"
case "$1" in auth) exit 0 ;; esac
case "$*" in *"-X PUT"*) exit "${PUT_EXIT:-0}" ;; esac
case "${STARRED:-0}" in 1) printf 'HTTP/2.0 204 No Content\\n'; exit 0 ;; esac
printf 'HTTP/2.0 404 Not Found\\n'
exit 1"""


def _run_opt_in(
    tmp_path: Path, **extra: str
) -> tuple[subprocess.CompletedProcess[str], list[str], Path]:
    """Run the SessionStart path; return the run, gh's calls and the marker."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    gh = bin_dir / "gh"
    gh.write_text(f"#!/bin/sh\n{_GH_LOGGING}\n")
    gh.chmod(0o755)
    calls = tmp_path / "gh-calls"
    calls.write_text("")
    state = tmp_path / "state"
    env = {
        "HOME": str(tmp_path),
        "PATH": f"{bin_dir}:/usr/bin:/bin",
        "GH_CALLS": str(calls),
        "XDG_STATE_HOME": str(state),
        **extra,
    }
    run = subprocess.run(
        ["bash", str(HOOK_PATH)],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    marker = state / "claude-night-market" / "star-done"
    return run, calls.read_text().splitlines(), marker


def _output(run: subprocess.CompletedProcess[str]) -> dict[str, object]:
    assert run.returncode == 0, run.stderr
    lines = run.stdout.splitlines()
    assert len(lines) == 1, run.stdout
    parsed: dict[str, object] = json.loads(lines[0])
    return parsed


def _puts(calls: list[str]) -> list[str]:
    return [call for call in calls if "-X PUT" in call]


class TestStarIsOptIn:
    """The star_repo plugin option is the only thing that turns it on."""

    @pytest.mark.unit
    @pytest.mark.parametrize("value", [None, "", "false", "0", "no"])
    def test_without_the_option_gh_is_never_called(
        self, tmp_path: Path, value: str | None
    ) -> None:
        """
        GIVEN a user who has not starred the repo
        WHEN the option is unset or false
        THEN the hook calls nothing and adds nothing to the session.
        """
        extra = {} if value is None else {"CLAUDE_PLUGIN_OPTION_STAR_REPO": value}
        run, calls, marker = _run_opt_in(tmp_path, **extra)

        output = _output(run)
        assert calls == []
        assert not marker.exists()
        assert "systemMessage" not in output
        assert output["hookSpecificOutput"] == {
            "hookEventName": "SessionStart",
            "additionalContext": "",
        }

    @pytest.mark.unit
    @pytest.mark.parametrize("value", ["true", "TRUE", "1", "yes", "on"])
    def test_opted_in_and_not_starred_stars_once_and_tells_the_user(
        self, tmp_path: Path, value: str
    ) -> None:
        """
        GIVEN the option set and the repo not starred
        WHEN the hook runs
        THEN it stars with one PUT, leaves the marker, tells the user in a
        systemMessage, and gives the model no instruction.
        """
        run, calls, marker = _run_opt_in(tmp_path, CLAUDE_PLUGIN_OPTION_STAR_REPO=value)

        output = _output(run)
        assert _puts(calls) == [
            "api -X PUT /user/starred/athola/claude-night-market --silent"
        ]
        assert marker.exists()
        assert "athola/claude-night-market" in str(output["systemMessage"])
        assert output["hookSpecificOutput"] == {
            "hookEventName": "SessionStart",
            "additionalContext": "",
        }

    @pytest.mark.unit
    def test_a_second_session_does_nothing(self, tmp_path: Path) -> None:
        """
        GIVEN a session that already starred the repo
        WHEN the next session starts, even after the user unstarred it
        THEN the marker stops the hook before any call.
        """
        _run_opt_in(tmp_path, CLAUDE_PLUGIN_OPTION_STAR_REPO="true")
        run, calls, marker = _run_opt_in(
            tmp_path, CLAUDE_PLUGIN_OPTION_STAR_REPO="true"
        )

        output = _output(run)
        assert calls == []
        assert marker.exists()
        assert "systemMessage" not in output

    @pytest.mark.unit
    def test_already_starred_is_left_alone_and_never_checked_again(
        self, tmp_path: Path
    ) -> None:
        """
        GIVEN the option set and the repo already starred
        WHEN the hook runs
        THEN it sends no PUT, says nothing, and leaves the marker.
        """
        run, calls, marker = _run_opt_in(
            tmp_path, CLAUDE_PLUGIN_OPTION_STAR_REPO="true", STARRED="1"
        )

        output = _output(run)
        assert calls, "the status check should have run"
        assert _puts(calls) == []
        assert marker.exists()
        assert "systemMessage" not in output

    @pytest.mark.unit
    def test_a_failed_star_leaves_no_marker_so_the_next_session_retries(
        self, tmp_path: Path
    ) -> None:
        """
        GIVEN the option set and a PUT that fails
        WHEN the hook runs
        THEN it exits 0 with no message and no marker.
        """
        run, calls, marker = _run_opt_in(
            tmp_path, CLAUDE_PLUGIN_OPTION_STAR_REPO="true", PUT_EXIT="1"
        )

        output = _output(run)
        assert len(_puts(calls)) == 1
        assert not marker.exists()
        assert "systemMessage" not in output

    @pytest.mark.unit
    def test_the_env_opt_out_overrides_the_option(self, tmp_path: Path) -> None:
        """
        GIVEN the option set and CLAUDE_NIGHT_MARKET_NO_STAR_PROMPT=1
        WHEN the hook runs
        THEN the opt-out wins and nothing is called.
        """
        run, calls, marker = _run_opt_in(
            tmp_path,
            CLAUDE_PLUGIN_OPTION_STAR_REPO="true",
            CLAUDE_NIGHT_MARKET_NO_STAR_PROMPT="1",
        )

        _output(run)
        assert calls == []
        assert not marker.exists()

    @pytest.mark.unit
    def test_the_source_never_instructs_the_model(self, hook_source: str) -> None:
        """
        GIVEN the hook source
        WHEN scanning for the old prompt
        THEN no text asks the model to request a star.
        """
        assert "star-prompt:" not in hook_source
        assert "Would you like to star" not in hook_source
