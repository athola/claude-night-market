"""curate_problems.py -- Problem bank curation and gap analysis.

Read-only analysis tool. Surveys the current YAML problem bank,
compares coverage against the manifest expected counts, identifies
gaps, and proposes schema-valid entries for human review.

This script intentionally has NO --write or --fix flag. It never
modifies files under data/problems/. All output is a markdown report
written to a separate path, or printed to stdout.

Usage::

    python scripts/curate_problems.py [PROBLEMS_DIR] [--output PATH]

Arguments:
    PROBLEMS_DIR    Path to data/problems/ directory.
                    Defaults to data/problems/ relative to repo root.
    --output PATH   Write the markdown report to PATH instead of stdout.
    --verbose       Print per-category counts in addition to gaps.

"""

from __future__ import annotations

import argparse
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Resolve the gauntlet package from the src layout so this standalone script
# can import it without installing via pip when run directly.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).parents[3]
_SRC = _REPO_ROOT / "plugins" / "gauntlet" / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from gauntlet.models import (  # noqa: E402 - must follow sys.path mutation
    BankProblem,
    Difficulty,
)

# Valid difficulty strings (mirrors Difficulty enum)
_VALID_DIFFICULTIES = {d.value for d in Difficulty}

# Valid challenge_type strings (mirrors ChallengeType enum values)
_VALID_CHALLENGE_TYPES = {
    "explain_why",
    "multiple_choice",
    "trace",
    "code_complete",
    "debug",
    "rank",
}

# Required fields for a proposed problem entry
_REQUIRED_FIELDS = {"id", "title", "difficulty", "prompt"}


# ---------------------------------------------------------------------------
# Public API (imported by tests)
# ---------------------------------------------------------------------------


def survey_bank_coverage(problems_dir: Path) -> dict[str, int]:
    """Return a dict mapping category_id to problem count.

    Reads all *.yaml files in *problems_dir* that do not start with '_'.
    Each file must have a top-level ``category`` key and a ``problems``
    list.  The returned category key is taken from the file-level
    ``category`` field when present; otherwise from the filename stem.
    """
    counts: dict[str, int] = {}
    for yaml_file in sorted(problems_dir.glob("*.yaml")):
        if yaml_file.name.startswith("_"):
            continue
        data = _load_yaml_safe(yaml_file)
        problems = data.get("problems", [])
        if not problems:
            continue
        category = data.get("category", yaml_file.stem)
        counts[category] = len(problems)
    return counts


def identify_gaps(
    current_counts: dict[str, int],
    manifest_categories: list[dict],
) -> list[dict]:
    """Return categories whose problem count is below the expected NeetCode count.

    Each gap entry is a dict with keys:
        category_id, category_name, expected, actual, missing

    The list is sorted descending by *missing* so the worst gaps come first.
    Categories with ``neetcode_count == 0`` are not considered gaps.
    """
    gaps: list[dict] = []
    for cat in manifest_categories:
        expected = cat.get("neetcode_count", 0)
        if expected == 0:
            continue
        cat_id = cat["id"]
        actual = current_counts.get(cat_id, 0)
        if actual < expected:
            gaps.append(
                {
                    "category_id": cat_id,
                    "category_name": cat.get("name", cat_id),
                    "expected": expected,
                    "actual": actual,
                    "missing": expected - actual,
                }
            )
    gaps.sort(key=lambda g: g["missing"], reverse=True)
    return gaps


def validate_proposed_entry(proposed: dict[str, Any]) -> list[str]:
    """Validate one proposed problem dict against the BankProblem schema.

    Returns a list of human-readable error strings.  Empty means valid.
    Does not write anything to disk.
    """
    errors: list[str] = []

    # Required field check
    for field in _REQUIRED_FIELDS:
        if field not in proposed:
            errors.append(f"Missing required field: '{field}'")

    # Difficulty enum check
    difficulty = proposed.get("difficulty")
    if difficulty is not None and difficulty not in _VALID_DIFFICULTIES:
        valid = ", ".join(sorted(_VALID_DIFFICULTIES))
        errors.append(f"Invalid difficulty '{difficulty}'. Must be one of: {valid}")

    # challenge_type check (optional field)
    challenge_type = proposed.get("challenge_type")
    if challenge_type is not None and challenge_type not in _VALID_CHALLENGE_TYPES:
        valid = ", ".join(sorted(_VALID_CHALLENGE_TYPES))
        errors.append(
            f"Invalid challenge_type '{challenge_type}'. Must be one of: {valid}"
        )

    # Try constructing a BankProblem for deep validation when no prior errors
    if not errors:
        try:
            BankProblem.from_dict(proposed)
        except Exception as exc:  # noqa: BLE001 - BankProblem.from_dict raises various exception types
            errors.append(f"Schema validation failed: {exc}")

    return errors


