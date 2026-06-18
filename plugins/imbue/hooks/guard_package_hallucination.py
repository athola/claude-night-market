#!/usr/bin/env python3
"""Guard: package hallucination / slopsquatting (PreToolUse on Bash).

Intercepts dependency-install commands (pip, uv, npm, pnpm, yarn,
cargo, poetry, pdm) and checks each package the command would fetch
against two signals:

  - typosquat / slopsquat: the name is one or two edits from a popular
    package (deterministic, offline);
  - nonexistent: the name is absent from its registry (network lookup,
    only for names not already known-popular).

LLM-suggested packages are hallucinated 5.2-21.7% of the time
(Spracklen et al. 2024) and 58% of fabricated names recur, so they are
predictable supply-chain attack targets. This guard turns "the agent
suggested it, so I installed it" into "the name was verified to exist".

Shadow mode is ON by default (warn only). Set VOW_SHADOW_MODE=0 to
block typosquat/nonexistent installs. Registry network checks can be
disabled with IMBUE_PKG_REGISTRY_CHECK=0; the guard never blocks on a
network failure (those are reported as 'unverified', warn-only).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from shared.package_guard import (  # noqa: E402 - hook injects sys.path before importing sibling shared/ module
    assess_packages,
)
from shared.vow_utils import (  # noqa: E402 - same path-injection pattern as sibling vow hooks
    shadow_mode_active,
)

_REGISTRY_URLS = {
    "pypi": "https://pypi.org/pypi/{name}/json",
    "npm": "https://registry.npmjs.org/{name}",
    "crates": "https://crates.io/api/v1/crates/{name}",
}
_REGISTRY_TIMEOUT = 1.5
_HTTP_OK_MIN = 200
_HTTP_OK_MAX = 300
_HTTP_NOT_FOUND = 404


def _registry_url(name: str, ecosystem: str) -> str | None:
    """Build the https registry URL for a package, or None if not checkable.

    Returns None when network checks are disabled, the ecosystem is
    unknown, or the resulting URL is not https (defensive scheme guard
    that also closes the S310 audit concern).
    """
    if os.environ.get("IMBUE_PKG_REGISTRY_CHECK", "1").strip() in ("0", "false", "no"):
        return None
    url_template = _REGISTRY_URLS.get(ecosystem)
    if url_template is None:
        return None
    url = url_template.format(name=urllib.parse.quote(name, safe=""))
    return url if url.startswith("https://") else None


def _registry_exists(name: str, ecosystem: str) -> bool | None:
    """Return True/False if the registry confirms/denies a package, else None.

    None means the lookup could not be completed (disabled, offline,
    timeout, rate limit). The caller treats None as 'unverified', never
    as a block.
    """
    url = _registry_url(name, ecosystem)
    if url is None:
        return None
    request = urllib.request.Request(  # noqa: S310 - https-only registry hosts, scheme guarded in _registry_url
        url, headers={"User-Agent": "imbue-pkg-guard"}
    )
    try:
        with urllib.request.urlopen(request, timeout=_REGISTRY_TIMEOUT) as response:  # noqa: S310 - https-only registry hosts, scheme guarded in _registry_url
            return bool(_HTTP_OK_MIN <= response.status < _HTTP_OK_MAX)
    except urllib.error.HTTPError as exc:
        return False if exc.code == _HTTP_NOT_FOUND else None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None


def _format_reason(findings: list[dict[str, str]], shadow: bool) -> str:
    lines = ["Package-hallucination guard flagged install target(s):"]
    for finding in findings:
        lines.append(f"  - [{finding['kind']}] {finding['detail']}")
    if shadow:
        lines.append(
            "Shadow mode active -- this warns now and will block "
            "typosquat/nonexistent installs once VOW_SHADOW_MODE=0."
        )
    else:
        lines.append("Verify the exact package name, then re-run the install.")
    return "\n".join(lines)


def main() -> None:
    """Entry point for the PreToolUse hook."""
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        sys.exit(0)

    try:
        if data.get("tool_name", "") != "Bash":
            sys.exit(0)
        command = data.get("tool_input", {}).get("command", "")
        if not command:
            sys.exit(0)

        findings = assess_packages(command, registry_fn=_registry_exists)
        if not findings:
            sys.exit(0)

        shadow = shadow_mode_active()
        hard = [f for f in findings if f["kind"] in ("typosquat", "nonexistent")]
        # Hard findings block when blocking is enabled; unverified always warns.
        decision = "block" if (hard and not shadow) else "warn"

        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": _format_reason(findings, shadow),
            }
        }
        print(json.dumps(output))
        kinds = ",".join(sorted({f["kind"] for f in findings}))
        print(
            f"[guard-package-hallucination] {decision.upper()}: {kinds}",
            file=sys.stderr,
        )
        sys.exit(0)

    except Exception as exc:  # hook must never crash the agent
        print(f"[guard-package-hallucination] internal error: {exc}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
