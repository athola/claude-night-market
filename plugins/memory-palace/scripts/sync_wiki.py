#!/usr/bin/env python3
"""Sync the GitHub Wiki knowledge corpus to a local clone.

Clones on first run, pulls on subsequent runs. The local clone is used
by the cache interceptor (research_interceptor.py) for search-before-web.

Usage:
    python scripts/sync_wiki.py              # clone or pull
    python scripts/sync_wiki.py --status     # show sync status
    python scripts/sync_wiki.py --push       # push local changes to wiki
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
WIKI_DIR = PLUGIN_ROOT / "data" / "wiki"
REPO_URL = "git@github.com:athola/claude-night-market.wiki.git"


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def clone() -> bool:
    """Clone the wiki repo to WIKI_DIR."""
    WIKI_DIR.parent.mkdir(parents=True, exist_ok=True)
    result = _run(["git", "clone", REPO_URL, str(WIKI_DIR)])
    if result.returncode != 0:
        print(f"Clone failed: {result.stderr.strip()}", file=sys.stderr)
        return False
    count = len(list(WIKI_DIR.glob("*.md")))
    print(f"Cloned wiki to {WIKI_DIR} ({count} pages)")
    return True


def pull() -> bool:
    """Pull latest changes from the wiki."""
    result = _run(["git", "pull", "--ff-only"], cwd=WIKI_DIR)
    if result.returncode != 0:
        print(f"Pull failed: {result.stderr.strip()}", file=sys.stderr)
        return False
    output = result.stdout.strip()
    if "Already up to date" in output:
        print("Wiki is up to date.")
    else:
        print(f"Updated: {output}")
    return True


def push() -> bool:
    """Push local wiki changes to remote."""
    # Check for uncommitted changes
    status = _run(["git", "status", "--porcelain"], cwd=WIKI_DIR)
    if status.stdout.strip():
        # Stage and commit
        _run(["git", "add", "-A"], cwd=WIKI_DIR)
        _run(
            ["git", "commit", "-m", "Update knowledge corpus from intake pipeline"],
            cwd=WIKI_DIR,
        )

    result = _run(["git", "push"], cwd=WIKI_DIR)
    if result.returncode != 0:
        print(f"Push failed: {result.stderr.strip()}", file=sys.stderr)
        return False
    print("Pushed wiki changes to remote.")
    return True


def status() -> None:
    """Show sync status."""
    if not WIKI_DIR.is_dir():
        print(f"Wiki not cloned yet. Run: python {__file__}")
        return

    pages = list(WIKI_DIR.glob("*.md"))
    print(f"Wiki directory: {WIKI_DIR}")
    print(f"Pages: {len(pages)}")

    log = _run(["git", "log", "-1", "--format=%h %s (%cr)"], cwd=WIKI_DIR)
    if log.returncode == 0:
        print(f"Last commit: {log.stdout.strip()}")

    git_status = _run(["git", "status", "--porcelain"], cwd=WIKI_DIR)
    if git_status.stdout.strip():
        print(f"Uncommitted changes: {len(git_status.stdout.strip().splitlines())}")
    else:
        print("Working tree clean.")


def sync() -> bool:
    """Clone or pull the wiki."""
    if WIKI_DIR.is_dir() and (WIKI_DIR / ".git").is_dir():
        return pull()
    elif WIKI_DIR.exists():
        print(f"{WIKI_DIR} exists but is not a git repo. Remove it first.")
        return False
    else:
        return clone()


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync wiki knowledge corpus")
    parser.add_argument("--status", action="store_true", help="Show sync status")
    parser.add_argument("--push", action="store_true", help="Push local changes")
    args = parser.parse_args()

    if args.status:
        status()
    elif args.push:
        if not WIKI_DIR.is_dir():
            print("Wiki not cloned. Run sync first.")
            sys.exit(1)
        sys.exit(0 if push() else 1)
    else:
        sys.exit(0 if sync() else 1)


if __name__ == "__main__":
    main()
