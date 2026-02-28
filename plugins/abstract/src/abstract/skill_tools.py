#!/usr/bin/env python3
"""Provide shared skill tools importable by any skill.

Usage from within a skill:
    from abstract.skill_tools import analyze_skill, estimate_tokens

    # These functions work relative to the skill's location
    analysis = analyze_skill(".", threshold=150)
    tokens = estimate_tokens("SKILL.md")
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Add abstract/src to Python path for imports (must be before abstract imports)
sys.path.insert(0, str(Path(__file__).parent.parent))

from abstract.tokens import TokenAnalyzer, extract_code_blocks
from abstract.utils import find_skill_files


def analyze_skill(
    path: str = ".",
    threshold: int = 150,
    verbose: bool = False,
) -> dict[str, Any]:
    """Analyze skill complexity and token usage.

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

            results.append(result)

        except Exception as e:
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
