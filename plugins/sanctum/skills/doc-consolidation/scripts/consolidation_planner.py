#!/usr/bin/env python3
"""Consolidation Planner - Fast model triage for doc consolidation.

Delegates Phase 1 analysis tasks to haiku-class models for efficiency.
Phase 2 execution remains on the main conversation model.

Usage:
    python consolidation_planner.py scan [--repo-path PATH]
    python consolidation_planner.py analyze FILE [FILE...]
    python consolidation_planner.py route --chunks CHUNKS_JSON --docs-dir PATH
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Standard locations to exclude from candidate detection
STANDARD_LOCATIONS = {
    "docs/",
    "skills/",
    "modules/",
    "commands/",
    "agents/",
    ".github/",
    "tests/",
    "src/",
}

# Standard file names to exclude
STANDARD_NAMES = {
    "README.md",
    "README",
    "LICENSE.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "HISTORY.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
}

# ALL_CAPS patterns that indicate LLM reports
REPORT_PATTERNS = [
    r".*_REPORT\.md$",
    r".*_ANALYSIS\.md$",
    r".*_REVIEW\.md$",
    r".*_FINDINGS\.md$",
    r".*_AUDIT\.md$",
]

# Strong content markers (any one = candidate)
STRONG_MARKERS = [
    r"^\*?\*?Date\*?\*?:",
    r"^##\s+Executive Summary",
    r"^##\s+Summary$",
    r"^##\s+Findings",
    r"^##\s+Action Items",
    r"^##\s+Recommendations",
    r"^##\s+Conclusion",
]

# Supporting markers (need 2+ to qualify)
SUPPORTING_MARKERS = [
    r"^\|.*\|.*\|",  # Markdown tables
    r"^###\s+(High|Medium|Low)\s+Priority",
    r"^-\s+\[\s*\]",  # Unchecked checkboxes
    r"^##\s+\d+\.",  # Numbered sections
    r"^\*?\*?Scope\*?\*?:",
    r"^\*?\*?Status\*?\*?:",
    r"^[✅⚠️❌]",  # Status emojis
]

# Content category patterns
CATEGORY_PATTERNS = {
    "actionable": [
        r"action\s*items?",
        r"next\s*steps?",
        r"todo",
        r"tasks?",
        r"-\s*\[\s*\]",
    ],
    "decisions": [
        r"decision",
        r"chose|chosen",
        r"tradeoff",
        r"rationale",
        r"why\s+we",
        r"approach",
    ],
    "findings": [
        r"finding",
        r"observation",
        r"analysis",
        r"discovered",
        r"audit",
        r"review\s+result",
    ],
    "metrics": [
        r"\d+%",
        r"before.*after",
        r"improvement",
        r"reduction",
        r"benchmark",
        r"\|\s*\d+\s*\|",
    ],
    "migration": [
        r"migration",
        r"step\s*\d",
        r"how\s+to",
        r"procedure",
        r"```bash",
    ],
    "api_changes": [
        r"api",
        r"breaking\s+change",
        r"deprecat",
        r"endpoint",
        r"interface",
    ],
}


@dataclass
class CandidateFile:
    """A file identified as a consolidation candidate."""

    path: str
    score: int
    reasons: list[str] = field(default_factory=list)


@dataclass
class ContentChunk:
    """An extracted content chunk from a source file."""

    header: str
    content: str
    category: str
    value: str  # high, medium, low
    char_count: int = 0

    def __post_init__(self) -> None:
        self.char_count = len(self.content)


@dataclass
class Route:
    """A routing decision for a content chunk."""

    chunk_header: str
    category: str
    value: str
    destination: str
    strategy: str  # CREATE_NEW, INTELLIGENT_WEAVE, REPLACE_SECTION, APPEND_WITH_CONTEXT
    rationale: str


@dataclass
class ConsolidationPlan:
    """Complete consolidation plan for user review."""

    source: str
    routes: list[Route]
    skipped: list[dict[str, str]]
    summary: dict[str, int]


def git_untracked_files(repo_path: str = ".") -> list[str]:
    """Get list of untracked files from git status."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        untracked = []
        for line in result.stdout.splitlines():
            if line.startswith("??"):
                file_path = line[3:].strip()
                untracked.append(file_path)
        return untracked
    except subprocess.CalledProcessError:
        return []


