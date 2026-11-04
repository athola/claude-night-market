"""FR-6: run one tier of the activation suite against one model arm.

Live runs spend money, so every path prints its cost first: `--dry-run`
stops there, and a live run always passes `--max-cost-usd` to the eval.
A run records enough about its tree (commit, dirty diff hash, library
and case-set hashes) that compare.py can refuse a pairing that differs
in more than the declared change.

Usage:
  python -m scripts.activation.run --tier change|anchor|full --arm default|haiku [--change FILE]
         [--runs R] [--max-cost-usd USD] [--dry-run]
  python -m scripts.activation.run declare FILE     freeze a change file's case list on the base tree
  python -m scripts.activation.run anchor-select    write anchor.txt from the labels and router
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter
from collections.abc import Callable
from pathlib import Path

import yaml

from .analyze import analyze_host, render_report
from .host import build_host
from .inventory import (
    Item,
    build_inventory,
    item_hashes,
    library_hash,
)
from .labels import Case, coverage_gaps, load_cases, validate
from .router import Router, evaluate

CEILINGS = {"change": 30.0, "anchor": 75.0, "full": 800.0}
DEFAULT_COST = {"default": 0.20}
ANCHOR_SIZE = 100
ANCHOR_PAIRS = 40
ANCHOR_NEGATIVES = 10
EXIT_CEILING = 3
WATCHED = ("plugins", "evals/activation/labels")

Runner = Callable[[list[str]], int]


class RunRefused(RuntimeError):
    """The requested run would produce a number nobody should compare."""


def suite_dir(root: Path) -> Path:
    return root / "evals/activation"


def load_config(root: Path) -> dict:
    return yaml.safe_load((suite_dir(root) / "config.yaml").read_text())


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    ).stdout


def tree_state(root: Path) -> dict:
    status = _git(root, "status", "--porcelain", "--", *WATCHED)
    diff = _git(root, "diff", "HEAD", "--", *WATCHED)
    return {
        "commit": _git(root, "rev-parse", "HEAD").strip(),
        "dirty": bool(status.strip()),
        "diff_sha256": hashlib.sha256(diff.encode()).hexdigest()
        if status.strip()
        else None,
    }


def read_anchor(root: Path) -> list[str]:
    path = suite_dir(root) / "anchor.txt"
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def select_cases(
    tier: str, cases: list[Case], anchor: list[str], change: dict | None
) -> list[Case]:
    by_id = {c.id: c for c in cases}
    if tier == "full":
        wanted = sorted(by_id)
    elif tier == "anchor":
        wanted = anchor
    else:
        if not change or not change.get("cases"):
            raise RunRefused(
                "change tier needs a change file with cases; run `uv run python -m scripts.activation.run declare <file>` first"
            )
        wanted = change["cases"]
    unknown = [cid for cid in wanted if cid not in by_id]
    if unknown:
        raise RunRefused(f"unknown case ids: {', '.join(unknown[:5])}")
    return [by_id[cid] for cid in wanted]


def select_anchor(
    cases: list[Case], items: list[Item], router_metrics: dict
) -> list[str]:
    """Initial anchor (spec FR-6): confusable pairs first, then coverage."""
    chosen: list[str] = []
    plugin_of = {i.id: i.plugin for i in items}

    def take(case: Case) -> None:
        if case.id not in chosen and len(chosen) < ANCHOR_SIZE:
            chosen.append(case.id)

    pairs = sorted(router_metrics["collisions"].items(), key=lambda kv: (-kv[1], kv[0]))
    near = sorted((c for c in cases if c.type == "near_miss"), key=lambda c: c.id)
    for pair, _ in pairs[:ANCHOR_PAIRS]:
        target = pair.split("->")[0].strip()
        for case in near:
            if case.target == target:
                take(case)
    plain = sorted((c for c in cases if c.type == "positive"), key=lambda c: c.id)
    per_plugin: Counter = Counter(
        plugin_of.get(c.target) for c in cases if c.id in chosen and c.target
    )
    for plugin in sorted(set(plugin_of.values())):
        for case in plain:
            if per_plugin[plugin] >= 2:
                break
            if plugin_of.get(case.target) == plugin and case.id not in chosen:
                take(case)
                per_plugin[plugin] += 1
    sources_used: set[str] = set()
    for case in sorted((c for c in cases if c.type == "negative"), key=lambda c: c.id):
        if len(sources_used) >= ANCHOR_NEGATIVES:
            break
        if case.cluster not in sources_used:
            take(case)
            sources_used.add(case.cluster)
    item_count = Counter(plugin_of.values())
    order = sorted(item_count, key=lambda p: (-item_count[p], p))
    queues = {
        p: [c for c in plain if plugin_of.get(c.target) == p and c.id not in chosen]
        for p in order
    }
    while len(chosen) < ANCHOR_SIZE and any(queues.values()):
        for plugin in order:
            if queues[plugin]:
                take(queues[plugin].pop(0))
    return chosen


def declare(root: Path, change_path: Path) -> dict:
    change = yaml.safe_load(change_path.read_text())
    items = build_inventory(root)
    cases = load_cases(suite_dir(root) / "labels")
    changed = set(change["items"])
    unknown = sorted(changed - {i.id for i in items})
    if unknown:
        raise RunRefused(f"change names unknown items: {', '.join(unknown)}")
    neighbors = evaluate(Router(items), cases)["neighbors"]
    near = {n for item in changed for n in neighbors.get(item, [])}
    wanted = {
        c.id
        for c in cases
        if c.target in changed or c.competitor in changed or c.target in near
    }
    negatives = {c.id for c in cases if c.type == "negative"}
    anchor_negatives = [cid for cid in read_anchor(root) if cid in negatives]
    if not anchor_negatives:
        raise RunRefused(
            "anchor.txt lists no negative cases, so the change tier would have no "
            "false-activation denominator; run "
            "`uv run python -m scripts.activation.run anchor-select` first"
        )
    wanted.update(
        [cid for cid in read_anchor(root) if cid in negatives][:ANCHOR_NEGATIVES]
    )
    change["cases"] = sorted(wanted)
    change["declared_at"] = _git(root, "rev-parse", "HEAD").strip()
    change_path.write_text(yaml.safe_dump(change, sort_keys=False))
    return change


def estimate_cost(root: Path, arm: str) -> float | None:
    """Mean cost per case-run from the arm's latest committed metrics."""
    reports = sorted((suite_dir(root) / "reports").glob(f"baseline-{arm}-*.json"))
    if reports:
        m = json.loads(reports[-1].read_text())
        valid = sum(r["v"] for r in m["cases"].values())
        if valid:
            return m["cost_usd"] / valid
    return DEFAULT_COST.get(arm)


