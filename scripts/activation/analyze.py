"""FR-7: turn one run host's kept traces into library activation rates.

Numbers come from the Skill tool_use events in each trace, never from
grader verdicts, so a grader regex cannot decide a metric by itself.
Intervals resample clusters (a positive case's target item, a
negative's prompt source) because runs of one item are correlated:
treating them as independent would claim precision the set lacks.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .inventory import Item, missing_from_listing
from .labels import Case

CEILING = 0.95
PARTIAL_ERROR_SHARE = 0.05
BOOTSTRAP_B = 2000
RATES = ("sensitivity", "fa_negative", "fa_positive")


@dataclass
class TraceRun:
    model: str | None
    version: str | None
    plugins: tuple[str, ...]
    init: dict
    skills: list[str]
    cost: float


def parse_trace(path: Path) -> TraceRun | None:
    """None means errored: no file, unreadable, or no init event.

    A result with subtype ``error_max_turns`` is not an error here: the
    runner caps turns on purpose, and the routing decision is already
    in the trace by then.
    """
    if not path.exists():
        return None
    init = None
    skills: list[str] = []
    cost = 0.0
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        events = [json.loads(line) for line in lines if line.strip()]
    except (OSError, json.JSONDecodeError):
        return None
    for event in events:
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init" and init is None:
            init = event
        elif kind == "assistant":
            for block in event.get("message", {}).get("content", []) or []:
                if block.get("type") == "tool_use" and block.get("name") == "Skill":
                    skills.append(str(block.get("input", {}).get("skill", "")))
        elif kind == "result":
            cost = float(event.get("total_cost_usd") or 0.0)
    if init is None:
        return None
    plugins = tuple(
        sorted(
            p["name"] if isinstance(p, dict) else str(p)
            for p in init.get("plugins", [])
        )
    )
    return TraceRun(
        init.get("model"), init.get("claude_code_version"), plugins, init, skills, cost
    )


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (round(centre - half, 6), round(centre + half, 6))


def cluster_bootstrap(
    clusters: dict[str, tuple[int, int]], seed: int = 0
) -> tuple[float, float]:
    """Percentile interval of a pooled ratio, resampling whole clusters."""
    keys = sorted(k for k, (_, n) in clusters.items() if n)
    if not keys:
        return (0.0, 1.0)
    rng = random.Random(seed)
    stats = []
    for _ in range(BOOTSTRAP_B):
        draw = [clusters[rng.choice(keys)] for _ in keys]
        stats.append(sum(k for k, _ in draw) / sum(n for _, n in draw))
    stats.sort()
    return (
        round(stats[int(0.025 * BOOTSTRAP_B)], 6),
        round(stats[int(0.975 * BOOTSTRAP_B) - 1], 6),
    )


def resolve_skill(raw: str, items: list[Item]) -> str | None:
    """Map a Skill input to an inventory id, or None if it names no item."""
    name = raw.strip().lstrip("/")
    ids = {i.id for i in items}
    if name in ids:
        return name
    if ":" not in name:
        matches = [i.id for i in items if i.name == name]
        if len(matches) == 1:
            return matches[0]
    return None


def _load_host(host: Path) -> tuple[dict, list[Case], list[Item], dict]:
    run = json.loads((host / "run.json").read_text())
    cases = [
        Case.from_dict(row) for row in json.loads((host / "cases.json").read_text())
    ]
    inventory = json.loads((host / "inventory.json").read_text())
    items = [Item(**row) for row in inventory["items"]]
    return run, cases, items, inventory


def analyze_host(host: Path) -> dict:
    run, cases, items, inventory = _load_host(host)
    runs_per_case = int(run["runs"])
    tallies = {rate: {"k": 0, "n": 0, "clusters": {}} for rate in RATES}
    per_case: dict[str, dict] = {}
    per_item: dict[str, list[int]] = {}
    confusion: dict[str, Counter] = {}
    outside: Counter = Counter()
    seen_runs: list[TraceRun] = []
    errored = 0
    cost = 0.0

    def tally(rate: str, cluster: str, k: int, n: int) -> None:
        t = tallies[rate]
        t["k"] += k
        t["n"] += n
        ck, cn = t["clusters"].get(cluster, (0, 0))
        t["clusters"][cluster] = (ck + k, cn + n)

    for case in cases:
        row = {"v": 0, "errored": 0, "hit": 0, "fa": 0}
        for n in range(runs_per_case):
            path = host / "traces" / case.id / f"{n}.jsonl"
            trace = None if path.with_suffix(".error").exists() else parse_trace(path)
            if trace is None:
                row["errored"] += 1
                continue
            seen_runs.append(trace)
            cost += trace.cost
            fired = []
            for raw in trace.skills:
                resolved = resolve_skill(raw, items)
                if resolved is None:
                    outside[raw] += 1
                else:
                    fired.append(resolved)
            row["v"] += 1
            if case.is_positive:
                row["hit"] += case.target in fired
                row["fa"] += bool(fired) and fired[0] != case.target
                confusion.setdefault(case.target, Counter())[
                    fired[0] if fired else "none"
                ] += 1
            else:
                row["fa"] += bool(fired)
        errored += row["errored"]
        per_case[case.id] = row
        if case.is_positive:
            tally("sensitivity", case.cluster, row["hit"], row["v"])
            tally("fa_positive", case.cluster, row["fa"], row["v"])
            stats = per_item.setdefault(case.target, [0, 0])
            stats[0] += row["hit"]
            stats[1] += row["v"]
        else:
            tally("fa_negative", case.cluster, row["fa"], row["v"])

    rates = {}
    for rate, t in tallies.items():
        rates[rate] = {
            "k": t["k"],
            "n": t["n"],
            "rate": round(t["k"] / t["n"], 6) if t["n"] else None,
            "ci": list(cluster_bootstrap(t["clusters"])),
            "wilson": list(wilson(t["k"], t["n"])),
        }

    problems = []
    for label, values in (
        ("model", {r.model for r in seen_runs}),
        ("claude_code_version", {r.version for r in seen_runs}),
        ("plugins", {r.plugins for r in seen_runs}),
    ):
        if len(values) > 1:
            problems.append(
                f"{label} differs across case-runs: {sorted(map(str, values))}"
            )
    missing = sorted(
        {m for r in seen_runs for m in missing_from_listing(items, r.init)}
    )
    if missing:
        problems.append(f"{len(missing)} inventory items missing from the listing")
    total_runs = runs_per_case * len(cases)
    sensitivity = rates["sensitivity"]["rate"]
    ceiling = sensitivity is not None and sensitivity >= CEILING
    first = seen_runs[0] if seen_runs else None
    return {
        "run": run,
        "rates": rates,
        "cases": per_case,
        "case_meta": {c.id: c.to_dict() for c in cases},
        "items": {
            item: {
                "k": k,
                "n": n,
                "rate": round(k / n, 6) if n else None,
                "wilson": list(wilson(k, n)),
            }
            for item, (k, n) in sorted(per_item.items())
        },
        "confusion": {t: dict(c) for t, c in sorted(confusion.items())},
        "outside_inventory": dict(sorted(outside.items())),
        "errored": errored,
        "partial": run.get("eval_exit") == 2
        or (total_runs > 0 and errored / total_runs > PARTIAL_ERROR_SHARE),
        "ceiling": ceiling,
        "ceiling_cases": sorted(
            cid
            for cid, r in per_case.items()
            if ceiling and r["v"] and r["hit"] == r["v"]
        ),
        "fingerprint": {
            "arm": run["arm"],
            "model": first.model if first else None,
            "claude_code_version": first.version if first else None,
            "plugins": list(first.plugins) if first else [],
            "library_hash": inventory["library_hash"],
            "item_hashes": inventory["item_hashes"],
            "case_set_hash": run["case_set_hash"],
            "runs": runs_per_case,
            "tier": run["tier"],
            "commit": run["commit"],
            "dirty": run.get("dirty", False),
        },
        "fingerprint_valid": not problems,
        "fingerprint_problems": problems,
        "missing_from_listing": missing,
        "cost_usd": round(cost, 4),
    }


def _fmt(rate: dict) -> str:
    if rate["rate"] is None:
        return "n/a (no case-runs)"
    lo, hi = rate["ci"]
    return f"{rate['rate']:.3f} ({rate['k']}/{rate['n']}), 95% cluster CI {lo:.3f}-{hi:.3f}"


def render_report(m: dict) -> str:
    fp = m["fingerprint"]
    positives = [c for c in m["case_meta"].values() if c["type"] != "negative"]
    router_only = sum(c["proposers"] == ["router"] for c in positives)
    echo = 100 * router_only / len(positives) if positives else 0.0
    lines = [
        f"# Activation report: {fp['tier']} tier, {fp['arm']} arm",
        "",
        f"- Sensitivity: {_fmt(m['rates']['sensitivity'])}",
        f"- False activation on negatives: {_fmt(m['rates']['fa_negative'])}",
        f"- False activation on positives: {_fmt(m['rates']['fa_positive'])}",
        f"- Ceiling (sensitivity >= {CEILING}): {str(m['ceiling']).lower()}",
        f"- Partial: {str(m['partial']).lower()}, errored case-runs: {m['errored']}",
        f"- Fingerprint valid: {str(m['fingerprint_valid']).lower()}"
        + (
            f" ({'; '.join(m['fingerprint_problems'])})"
            if m["fingerprint_problems"]
            else ""
        ),
        f"- Model {fp['model']}, Claude Code {fp['claude_code_version']}, R = {fp['runs']}, "
        f"commit {fp['commit']}{' (dirty)' if fp['dirty'] else ''}",
        f"- Library {fp['library_hash'][:12]}, case set {fp['case_set_hash'][:12]}, "
        f"cost ${m['cost_usd']:.2f}",
        "",
        f"Echo risk: {echo:.0f}% of positive cases have a target only the router "
        "proposed. The judge reads skill bodies, which often repeat description "
        "wording, so judge-proposed labels reduce echo risk without removing it.",
        "",
        "## Worst 20 items by sensitivity",
        "",
        "| Item | Hits | Runs | Rate |",
        "|---|---|---|---|",
    ]
    worst = sorted(
        (i for i in m["items"].items() if i[1]["n"]),
        key=lambda kv: (kv[1]["rate"], kv[0]),
    )[:20]
    lines += [
        f"| {item} | {s['k']} | {s['n']} | {s['rate']:.2f} |" for item, s in worst
    ]
    pairs = Counter()
    for target, firsts in m["confusion"].items():
        for fired, count in firsts.items():
            if fired != target:
                pairs[(target, fired)] += count
    lines += [
        "",
        "## Top 20 confusion pairs",
        "",
        "| Target | Fired first | Count |",
        "|---|---|---|",
    ]
    lines += [
        f"| {t} | {f} | {c} |"
        for (t, f), c in sorted(pairs.items(), key=lambda kv: (-kv[1], kv[0]))[:20]
    ]
    if m["outside_inventory"]:
        lines += ["", "## Skill calls outside the inventory (not counted)", ""]
        lines += [
            f"- {name}: {count}" for name, count in m["outside_inventory"].items()
        ]
    if m["ceiling_cases"]:
        lines += ["", "## Cases at ceiling", "", ", ".join(m["ceiling_cases"])]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", type=Path)
    args = parser.parse_args(argv)
    metrics = analyze_host(args.host)
    (args.host / "metrics.json").write_text(
        json.dumps(metrics, indent=1, sort_keys=True) + "\n"
    )
    (args.host / "report.md").write_text(render_report(metrics))
    sys.stdout.write(render_report(metrics).split("\n## ")[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
