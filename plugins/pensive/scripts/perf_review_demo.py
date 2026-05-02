"""LIVE demo: dogfood the performance-review skill on pensive's own source.

Walks `src/pensive/` and prints any time/space complexity findings the
skill detects. Used by `make demo-performance-review`.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

from pensive.skills.performance_review import PerformanceReviewSkill


def main() -> int:
    skill = PerformanceReviewSkill()
    src_root = Path("src/pensive")
    if not src_root.is_dir():
        print("Run from plugins/pensive: src/pensive not found.")
        return 1

    files = sorted(src_root.rglob("*.py"))
    print("=== performance-review Demo: pensive/src/pensive (LIVE) ===")
    print(f"Scanning {len(files)} Python files...\n")

    by_severity: dict[str, int] = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
    }
    total = 0
    for path in files:
        ctx = Mock()
        ctx.get_file_content.return_value = path.read_text(encoding="utf-8")
        result = skill.analyze(ctx, str(path))
        if not result.issues:
            continue
        print(f"{path}:")
        for finding in result.issues:
            print(
                f"  [{finding.severity}] L{finding.line} "
                f"{finding.category}: {finding.message}"
            )
            by_severity[finding.severity] = by_severity.get(finding.severity, 0) + 1
            total += 1
        print()

    print(f"=== Summary: {total} finding(s) across {len(files)} file(s) ===")
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        print(f"  {sev:8s} {by_severity.get(sev, 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
