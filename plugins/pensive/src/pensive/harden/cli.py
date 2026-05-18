"""CLI entry point for the harden detector pipeline.

Wired as ``python -m pensive.harden`` (see ``__main__.py``). The
skill's /harden command shells out to this module to collect
findings, then renders them into the user-facing report.

This is the v1 detector wiring: AST-based Python detectors only,
no proposals applied, JSON or text output. The skill's modules
document the additional pipeline phases (proposal generation,
approval gate, apply + validate); future versions will extend the
CLI to drive those phases.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from .scanner import scan_directory
from .types import Finding


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pensive-harden",
        description=(
            "Scan a Python codebase for hardening opportunities. Emits a "
            "list of findings with CWE / NIST SSDF citations. Detector "
            "set is the v1 MVP (PY01-PY20 partial); see the harden "
            "skill's modules for the full ruleset."
        ),
    )
    p.add_argument(
        "--path",
        type=Path,
        default=Path.cwd(),
        help="Directory to scan (default: current dir).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable text.",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Exit non-zero when any HIGH-or-above finding is reported. "
            "Suitable for CI gates."
        ),
    )
    p.add_argument(
        "--severity",
        choices=("CRITICAL", "HIGH", "MEDIUM", "LOW", "ADVISORY"),
        default="LOW",
        help="Report findings at this severity or higher (default: LOW).",
    )
    return p


_SEVERITY_RANK = {
    "ADVISORY": 0,
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}


def _filter_severity(findings: list[Finding], floor: str) -> list[Finding]:
    floor_rank = _SEVERITY_RANK[floor]
    return [f for f in findings if _SEVERITY_RANK[f.severity] >= floor_rank]


def _render_text(findings: list[Finding], path: Path) -> str:
    if not findings:
        return f"harden: no findings under {path}\n"

    by_severity: dict[str, int] = dict(Counter(f.severity for f in findings))
    lines = [
        f"harden: {len(findings)} finding(s) under {path}",
        "  by severity: "
        + ", ".join(
            f"{k}={by_severity.get(k, 0)}"
            for k in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "ADVISORY")
            if by_severity.get(k, 0)
        ),
        "",
    ]
    for f in findings:
        cite = str(f.citation) if f.citation is not None else "(uncited advisory)"
        lines.append(f"[{f.severity}] {f.id} {f.file}:{f.line}")
        lines.append(f"  citation: {cite}")
        lines.append(f"  signal: {f.detection_signal}")
        if f.proposal:
            lines.append(f"  proposal: {f.proposal}")
        lines.append("")
    return "\n".join(lines)


def run_cli(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    findings = scan_directory(args.path)
    findings = _filter_severity(findings, args.severity)

    if args.json:
        payload = {
            "success": True,
            "data": {
                "path": str(args.path),
                "finding_count": len(findings),
                "by_severity": dict(Counter(str(f.severity) for f in findings)),
                "findings": [f.to_dict() for f in findings],
            },
        }
        print(json.dumps(payload, indent=2))
    else:
        sys.stdout.write(_render_text(findings, args.path))

    if args.strict:
        # Strict mode: any HIGH-or-above finding is an exit-non-zero condition.
        high_or_above = [
            f for f in findings if _SEVERITY_RANK[f.severity] >= _SEVERITY_RANK["HIGH"]
        ]
        if high_or_above:
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(run_cli())
