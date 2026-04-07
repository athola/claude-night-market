"""Problem bank loader and filter for standalone DSA/system design problems."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

import yaml

from gauntlet.models import BankProblem, Challenge, ChallengeType, Difficulty

_DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "problems"
_log = logging.getLogger(__name__)


def load_bank(data_dir: Path | None = None) -> list[BankProblem]:
    """Load all problems from YAML files in the data directory."""
    directory = data_dir or _DEFAULT_DATA_DIR
    problems: list[BankProblem] = []
    for yaml_file in sorted(directory.glob("*.yaml")):
        if yaml_file.name.startswith("_"):
            continue  # skip manifest and other meta files
        try:
            with open(yaml_file) as f:  # noqa: S108 - reading from plugin data dir, not temp
                data = yaml.safe_load(f)
        except yaml.YAMLError:
            _log.warning("Skipping malformed YAML: %s", yaml_file.name)
            continue
        if not data or "problems" not in data:
            continue
        for item in data["problems"]:
            # Inherit category from file-level metadata if not set per-problem
            if "category" not in item and "category" in data:
                item["category"] = data["category"]
            try:
                problems.append(BankProblem.from_dict(item))
            except (KeyError, ValueError):
                _log.warning("Skipping invalid problem in %s", yaml_file.name)
    return problems


def filter_problems(
    problems: list[BankProblem],
    *,
    category: str | None = None,
    difficulty: Difficulty | None = None,
    tags: list[str] | None = None,
) -> list[BankProblem]:
    """Filter problems by category, difficulty, and/or tags."""
    result = problems
    if category is not None:
        result = [p for p in result if p.category == category]
    if difficulty is not None:
        result = [p for p in result if p.difficulty == difficulty]
    if tags is not None:
        tag_set = set(tags)
        result = [p for p in result if tag_set & set(p.tags)]
    return result


def bank_problem_to_challenge(problem: BankProblem) -> Challenge:
    """Convert a BankProblem to a Challenge for spaced-repetition."""
    try:
        ctype = ChallengeType(problem.challenge_type)
    except ValueError:
        ctype = ChallengeType.EXPLAIN_WHY

    return Challenge(
        id="bank-" + uuid.uuid4().hex[:12],
        type=ctype,
        knowledge_entry_id=f"bank:{problem.id}",
        difficulty=problem.difficulty.to_numeric(),
        prompt=problem.prompt,
        context=f"{problem.title} [{problem.category}]",
        answer=problem.solution_outline,
        hints=problem.hints,
        scope_files=[],
        options=None,
    )


def load_manifest(data_dir: Path | None = None) -> dict[str, Any]:
    """Load the problem bank manifest with category metadata."""
    directory = data_dir or _DEFAULT_DATA_DIR
    manifest_path = directory / "_manifest.yaml"
    if not manifest_path.exists():
        return {}
    with open(manifest_path) as f:  # noqa: S108 - reading from plugin data dir, not temp
        return yaml.safe_load(f) or {}
