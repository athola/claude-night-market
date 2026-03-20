"""Shared deferred-capture logic (leyline contract implementation).

Provides the core functions for creating GitHub issues from
deferred items. Plugin wrappers import this module and pass
a PluginConfig with their label subset and context enrichment.

Python 3.9 compatible.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class PluginConfig:
    """Per-plugin configuration for deferred capture."""

    plugin_name: str
    label_colors: dict[str, str]
    enrich_context: Callable[[str, str], str] | None = None
    description: str = "Create a GitHub issue for a deferred item."
    source_help: str = "Origin skill"


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def build_title(raw: str) -> str:
    """Prefix title with [Deferred] unless already present."""
    if raw.startswith("[Deferred]"):
        return raw
    return f"[Deferred] {raw}"


def build_labels(source: str, extras: list[str]) -> list[str]:
    """Build deduped label list: deferred + source + extras."""
    seen: dict[str, None] = {}
    for label in ["deferred", source, *extras]:
        label = label.strip()
        if label:
            seen[label] = None
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
    return (
        "## Deferred Item\n\n"
        f"**Source:** {source} (session {session_id})\n"
        f"**Captured:** {today}\n"
        f"**Branch:** {branch}\n"
        f"**Captured by:** {captured_by}\n\n"
        "### Context\n\n"
        f"{context}\n\n"
        "### Original Artifact\n\n"
        f"{artifact}\n\n"
        "### Next Steps\n\n"
        "- [ ] Evaluate feasibility in a future cycle\n"
        "- [ ] Link to related work if applicable\n"
    )


def ensure_label(label: str, color: str) -> None:
    """Create GitHub label if it does not exist; log unexpected errors."""
    try:
        result = subprocess.run(
            ["gh", "label", "create", label, "--color", color],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if result.returncode != 0 and "already exists" not in result.stderr:
            sys.stderr.write(
                f"deferred_capture: ensure_label({label}): {result.stderr.strip()}\n"
            )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        sys.stderr.write(f"deferred_capture: ensure_label({label}): {exc}\n")


def find_duplicate(bare_title: str) -> dict[str, object] | None:
    """Search open issues for an exact title match (case-insensitive)."""
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
            return dict(issue)
    return None


def create_issue(title: str, body: str, labels: list[str]) -> dict[str, object]:
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
    return dict(json.loads(result.stdout))


# -------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------


def parse_args(
    config: PluginConfig,
    argv: list[str] | None = None,
) -> argparse.Namespace:
    """Parse CLI arguments using plugin-specific config."""
    parser = argparse.ArgumentParser(description=config.description)
    parser.add_argument(
        "--title",
        required=True,
        help="Concise description (prefixed with [Deferred])",
    )
    parser.add_argument(
        "--source",
        required=True,
        help=config.source_help,
    )
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


def run_capture(
    config: PluginConfig,
    argv: list[str] | None = None,
) -> int:
    """Main entry point for deferred capture with plugin config."""
    args = parse_args(config, argv)

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

    # Apply plugin-specific context enrichment
    context = args.context
    if config.enrich_context is not None:
        context = config.enrich_context(args.source, context)

    body = build_body(
        source=args.source,
        session_id=session_id,
        context=context,
        artifact_path=args.artifact_path,
        captured_by=args.captured_by,
    )

    if args.dry_run:
        output = {
            "status": "dry_run",
            "title": title,
            "source": args.source,
            "session_id": session_id,
            "labels": labels,
            "body": body,
        }
        print(json.dumps(output, indent=2))
        return 0

    # Ensure all labels exist in GitHub
    for label in labels:
        color = config.label_colors.get(label, "#CCCCCC")
        ensure_label(label, color)

    # Duplicate detection
    try:
        dupe = find_duplicate(bare_title)
    except FileNotFoundError:
        print(json.dumps({"status": "error", "message": "gh CLI not found"}))
        return 1
    except subprocess.TimeoutExpired:
        print(json.dumps({"status": "error", "message": "gh CLI timed out"}))
        return 1

    if dupe:
        print(
            json.dumps(
                {
                    "status": "duplicate",
                    "existing_url": dupe.get("url", ""),
                    "number": dupe.get("number"),
                }
            )
        )
        return 0

    # Create issue
    try:
        created = create_issue(title, body, labels)
    except FileNotFoundError:
        print(json.dumps({"status": "error", "message": "gh CLI not found"}))
        return 1
    except subprocess.TimeoutExpired:
        print(json.dumps({"status": "error", "message": "gh CLI timed out"}))
        return 1
    except RuntimeError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}))
        return 1

    print(
        json.dumps(
            {
                "status": "created",
                "issue_url": created.get("url", ""),
                "number": created.get("number"),
            }
        )
    )
    return 0
