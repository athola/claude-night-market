"""Python wrapper for the ``leyline:git-platform`` skill (AR-30).

Routes plugin-side ``gh`` invocations through one tested shim
so the seven sites listed in the synthesis (verify_plugin,
notify, promote_discussion_to_issue, post_learnings_to_discussions,
auto_promote_learnings, ...) no longer hand-build argv lists.

Future GitLab/Bitbucket support gains a single switching point
at ``gh_api`` / ``gh_graphql``.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 - sole purpose of this module is to wrap gh
from typing import Any

DEFAULT_TIMEOUT_SECONDS = 30


class GhCommandError(RuntimeError):
    """Raised when a ``gh`` invocation fails or returns non-JSON."""


def gh_api(
    endpoint: str,
    *,
    method: str = "GET",
    fields: dict[str, str] | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> Any:
    """Call ``gh api <endpoint>`` and return the parsed JSON body.

    Args:
        endpoint: REST endpoint (e.g. ``repos/foo/bar/issues``).
        method: HTTP method; passed via ``-X`` when not GET.
        fields: Optional ``-f key=value`` field pairs.
        timeout: Subprocess timeout in seconds.

    Raises:
        GhCommandError: If gh exits non-zero or stdout is not JSON.
    """
    cmd = ["gh", "api", endpoint]
    if method.upper() != "GET":
        cmd.extend(["-X", method.upper()])
    if fields:
        for key, value in fields.items():
            cmd.extend(["-f", f"{key}={value}"])
    return _run_and_parse(cmd, timeout=timeout)


def gh_graphql(
    query: str,
    variables: dict[str, str] | None = None,
    *,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> Any:
    """Call ``gh api graphql -f query=<query>`` and return parsed JSON.

    Args:
        query: GraphQL query / mutation string.
        variables: Optional ``-f key=value`` variable pairs that
            ``gh`` substitutes into the query.
        timeout: Subprocess timeout in seconds.

    Raises:
        GhCommandError: If gh exits non-zero or stdout is not JSON.
    """
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    if variables:
        for key, value in variables.items():
            cmd.extend(["-f", f"{key}={value}"])
    return _run_and_parse(cmd, timeout=timeout)


def _run_and_parse(cmd: list[str], *, timeout: int) -> Any:
    result = subprocess.run(  # nosec B603 - argv built from typed params
        cmd,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise GhCommandError(
            f"{' '.join(cmd[:3])} failed (exit {result.returncode}): "
            f"{result.stderr.strip()}",
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise GhCommandError(
            f"{' '.join(cmd[:3])} returned non-JSON: {result.stdout[:200]}",
        ) from exc