def eval_command(
    host: Path, *, model: str | None, runs: int, ceiling: float
) -> list[str]:
    cmd = [
        "claude",
        "plugin",
        "eval",
        str(host),
        "--trust-plugin",
        "--keep-temp",
        "--ablation",
        "none",
        "--runs",
        str(runs),
        "--no-publish",
        "--threshold",
        "0",
        "--json",
        str(host / "result.json"),
        "--output-dir",
        str(host / "out"),
        "--max-cost-usd",
        f"{ceiling:g}",
        "-j",
        "4",
    ]
    if model:
        cmd += ["--model", model]
    return cmd


def _runs_of(case_result: dict) -> list[dict]:
    arms = case_result.get("arms") or {}
    return list(arms.get("with") or case_result.get("runs") or [])


def collect_traces(host: Path) -> int:
    """Copy each run's kept trace into the host before temp cleanup can
    remove it. A run stopped at max_turns keeps its trace: the cap is
    deliberate and the routing decision is already recorded. A run with
    any other error, or no trace, gets an ``.error`` marker,
    which analyze.py counts as errored. Returns the traces copied.
    """
    result = json.loads((host / "result.json").read_text())
    copied = 0
    for case_result in result.get("cases", []):
        cid = case_result.get("name") or case_result.get("id")
        for n, run in enumerate(_runs_of(case_result)):
            dest = host / "traces" / cid / f"{n}.jsonl"
            dest.parent.mkdir(parents=True, exist_ok=True)
            trace = Path(run["tracePath"]) if run.get("tracePath") else None
            error = str(run.get("error") or "")
            capped = error.startswith("exit 1: Reached maximum number of turns")
            if (error and not capped) or trace is None or not trace.exists():
                dest.with_suffix(".error").write_text(
                    str(run.get("error") or "no trace")
                )
                continue
            shutil.copyfile(trace, dest)
            copied += 1
    return copied


def subprocess_runner(cmd: list[str]) -> int:
    return subprocess.run(cmd, check=False).returncode


def execute(
    root: Path,
    cases: list[Case],
    run_meta: dict,
    *,
    runner: Runner = subprocess_runner,
    mutate: Callable[[Path, list[Item]], None] | None = None,
) -> tuple[Path, dict]:
    items = build_inventory(root)
    host = build_host(root, cases, items, run_meta)
    if mutate is not None:
        mutate(host, items)
        mutated = build_inventory(host)
        (host / "inventory.json").write_text(
            json.dumps(
                {
                    "items": [i.__dict__ for i in mutated],
                    "library_hash": library_hash(mutated),
                    "item_hashes": item_hashes(mutated),
                },
                indent=1,
            )
        )
    cmd = eval_command(
        host,
        model=run_meta.get("model"),
        runs=run_meta["runs"],
        ceiling=run_meta["max_cost_usd"],
    )
    code = runner(cmd)
    run = json.loads((host / "run.json").read_text())
    run["eval_exit"] = code
    (host / "run.json").write_text(json.dumps(run, indent=1, sort_keys=True))
    if code not in (0, 1, 2):
        raise RunRefused(f"claude plugin eval exited {code}; see its output above")
    collect_traces(host)
    metrics = analyze_host(host)
    (host / "metrics.json").write_text(
        json.dumps(metrics, indent=1, sort_keys=True) + "\n"
    )
    (host / "report.md").write_text(render_report(metrics))
    return host, metrics