def validate_proposed_entries(
    proposals: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """Validate a batch of proposed entries.

    Returns a dict mapping each entry's ``id`` (or its list index as a
    string) to a list of error strings.
    """
    results: dict[str, list[str]] = {}
    for i, proposal in enumerate(proposals):
        key = str(proposal.get("id", i))
        results[key] = validate_proposed_entry(proposal)
    return results


def generate_report(problems_dir: Path, output_path: Path) -> None:
    """Analyse *problems_dir* and write a markdown report to *output_path*.

    Never modifies any file inside *problems_dir*.
    """
    manifest_path = problems_dir / "_manifest.yaml"
    manifest = _load_yaml_safe(manifest_path) if manifest_path.exists() else {}
    manifest_categories = manifest.get("categories", [])

    coverage = survey_bank_coverage(problems_dir)
    gaps = identify_gaps(coverage, manifest_categories)

    lines = _build_report_lines(coverage, manifest_categories, gaps)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    """Return the CLI argument parser for curate_problems.

    Intentionally exposes no --write or --fix flag to prevent accidental
    mutation of curated problem files.
    """
    parser = argparse.ArgumentParser(
        prog="curate_problems",
        description=(
            "Survey the gauntlet problem bank, identify coverage gaps, and "
            "produce a human-review report. Read-only: never modifies "
            "data/problems/ files."
        ),
    )
    parser.add_argument(
        "problems_dir",
        nargs="?",
        type=Path,
        default=None,
        help=(
            "Path to the problems directory (default: "
            "plugins/gauntlet/data/problems/ relative to repo root)."
        ),
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Write the markdown report to this file instead of stdout.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print per-category counts in addition to gap analysis.",
    )
    return parser


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_yaml_safe(path: Path) -> dict[str, Any]:
    """Load YAML from *path*, returning an empty dict on any error."""
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001 - yaml errors, file errors, and type errors all safe to swallow here
        return {}


def _build_report_lines(
    coverage: dict[str, int],
    manifest_categories: list[dict],
    gaps: list[dict],
) -> list[str]:
    """Return a list of markdown lines for the curation report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines: list[str] = [
        "# Gauntlet Problem Bank Curation Report",
        "",
        f"Generated: {now}",
        "",
        "## Coverage Summary",
        "",
    ]

    if manifest_categories:
        lines += [
            "| Category | Expected | Actual | Status |",
            "|----------|----------|--------|--------|",
        ]
        cat_map = {c["id"]: c for c in manifest_categories}
        for cat_id, actual in sorted(coverage.items()):
            expected = cat_map.get(cat_id, {}).get("neetcode_count", "?")
            if isinstance(expected, int) and actual >= expected:
                status = "complete"
            elif isinstance(expected, int):
                status = f"gap ({expected - actual} missing)"
            else:
                status = "unknown"
            lines.append(f"| {cat_id} | {expected} | {actual} | {status} |")
        # Categories in manifest but not in bank
        for cat in manifest_categories:
            if cat["id"] not in coverage and cat.get("neetcode_count", 0) > 0:
                expected = cat["neetcode_count"]
                lines.append(
                    f"| {cat['id']} | {expected} | 0 | gap ({expected} missing) |"
                )
    else:
        lines += [
            "| Category | Actual |",
            "|----------|--------|",
        ]
        for cat_id, actual in sorted(coverage.items()):
            lines.append(f"| {cat_id} | {actual} |")

    lines += [""]

    if gaps:
        lines += [
            "## Coverage Gaps",
            "",
            "The following categories have fewer problems than expected.",
            "These are candidates for new problem proposals.",
            "",
            "| Category | Expected | Actual | Missing |",
            "|----------|----------|--------|---------|",
        ]
        for gap in gaps:
            lines.append(
                f"| {gap['category_name']} | {gap['expected']} "
                f"| {gap['actual']} | {gap['missing']} |"
            )
        lines += [""]
    else:
        lines += [
            "## Coverage Gaps",
            "",
            "No gaps detected. All categories meet the expected counts.",
            "",
        ]

    lines += [
        "## Proposed New Problems",
        "",
        "Place proposed YAML entries below for human review.",
        "Each entry must follow the BankProblem schema:",
        "",
        "```yaml",
        "- id: category-NNN",
        "  title: Problem Title",
        "  difficulty: easy  # easy | medium | hard | extra_hard",
        "  prompt: |",
        "    Problem statement here.",
        "  hints:",
        "    - First hint.",
        "  solution_outline: |",
        "    Approach and complexity.",
        "  tags: [tag1, tag2]",
        "  neetcode_id: neetcode-NNN",
        "  challenge_type: explain_why",
        "```",
        "",
        "Run `python scripts/curate_problems.py --validate-proposals FILE`",
        "to validate entries before submitting a pull request.",
        "",
        "## Notes",
        "",
        "This report is for human review only. The curate_problems script",
        "does not modify any files under data/problems/.",
    ]
    return lines


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:  # pragma: no cover
    """Entry point for the curate_problems CLI."""
    parser = build_arg_parser()
    args = parser.parse_args()

    default_dir = Path(__file__).parents[1] / "data" / "problems"
    problems_dir: Path = args.problems_dir or default_dir

    if not problems_dir.is_dir():
        print(f"ERROR: problems directory not found: {problems_dir}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        generate_report(problems_dir, args.output)
        print(f"Report written to {args.output}")
    else:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        generate_report(problems_dir, tmp_path)
        print(tmp_path.read_text(encoding="utf-8"))
        tmp_path.unlink()


if __name__ == "__main__":
    main()
