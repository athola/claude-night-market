"""Rules validator for Claude Code .claude/rules/ directories.

Validates YAML frontmatter, glob patterns, content quality, and organization
of Claude Code rule files. Supports path-scoped rules (via `paths` frontmatter)
and unconditional rules (no `paths` field).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

# Cursor-specific fields that should NOT appear in Claude Code rules
CURSOR_FIELDS = frozenset({"globs", "alwaysApply", "always_apply"})

# Known valid frontmatter fields for Claude Code rules
VALID_FIELDS = frozenset({"paths", "description"})

# Non-descriptive filenames that suggest poor organization
NON_DESCRIPTIVE_NAMES = frozenset(
    {
        "rules",
        "rules1",
        "rules2",
        "misc",
        "todo",
        "temp",
        "test",
        "stuff",
        "notes",
        "other",
        "general",
    }
)

# Overly broad glob patterns
BROAD_PATTERNS = frozenset({"**/*", "**", "*"})

# Content quality thresholds
MIN_WORD_COUNT = 10
MAX_TOKEN_COUNT = 500
HIGH_TOKEN_COUNT = 1000


def _parse_frontmatter(content: str) -> tuple[dict[str, Any] | None, str, str | None]:
    """Parse YAML frontmatter from markdown content.

    Returns:
        Tuple of (parsed_data, body_content, error_message).
        parsed_data is None if no frontmatter or parse error.
        error_message is None if no error.

    """
    if not content.startswith("---"):
        return None, content, None

    # Find closing delimiter
    end_match = re.search(r"\n---\s*\n", content[3:])
    if end_match is None:
        # Check for closing delimiter at end of content
        end_match = re.search(r"\n---\s*$", content[3:])
        if end_match is None:
            return None, content, None

    yaml_str = content[4 : 3 + end_match.start() + 1]
    body = content[3 + end_match.end() :]

    try:
        parsed = yaml.safe_load(yaml_str)
        if parsed is None:
            parsed = {}
        if not isinstance(parsed, dict):
            return None, body, "Frontmatter must be a YAML mapping"
        return parsed, body, None
    except yaml.YAMLError as exc:
        return None, body, f"YAML parse error: {exc}"


def validate_frontmatter(rule_file: Path) -> dict[str, Any]:
    """Validate frontmatter of a single rule file.

    Args:
        rule_file: Path to the rule markdown file.

    Returns:
        Dict with 'valid' (bool), 'errors' (list[str]), 'warnings' (list[str]),
        'score' (int out of 25).

    """
    errors: list[str] = []
    warnings: list[str] = []
    score = 25  # Start with full score, deduct for issues

    try:
        content = rule_file.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"Cannot read file: {exc}")
        return {"valid": False, "errors": errors, "warnings": [], "score": 0}
    parsed, _body, parse_error = _parse_frontmatter(content)

    # No frontmatter is valid (plain rules file)
    if parsed is None and parse_error is None:
        return {"valid": True, "errors": [], "warnings": [], "score": 25}

    # YAML parse error
    if parse_error is not None:
        errors.append(parse_error)
        return {"valid": False, "errors": errors, "warnings": [], "score": 0}

    if parsed is None:  # pragma: no cover - unreachable but satisfies type checker
        return {"valid": True, "errors": [], "warnings": [], "score": 25}

    # Check for Cursor-specific fields
    for field in CURSOR_FIELDS:
        if field in parsed:
            errors.append(
                f"'{field}' is a Cursor-specific field, not supported by Claude Code. "
                f"Use 'paths' for conditional loading or omit for unconditional rules."
            )
            score -= 5

    # Check unknown fields
    for field in parsed:
        if field not in VALID_FIELDS and field not in CURSOR_FIELDS:
            warnings.append(f"Unknown frontmatter field: '{field}'")
            score -= 2

    # Validate paths field type
    if "paths" in parsed:
        paths_val = parsed["paths"]
        if not isinstance(paths_val, list):
            val_type = type(paths_val).__name__
            errors.append(f"'paths' must be a list of glob patterns, got {val_type}")
            score -= 5
        elif not paths_val:
            warnings.append(
                "'paths' is an empty list; consider removing it for unconditional rules"
            )
            score -= 1

    valid = len(errors) == 0
    score = max(0, score)
    return {"valid": valid, "errors": errors, "warnings": warnings, "score": score}


def validate_glob_patterns(patterns: list[str]) -> dict[str, Any]:
    """Validate a list of glob patterns for correctness and specificity.

    Args:
        patterns: List of glob pattern strings.

    Returns:
        Dict with 'valid' (bool), 'errors' (list[str]), 'warnings' (list[str]),
        'score' (int out of 20).

    """
    errors: list[str] = []
    warnings: list[str] = []
    score = 20

    if not patterns:
        return {"valid": True, "errors": [], "warnings": [], "score": 20}

    for pattern in patterns:
        # Check overly broad patterns
        if pattern in BROAD_PATTERNS:
            warnings.append(
                f"Pattern '{pattern}' is overly broad and matches too many files"
            )
            score -= 5

        # Check for empty pattern
        if not pattern.strip():
            errors.append("Empty glob pattern found")
            score -= 4

    valid = len(errors) == 0
    score = max(0, score)
    return {"valid": valid, "errors": errors, "warnings": warnings, "score": score}


def validate_organization(rules_dir: Path) -> dict[str, Any]:
    """Validate the organization of a rules directory.

    Args:
        rules_dir: Path to the rules directory.

    Returns:
        Dict with 'score' (int out of 15), 'warnings' (list[str]), 'errors' (list[str]).

    """
    warnings: list[str] = []
    errors: list[str] = []
    score = 15

    if not rules_dir.exists():
        errors.append(f"Rules directory does not exist: {rules_dir}")
        return {"score": 0, "warnings": [], "errors": errors}

    md_files = list(rules_dir.rglob("*.md"))
    if not md_files:
        warnings.append("No rule files found in directory")
        return {"score": 0, "warnings": warnings, "errors": []}

    for md_file in md_files:
        stem = md_file.stem.lower()

        # Check for non-descriptive names
        if stem in NON_DESCRIPTIVE_NAMES:
            warnings.append(
                f"Non-descriptive filename: '{md_file.name}'. "
                f"Use a descriptive name like 'api-validation.md'"
            )
            score -= 3

        # Check for spaces in filename
        if " " in md_file.name:
            warnings.append(
                f"Filename contains spaces: '{md_file.name}'. Use kebab-case instead."
            )
            score -= 2

        # Check for non-kebab-case (uppercase, underscores)
        if re.search(r"[A-Z_]", md_file.stem):
            warnings.append(
                f"Filename not in kebab-case: '{md_file.name}'. "
                f"Use lowercase with hyphens."
            )
            score -= 1

        # Check for broken symlinks
        if md_file.is_symlink() and not md_file.resolve().exists():
            errors.append(f"Broken symlink: '{md_file.name}'")
            score -= 3

    score = max(0, score)
    return {"score": score, "warnings": warnings, "errors": errors}


def validate_content_quality(content: str) -> dict[str, Any]:
    """Assess the quality of rule content.

    Args:
        content: The body content of a rule file (after frontmatter).

    Returns:
        Dict with 'score' (int out of 25), 'warnings' (list[str]),
        'token_count' (int estimated).

    """
    warnings: list[str] = []
    score = 25

    # Rough token estimate (words * 1.3)
    words = content.split()
    token_count = int(len(words) * 1.3)

    # Empty content
    if not content.strip():
        warnings.append("Rule file has no content. Add actionable guidance.")
        return {"score": 0, "warnings": warnings, "token_count": 0}

    # Very short content
    if len(words) < MIN_WORD_COUNT:
        warnings.append("Rule content is very short. Consider adding more detail.")
        score -= 5

    # Verbose content
    if token_count > MAX_TOKEN_COUNT:
        warnings.append(
            f"Rule content is verbose ({token_count} estimated tokens). "
            f"Consider splitting into multiple focused files."
        )
        score -= 5

    return {"score": max(0, score), "warnings": warnings, "token_count": token_count}


def evaluate_rules_directory(rules_dir: Path) -> dict[str, Any]:  # noqa: PLR0915
    """Run a comprehensive evaluation of a rules directory.

    Args:
        rules_dir: Path to the .claude/rules/ directory.

    Returns:
        Dict with 'total_score' (int 0-100), 'files_evaluated' (int),
        'errors' (list[str]), 'warnings' (list[str]), 'file_results' (list).

    """
    all_errors: list[str] = []
    all_warnings: list[str] = []
    file_results: list[dict[str, Any]] = []

    if not rules_dir.exists():
        all_errors.append(f"Rules directory does not exist: {rules_dir}")
        return {
            "total_score": 0,
            "files_evaluated": 0,
            "errors": all_errors,
            "warnings": [],
            "file_results": [],
        }

    md_files = sorted(rules_dir.rglob("*.md"))
    if not md_files:
        all_warnings.append("No rule files found")
        return {
            "total_score": 0,
            "files_evaluated": 0,
            "errors": [],
            "warnings": all_warnings,
            "file_results": [],
        }

    # Evaluate organization (15 points)
    org_result = validate_organization(rules_dir)
    org_score = org_result["score"]
    all_warnings.extend(org_result["warnings"])
    all_errors.extend(org_result["errors"])

    # Evaluate each file
    total_frontmatter_score = 0
    total_glob_score = 0
    total_content_score = 0
    total_token_score = 0

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
        except OSError as exc:
            all_errors.append(f"Cannot read {md_file}: {exc}")
            continue
        parsed, body, _parse_error = _parse_frontmatter(content)

        # Frontmatter validation (25 points)
        fm_result = validate_frontmatter(md_file)
        total_frontmatter_score += fm_result["score"]
        all_errors.extend(fm_result["errors"])
        all_warnings.extend(fm_result.get("warnings", []))

        # Glob pattern validation (20 points)
        if parsed and "paths" in parsed and isinstance(parsed["paths"], list):
            glob_result = validate_glob_patterns(parsed["paths"])
            total_glob_score += glob_result["score"]
            all_errors.extend(glob_result["errors"])
            all_warnings.extend(glob_result["warnings"])
        else:
            total_glob_score += 20  # No patterns = full score

        # Content quality (25 points)
        content_result = validate_content_quality(body)
        total_content_score += content_result["score"]
        all_warnings.extend(content_result["warnings"])

        # Token efficiency (15 points) - separate scoring dimension
        if content_result["token_count"] <= MAX_TOKEN_COUNT:
            total_token_score += 15
        elif content_result["token_count"] <= HIGH_TOKEN_COUNT:
            total_token_score += 8
        else:
            total_token_score += 3

        file_results.append(
            {
                "file": str(md_file),
                "frontmatter_score": fm_result["score"],
                "content_score": content_result["score"],
                "token_count": content_result["token_count"],
            }
        )

    n = len(md_files)
    # Average scores across files, then combine with org score
    avg_frontmatter = total_frontmatter_score / n  # out of 25
    avg_glob = total_glob_score / n  # out of 20
    avg_content = total_content_score / n  # out of 25
    avg_token = total_token_score / n  # out of 15
    total_score = int(avg_frontmatter + avg_glob + avg_content + org_score + avg_token)
    total_score = min(100, max(0, total_score))

    return {
        "total_score": total_score,
        "files_evaluated": n,
        "errors": all_errors,
        "warnings": all_warnings,
        "file_results": file_results,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate Claude Code rules directory")
    parser.add_argument(
        "rules_dir",
        nargs="?",
        default=".claude/rules",
        help="Path to rules directory (default: .claude/rules)",
    )
    parser.add_argument("--detailed", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    result = evaluate_rules_directory(Path(args.rules_dir))

    print("=== Rules Evaluation Report ===")
    print(f"Directory: {args.rules_dir}")
    print(f"Files evaluated: {result['files_evaluated']}")
    print(f"Total score: {result['total_score']}/100")

    if result["errors"]:
        print(f"\n=== Errors ({len(result['errors'])}) ===")
        for err in result["errors"]:
            print(f"  [ERROR] {err}")

    if result["warnings"]:
        print(f"\n=== Warnings ({len(result['warnings'])}) ===")
        for warn in result["warnings"]:
            print(f"  [WARN] {warn}")

    if args.detailed and result["file_results"]:
        print("\n=== Per-File Results ===")
        for fr in result["file_results"]:
            print(f"  {fr['file']}:")
            print(f"    Frontmatter: {fr['frontmatter_score']}/25")
            print(f"    Content: {fr['content_score']}/25")
            print(f"    Tokens: ~{fr['token_count']}")
