"""FR-9 (C6): the mutation self-check.

A suite that cannot detect blanked or swapped descriptions cannot
detect a subtle description edit either, so its comparisons are not
trusted until it passes. Mutants are chosen from cases the clean run
activated, because only those can flip to a miss.

Floors: an exact two-sided McNemar needs 7 one-way discordant cases to
pass the strictest Holm step (0.05 / 3), so fewer than 7 activated
cases is infeasible; 12 is the target because one item carries only 3.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import yaml

from . import run as run_mod
from .compare import CompareRefused, compare
from .inventory import _FRONTMATTER, Item, build_inventory
from .labels import load_cases
from .router import Router, evaluate

TARGET = 12
FLOOR = 7


def _activated_by_item(clean: dict, anchor: set[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for cid, row in clean["cases"].items():
        meta = clean["case_meta"][cid]
        if (
            cid in anchor
            and meta["type"] != "negative"
            and row["v"]
            and 2 * row["hit"] > row["v"]
        ):
            counts[meta["target"]] = counts.get(meta["target"], 0) + 1
    return counts


def _status(covered: int) -> str:
    if covered >= TARGET:
        return "ok"
    return "below_target" if covered >= FLOOR else "infeasible"


def select_blank(clean: dict, *, anchor: set[str]) -> dict:
    counts = _activated_by_item(clean, anchor)
    chosen, covered = [], 0
    for item in sorted(counts, key=lambda i: (-counts[i], i)):
        if covered >= TARGET:
            break
        chosen.append(item)
        covered += counts[item]
    return {
        "mutant": "blank",
        "items": chosen,
        "covered": covered,
        "status": _status(covered),
    }


def select_swap(clean: dict, *, anchor: set[str], collisions: dict[str, int]) -> dict:
    """Swap descriptions across router collision pairs, most frequent first."""
    counts = _activated_by_item(clean, anchor)
    pairs, used, covered = [], set(), 0
    for pair in sorted(collisions, key=lambda p: (-collisions[p], p)):
        if covered >= TARGET:
            break
        left, right = (s.strip() for s in pair.split("->"))
        if left in used or right in used or left not in counts or right not in counts:
            continue
        pairs.append([left, right])
        used.update((left, right))
        covered += counts[left] + counts[right]
    items = sorted(used)
    return {
        "mutant": "swap",
        "pairs": pairs,
        "items": items,
        "covered": covered,
        "status": _status(covered),
    }


def _replace(path: Path, text: str) -> None:
    """Write a new file; never write through a hard link into the repo."""
    path.unlink()
    path.write_text(text, encoding="utf-8")


def _js_literal(text: str) -> str:
    return "'" + text.replace("\\", "\\\\").replace("'", "\\'") + "'"


def set_description(path: Path, kind: str, description: str) -> None:
    source = path.read_text(encoding="utf-8")
    if kind == "workflow":
        string = r"""(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")"""
        start = source.index("export const meta")  # inventory reads from here on
        head, meta = source[:start], source[start:]
        meta = re.sub(
            rf"(\bdescription:\s*){string}",
            lambda m: m.group(1) + _js_literal(description),
            meta,
            count=1,
        )
        meta = re.sub(
            rf"(\bwhenToUse:\s*){string}", lambda m: m.group(1) + "''", meta, count=1
        )
        _replace(path, head + meta)
        return
    match = _FRONTMATTER.match(source)
    meta = yaml.safe_load(match.group(1)) or {}
    meta["description"] = description
    front = yaml.safe_dump(
        meta, sort_keys=False, allow_unicode=True, width=10_000
    ).rstrip("\n")
    _replace(path, f"---\n{front}\n---" + source[match.end() :])


def apply_descriptions(host_root: Path, items: list[Item], new: dict[str, str]) -> None:
    by_id = {i.id: i for i in items}
    for item_id, description in new.items():
        item = by_id[item_id]
        set_description(host_root / item.path, item.kind, description)


def mutant_descriptions(selection: dict, items: list[Item]) -> dict[str, str]:
    if selection["mutant"] == "blank":
        return dict.fromkeys(selection["items"], ".")
    by_id = {i.id: i.description for i in items}
    swapped = {}
    for left, right in selection["pairs"]:
        swapped[left], swapped[right] = by_id[right], by_id[left]
    return swapped


def self_check_passed(compare_out: dict) -> bool:
    return compare_out["rates"]["sensitivity"]["verdict"] == "regressed"


def run_self_check(root: Path, arm: str, *, runner=None) -> dict:
    """Clean anchor run, then a blank and a swap mutant, each compared
    to the clean run in self-check mode. Writes the report and returns
    the summary.
    """
    runner = runner or run_mod.subprocess_runner
    args = argparse.Namespace(
        tier="anchor", arm=arm, runs=None, change=None, max_cost_usd=None
    )
    selected, meta = run_mod.plan_run(root, args)
    anchor = {c.id for c in selected}
    base_id = meta["run_id"]
    _, clean = run_mod.execute(
        root, selected, {**meta, "run_id": f"{base_id}-clean"}, runner=runner
    )
    items = build_inventory(root)
    collisions = evaluate(
        Router(items), load_cases(run_mod.suite_dir(root) / "labels")
    )["collisions"]
    selections = [
        select_blank(clean, anchor=anchor),
        select_swap(clean, anchor=anchor, collisions=collisions),
    ]
    results = []
    for sel in selections:
        row = {
            "mutant": sel["mutant"],
            "items": sel["items"],
            "covered": sel["covered"],
            "status": sel["status"],
            "passed": False,
        }
        if sel["status"] == "infeasible":
            results.append(row)
            continue
        record = {
            "id": f"self-check-{sel['mutant']}",
            "items": sel["items"],
            "cases": sorted(anchor),
            "declared_at": None,
        }

        def mutate(host: Path, host_items: list[Item], sel=sel, record=record) -> None:
            path = host / "changes" / f"{record['id']}.yaml"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(yaml.safe_dump(record, sort_keys=False))
            apply_descriptions(host, host_items, mutant_descriptions(sel, host_items))
            run = json.loads((host / "run.json").read_text())
            run["change_recorded_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
            (host / "run.json").write_text(json.dumps(run, indent=1, sort_keys=True))

        _, mutated = run_mod.execute(
            root,
            selected,
            {**meta, "run_id": f"{base_id}-{sel['mutant']}"},
            runner=runner,
            mutate=mutate,
        )
        try:
            out = compare(clean, mutated, record, self_check=True)
        except CompareRefused as err:
            row["refused"] = str(err)
            results.append(row)
            continue
        row["sensitivity"] = out["rates"]["sensitivity"]
        row["passed"] = self_check_passed(out)
        results.append(row)
    summary = {
        "arm": arm,
        "date": dt.date.today().isoformat(),
        "passed": all(r["passed"] for r in results),
        "mutants": results,
        "anchor_case_set_hash": clean["fingerprint"]["case_set_hash"],
        "cost_usd": clean["cost_usd"],
    }
    reports = run_mod.suite_dir(root) / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    stem = reports / f"self-check-{arm}-{summary['date']}"
    stem.with_suffix(".json").write_text(
        json.dumps(summary, indent=1, sort_keys=True) + "\n"
    )
    lines = [
        f"# Mutation self-check: {arm} arm, {summary['date']}",
        "",
        f"Result: {'PASS' if summary['passed'] else 'FAIL'}. A failing self-check marks "
        "comparisons on this anchor set untrusted until a later self-check passes.",
        "",
        "| Mutant | Items | Activated cases covered | Status | Sensitivity verdict |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        verdict = r.get("sensitivity", {}).get("verdict", r.get("refused", "not run"))
        lines.append(
            f"| {r['mutant']} | {len(r['items'])} | {r['covered']} | {r['status']} | {verdict} |"
        )
    stem.with_suffix(".md").write_text("\n".join(lines) + "\n")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", default="default")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.dry_run:
        plan = argparse.Namespace(
            tier="anchor", arm=args.arm, runs=None, change=None, max_cost_usd=None
        )
        selected, meta = run_mod.plan_run(args.root, plan)
        per_run = run_mod.estimate_cost(args.root, args.arm)
        case_runs = 3 * len(selected) * meta["runs"]
        estimate = (
            f"${per_run * case_runs:.2f}" if per_run is not None else "unmeasured"
        )
        sys.stdout.write(
            f"self-check, {args.arm} arm: 3 anchor runs, {case_runs} case-runs, "
            f"estimate {estimate}, ceiling ${3 * meta['max_cost_usd']:g}\n"
        )
        return 0
    summary = run_self_check(args.root, args.arm)
    sys.stdout.write(f"self-check {'PASS' if summary['passed'] else 'FAIL'}\n")
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
