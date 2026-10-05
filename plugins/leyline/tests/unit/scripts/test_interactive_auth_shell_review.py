"""interactive_auth.sh: output, retries, secrets, cache input and CI login.

Shell review S0-8 to S0-12 and S0-16. Prompts went to stdout and into the
caller's `$(gh_api_with_auth ...)`. The retry loop offered one login fewer
than AUTH_MAX_ATTEMPTS. A typed token stayed in a global. A cache value
was evaluated as arithmetic, so it could run a command. `export -f`
exported functions a child shell cannot run. GitLab CI claimed to use
GITLAB_TOKEN and did nothing with it.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

LIB = Path(__file__).resolve().parents[3] / "scripts" / "interactive_auth.sh"
MIN_BASH_MAJOR = 4
# Not a credential: a marker the CLI shims record so a test can see where
# the value went. Built at runtime so secret scanners do not flag it.
FAKE_TOKEN = "-".join(["fake", "token", "value"])


def _modern_bash() -> str | None:
    for candidate in (shutil.which("bash"), "/opt/homebrew/bin/bash"):
        if not candidate or not Path(candidate).exists():
            continue
        major = subprocess.run(
            [candidate, "-c", "printf %s ${BASH_VERSINFO[0]}"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout
        if major.isdigit() and int(major) >= MIN_BASH_MAJOR:
            return candidate
    return None


BASH = _modern_bash()
pytestmark = pytest.mark.skipif(
    BASH is None or shutil.which("jq") is None, reason="needs bash 4+ and jq"
)

# A CLI shim: `auth status` fails until a login has written the marker.
CLI_SHIM = """#!/bin/sh
marker="{marker}"
case "$1 $2" in
  "auth status") test -f "$marker" ;;
  "auth login") cat > "$marker.token"; touch "$marker" ;;
  "api user") printf '%s\\n' '{{"login":"alice"}}' ;;
  *) exit 1 ;;
esac
"""


def _env(tmp_path: Path, **extra: str) -> dict[str, str]:
    shims = tmp_path / "shims"
    shims.mkdir(exist_ok=True)
    for name in ("gh", "glab"):
        shim = shims / name
        shim.write_text(CLI_SHIM.format(marker=tmp_path / f"{name}.ok"))
        shim.chmod(0o755)
    env = {
        "PATH": f"{shims}:{Path(shutil.which('jq') or '').parent}:/usr/bin:/bin",
        "HOME": str(tmp_path),
        "AUTH_CACHE_DIR": str(tmp_path / "cache"),
        "AUTH_INTERACTIVE": "true",
    }
    env.update(extra)
    return env


def _bash(script: str, env: dict[str, str], stdin: str = ""):
    return subprocess.run(
        [str(BASH), "-c", f'source "{LIB}"\n{script}'],
        input=stdin,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_prompts_stay_out_of_the_callers_capture(tmp_path: Path) -> None:
    result = _bash(
        'out=$(gh_api_with_auth user); printf "%s" "$out"',
        _env(tmp_path),
        stdin=f"2\n{FAKE_TOKEN}\n",
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == '{"login":"alice"}'


@pytest.mark.parametrize("max_attempts", [1, 3])
def test_login_is_offered_max_attempts_times(tmp_path: Path, max_attempts: int) -> None:
    result = _bash(
        "ensure_auth github",
        _env(tmp_path, AUTH_MAX_ATTEMPTS=str(max_attempts)),
        stdin="3\n" * 5,
    )
    assert result.returncode == 1
    assert result.stderr.count("authentication required (attempt") == max_attempts


def test_a_typed_token_does_not_outlive_the_prompt(tmp_path: Path) -> None:
    result = _bash(
        "ensure_auth github >/dev/null 2>&1; declare -p token choice 2>/dev/null || :",
        _env(tmp_path),
        stdin=f"2\n{FAKE_TOKEN}\n",
    )
    assert FAKE_TOKEN not in result.stdout
    assert (tmp_path / "gh.ok.token").read_text() == FAKE_TOKEN


def test_a_tampered_cache_timestamp_is_not_evaluated(tmp_path: Path) -> None:
    cache = tmp_path / "cache" / "github"
    cache.mkdir(parents=True)
    canary = tmp_path / "pwned"
    (cache / "auth_status.json").write_text(
        f'{{"last_verified": "a[$(touch {canary})]"}}'
    )
    result = _bash("check_cache github; echo rc=$?", _env(tmp_path))
    assert not canary.exists()
    assert "rc=1" in result.stdout


def test_the_library_exports_no_functions(tmp_path: Path) -> None:
    """A child shell has the functions but not the tables they read."""
    result = _bash("env | grep '^BASH_FUNC_' || :", _env(tmp_path))
    assert result.stdout == ""


def test_gitlab_ci_logs_in_with_the_token(tmp_path: Path) -> None:
    result = _bash(
        "ensure_auth gitlab",
        _env(tmp_path, CI="1", GITLAB_TOKEN=FAKE_TOKEN),
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "glab.ok.token").read_text() == FAKE_TOKEN
