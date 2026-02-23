#!/usr/bin/env python3
"""Promote highly-voted GitHub Discussions to Issues.

Checks athola/claude-night-market Discussions for items with sufficient
fire emoji reactions and promotes them to GitHub Issues for triage.

Part of Issue #69 Phase 6c: Collective Intelligence Loop

Features:
- Configurable reaction threshold (default: 3 fire reactions)
- Deduplication via promoted.json tracking
- Creates Issues with [Community Learning] prefix and labels
- Graceful failure (warns to stderr, exits 0)
"""

from __future__ import annotations

import json
import subprocess  # nosec B404
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Hardcoded target repository
TARGET_REPO = "athola/claude-night-market"
TARGET_OWNER = "athola"
TARGET_NAME = "claude-night-market"

# Discussion category IDs to scan
LEARNINGS_CATEGORY_ID = "DIC_kwDOQbN88M4C2zJo"

# Max chars of discussion body to include in promoted Issue
BODY_PREVIEW_LIMIT = 2000


def get_config_dir() -> Path:
    """Get the discussions config directory."""
    return Path.home() / ".claude" / "skills" / "discussions"


@dataclass
class PromotionConfig:
    """Configuration for discussion promotion."""

    promotion_threshold: int = 3
    promotion_emoji: str = "\U0001f525"  # fire emoji
    target_repo: str = TARGET_REPO

    @classmethod
    def load(cls) -> PromotionConfig:
        """Load config from disk, falling back to defaults."""
        config_path = get_config_dir() / "config.json"
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text())
                return cls(
                    promotion_threshold=data.get("promotion_threshold", 3),
                    promotion_emoji=data.get("promotion_emoji", "\U0001f525"),
                    target_repo=data.get("target_repo", TARGET_REPO),
                )
            except (json.JSONDecodeError, OSError) as e:
                print(
                    f"Warning: Could not load config: {e}",
                    file=sys.stderr,
                )
        return cls()


@dataclass
class PromotedRecord:
    """Tracks promoted discussions to avoid duplicates."""

    promoted: dict[str, str] = field(default_factory=dict)  # discussion_id -> issue_url

    @classmethod
    def load(cls) -> PromotedRecord:
        """Load promoted record from disk."""
        record_path = get_config_dir() / "promoted.json"
        if record_path.exists():
            try:
                data = json.loads(record_path.read_text())
                return cls(promoted=data.get("promoted", {}))
            except (json.JSONDecodeError, OSError):
                pass
        return cls()

    def save(self) -> None:
        """Save promoted record to disk."""
        record_path = get_config_dir() / "promoted.json"
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(json.dumps({"promoted": self.promoted}, indent=2))

    def is_promoted(self, discussion_id: str) -> bool:
        """Check if a discussion has already been promoted."""
        return discussion_id in self.promoted


@dataclass
class DiscussionItem:
    """A GitHub Discussion with reaction data."""

    discussion_id: str
    title: str
    url: str
    body: str
    reaction_count: int


def run_gh_graphql(query: str, variables: dict[str, Any] | None = None) -> Any:
    """Run a GraphQL query via gh api.

    Args:
        query: GraphQL query string
        variables: Optional query variables

    Returns:
        Parsed JSON response

    Raises:
        RuntimeError: If gh command fails

    """
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    if variables:
        for key, value in variables.items():
            cmd.extend(["-f", f"{key}={value}"])

    result = subprocess.run(  # noqa: S603, S607  # nosec B603
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"gh api graphql failed (exit {result.returncode}): {result.stderr}"
        )

    return json.loads(result.stdout)


def get_repo_node_id() -> str:
    """Get the repository node ID.

    Returns:
        Repository node ID string

    """
    query = (
        f'query {{ repository(owner: "{TARGET_OWNER}",'
        f' name: "{TARGET_NAME}") {{ id }} }}'
    )

    response = run_gh_graphql(query)
    return str(response["data"]["repository"]["id"])


