"""Leyline SessionStart hooks on inputs their happy path never saw.

Shell review S2-16 and S1-1. detect-git-platform matched "github." anywhere
in the remote URL, so a GitLab repo named alice.github.io was reported as
GitHub. auto-star-repo built its prompt with jq and, on a machine without
jq, exited 127 with empty stdout instead of emitting the hook JSON.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[2] / "hooks"


def _clean_env(**extra: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.pop("CLAUDE_NIGHT_MARKET_NO_STAR_PROMPT", None)
    env.update(extra)
    return env


def _context(stdout: str) -> str:
    return json.loads(stdout)["hookSpecificOutput"]["additionalContext"]


@pytest.mark.parametrize(
    ("remote", "platform"),
    [
        ("https://gitlab.com/alice/alice.github.io.git", "gitlab"),
        ("git@gitlab.example.com:team/github-mirror.git", "gitlab"),
        ("https://github.com/alice/gitlab-tools.git", "github"),
        ("git@github.com:alice/repo.git", "github"),
        ("ssh://git@bitbucket.org/team/github.io-site.git", "bitbucket"),
    ],
)
def test_platform_comes_from_the_host_not_the_path(
    tmp_path: Path, remote: str, platform: str
) -> None:
    env = _clean_env(HOME=str(tmp_path))
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, env=env, check=True)
    subprocess.run(
        ["git", "remote", "add", "origin", remote], cwd=tmp_path, env=env, check=True
    )
    result = subprocess.run(
        ["/bin/bash", str(HOOKS / "detect-git-platform.sh")],
        cwd=tmp_path,
        env=env,
        input="",
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert _context(result.stdout).startswith(f"git_platform: {platform},")


def test_star_prompt_is_emitted_without_jq(tmp_path: Path) -> None:
    """The unstarred path must still print hook JSON when jq is absent."""
    shims = tmp_path / "bin"
    shims.mkdir()
    for tool in ("head", "grep"):
        (shims / tool).symlink_to(f"/usr/bin/{tool}")
    gh = shims / "gh"
    gh.write_text(
        "#!/bin/sh\n"
        'case "$1" in\n'
        "  auth) exit 0 ;;\n"
        "  api) printf 'HTTP/2.0 404 Not Found\\n'; exit 1 ;;\n"
        "esac\n"
    )
    gh.chmod(0o755)
    result = subprocess.run(
        ["/bin/bash", str(HOOKS / "auto-star-repo.sh")],
        env=_clean_env(PATH=f"{shims}:/bin", HOME=str(tmp_path)),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    context = _context(result.stdout)
    assert context.startswith("star-prompt:")
    assert '"Would you like to star' in context
