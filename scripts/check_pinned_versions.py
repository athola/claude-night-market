#!/usr/bin/env python3
"""Pre-commit check: flag when GitHub-sourced tooling pins lag upstream.

Companion to ``check_ruff_version.py`` (which covers the PyPI-sourced,
uv-managed ruff). This hook covers the other half of our pinned tooling:

* CI action pins -- ``uses: owner/repo@ref`` in ``.github/workflows/*``
* Pre-commit hook pins -- external ``rev:`` pins in
  ``.pre-commit-config.yaml`` (e.g. pre-commit-hooks, bandit)

For each pin it asks GitHub for the latest release tag and compares at the
*granularity of the pin*: a major-only pin like ``@v4`` is flagged only
when a newer major exists; an exact pin like ``v6.0.0`` is flagged on any
newer release. This avoids false positives on actions that pin to a
floating major tag.

Blocking by design (``OUTDATED_IS_BLOCKING = True``): a confirmed
behind-upstream pin exits 1 so the bump happens before the commit lands.
But it never blocks on *inability* to check -- offline, rate-limited, or
unparseable responses skip cleanly (exit 0). A flaky network must never
wedge a commit.

Runs only when ``.pre-commit-config.yaml`` or a workflow file is staged
(see the hook's ``files:`` filter), so ordinary commits pay no network
cost.

Exit codes:
    0 - all current, or advisory mode, or nothing resolvable (offline)
    1 - blocking mode and at least one pin is confirmed behind upstream
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

PRECOMMIT_CONFIG = ".pre-commit-config.yaml"
WORKFLOWS_DIR = ".github/workflows"
OUTDATED_IS_BLOCKING = True

# uses: owner/repo[/subpath]@ref  -- skip ./local and docker:// actions.
_USES_RE = re.compile(
    r"""uses:\s*['"]?
        (?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)   # owner/repo
        (?:/[\w./-]+)?                          # optional subpath (ignored)
        @(?P<ref>[\w.-]+)""",
    re.VERBOSE,
)
# Pre-commit external GitHub repo followed by its rev pin.
_REPO_RE = re.compile(
    r"-\s*repo:\s*https://github\.com/(?P<repo>[\w.-]+/[\w.-]+?)(?:\.git)?\s*$"
)
_REV_RE = re.compile(r"^\s*rev:\s*['\"]?(?P<rev>[\w.-]+)")


def precommit_pins(text: str) -> list[tuple[str, str]]:
    """Return (owner/repo, rev) for each external GitHub repo in config text."""
    pins: list[tuple[str, str]] = []
    pending: str | None = None
    for line in text.splitlines():
        repo_match = _REPO_RE.search(line)
        if repo_match:
            pending = repo_match.group("repo")
            continue
        if pending:
            rev_match = _REV_RE.match(line)
            if rev_match:
                pins.append((pending, rev_match.group("rev")))
                pending = None
    return pins


def workflow_action_pins(text: str) -> list[tuple[str, str]]:
    """Return unique (owner/repo, ref) action pins from workflow text.

    Subpaths (``owner/repo/sub@ref``) collapse to ``owner/repo``; local
    (``./``) and ``docker://`` actions are skipped by the regex.
    """
    pins: list[tuple[str, str]] = []
    for match in _USES_RE.finditer(text):
        pin = (
            f"{match.group('owner')}/{match.group('repo')}",
            match.group("ref"),
        )
        if pin not in pins:
            pins.append(pin)
    return pins


def _as_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", version))


# A commit SHA pin (uses: owner/repo@0a1b2c3...), the GitHub-recommended
# secure form: 7-40 hex chars with no dotted version structure. These are
# not comparable as versions, so is_behind() must skip them rather than
# read their leading hex run as a major number.
_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


def _is_sha(ref: str) -> bool:
    return "." not in ref and bool(_SHA_RE.fullmatch(ref))


def is_behind(pinned: str, latest: str) -> bool:
    """True when ``latest`` exceeds ``pinned`` at the pin's granularity.

    The latest version is truncated to the number of numeric components in
    the pin, so ``@v4`` compares major-only while ``v6.0.0`` compares the
    full triple. SHA-pinned refs are never "behind": a commit SHA is not a
    version, so it is skipped rather than mis-parsed as one.
    """
    if _is_sha(pinned):
        return False
    pinned_parts = _as_tuple(pinned)
    if not pinned_parts:
        return False
    latest_parts = _as_tuple(latest)[: len(pinned_parts)]
    return latest_parts > pinned_parts


def latest_github_tag(repo: str) -> str | None:
    """Return the latest release tag for ``owner/repo``, or None.

    Prefers an authenticated ``gh api`` call (higher rate limit, works in
    CI); falls back to the unauthenticated REST API. Returns None on any
    failure so the caller skips cleanly.
    """
    tag = _gh_latest(repo) if shutil.which("gh") else None
    return tag if tag else _rest_latest(repo)


def _gh_latest(repo: str) -> str | None:
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/releases/latest", "--jq", ".tag_name"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    tag = result.stdout.strip()
    return tag or None


def _rest_latest(repo: str) -> str | None:
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return json.load(response).get("tag_name") or None
    except Exception:
        return None


def collect_pins() -> list[tuple[str, str, str]]:
    """Gather (repo, pinned, source) across config and workflow files.

    Deduplicates by (repo, pinned) so a repo used in many workflows is
    queried once.
    """
    pins: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()

    config = Path(PRECOMMIT_CONFIG)
    if config.is_file():
        try:
            config_text = config.read_text(encoding="utf-8")
        except OSError as exc:
            sys.stderr.write(f"check_pinned_versions: skip {config}: {exc}\n")
            config_text = ""
        for repo, rev in precommit_pins(config_text):
            if (repo, rev) not in seen:
                seen.add((repo, rev))
                pins.append((repo, rev, "pre-commit"))

    workflows = Path(WORKFLOWS_DIR)
    if workflows.is_dir():
        for path in sorted(workflows.glob("*.y*ml")):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError as exc:
                sys.stderr.write(f"check_pinned_versions: skip {path}: {exc}\n")
                continue
            for repo, ref in workflow_action_pins(text):
                if (repo, ref) not in seen:
                    seen.add((repo, ref))
                    pins.append((repo, ref, "ci"))
    return pins


def main() -> int:
    pins = collect_pins()
    if not pins:
        print("check_pinned_versions: no GitHub-sourced pins found; skipping")
        return 0

    behind: list[tuple[str, str, str, str]] = []
    skipped = 0
    for repo, pinned, source in pins:
        latest = latest_github_tag(repo)
        if not latest:
            skipped += 1
            continue
        if is_behind(pinned, latest):
            behind.append((repo, pinned, latest, source))

    if not behind:
        checked = len(pins) - skipped
        note = f" ({skipped} unresolvable, skipped)" if skipped else ""
        print(f"check_pinned_versions: {checked} pin(s) current{note}.")
        return 0

    lines = ["check_pinned_versions: pinned tooling is behind upstream:"]
    for repo, pinned, latest, source in behind:
        lines.append(f"  [{source}] {repo}: {pinned} -> {latest}")
    lines.append("  Bump pre-commit pins with: uv run pre-commit autoupdate")
    lines.append("  Bump CI actions by editing the uses: pins in .github/workflows/.")
    print("\n".join(lines), file=sys.stderr)
    return 1 if OUTDATED_IS_BLOCKING else 0


if __name__ == "__main__":
    raise SystemExit(main())
