#!/usr/bin/env python3
"""Analyze stargazer overlap for athola/claude-night-market.

Fetches stargazers, then for each stargazer fetches their starred
repos to build a frequency map of co-starred repositories.

Usage:
    python scripts/stargazer_overlap.py
    python scripts/stargazer_overlap.py --limit 50 --top 10
    python scripts/stargazer_overlap.py --no-cache
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO = "athola/claude-night-market"
CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
CACHE_FILE = CACHE_DIR / "stargazer_overlap.json"

# GitHub API rate limit: 5000/hr for authenticated users.
# Conservative default delay between per-user requests.
DEFAULT_DELAY = 0.5


# ---------- gh api helpers ----------


def gh_api(
    endpoint: str,
    paginate: bool = False,
    jq_filter: str | None = None,
) -> Any:
    """Call ``gh api`` and return parsed JSON.

    Parameters
    ----------
    endpoint:
        GitHub API path (e.g. ``repos/owner/repo/stargazers``).
    paginate:
        If True, add ``--paginate`` to fetch all pages.
    jq_filter:
        Optional jq expression passed via ``--jq``.

    Returns
    -------
    Parsed JSON (list or dict), or an empty list on error.
    """
    cmd: list[str] = ["gh", "api", endpoint]
    if paginate:
        cmd.append("--paginate")
    if jq_filter:
        cmd.extend(["--jq", jq_filter])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        stderr = result.stderr.strip()
        # Rate-limit detection: look for 403 or "rate limit"
        if "rate limit" in stderr.lower() or "403" in stderr:
            return None  # sentinel for rate-limited
        print(f"  gh api error: {stderr}", file=sys.stderr)
        return []

    text = result.stdout.strip()
    if not text:
        return []

    # --paginate with --jq can produce newline-separated values
    # rather than a single JSON array.
    if jq_filter:
        lines = text.splitlines()
        # If each line looks like a JSON value, collect them.
        collected: list[Any] = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                collected.append(json.loads(line))
            except json.JSONDecodeError:
                collected.append(line)
        return collected

    return json.loads(text)


def get_rate_limit_remaining() -> int:
    """Return remaining core API calls, or -1 on error."""
    data = gh_api("rate_limit")
    if isinstance(data, dict):
        try:
            return int(data["resources"]["core"]["remaining"])
        except (KeyError, TypeError, ValueError):
            pass
    return -1


# ---------- data fetching ----------


def fetch_stargazers(limit: int | None = None) -> list[str]:
    """Return list of stargazer login names."""
    print(f"Fetching stargazers for {REPO}...")
    raw = gh_api(
        f"repos/{REPO}/stargazers",
        paginate=True,
        jq_filter=".[].login",
    )
    if not isinstance(raw, list):
        return []
    logins: list[str] = [str(x) for x in raw if x]
    if limit is not None and limit > 0:
        logins = logins[:limit]
    print(f"  Found {len(logins)} stargazer(s) to process.")
    return logins


def fetch_user_stars(login: str) -> list[str]:
    """Return list of ``owner/repo`` strings the user has starred."""
    raw = gh_api(
        f"users/{login}/starred",
        paginate=True,
        jq_filter=".[].full_name",
    )
    if raw is None:
        return []  # rate limited
    if not isinstance(raw, list):
        return []
    return [str(r) for r in raw if r]


def build_overlap(
    stargazers: list[str],
    delay: float = DEFAULT_DELAY,
) -> dict[str, int]:
    """Build frequency map of co-starred repos.

    Parameters
    ----------
    stargazers:
        List of GitHub login names.
    delay:
        Seconds to sleep between per-user requests.

    Returns
    -------
    Dict mapping ``owner/repo`` to count of stargazers who also
    starred that repo.
    """
    freq: dict[str, int] = {}
    total = len(stargazers)

    for idx, login in enumerate(stargazers, 1):
        print(f"  [{idx}/{total}] Fetching stars for {login}...")
        stars = fetch_user_stars(login)

        if not stars:
            # Could be rate-limited or the user has no stars.
            remaining = get_rate_limit_remaining()
            if remaining == 0:
                print(
                    "  Rate limit exhausted. Stopping early.",
                    file=sys.stderr,
                )
                break
            if remaining != -1 and remaining < 50:
                wait = 60
                print(
                    f"  Low rate limit ({remaining}). Sleeping {wait}s...",
                    file=sys.stderr,
                )
                time.sleep(wait)

        for repo in stars:
            freq[repo] = freq.get(repo, 0) + 1

        if delay > 0 and idx < total:
            time.sleep(delay)

    # Remove our own repo from the results
    freq.pop(REPO, None)
    return freq


# ---------- caching ----------


def load_cache() -> dict[str, Any] | None:
    """Load cached results if available."""
    if not CACHE_FILE.exists():
        return None
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)  # type: ignore[no-any-return]
    except (json.JSONDecodeError, OSError):
        return None


def save_cache(data: dict[str, Any]) -> None:
    """Persist results to the cache file."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Results cached to {CACHE_FILE}")


# ---------- output ----------


def render_table(
    freq: dict[str, int],
    top: int = 20,
) -> str:
    """Return a markdown table of the top co-starred repos.

    Columns: Rank, Repo, Co-starred Count.
    """
    sorted_repos = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    rows = sorted_repos[:top]

    lines: list[str] = []
    lines.append("| Rank | Repo | Co-starred Count |")
    lines.append("|------|------|-----------------|")
    for rank, (repo, count) in enumerate(rows, 1):
        lines.append(f"| {rank} | {repo} | {count} |")

    return "\n".join(lines)


# ---------- CLI ----------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=("Analyze stargazer overlap for athola/claude-night-market."),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help=("Max number of stargazers to process (0 = all, default: 0)"),
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Number of top repos to display (default: 20)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore cached results and re-fetch from GitHub",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=(f"Seconds to wait between per-user API calls (default: {DEFAULT_DELAY})"),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    args = parse_args(argv)

    # Try cache first
    if not args.no_cache:
        cached = load_cache()
        if cached and "freq" in cached:
            print("Using cached results. Pass --no-cache to refresh.")
            freq: dict[str, int] = cached["freq"]
            print()
            print(render_table(freq, top=args.top))
            return 0

    limit = args.limit if args.limit > 0 else None
    stargazers = fetch_stargazers(limit=limit)
    if not stargazers:
        print("No stargazers found (or gh auth issue).")
        return 1

    freq = build_overlap(stargazers, delay=args.delay)
    if not freq:
        print("No co-starred repos found.")
        return 1

    # Cache results
    save_cache({"freq": freq, "stargazer_count": len(stargazers)})

    print()
    print(render_table(freq, top=args.top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
