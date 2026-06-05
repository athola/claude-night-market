#!/usr/bin/env python3
"""Verify review findings are grounded in real source.

The semantic complement to ``contract_validator`` (which checks finding
*structure*). For each finding this re-reads the cited ``file:line`` and
confirms a verbatim ``anchor`` snippet actually appears there. A finding
whose path does not resolve, whose line is out of range, or whose anchor
does not match the source is FAILED -- that is the hallucination guard.

Exit codes: 0 all findings verified (or lenient), 1 a finding failed,
2 the findings file is missing or unparseable.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# A structured-output finding block: "- **Location**: path:line"
LOCATION_PATTERN = re.compile(r"-\s*\*\*Location\*\*:\s*([^\s:]+):(\d+)", re.IGNORECASE)
# "- **Anchor**: `verbatim text`" (backticks optional)
ANCHOR_PATTERN = re.compile(
    r"-\s*\*\*Anchor\*\*:\s*`?([^`\n]+?)`?\s*$", re.IGNORECASE | re.MULTILINE
)
# "### [SEVERITY] Title" finding heading
HEADING_PATTERN = re.compile(r"^###\s+(.+)$", re.MULTILINE)

# How many lines on either side of the cited line the anchor may appear on.
DEFAULT_WINDOW = 2


def _normalize(text: str) -> str:
    """Collapse all whitespace runs and strip, for tolerant matching."""
    return " ".join(text.split())


@dataclass
class Finding:
    """A single review finding with a citation to verify."""

    id: str
    file: str
    line: int | None
    anchor: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Finding:
        """Build a Finding from a findings-file entry."""
        raw_line = data.get("line")
        line: int | None
        try:
            line = int(raw_line) if raw_line is not None else None
        except (TypeError, ValueError):
            line = None
        return cls(
            id=str(data.get("id", "?")),
            file=str(data.get("file", "") or ""),
            line=line,
            anchor=str(data.get("anchor", "") or ""),
        )


@dataclass
class CitationResult:
    """Verdict for one finding's citation."""

    id: str
    status: str  # "VERIFIED" | "FAILED"
    reason: str = ""


@dataclass
class VerificationReport:
    """Aggregate verdict across all findings."""

    passed: bool
    verified_count: int
    failed_count: int
    results: list[CitationResult] = field(default_factory=list)

    def failures(self) -> list[CitationResult]:
        """Return only the FAILED citation results."""
        return [r for r in self.results if r.status == "FAILED"]

    def report_text(self) -> str:
        """Render a human-readable verdict block."""
        verdict = "PASS" if self.passed else "FAIL"
        lines = [
            f"Citation verification: {verdict}",
            f"  Verified: {self.verified_count}  Failed: {self.failed_count}",
        ]
        for r in self.results:
            if r.status == "FAILED":
                lines.append(f"  [FAILED] {r.id}: {r.reason}")
        return "\n".join(lines)


def _read_cited_file(
    finding: Finding,
    repo_root: Path,
) -> tuple[list[str], str | None]:
    """Resolve the cited file and return its lines, or an error reason.

    Folds the path-escape and existence checks into one place so the
    caller stays within a single failure branch.
    """
    repo_resolved = repo_root.resolve()
    target = (repo_root / finding.file).resolve()
    if not (target == repo_resolved or repo_resolved in target.parents):
        return [], f"path escapes repo root: {finding.file}"
    if not target.is_file():
        return [], f"file not found: {finding.file}"
    return target.read_text(errors="replace").splitlines(), None


def verify_finding(
    finding: Finding,
    repo_root: Path,
    window: int = DEFAULT_WINDOW,
) -> CitationResult:
    """Re-read the cited file:line and confirm the anchor is present.

    Order of checks: a finding must have an anchor and a line, the path
    must resolve inside the repo and exist, the line must be in range,
    and the normalized anchor must appear within +/-window lines.
    """
    if not finding.anchor.strip():
        return CitationResult(finding.id, "FAILED", "no anchor provided")
    if finding.line is None:
        return CitationResult(finding.id, "FAILED", "no line provided")

    source_lines, error = _read_cited_file(finding, repo_root)
    if error is not None:
        return CitationResult(finding.id, "FAILED", error)

    total = len(source_lines)
    if finding.line < 1 or finding.line > total:
        return CitationResult(
            finding.id,
            "FAILED",
            f"line {finding.line} out of range (file has {total} lines)",
        )

    # 1-indexed line -> 0-indexed slice, inclusive +/- window.
    start = max(0, finding.line - 1 - window)
    end = min(total, finding.line - 1 + window + 1)
    needle = _normalize(finding.anchor)
    for src in source_lines[start:end]:
        if needle in _normalize(src):
            return CitationResult(finding.id, "VERIFIED")
    return CitationResult(
        finding.id, "FAILED", f"anchor not found near line {finding.line}"
    )


