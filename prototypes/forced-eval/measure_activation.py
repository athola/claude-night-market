#!/usr/bin/env python3
"""Measure forced-eval skill-activation lift (PROTOTYPE harness).

Implements the baseline-vs-treatment methodology from README.md
("Measuring activation lift"): run a labelled prompt set through
`claude -p --output-format stream-json --max-turns 1 --allowedTools
Skill`, count how often the expected Skill() event fires, and compare
the activation rate with the forced-eval hook off (baseline) versus on
(treatment). True-negative prompts are included so a high positive rate
is not vanity.

The pure scoring/parsing logic is unit-tested in
test_measure_activation.py. Live `claude` invocation is gated behind
--live so the harness is safe (and testable) without spending tokens.

NOT WIRED. This measures the prototype; it does not install it.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_CASES = HERE / "activation_cases.json"
FORCED_EVAL = HERE / "forced_eval.py"


# --------------------------------------------------------------------------
# Pure logic (unit-tested, no I/O)
# --------------------------------------------------------------------------
def load_cases(path: Path) -> list[dict[str, Any]]:
    """Load labelled cases. Each: {id, prompt, kind, expect[]}.

    kind is "positive" (a skill in expect[] should fire) or "negative"
    (no skill should fire; expect[] is ignored).
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = data["cases"]
    for case in cases:
        if case.get("kind") not in {"positive", "negative"}:
            raise ValueError(f"case {case.get('id')!r}: kind must be positive/negative")
    return cases


def _walk_for_skills(node: Any) -> list[str]:
    """Recursively collect Skill tool_use identifiers from any nesting."""
    found: list[str] = []
    if isinstance(node, dict):
        if node.get("type") == "tool_use" and node.get("name") == "Skill":
            inp = node.get("input") or {}
            ident = inp.get("skill") or inp.get("command") or inp.get("name")
            if ident:
                found.append(str(ident))
        for value in node.values():
            found.extend(_walk_for_skills(value))
    elif isinstance(node, list):
        for value in node:
            found.extend(_walk_for_skills(value))
    return found


def extract_fired_skills(stream_lines: Iterable[str]) -> list[str]:
    """Parse `claude -p` stream-json lines into fired Skill identifiers.

    Tolerant by design: non-JSON lines are skipped and the event shape
    is discovered by walking, so a schema tweak does not break parsing.
    """
    fired: list[str] = []
    for line in stream_lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        fired.extend(_walk_for_skills(obj))
    return fired


def score_trial(case: dict[str, Any], fired: list[str]) -> dict[str, Any]:
    """Score one trial's fired skills against the case label.

    positive: correct iff some expected identifier is a substring of a
    fired identifier. negative: correct iff nothing fired.
    """
    activated = len(fired) > 0
    if case["kind"] == "positive":
        correct = any(exp in f for exp in case["expect"] for f in fired)
    else:
        correct = not activated
    return {
        "id": case["id"],
        "kind": case["kind"],
        "fired": fired,
        "activated": activated,
        "correct": correct,
    }


def _mean(values: list[bool]) -> float:
    """Mean of a boolean list; 0.0 for an empty list."""
    return (sum(1 for v in values if v) / len(values)) if values else 0.0


def aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Roll trial results into per-condition rates."""
    positives = [r for r in results if r["kind"] == "positive"]
    negatives = [r for r in results if r["kind"] == "negative"]
    return {
        "n_positive": len(positives),
        "n_negative": len(negatives),
        "activation_rate": _mean([r["correct"] for r in positives]),
        "false_activation_rate": _mean([r["activated"] for r in negatives]),
    }


def paired_mcnemar(
    baseline: list[dict[str, Any]], treatment: list[dict[str, Any]]
) -> dict[str, Any]:
    """Paired discordance between conditions, matched by case id.

    b = baseline correct, treatment wrong. c = treatment correct,
    baseline wrong. c > b means treatment helped. Reports the
    continuity-corrected McNemar chi-square (df=1; >= 3.84 is p < .05).
    """
    base_by_id = {r["id"]: r["correct"] for r in baseline}
    treat_by_id = {r["id"]: r["correct"] for r in treatment}
    shared = base_by_id.keys() & treat_by_id.keys()
    b = sum(1 for i in shared if base_by_id[i] and not treat_by_id[i])
    c = sum(1 for i in shared if treat_by_id[i] and not base_by_id[i])
    discordant = b + c
    chi2 = ((abs(b - c) - 1) ** 2) / discordant if discordant else 0.0
    return {
        "b_baseline_only": b,
        "c_treatment_only": c,
        "n_discordant": discordant,
        "mcnemar_chi2_cc": round(chi2, 3),
        "significant_p05": chi2 >= 3.84,
    }


# --------------------------------------------------------------------------
# Live invocation (gated behind --live)
# --------------------------------------------------------------------------
def build_claude_cmd(prompt: str, settings_path: Path | None) -> list[str]:
    """Assemble the `claude -p` command for one trial."""
    cmd = [
        "claude",
        "-p",
        prompt,
        "--output-format",
        "stream-json",
        "--verbose",
        "--max-turns",
        "1",
        "--allowedTools",
        "Skill",
    ]
    if settings_path is not None:
        cmd += ["--settings", str(settings_path)]
    return cmd


def write_treatment_settings(path: Path) -> Path:
    """Write a settings.json that wires forced_eval.py as a hook."""
    settings = {
        "hooks": {
            "UserPromptSubmit": [
                {"hooks": [{"type": "command", "command": f"python3 {FORCED_EVAL}"}]}
            ]
        }
    }
    path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    return path


def run_trial(
    prompt: str, settings_path: Path | None, env: dict[str, str]
) -> list[str]:
    """Invoke claude once and return fired skill identifiers."""
    proc = subprocess.run(
        build_claude_cmd(prompt, settings_path),
        capture_output=True,
        text=True,
        env=env,
        timeout=180,
    )
    return extract_fired_skills(proc.stdout.splitlines())


def run_condition(
    cases: list[dict[str, Any]],
    settings_path: Path | None,
    repeats: int,
    env: dict[str, str],
) -> list[dict[str, Any]]:
    """Run every case under one condition; majority-vote over repeats."""
    results = []
    for case in cases:
        votes = [run_trial(case["prompt"], settings_path, env) for _ in range(repeats)]
        scored = [score_trial(case, fired) for fired in votes]
        correct = _mean([s["correct"] for s in scored]) >= 0.5
        activated = _mean([s["activated"] for s in scored]) >= 0.5
        results.append(
            {
                "id": case["id"],
                "kind": case["kind"],
                "fired": votes[-1],
                "activated": activated,
                "correct": correct,
            }
        )
    return results


def render_report(
    base_agg: dict[str, Any], treat_agg: dict[str, Any], mcnemar: dict[str, Any]
) -> str:
    """Markdown summary table comparing the two conditions."""
    lift = treat_agg["activation_rate"] - base_agg["activation_rate"]
    return (
        "# Forced-eval activation measurement\n\n"
        "| Metric | Baseline | Treatment |\n"
        "|--------|----------|----------|\n"
        f"| Activation rate (positives) | {base_agg['activation_rate']:.0%} "
        f"| {treat_agg['activation_rate']:.0%} |\n"
        f"| False-activation rate (negatives) | {base_agg['false_activation_rate']:.0%} "
        f"| {treat_agg['false_activation_rate']:.0%} |\n\n"
        f"Activation lift: {lift:+.0%}\n\n"
        f"McNemar (paired): b={mcnemar['b_baseline_only']} "
        f"c={mcnemar['c_treatment_only']} chi2cc={mcnemar['mcnemar_chi2_cc']} "
        f"significant_p05={mcnemar['significant_p05']}\n"
    )


def main(argv: list[str] | None = None) -> None:
    """Harness entrypoint."""
    parser = argparse.ArgumentParser(description="Measure forced-eval activation lift")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument(
        "--root",
        type=Path,
        default=HERE,
        help="FORCED_EVAL_ROOT for treatment (a plugin tree with skills/)",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help="Trials per case per condition (majority vote)",
    )
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--out", type=Path, default=HERE / "results")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Actually invoke claude (spends tokens). Off = dry run.",
    )
    args = parser.parse_args(argv)

    cases = load_cases(args.cases)
    if args.max_cases:
        cases = cases[: args.max_cases]
    n_pos = sum(1 for c in cases if c["kind"] == "positive")
    n_neg = len(cases) - n_pos

    if not args.live:
        print("DRY RUN (no --live): no claude calls, no tokens spent.")
        print(f"  Cases: {len(cases)} ({n_pos} positive, {n_neg} negative)")
        print(
            f"  Repeats/case: {args.repeats}  -> {len(cases) * args.repeats * 2} "
            "total claude calls when live (baseline + treatment)"
        )
        print(f"  Treatment FORCED_EVAL_ROOT: {args.root}")
        print(
            "  Baseline cmd:  " + " ".join(build_claude_cmd(cases[0]["prompt"], None))
        )
        print(
            "  Treatment cmd: "
            + " ".join(
                build_claude_cmd(cases[0]["prompt"], Path("<tmp-settings.json>"))
            )
        )
        return

    args.out.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    settings_path = write_treatment_settings(
        args.out / f"treatment-settings-{stamp}.json"
    )
    treat_env = {**os.environ, "FORCED_EVAL_ROOT": str(args.root)}

    baseline = run_condition(cases, None, args.repeats, dict(os.environ))
    treatment = run_condition(cases, settings_path, args.repeats, treat_env)

    base_agg = aggregate(baseline)
    treat_agg = aggregate(treatment)
    mcnemar = paired_mcnemar(baseline, treatment)

    (args.out / f"results-{stamp}.json").write_text(
        json.dumps(
            {
                "baseline": baseline,
                "treatment": treatment,
                "baseline_agg": base_agg,
                "treatment_agg": treat_agg,
                "mcnemar": mcnemar,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    report = render_report(base_agg, treat_agg, mcnemar)
    (args.out / f"report-{stamp}.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
