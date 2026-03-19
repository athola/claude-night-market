#!/usr/bin/env python3
"""Deferred Capture - egregore plugin wrapper.

Thin wrapper implementing the leyline deferred-capture contract with
egregore-specific defaults and context enrichment.

Usage:
    python deferred_capture.py --title TITLE --source SOURCE
                               --context CONTEXT [options]
    python deferred_capture.py --title "My idea" --source egregore
                               --context "Out of scope" --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import cast

# ---------------------------------------------------------------------------
# Label taxonomy (egregore-relevant labels)
# ---------------------------------------------------------------------------
LABEL_COLORS: dict[str, str] = {
    "deferred": "#7B61FF",
    "egregore": "#5319E7",
}

VALID_SOURCES = set(LABEL_COLORS.keys()) - {"deferred"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def build_title(raw: str) -> str:
    """Prefix title with [Deferred] unless already present."""
    if raw.startswith("[Deferred]"):
        return raw
    return f"[Deferred] {raw}"


def build_labels(source: str, extras: list[str]) -> list[str]:
    """Build deduped label list: deferred + source + extras."""
    seen: dict[str, None] = {}
    for lbl in ["deferred", source, *extras]:
        stripped = lbl.strip()
        if stripped:
            seen[stripped] = None
    return list(seen.keys())


def get_session_id(explicit: str | None) -> str:
    """Return explicit ID, $CLAUDE_SESSION_ID, or UTC timestamp."""
    if explicit:
        return explicit
    env_id = os.environ.get("CLAUDE_SESSION_ID", "")
    if env_id:
        return env_id
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def get_current_branch() -> str:
    """Return current git branch name, or 'unknown' on failure."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return "unknown"


def enrich_context(context: str) -> str:
    """Apply egregore-specific context enrichment."""
    step = os.environ.get("EGREGORE_STEP", "")
    if step:
        context = f"{context}\n\nEgregore pipeline step: {step}"
    return context


def build_body(
    source: str,
    session_id: str,
    context: str,
    artifact_path: str | None,
    captured_by: str,
) -> str:
    """Build the issue body from the leyline contract template."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    branch = get_current_branch()
    artifact = artifact_path if artifact_path else "N/A"
    enriched = enrich_context(context)
    return (
        "## Deferred Item\n\n"
        f"**Source:** {source} (session {session_id})\n"
        f"**Captured:** {today}\n"
        f"**Branch:** {branch}\n"
        f"**Captured by:** {captured_by}\n\n"
        "### Context\n\n"
        f"{enriched}\n\n"
        "### Original Artifact\n\n"
        f"{artifact}\n\n"
        "### Next Steps\n\n"
        "- [ ] Evaluate feasibility in a future cycle\n"
        "- [ ] Link to related work if applicable\n"
    )


def ensure_label(label: str, color: str) -> None:
    """Create GitHub label if it does not exist; ignore errors."""
    try:
        subprocess.run(
            ["gh", "label", "create", label, "--color", color],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def find_duplicate(bare_title: str) -> dict | None:
    """Search open issues for an exact title match (case-insensitive)."""
    try:
        result = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--search",
                f"{bare_title} in:title",
                "--state",
                "open",
                "--json",
                "number,title,url",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except FileNotFoundError:
        raise
    except subprocess.TimeoutExpired:
        raise

    if result.returncode != 0:
        return None

    try:
        issues = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

    needle = bare_title.lower()
    for issue in issues:
        candidate = issue.get("title", "")
        if candidate.startswith("[Deferred]"):
            candidate = candidate[len("[Deferred]") :].strip()
        if candidate.lower() == needle:
            return cast(dict, issue)
    return None


def create_issue(title: str, body: str, labels: list[str]) -> dict:
    """Create a GitHub issue and return parsed JSON result."""
    label_args: list[str] = []
    for label in labels:
        label_args += ["--label", label]

    result = subprocess.run(
        [
            "gh",
            "issue",
            "create",
            "--title",
            title,
            "--body",
            body,
            *label_args,
            "--json",
            "number,url",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return cast(dict, json.loads(result.stdout))


def _emit(data: dict, indent: int | None = None) -> None:
    """Print JSON output to stdout."""
    print(json.dumps(data, indent=indent))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Create a GitHub issue for a deferred item (egregore).",
    )
    parser.add_argument(
        "--title",
        required=True,
        help="Concise description (will be prefixed with [Deferred] if not already)",
    )
    parser.add_argument("--source", required=True, help="Origin skill (e.g. egregore)")
    parser.add_argument("--context", required=True, help="Why raised and why deferred")
    parser.add_argument("--labels", default="", help="Comma-separated extra labels")
    parser.add_argument(
        "--session-id",
        dest="session_id",
        default=None,
        help="Session ID (default: $CLAUDE_SESSION_ID or UTC timestamp)",
    )
    parser.add_argument(
        "--artifact-path",
        dest="artifact_path",
        default=None,
        help="Path to source artifact",
    )
    parser.add_argument(
        "--captured-by",
        dest="captured_by",
        default="explicit",
        choices=["explicit", "safety-net"],
        help="How the item was captured",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print JSON output without creating issue",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point: parse args, build issue, create or dry-run."""
    args = parse_args(argv)

    title = build_title(args.title)
    bare_title = (
        args.title[len("[Deferred]") :].strip()
        if args.title.startswith("[Deferred]")
        else args.title
    )

    extras = (
        [lbl for lbl in args.labels.split(",") if lbl.strip()] if args.labels else []
    )
    labels = build_labels(args.source, extras)
    session_id = get_session_id(args.session_id)
    body = build_body(
        source=args.source,
        session_id=session_id,
        context=args.context,
        artifact_path=args.artifact_path,
        captured_by=args.captured_by,
    )

    if args.dry_run:
        _emit(
            {
                "status": "dry_run",
                "title": title,
                "source": args.source,
                "session_id": session_id,
                "labels": labels,
                "body": body,
            },
            indent=2,
        )
        return 0

    for label in labels:
        color = LABEL_COLORS.get(label, "#CCCCCC")
        ensure_label(label, color)

    try:
        dupe = find_duplicate(bare_title)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        msg = (
            "gh CLI not found in PATH"
            if isinstance(exc, FileNotFoundError)
            else "gh CLI timed out"
        )
        _emit({"status": "error", "message": msg})
        return 1

    if dupe:
        _emit(
            {
                "status": "duplicate",
                "existing_url": dupe.get("url", ""),
                "number": dupe.get("number"),
            }
        )
        return 0

    try:
        created = create_issue(title, body, labels)
    except (FileNotFoundError, subprocess.TimeoutExpired, RuntimeError) as exc:
        if isinstance(exc, FileNotFoundError):
            msg = "gh CLI not found in PATH"
        elif isinstance(exc, subprocess.TimeoutExpired):
            msg = "gh CLI timed out"
        else:
            msg = str(exc)
        _emit({"status": "error", "message": msg})
        return 1

    _emit(
        {
            "status": "created",
            "issue_url": created.get("url", ""),
            "number": created.get("number"),
        }
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