def verify_findings(
    findings: list[dict[str, Any]],
    repo_root: Path,
    strictness: str = "normal",
    window: int = DEFAULT_WINDOW,
) -> VerificationReport:
    """Verify every finding; aggregate into a report.

    ``strictness`` mirrors the proof-of-work output-contract vocabulary:
    ``strict``/``normal`` fail on any unresolved citation; ``lenient``
    records failures but still passes (for exploratory work).
    """
    results = [
        verify_finding(Finding.from_dict(f), repo_root, window) for f in findings
    ]
    failed_count = sum(1 for r in results if r.status == "FAILED")
    verified_count = sum(1 for r in results if r.status == "VERIFIED")
    passed = True if strictness == "lenient" else failed_count == 0
    return VerificationReport(
        passed=passed,
        verified_count=verified_count,
        failed_count=failed_count,
        results=results,
    )


def parse_markdown_findings(text: str) -> list[dict[str, Any]]:
    """Extract findings from structured-output markdown blocks.

    Each block is delimited by a ``### Title`` heading and carries a
    ``**Location**: file:line`` and optional ``**Anchor**: `snippet```.
    """
    findings: list[dict[str, Any]] = []
    headings = list(HEADING_PATTERN.finditer(text))
    for idx, match in enumerate(headings):
        start = match.end()
        end = headings[idx + 1].start() if idx + 1 < len(headings) else len(text)
        block = text[start:end]
        loc = LOCATION_PATTERN.search(block)
        if not loc:
            continue
        anchor_match = ANCHOR_PATTERN.search(block)
        findings.append(
            {
                "id": match.group(1).strip() or f"F{idx + 1}",
                "file": loc.group(1),
                "line": int(loc.group(2)),
                "anchor": anchor_match.group(1).strip() if anchor_match else "",
            }
        )
    return findings


def load_findings(path: Path) -> list[dict[str, Any]]:
    """Load findings from a JSON list, a wrapped object, or markdown."""
    text = path.read_text()
    if path.suffix.lower() in {".md", ".markdown"}:
        return parse_markdown_findings(text)
    if path.suffix.lower() == ".json":
        return _findings_from_json(json.loads(text))
    # Unknown suffix: try JSON, fall back to markdown.
    try:
        return _findings_from_json(json.loads(text))
    except json.JSONDecodeError:
        return parse_markdown_findings(text)


def _findings_from_json(data: Any) -> list[dict[str, Any]]:
    """Normalize parsed JSON into a list of finding dicts."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "findings" in data:
            findings = data["findings"]
            if not isinstance(findings, list):
                raise json.JSONDecodeError("'findings' must be a list", str(data), 0)
            return findings
        return [data]
    raise json.JSONDecodeError("unexpected findings JSON shape", str(data), 0)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: verify a findings file against the source tree."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--findings",
        type=Path,
        required=True,
        help="Path to findings file (.json or .md)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Repo root the file:line citations resolve against",
    )
    parser.add_argument(
        "--strictness",
        choices=["strict", "normal", "lenient"],
        default="normal",
        help="strict/normal fail on any unresolved citation; lenient warns",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args(argv)

    if not args.findings.exists():
        print(f"ERROR: findings file not found: {args.findings}")
        return 2
    try:
        findings = load_findings(args.findings)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: could not parse findings file: {exc}")
        return 2

    report = verify_findings(findings, args.repo_root, strictness=args.strictness)

    if args.format == "json":
        print(
            json.dumps(
                {
                    "passed": report.passed,
                    "verified_count": report.verified_count,
                    "failed_count": report.failed_count,
                    "failures": [
                        {"id": r.id, "reason": r.reason} for r in report.failures()
                    ],
                },
                indent=2,
            )
        )
    else:
        print(report.report_text())

    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
