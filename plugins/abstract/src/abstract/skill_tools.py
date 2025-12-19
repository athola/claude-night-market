#!/usr/bin/env python3
"""Shared skill tools that can be imported by any skill.

Shared functionality for skills.

Usage from within a skill:
    from abstract.skill_tools import analyze_skill, estimate_tokens

    # These functions work relative to the skill's location
    analysis = analyze_skill(".", threshold=150)
    tokens = estimate_tokens("SKILL.md")
"""

import sys
from pathlib import Path
from typing import Any

# Add project root to Python path for imports (must be before abstract imports)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from abstract.tokens import TokenAnalyzer, extract_code_blocks
from abstract.utils import find_skill_files


def analyze_skill(
    path: str = ".",
    threshold: int = 150,
    verbose: bool = False,
) -> dict[str, Any]:
    """Analyze a skill for complexity and token usage.

    Args:
        path: Path to analyze (default: current directory)
        threshold: Line count threshold for warnings (default: 150)
        verbose: Enable verbose output (default: False)

    Returns:
        Dictionary containing analysis results

    """
    skill_path = Path(path).resolve()

    if not skill_path.exists():
        msg = f"Path does not exist: {skill_path}"
        raise FileNotFoundError(msg)

    # Find skill files
    skill_files = [skill_path] if skill_path.is_file() else find_skill_files(skill_path)

    results = []

    for skill_file in skill_files:
        try:
            with open(skill_file, encoding="utf-8") as f:
                content = f.read()

            # Basic metrics
            lines = len(content.splitlines())
            analysis = TokenAnalyzer.analyze_content(content)
            tokens = analysis["total_tokens"]
            code_blocks = len(extract_code_blocks(content))

            # Complexity assessment
            complexity = "low"
            if lines > threshold * 2:
                complexity = "high"
            elif lines > threshold:
                complexity = "medium"

            result = {
                "path": str(skill_file),
                "lines": lines,
                "tokens": tokens,
                "code_blocks": code_blocks,
                "complexity": complexity,
                "above_threshold": lines > threshold,
            }

            if verbose:
                pass

            results.append(result)

        except Exception as e:
            if verbose:
                pass
            results.append(
                {
                    "path": str(skill_file),
                    "error": str(e),
                    "lines": 0,
                    "tokens": 0,
                    "code_blocks": 0,
                    "complexity": "error",
                    "above_threshold": False,
                },
            )

    return {
        "path": str(skill_path),
        "results": results,
        "total_files": len(results),
        "threshold": threshold,
    }


def estimate_tokens(file_path: str) -> dict[str, Any]:
    """Estimate token usage for a skill file.

    Args:
        file_path: Path to the skill file

    Returns:
        Dictionary containing token estimates

    """
    path = Path(file_path).resolve()

    if not path.exists():
        msg = f"File does not exist: {path}"
        raise FileNotFoundError(msg)

    with open(path, encoding="utf-8") as f:
        content = f.read()

    # Use TokenAnalyzer for consistent analysis
    analysis = TokenAnalyzer.analyze_content(content)

    return {
        "file_path": str(path),
        "total_tokens": analysis["total_tokens"],
        "frontmatter_tokens": analysis["frontmatter_tokens"],
        "body_tokens": analysis["body_tokens"],
        "code_tokens": analysis["code_tokens"],
        "code_blocks_count": len(extract_code_blocks(content)),
        "estimated_tokens": analysis["total_tokens"],  # Alias for compatibility
    }


def validate_skill_structure(skill_path: str = ".") -> dict[str, Any]:
    """Validate that a skill follows expected structure.

    Args:
        skill_path: Path to the skill directory

    Returns:
        Dictionary containing validation results

    """
    path = Path(skill_path).resolve()

    # Check for required files
    required_files = ["SKILL.md"]
    missing_files = []

    for required_file in required_files:
        if not (path / required_file).exists():
            missing_files.append(required_file)

    # Check for common directories
    common_dirs = ["modules", "scripts", "examples", "tests"]
    existing_dirs = [d for d in common_dirs if (path / d).exists()]

    # Look for skill files
    skill_files = find_skill_files(path)

    return {
        "path": str(path),
        "valid": len(missing_files) == 0,
        "missing_files": missing_files,
        "existing_directories": existing_dirs,
        "skill_files": [str(f) for f in skill_files],
        "total_skill_files": len(skill_files),
    }


# CLI entry points for when run directly
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Skill analysis tools")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze skill complexity")
    analyze_parser.add_argument("path", nargs="?", default=".", help="Path to analyze")
    analyze_parser.add_argument(
        "--threshold",
        type=int,
        default=150,
        help="Complexity threshold",
    )
    analyze_parser.add_argument("--verbose", action="store_true", help="Verbose output")

    # Token estimation command
    token_parser = subparsers.add_parser("tokens", help="Estimate token usage")
    token_parser.add_argument("file", help="File to analyze")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate skill structure")
    validate_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to validate",
    )

    args = parser.parse_args()

    if args.command == "analyze":
        result = analyze_skill(args.path, args.threshold, args.verbose)
        for r in result["results"]:
            if "error" in r:
                pass
            else:
                status = "WARN" if r["above_threshold"] else "OK"
                lines = r["lines"]
                tokens = r["tokens"]
                complexity = r["complexity"]

    elif args.command == "tokens":
        result = estimate_tokens(args.file)
        code_tokens = result["code_tokens"]
        blocks_count = result["code_blocks_count"]

    elif args.command == "validate":
        result = validate_skill_structure(args.path)
        if result["valid"]:
            pass
        else:
            pass
        if result["existing_directories"]:
            pass

    else:
        parser.print_help()