def is_standard_location(file_path: str) -> bool:
    """Check if file is in a standard documentation location."""
    return any(file_path.startswith(loc) for loc in STANDARD_LOCATIONS)


def is_standard_name(file_path: str) -> bool:
    """Check if file has a standard name."""
    name = Path(file_path).name
    return name in STANDARD_NAMES


def is_allcaps_report(file_path: str) -> bool:
    """Check if file matches ALL_CAPS report patterns."""
    name = Path(file_path).name
    return any(re.match(pattern, name) for pattern in REPORT_PATTERNS)


def count_content_markers(content: str) -> tuple[int, int]:
    """Count strong and supporting markers in content."""
    strong = 0
    supporting = 0

    for pattern in STRONG_MARKERS:
        if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
            strong += 1

    for pattern in SUPPORTING_MARKERS:
        if re.search(pattern, content, re.MULTILINE):
            supporting += 1

    return strong, supporting


def scan_for_candidates(repo_path: str = ".") -> list[CandidateFile]:
    """Scan repository for consolidation candidates."""
    candidates = []
    untracked = git_untracked_files(repo_path)

    for file_path in untracked:
        # Only markdown files
        if not file_path.endswith(".md"):
            continue

        # Skip standard locations and names
        if is_standard_location(file_path):
            continue
        if is_standard_name(file_path):
            continue

        score = 0
        reasons = []

        # Check naming pattern
        if is_allcaps_report(file_path):
            score += 3
            reasons.append("ALL_CAPS report name")

        # Check content markers
        full_path = Path(repo_path) / file_path
        if full_path.exists():
            try:
                # Read first 100 lines
                with open(full_path) as f:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= 100:
                            break
                        lines.append(line)
                    content = "".join(lines)

                strong, supporting = count_content_markers(content)

                if strong > 0:
                    score += 3
                    reasons.append(f"Strong markers: {strong}")

                if supporting >= 2:
                    score += 2
                    reasons.append(f"Supporting markers: {supporting}")
            except (OSError, UnicodeDecodeError):
                pass

        # Threshold: score >= 2
        if score >= 2:
            candidates.append(
                CandidateFile(path=file_path, score=score, reasons=reasons)
            )

    return sorted(candidates, key=lambda c: c.score, reverse=True)


def extract_chunks(file_path: str) -> list[ContentChunk]:
    """Extract content chunks from a markdown file."""
    path = Path(file_path)
    if not path.exists():
        return []

    content = path.read_text()
    chunks = []
    current_header = None
    current_lines: list[str] = []

    for line in content.split("\n"):
        # New section header
        if line.startswith("## "):
            if current_header:
                chunk = make_chunk(current_header, current_lines)
                if chunk:
                    chunks.append(chunk)
            current_header = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Don't forget last section
    if current_header:
        chunk = make_chunk(current_header, current_lines)
        if chunk:
            chunks.append(chunk)

    return chunks


def make_chunk(header: str, lines: list[str]) -> ContentChunk | None:
    """Create a ContentChunk from header and lines."""
    content = "\n".join(lines).strip()
    if not content:
        return None

    category = categorize_content(header, content)
    value = score_value(content, category)

    return ContentChunk(header=header, content=content, category=category, value=value)


def categorize_content(header: str, content: str) -> str:
    """Determine content category based on header and content."""
    combined = f"{header}\n{content}".lower()

    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                return category

    return "findings"  # Default category


