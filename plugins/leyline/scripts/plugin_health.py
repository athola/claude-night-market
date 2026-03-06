#!/usr/bin/env python3
"""Plugin health dimensions measurement.

Measures five health dimensions per plugin:
1. Documentation freshness
2. Test coverage
3. Code quality
4. Contributor friendliness
5. Improvement velocity

All dimensions return descriptive strings, not numeric scores.

Part of the stewardship framework. See: STEWARDSHIP.md
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

from stewardship_tracker import read_actions

NOT_MEASURED = "not measured"


def measure_doc_freshness(plugin_dir: Path) -> str:
    """Measure how recently documentation was updated.

    Returns a descriptive string like "updated 3 days ago"
    or "not measured" if no .md files exist.
    """
    if not plugin_dir.exists():
        return NOT_MEASURED

    md_files = list(plugin_dir.rglob("*.md"))
    if not md_files:
        return NOT_MEASURED

    most_recent = max(f.stat().st_mtime for f in md_files)
    age_days = int((time.time() - most_recent) / 86400)

    if age_days == 0:
        return "docs updated today"
    elif age_days == 1:
        return "docs updated 1 day ago"
    else:
        return f"docs updated {age_days} days ago"


def measure_test_coverage(plugin_dir: Path) -> str:
    """Report test coverage if available.

    Looks for a coverage report file. Returns "not measured"
    if unavailable.
    """
    coverage_file = plugin_dir / ".coverage"

    if coverage_file.exists():
        return "coverage data available (run pytest --cov for details)"

    return NOT_MEASURED


def measure_code_quality(plugin_dir: Path) -> str:
    """Report code quality indicators.

    Checks for presence of quality tooling configuration.
    """
    if not plugin_dir.exists():
        return NOT_MEASURED

    indicators: list[str] = []
    if (plugin_dir / "pyproject.toml").exists():
        indicators.append("pyproject.toml configured")
    if list(plugin_dir.glob("tests/**/*.py")):
        indicators.append("tests present")
    if (plugin_dir / "Makefile").exists():
        indicators.append("Makefile targets available")

    if not indicators:
        return NOT_MEASURED

    return ", ".join(indicators)


def measure_contributor_friendliness(plugin_dir: Path) -> str:
    """Report contributor-friendliness indicators.

    Checks for README, stewardship section, examples.
    """
    if not plugin_dir.exists():
        return NOT_MEASURED

    indicators: list[str] = []
    readme = plugin_dir / "README.md"
    if readme.exists():
        content = readme.read_text()
        indicators.append("README present")
        if "## Stewardship" in content:
            indicators.append("stewardship section")
        if "```" in content:
            indicators.append("code examples")

    if not indicators:
        return NOT_MEASURED

    return ", ".join(indicators)


def measure_improvement_velocity(
    actions_dir: Path,
    plugin_name: str,
) -> str:
    """Count stewardship actions for a plugin in the last 30 days.

    Delegates JSONL parsing to stewardship_tracker.read_actions(),
    then filters by timestamp.
    """
    actions = read_actions(actions_dir, plugin=plugin_name)
    if not actions and not (actions_dir / "actions.jsonl").exists():
        return NOT_MEASURED

    cutoff = time.time() - (30 * 86400)
    count = 0
    for entry in actions:
        timestamp_str = entry.get("timestamp", "")
        if timestamp_str:
            try:
                entry_time = datetime.fromisoformat(
                    timestamp_str.replace("Z", "+00:00")
                )
                if entry_time.timestamp() < cutoff:
                    continue
            except (ValueError, AttributeError):
                pass
        count += 1

    if count == 0:
        return "no stewardship actions recorded"
    elif count == 1:
        return "1 stewardship action recorded"
    else:
        return f"{count} stewardship actions recorded"


def get_plugin_health(
    plugin_dir: Path,
    actions_dir: Path,
    plugin_name: str,
) -> dict[str, str]:
    """Get all five health dimensions for a plugin.

    Returns a dict with descriptive strings for each dimension.
    """
    return {
        "doc_freshness": measure_doc_freshness(plugin_dir),
        "test_coverage": measure_test_coverage(plugin_dir),
        "code_quality": measure_code_quality(plugin_dir),
        "contributor_friendliness": measure_contributor_friendliness(plugin_dir),
        "improvement_velocity": measure_improvement_velocity(actions_dir, plugin_name),
    }
