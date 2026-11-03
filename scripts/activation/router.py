"""FR-3: offline BM25 router and the per-commit confusability gate.

It ranks every model-routed item against each labeled prompt using only
names and descriptions, which is all the model sees at routing time. It
is a proxy: it measures whether an edit made two items lexically harder
to tell apart, never whether the model activates either. Because the
router also proposed labels, its scores measure agreement with its own
proposals, not correctness.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

from .inventory import Item, build_inventory, item_hashes
from .labels import Case, load_cases

K1 = 1.5
B = 0.75
MRR_TOLERANCE = 0.01
_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class Router:
    def __init__(self, items: list[Item]):
        self.ids = [i.id for i in sorted(items, key=lambda i: i.id)]
        by_id = {i.id: i for i in items}
        self.docs = [
            Counter(
                tokenize(by_id[i].name.replace("-", " ") + " " + by_id[i].description)
            )
            for i in self.ids
        ]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avgdl = (sum(self.lengths) / len(self.lengths)) if self.lengths else 0.0
        df: Counter = Counter()
        for doc in self.docs:
            df.update(doc.keys())
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def scores(self, prompt: str) -> dict[str, float]:
        terms = tokenize(prompt)
        out = {}
        for item_id, doc, length in zip(self.ids, self.docs, self.lengths):
            score = 0.0
            for term in terms:
                tf = doc.get(term, 0)
                if tf:
                    norm = K1 * (1 - B + B * length / self.avgdl)
                    score += self.idf[term] * tf * (K1 + 1) / (tf + norm)
            out[item_id] = score
        return out

    def rank(self, prompt: str) -> list[tuple[str, float]]:
        """Total, deterministic order: score descending, then id ascending."""
        return sorted(self.scores(prompt).items(), key=lambda kv: (-kv[1], kv[0]))


def evaluate(router: Router, cases: list[Case]) -> dict:
    positives = [c for c in cases if c.is_positive]
    per_case: dict[str, dict] = {}
    above: dict[str, Counter] = {}
    score_sum: dict[str, Counter] = {}
    case_count: Counter = Counter()
    for case in positives:
        ranking = router.rank(case.prompt)
        order = [i for i, _ in ranking]
        rank = order.index(case.target) + 1
        per_case[case.id] = {"target": case.target, "rank": rank, "top1": order[0]}
        above.setdefault(case.target, Counter()).update(order[: rank - 1])
        score_sum.setdefault(case.target, Counter()).update(dict(ranking))
        case_count[case.target] += 1
    collisions: Counter = Counter()
    for row in per_case.values():
        if row["top1"] != row["target"]:
            collisions[f"{row['target']} -> {row['top1']}"] += 1
    neighbors = {}
    for target, counts in above.items():
        chosen = [y for y, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))][
            :3
        ]
        fill = sorted(
            (y for y in score_sum[target] if y != target and y not in chosen),
            key=lambda y: (-score_sum[target][y] / case_count[target], y),
        )
        neighbors[target] = chosen + fill[: 3 - len(chosen)]
    total = len(per_case)
    return {
        "mrr": round(sum(1 / r["rank"] for r in per_case.values()) / total, 6)
        if total
        else 0.0,
        "top1": round(sum(r["rank"] == 1 for r in per_case.values()) / total, 6)
        if total
        else 0.0,
        "positives": total,
        "collisions": dict(sorted(collisions.items())),
        "neighbors": dict(sorted(neighbors.items())),
        "cases": dict(sorted(per_case.items())),
    }


def snapshot(items: list[Item], cases: list[Case]) -> dict:
    metrics = evaluate(Router(items), cases)
    metrics["item_hashes"] = item_hashes(items)
    return metrics


def check(base: dict, current: dict) -> tuple[bool, list[str]]:
    messages = []
    ok = True
    delta = current["mrr"] - base["mrr"]
    messages.append(f"MRR {base['mrr']:.4f} -> {current['mrr']:.4f} ({delta:+.4f})")
    if delta < -MRR_TOLERANCE:
        ok = False
        messages.append(f"FAIL: MRR dropped by more than {MRR_TOLERANCE}")
    old_hashes = base.get("item_hashes", {})
    new_hashes = current.get("item_hashes", {})

    def changed(item_id: str) -> bool:
        return old_hashes.get(item_id) != new_hashes.get(item_id)

    for cid, row in current["cases"].items():
        before = base["cases"].get(cid)
        if before is None:
            continue
        was_clean = before["top1"] == before["target"]
        now_collides = row["top1"] != row["target"]
        if (
            was_clean
            and now_collides
            and (changed(row["target"]) or changed(row["top1"]))
        ):
            ok = False
            messages.append(
                f"FAIL: new collision {cid}: {row['target']} lost to {row['top1']}"
            )
        elif not was_clean and not now_collides:
            messages.append(f"cleared collision {cid}: {row['target']}")
    return ok, messages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "baseline", "report"])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    suite = args.root / "evals/activation"
    baseline_path = suite / "router-baseline.json"
    current = snapshot(build_inventory(args.root), load_cases(suite / "labels"))
    if args.command == "baseline":
        baseline_path.write_text(json.dumps(current, indent=1, sort_keys=True) + "\n")
        sys.stdout.write(f"wrote {baseline_path} (MRR {current['mrr']:.4f})\n")
        return 0
    if args.command == "report":
        top = sorted(current["collisions"].items(), key=lambda kv: (-kv[1], kv[0]))[:20]
        sys.stdout.write(
            f"positives {current['positives']} MRR {current['mrr']:.4f} "
            f"top1 {current['top1']:.4f}\n"
        )
        for pair, count in top:
            sys.stdout.write(f"  {count:3d}  {pair}\n")
        return 0
    if not baseline_path.exists():
        sys.stderr.write(
            f"router: no baseline at {baseline_path}; run `uv run python -m scripts.activation.router baseline`\n"
        )
        return 1
    ok, messages = check(json.loads(baseline_path.read_text()), current)
    sys.stdout.write("\n".join(messages) + "\n")
    if not ok:
        sys.stdout.write(
            "If the change is intended, run `uv run python -m scripts.activation.router "
            "baseline` and commit the new baseline with it.\n"
        )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