def score_value(content: str, category: str) -> str:
    """Score content value as high, medium, or low."""
    # High value indicators
    high_indicators = [
        len(content) > 500,  # Substantial content
        bool(re.search(r"\b\d+\b", content)),  # Contains specific numbers
        bool(re.search(r"```", content)),  # Contains code blocks
        bool(re.search(r"\|.*\|.*\|", content)),  # Contains tables
        bool(re.search(r"-\s*\[\s*\]", content)),  # Contains checkboxes
    ]

    # Low value indicators
    low_indicators = [
        len(content) < 200,  # Short content
        "generic" in content.lower(),
        "overview" in content.lower() and len(content) < 300,
        content.lower().startswith("this ") and "review" in content.lower(),
    ]

    high_count = sum(high_indicators)
    low_count = sum(low_indicators)

    if high_count >= 2:
        return "high"
    if low_count >= 2:
        return "low"
    return "medium"


def find_existing_docs(docs_dir: str = "docs") -> list[str]:
    """Find existing documentation files."""
    docs_path = Path(docs_dir)
    if not docs_path.exists():
        return []

    docs = []
    for md_file in docs_path.rglob("*.md"):
        docs.append(str(md_file))

    # Also check for rst files
    for rst_file in docs_path.rglob("*.rst"):
        docs.append(str(rst_file))

    return docs


def compute_relevance(chunk: ContentChunk, doc_path: str) -> float:
    """Compute relevance score between chunk and document."""
    try:
        doc_content = Path(doc_path).read_text().lower()
    except (OSError, UnicodeDecodeError):
        return 0.0

    score = 0.0
    chunk_lower = chunk.header.lower()

    # Header matching
    if chunk_lower in doc_content:
        score += 0.4

    # Keyword overlap (simplified)
    chunk_words = set(re.findall(r"\b\w{4,}\b", chunk.content.lower()))
    doc_words = set(re.findall(r"\b\w{4,}\b", doc_content))

    if chunk_words:
        overlap = len(chunk_words & doc_words) / len(chunk_words)
        score += overlap * 0.3

    # File name relevance
    doc_name = Path(doc_path).stem.lower().replace("-", " ").replace("_", " ")
    if any(word in doc_name for word in chunk_lower.split()):
        score += 0.2

    return score


def route_chunk(
    chunk: ContentChunk, existing_docs: list[str], source_file: str
) -> Route:
    """Determine routing for a single chunk."""
    # Find best semantic match
    best_match = None
    best_score = 0.0

    for doc_path in existing_docs:
        relevance = compute_relevance(chunk, doc_path)
        if relevance > best_score and relevance >= 0.5:
            best_match = doc_path
            best_score = relevance

    # Determine destination and strategy
    if best_match:
        return Route(
            chunk_header=chunk.header,
            category=chunk.category,
            value=chunk.value,
            destination=best_match,
            strategy="INTELLIGENT_WEAVE",
            rationale=f"Semantic match (score: {best_score:.2f})",
        )

    # Fallback based on category
    topic = slugify(chunk.header or Path(source_file).stem.replace("_REPORT", ""))
    today = date.today().isoformat()

    fallback_destinations = {
        "actionable": f"docs/plans/{today}-{topic}.md",
        "decisions": f"docs/adr/{today}-{topic}.md",
        "findings": f"docs/{topic}.md",
        "metrics": "docs/benchmarks.md",
        "migration": "docs/migration-guide.md",
        "api_changes": "CHANGELOG.md",
    }

    destination = fallback_destinations.get(chunk.category, f"docs/{topic}.md")

    return Route(
        chunk_header=chunk.header,
        category=chunk.category,
        value=chunk.value,
        destination=destination,
        strategy="CREATE_NEW",
        rationale=f"No semantic match, using {chunk.category} fallback",
    )


