"""FR-4: render one `claude plugin eval` case.yaml per labeled case.

Graders here are a convenience view in the eval's own report. The
metrics come from traces (analyze.py), so a grader pattern can never
decide a rate by itself.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from .labels import Case

MAX_TURNS = 2
TIMEOUT_SECONDS = 300


def case_yaml(case: Case, *, plugins: list[str], runs: int) -> dict:
    if case.is_positive:
        plugin, name = case.target.split(":", 1)
        grader = {
            "name": "hit",
            "type": "tool_used",
            "tool": "Skill",
            "input_match": rf'"skill"\s*:\s*"/?(?:{re.escape(plugin)}:)?{re.escape(name)}"',
            "arm": "both",
        }
        tag = plugin
    else:
        alternatives = "|".join(re.escape(p) for p in plugins)
        grader = {
            "name": "no-routed-item",
            "type": "tool_used",
            "tool": "Skill",
            "input_match": rf'"skill"\s*:\s*"/?(?:{alternatives}):',
            "min": 0,
            "max": 0,
            "arm": "both",
        }
        tag = "none"
    return {
        "schema_version": "1.1",
        "name": case.id,
        "tags": [case.type, tag],
        "plugins": [f"../../plugins/{p}" for p in plugins],
        "runs": runs,
        "execution": {
            "max_turns": MAX_TURNS,
            "timeout_seconds": TIMEOUT_SECONDS,
            "allowed_tools": ["Skill"],
            "prompt": case.prompt,
        },
        "graders": [grader],
    }


def write_cases(
    cases: list[Case], evals_dir: Path, *, plugins: list[str], runs: int
) -> None:
    for case in cases:
        path = evals_dir / case.id / "case.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(
                case_yaml(case, plugins=plugins, runs=runs),
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
