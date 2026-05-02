#!/usr/bin/env python3
"""Convert a /pr-review markdown file into Findings and post them.

Closes the loop between in-session review work (running /pr-review,
/fix-pr, /update-tests, etc.) and the GitHub Discussions collective
memory: each review's findings get posted as Insight discussions so
patterns emerge across reviews over time.

Usage:
    python3 post_review_insights.py <path-to-review.md> [--pr 417]

The PR number is parsed from the first heading if not given. The
Discussions category resolves via post_insights_to_discussions
(prefers "insights", falls back to "learnings").
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from insight_types import (  # noqa: E402 - sys.path adjusted above to discover scripts dir
    Finding,
)
from post_insights_to_discussions import (  # noqa: E402 - sys.path adjusted above to discover scripts dir
    post_findings,
)


@dataclass
class ReviewSummary:
    """Structured representation of a /pr-review markdown file."""

    verdict: str = "unknown"
    pr_number: int | None = None
    blockers: list[dict[str, str]] = field(default_factory=list)
    non_blocking: list[dict[str, str]] = field(default_factory=list)


def extract_verdict(content: str) -> str:
    """Extract the **Verdict:** line from review markdown."""
    m = re.search(r"\*\*Verdict:\*\*\s*(.+)", content)
    return m.group(1).strip() if m else "unknown"


def extract_pr_number(content: str) -> int | None:
    """Extract the PR number from a heading like '# PR Review: #417 - ...'."""
    m = re.search(r"#\s*PR Review:\s*#(\d+)", content)
    return int(m.group(1)) if m else None


def extract_blockers(content: str) -> list[dict[str, str]]:
    """Parse the Blocking findings section into id/title/body records.

    Each blocker is rendered as `### B<n> - <title>` followed by
    a body that ends at the next `###` heading or the next `##`
    section.
    """
    section = _section(content, "## Blocking findings")
    if not section:
        return []
    items: list[dict[str, str]] = []
    for m in re.finditer(
        r"###\s*(?P<id>B\d+)\s*-\s*(?P<title>.+?)\n(?P<body>.*?)(?=\n###\s+B\d+\s*-|\n##\s+|\Z)",
        section,
        re.DOTALL,
    ):
        items.append(
            {
                "id": m.group("id").strip(),
                "title": m.group("title").strip(),
                "body": m.group("body").strip(),
            }
        )
    return items


def extract_non_blocking(content: str) -> list[dict[str, str]]:
    """Parse the Non-blocking findings table rows."""
    section = _section(content, "## Non-blocking findings")
    if not section:
        return []
    rows: list[dict[str, str]] = []
    table_re = re.compile(
        r"\|\s*(?P<id>NB\d+)\s*\|\s*(?P<source>[^\|]+?)\s*\|"
        r"\s*(?P<where>[^\|]+?)\s*\|\s*(?P<concern>[^\|]+?)\s*\|"
    )
    for m in table_re.finditer(section):
        rows.append(
            {
                "id": m.group("id").strip(),
                "source": m.group("source").strip(),
                "where": m.group("where").strip(),
                "concern": m.group("concern").strip(),
            }
        )
    return rows


def parse_review_markdown(content: str) -> ReviewSummary:
    """Combined parser producing a ReviewSummary."""
    return ReviewSummary(
        verdict=extract_verdict(content),
        pr_number=extract_pr_number(content),
        blockers=extract_blockers(content),
        non_blocking=extract_non_blocking(content),
    )


def review_to_findings(
    summary: ReviewSummary,
    pr_number: int | None = None,
) -> list[Finding]:
    """Convert a ReviewSummary to Finding objects for post_findings()."""
    pr = pr_number or summary.pr_number
    pr_link = f"PR #{pr}" if pr else "this PR"
    findings: list[Finding] = []

    for b in summary.blockers:
        findings.append(
            Finding(
                type="PR Finding",
                severity="high",
                skill="",
                summary=f"{b['id']}: {b['title']}",
                evidence=(f"From {pr_link} review.\n\n{b['body']}"),
                recommendation=(
                    f"Address blocking finding {b['id']} before merge. "
                    f"See review for suggested direction."
                ),
                source="pr-review",
            )
        )

    for nb in summary.non_blocking:
        findings.append(
            Finding(
                type="PR Finding",
                severity="medium",
                skill="",
                summary=f"{nb['id']}: {nb['concern']}",
                evidence=(
                    f"From {pr_link} review.\n\n"
                    f"Source: {nb['source']}\n"
                    f"Where: {nb['where']}\n"
                    f"Concern: {nb['concern']}"
                ),
                recommendation=("Non-blocking improvement; address opportunistically."),
                source="pr-review",
            )
        )

    return findings


def _section(content: str, heading: str) -> str | None:
    """Extract content between a heading and the next heading or EOF."""
    pattern = re.escape(heading) + r"\n(.*?)(?=\n## |\n---\n|\Z)"
    m = re.search(pattern, content, re.DOTALL)
    return m.group(1).strip() if m else None


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "review_file",
        type=Path,
        help="Path to the /pr-review markdown output (e.g., reviews/pr-NNN-review.md)",
    )
    parser.add_argument(
        "--pr",
        type=int,
        default=None,
        help="PR number (auto-detected from review heading if omitted)",
    )
    args = parser.parse_args()

    if not args.review_file.exists():
        print(f"Review file not found: {args.review_file}", file=sys.stderr)
        sys.exit(1)

    content = args.review_file.read_text()
    summary = parse_review_markdown(content)
    findings = review_to_findings(summary, pr_number=args.pr)

    if not findings:
        print(
            f"No findings extracted from {args.review_file}. "
            "Confirm the review uses ### B<n> blockers and an NB table.",
            file=sys.stderr,
        )
        sys.exit(0)

    print(
        f"Posting {len(findings)} review findings "
        f"({sum(1 for f in findings if f.severity == 'high')} blocking) "
        f"from {args.review_file}...",
        file=sys.stderr,
    )
    urls = post_findings(findings)
    for url in urls:
        print(url)
    sys.exit(0)


if __name__ == "__main__":
    main()