def slugify(text: str) -> str:
    """Convert text to kebab-case slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:50]


def generate_plan(source_file: str, docs_dir: str = "docs") -> ConsolidationPlan:
    """Generate complete consolidation plan for a source file."""
    chunks = extract_chunks(source_file)
    existing_docs = find_existing_docs(docs_dir)

    routes = []
    skipped = []

    for chunk in chunks:
        if chunk.value == "low":
            skipped.append({"header": chunk.header, "reason": "Low value content"})
            continue

        route = route_chunk(chunk, existing_docs, source_file)
        routes.append(route)

    summary = {
        "total_chunks": len(chunks),
        "routed": len(routes),
        "skipped": len(skipped),
        "new_files": sum(1 for r in routes if r.strategy == "CREATE_NEW"),
        "updates": sum(1 for r in routes if r.strategy != "CREATE_NEW"),
    }

    return ConsolidationPlan(
        source=source_file, routes=routes, skipped=skipped, summary=summary
    )


def format_plan_markdown(plan: ConsolidationPlan) -> str:
    """Format consolidation plan as markdown for user review."""
    lines = ["# Consolidation Plan", "", f"## Source: {plan.source}", ""]

    if plan.routes:
        lines.extend(
            [
                "### Content to Consolidate",
                "",
                "| Chunk | Category | Value | Destination | Strategy |",
                "|-------|----------|-------|-------------|----------|",
            ]
        )
        for route in plan.routes:
            lines.append(
                f"| {route.chunk_header} | {route.category} | {route.value} | "
                f"`{route.destination}` | {route.strategy} |"
            )
        lines.append("")

    if plan.skipped:
        lines.extend(
            ["### Skipped (Low Value)", "", "| Chunk | Reason |", "|-------|--------|"]
        )
        for item in plan.skipped:
            lines.append(f"| {item['header']} | {item['reason']} |")
        lines.append("")

    lines.extend(
        [
            "### Summary",
            "",
            f"- Total chunks: {plan.summary['total_chunks']}",
            f"- To consolidate: {plan.summary['routed']}",
            f"- New files: {plan.summary['new_files']}",
            f"- Updates: {plan.summary['updates']}",
            f"- Skipped: {plan.summary['skipped']}",
            "",
            "### Post-Consolidation",
            f"- Delete: `{plan.source}`",
            "",
            "---",
            "**Proceed with consolidation? [Y/n]**",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Consolidation planner for doc-consolidation skill"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # scan command
    scan_parser = subparsers.add_parser(
        "scan", help="Scan for consolidation candidates"
    )
    scan_parser.add_argument("--repo-path", default=".", help="Repository path")
    scan_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # analyze command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze files and generate chunks"
    )
    analyze_parser.add_argument("files", nargs="+", help="Files to analyze")
    analyze_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # plan command
    plan_parser = subparsers.add_parser("plan", help="Generate consolidation plan")
    plan_parser.add_argument("file", help="Source file to plan")
    plan_parser.add_argument(
        "--docs-dir", default="docs", help="Documentation directory"
    )
    plan_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.command == "scan":
        candidates = scan_for_candidates(args.repo_path)
        if args.json:
            print(json.dumps([asdict(c) for c in candidates], indent=2))
        elif not candidates:
            print("No consolidation candidates found.")
        else:
            print(f"Found {len(candidates)} candidate(s):\n")
            for c in candidates:
                print(f"  {c.path} (score: {c.score})")
                for reason in c.reasons:
                    print(f"    - {reason}")
                print()

    elif args.command == "analyze":
        all_chunks = []
        for file_path in args.files:
            chunks = extract_chunks(file_path)
            if args.json:
                all_chunks.extend([asdict(c) for c in chunks])
            else:
                print(f"\n## {file_path}\n")
                for chunk in chunks:
                    print(
                        f"  [{chunk.category}] {chunk.header} ({chunk.value}, {chunk.char_count} chars)"
                    )

        if args.json:
            print(json.dumps(all_chunks, indent=2))

    elif args.command == "plan":
        plan = generate_plan(args.file, args.docs_dir)
        if args.json:
            print(json.dumps(asdict(plan), indent=2))
        else:
            print(format_plan_markdown(plan))

    return 0


if __name__ == "__main__":
    sys.exit(main())