def _require_committed(root: Path, path: Path) -> None:
    try:
        rel = str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        raise RunRefused(
            f"change file {path} is outside the repo root {root}"
        ) from None
    tracked = (
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", rel],
            cwd=root,
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )
    if not tracked or _git(root, "status", "--porcelain", "--", rel).strip():
        raise RunRefused(f"change file {rel} must be committed before the run (C7)")


def plan_run(root: Path, args: argparse.Namespace) -> tuple[list[Case], dict]:
    config = load_config(root)
    runs = args.runs or int(config.get("runs", 3))
    if runs % 2 == 0:
        raise RunRefused(
            f"--runs must be odd so a majority is always defined, got {runs}"
        )
    items = build_inventory(root)
    cases = load_cases(suite_dir(root) / "labels")
    validate(cases, items, root)
    if args.tier in ("anchor", "full") and not coverage_gaps(cases, items)["ok"]:
        raise RunRefused(
            f"{args.tier} tier refused: coverage gate fails (`uv run python -m scripts.activation.labels coverage`)"
        )
    change = yaml.safe_load(args.change.read_text()) if args.change else None
    selected = select_cases(args.tier, cases, read_anchor(root), change)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    meta = {
        "run_id": f"{stamp}-{args.tier}-{args.arm}",
        "tier": args.tier,
        "arm": args.arm,
        "model": (config.get("arms") or {}).get(args.arm),
        "runs": runs,
        "change": str(args.change) if args.change else None,
        "max_cost_usd": args.max_cost_usd or CEILINGS[args.tier],
        "started_at": stamp,
        **tree_state(root),
    }
    return selected, meta


def _parse(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--tier", choices=sorted(CEILINGS), required=True)
    parser.add_argument("--arm", default="default")
    parser.add_argument("--change", type=Path)
    parser.add_argument("--runs", type=int)
    parser.add_argument("--max-cost-usd", type=float)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, *, runner: Runner = subprocess_runner) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    root = Path.cwd()
    try:
        if argv[:1] == ["declare"]:
            change = declare(root, Path(argv[1]))
            sys.stdout.write(
                f"declared {len(change['cases'])} cases at {change['declared_at'][:12]}\n"
            )
            return 0
        if argv[:1] == ["anchor-select"]:
            items = build_inventory(root)
            cases = load_cases(suite_dir(root) / "labels")
            chosen = select_anchor(cases, items, evaluate(Router(items), cases))
            (suite_dir(root) / "anchor.txt").write_text("\n".join(chosen) + "\n")
            sys.stdout.write(f"wrote {len(chosen)} anchor cases\n")
            return 0
        args = _parse(argv)
        root = args.root
        selected, meta = plan_run(root, args)
        per_run = estimate_cost(root, args.arm)
        case_runs = len(selected) * meta["runs"]
        estimate = (
            f"${per_run * case_runs:.2f}" if per_run is not None else "unmeasured"
        )
        sys.stdout.write(
            f"{args.tier} tier, {args.arm} arm: {len(selected)} cases x R={meta['runs']} = "
            f"{case_runs} case-runs, estimate {estimate}, ceiling ${meta['max_cost_usd']:g}\n"
        )
        if meta["dirty"]:
            sys.stdout.write("warning: tree is dirty; this run cannot be compared\n")
        cmd = eval_command(
            Path(f"evals/activation/.runs/{meta['run_id']}"),
            model=meta["model"],
            runs=meta["runs"],
            ceiling=meta["max_cost_usd"],
        )
        sys.stdout.write(" ".join(cmd) + "\n")
        if args.dry_run:
            return 0
        if args.change:
            _require_committed(root, args.change)
        host, metrics = execute(root, selected, meta, runner=runner)
    except RunRefused as err:
        sys.stderr.write(f"run refused: {err}\n")
        return 2
    sys.stdout.write(render_report(metrics).split("\n## ")[0])
    sys.stdout.write(f"\nhost {host}\n")
    if args.tier == "anchor" and metrics["ceiling"]:
        sys.stderr.write(
            "anchor baseline is at ceiling (C4); the set cannot show improvement\n"
        )
        return EXIT_CEILING
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
