"""Python wrapper for the ``leyline:git-platform`` skill (AR-30).

Routes plugin-side ``gh`` invocations through one tested shim.
Current callers: ``verify_plugin.py``, ``post_learnings_to_discussions.py``,
``promote_discussion_to_issue.py``, and ``sanitize_external_content``
tests. See ``docs/refinement/2026-05-02/00-synthesis.md`` AR-30 for
the migration log; additional call sites adopt this wrapper as the
hand-rolled ``argv`` lists are touched.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 - sole purpose of this module is to wrap gh
from typing import Any

DEFAULT_TIMEOUT_SECONDS = 30


class GhCommandError(RuntimeError):
    """Raised when a ``gh`` invocation fails or returns non-JSON.

    Attributes:
        cmd: The argv list passed to ``subprocess.run``. Useful for
            log correlation and debugging without re-deriving the
            command from a free-text message.
        returncode: The subprocess exit code, or ``None`` when the
            failure was a parse error on a successful exit.
        stderr: The captured stderr (stripped) when the failure was a
            non-zero exit, or ``None`` for parse-error cases.
    """

    def __init__(
        self,
        message: str,
        *,
        cmd: list[str],
        returncode: int | None = None,
        stderr: str | None = None,
    ) -> None:
        super().__init__(message)
        self.cmd = list(cmd)
        self.returncode = returncode
        self.stderr = stderr


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
    method_upper = method.upper()
    if method_upper != "GET":
        cmd.extend(["-X", method_upper])
    for key, value in (fields or {}).items():
        if "=" in key:
            msg = (
                f"gh_api field key {key!r} contains '='; this would "
                f"smuggle extra fields into the gh argv. Use a "
                f"different key or quote the value side."
            )
            raise ValueError(msg)
        cmd.extend(["-f", f"{key}={value}"])
    return _run_and_parse(cmd, timeout=timeout)


def gh_graphql(
    query: str,
    variables: dict[str, Any] | None = None,
    *,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> Any:
    """Call ``gh api graphql -f query=<query>`` and return parsed JSON.

    Args:
        query: GraphQL query / mutation string.
        variables: Optional GraphQL variable values keyed by name.
            Strings are passed via ``gh``'s raw-field flag (``-f``).
            ``int`` / ``float`` / ``bool`` / ``None`` are rendered to
            JSON-compatible strings (``42`` / ``true`` / ``null``)
            and passed via the typed-field flag (``-F``) so ``gh``
            forwards them as JSON ``Int`` / ``Boolean`` / ``null`` to
            satisfy non-String GraphQL variable types. Other types
            are rejected with ``TypeError``.
        timeout: Subprocess timeout in seconds.

    Raises:
        GhCommandError: If gh exits non-zero or stdout is not JSON.
        TypeError: If a variable value is not str/int/float/bool/None.
    """
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in (variables or {}).items():
        flag, rendered = _render_graphql_variable(key, value)
        cmd.extend([flag, f"{key}={rendered}"])
    return _run_and_parse(cmd, timeout=timeout)


def _render_graphql_variable(key: str, value: Any) -> tuple[str, str]:
    """Map a Python value to ``(gh-flag, string-payload)``.

    Strings stay as raw ``-f`` (no type coercion). Numbers, booleans,
    and ``None`` go through ``-F`` with a JSON-compatible repr so
    ``gh`` decodes them as the matching JSON type. Booleans must be
    checked before ``int`` because ``bool`` is a subclass of ``int``
    in Python.
    """
    if isinstance(value, str):
        return ("-f", value)
    if isinstance(value, bool):
        return ("-F", "true" if value else "false")
    if value is None:
        return ("-F", "null")
    if isinstance(value, (int, float)):
        return ("-F", json.dumps(value))
    msg = (
        f"gh_graphql variable {key!r}: unsupported type "
        f"{type(value).__name__}; pass str/int/float/bool/None"
    )
    raise TypeError(msg)


def _run_and_parse(cmd: list[str], *, timeout: int) -> Any:
    result = subprocess.run(  # nosec B603 - argv built from typed params
        cmd,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise GhCommandError(
            f"{' '.join(cmd[:3])} failed (exit {result.returncode}): {stderr}",
            cmd=cmd,
            returncode=result.returncode,
            stderr=stderr,
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise GhCommandError(
            f"{' '.join(cmd[:3])} returned non-JSON: {result.stdout[:200]}",
            cmd=cmd,
            returncode=None,
            stderr=None,
        ) from exc
