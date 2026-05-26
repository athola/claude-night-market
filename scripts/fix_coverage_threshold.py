#!/usr/bin/env python3
"""Migrate coverage threshold enforcement out of pytest addopts/config.

Removes --cov-fail-under from addopts and fail_under from
[tool.coverage.report] in every plugin's pyproject.toml.
Writes the threshold value to [tool.nightmarket] so the
run-plugin-tests.sh script can enforce it explicitly for full
suite runs only.

This prevents content-assertion tests (SKILL.md tests that
don't import Python source) from tripping the coverage
threshold when run in isolation.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def extract_threshold(content: str) -> int:
    """Extract fail_under from [tool.coverage.report] or --cov-fail-under."""
    # Try [tool.coverage.report] fail_under first
    in_report = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == "[tool.coverage.report]":
            in_report = True
        elif stripped.startswith("[") and stripped.endswith("]"):
            in_report = False
        elif in_report:
            m = re.match(r"^fail_under\s*=\s*(\d+)", stripped)
            if m:
                return int(m.group(1))

    # Fallback: try --cov-fail-under in addopts
    m = re.search(r"--cov-fail-under=(\d+)", content)
    if m:
        return int(m.group(1))

    return 0


def remove_cov_fail_under_from_addopts(content: str) -> str:
    """Remove --cov-fail-under=N from addopts in both array and string forms."""
    # Array form: "    \"--cov-fail-under=90\",\n"
    content = re.sub(r'\n?\s*"--cov-fail-under=\d+",?', "", content)
    # String form inline: " --cov-fail-under=90"
    content = re.sub(r"\s*--cov-fail-under=\d+", "", content)
    return content


def remove_fail_under_from_report_section(content: str) -> str:
    """Remove fail_under = N from [tool.coverage.report] section."""
    lines = content.splitlines(keepends=True)
    in_report = False
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped == "[tool.coverage.report]":
            in_report = True
            result.append(line)
        elif stripped.startswith("[") and in_report:
            in_report = False
            result.append(line)
        elif in_report and re.match(r"^fail_under\s*=", stripped):
            pass  # drop this line
        else:
            result.append(line)
    return "".join(result)


def add_nightmarket_section(content: str, threshold: int) -> str:
    """Add [tool.nightmarket] with coverage_threshold if not already present."""
    if "[tool.nightmarket]" in content:
        # Update existing entry
        content = re.sub(
            r"(\[tool\.nightmarket\].*?)(coverage_threshold\s*=\s*\d+)",
            rf"\g<1>coverage_threshold = {threshold}",
            content,
            flags=re.DOTALL,
        )
        if "coverage_threshold" not in content[content.index("[tool.nightmarket]") :]:
            # Section exists but key missing — append key after section header
            content = content.replace(
                "[tool.nightmarket]",
                f"[tool.nightmarket]\ncoverage_threshold = {threshold}",
                1,
            )
        return content

    # Prefer inserting before [build-system] for visibility
    if "[build-system]" in content:
        return content.replace(
            "[build-system]",
            f"[tool.nightmarket]\ncoverage_threshold = {threshold}\n\n[build-system]",
            1,
        )
    return content + f"\n[tool.nightmarket]\ncoverage_threshold = {threshold}\n"


def migrate_plugin(pyproject_path: Path, dry_run: bool = False) -> bool:
    """Process one pyproject.toml. Returns True if changed."""
    content = pyproject_path.read_text()

    threshold = extract_threshold(content)
    if threshold == 0:
        print(f"  {pyproject_path.parent.name}: no coverage threshold found, skipping")
        return False

    updated = remove_cov_fail_under_from_addopts(content)
    updated = remove_fail_under_from_report_section(updated)
    updated = add_nightmarket_section(updated, threshold)

    if updated == content:
        print(f"  {pyproject_path.parent.name}: no changes needed")
        return False

    if dry_run:
        print(f"  {pyproject_path.parent.name}: would update (threshold={threshold}%)")
        return True

    pyproject_path.write_text(updated)
    print(f"  {pyproject_path.parent.name}: updated (threshold={threshold}%)")
    return True


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    root = Path(__file__).parent.parent
    plugins_dir = root / "plugins"

    print("Migrating coverage thresholds" + (" (dry run)" if dry_run else "") + ":")
    changed = 0
    for plugin_dir in sorted(plugins_dir.iterdir()):
        pyproject = plugin_dir / "pyproject.toml"
        if pyproject.exists():
            if migrate_plugin(pyproject, dry_run=dry_run):
                changed += 1

    print(f"\n{changed} plugins updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