def fetch_learnings_discussions() -> list[DiscussionItem]:
    """Fetch recent Discussions from the Learnings category with reactions.

    Returns:
        List of DiscussionItems with reaction counts

    """
    query = (
        f'query {{ repository(owner: "{TARGET_OWNER}", name: "{TARGET_NAME}") {{ '
        f'discussions(categoryId: "{LEARNINGS_CATEGORY_ID}", first: 20, '
        "orderBy: {field: CREATED_AT, direction: DESC}) { "
        "nodes { id title url body "
        "reactions(content: FIRE) { totalCount } } } } }"  # noqa: UP031
    )

    try:
        response = run_gh_graphql(query)
        nodes = (
            response.get("data", {})
            .get("repository", {})
            .get("discussions", {})
            .get("nodes", [])
        )

        items: list[DiscussionItem] = []
        for node in nodes:
            items.append(
                DiscussionItem(
                    discussion_id=node["id"],
                    title=node["title"],
                    url=node["url"],
                    body=node.get("body", ""),
                    reaction_count=node.get("reactions", {}).get("totalCount", 0),
                )
            )
        return items
    except (RuntimeError, KeyError, json.JSONDecodeError) as e:
        print(
            f"Warning: Could not fetch discussions: {e}",
            file=sys.stderr,
        )
        return []


def format_issue_body(item: DiscussionItem) -> str:
    """Format an Issue body from a promoted Discussion.

    Args:
        item: The discussion to promote

    Returns:
        Markdown-formatted issue body

    """
    lines: list[str] = []
    lines.append("## Community Learning Promotion")
    lines.append("")
    lines.append(
        f"This issue was auto-promoted from a GitHub Discussion "
        f"that received **{item.reaction_count}** "
        f"\U0001f525 reactions from the community."
    )
    lines.append("")
    lines.append(f"**Source Discussion**: {item.url}")
    lines.append(f"**Vote Count**: {item.reaction_count} \U0001f525")
    lines.append("")
    lines.append("## Original Content")
    lines.append("")
    body_preview = item.body[:BODY_PREVIEW_LIMIT]
    if len(item.body) > BODY_PREVIEW_LIMIT:
        body_preview += "\n\n*[Content truncated — see full discussion]*"
    lines.append(body_preview)
    lines.append("")
    lines.append("---")
    lines.append("*Auto-promoted by Phase 6c Collective Intelligence Loop (Issue #69)*")
    return "\n".join(lines)


def promote_discussion(repo_id: str, item: DiscussionItem) -> str:
    """Create a GitHub Issue from a Discussion.

    Args:
        repo_id: Repository node ID
        item: The discussion to promote

    Returns:
        URL of the created issue

    """
    title = f"[Community Learning] {item.title}"
    body = format_issue_body(item)

    query = """
    mutation($repoId: ID!, $title: String!, $body: String!) {
      createIssue(input: {
        repositoryId: $repoId,
        title: $title,
        body: $body
      }) {
        issue {
          url
        }
      }
    }
    """

    response = run_gh_graphql(
        query,
        variables={
            "repoId": repo_id,
            "title": title,
            "body": body,
        },
    )

    return str(response["data"]["createIssue"]["issue"]["url"])


def run_promotion() -> list[str]:
    """Main promotion workflow: scan discussions, promote qualifying items.

    Returns:
        List of created issue URLs

    """
    config = PromotionConfig.load()
    record = PromotedRecord.load()

    # Fetch discussions with reactions
    discussions = fetch_learnings_discussions()
    if not discussions:
        print("No discussions found to check.", file=sys.stderr)
        return []

    # Filter to promotable items
    promotable = [
        d
        for d in discussions
        if d.reaction_count >= config.promotion_threshold
        and not record.is_promoted(d.discussion_id)
    ]

    if not promotable:
        print("No discussions meet the promotion threshold.", file=sys.stderr)
        return []

    # Get repo ID for creating issues
    repo_id = get_repo_node_id()

    created_urls: list[str] = []
    for item in promotable:
        try:
            url = promote_discussion(repo_id, item)
            record.promoted[item.discussion_id] = url
            record.save()
            print(f"Promoted: {item.title} -> {url}")
            created_urls.append(url)
        except RuntimeError as e:
            print(
                f"Warning: Could not promote '{item.title}': {e}",
                file=sys.stderr,
            )

    return created_urls


def main() -> None:
    """CLI entry point."""
    try:
        urls = run_promotion()
        if urls:
            print(f"\nPromoted {len(urls)} discussion(s) to Issues.")
            for url in urls:
                print(f"  {url}")
        else:
            print("No discussions promoted.")
    except RuntimeError as e:
        print(f"Warning: Promotion failed: {e}", file=sys.stderr)
        sys.exit(0)
    except FileNotFoundError:
        print(
            "Warning: gh CLI not found. Install GitHub CLI to enable "
            "collective intelligence features.",
            file=sys.stderr,
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
