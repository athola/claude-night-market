"""FR-8: paired comparison of two runs, the "change Y moved it" claim.

The claim holds only when the two runs differ in nothing but Y (C1),
both rates are tested (C2), the test is an exact McNemar on discordant
cases with Holm across the rates (C3), and Y was declared before either
run (C7). Each condition is a refusal here rather than a footnote,
because a delta that skipped one is the number most likely to be
quoted.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import yaml

from .analyze import BOOTSTRAP_B, RATES

ALPHA = 0.05
MIN_DISCORDANT = 6
FINGERPRINT_KEYS = (
    "arm",
    "model",
    "claude_code_version",
    "plugins",
    "case_set_hash",
    "runs",
    "tier",
)
# Which per-case count a rate reads, which case kind it covers, and the
# direction that counts as better: +1 when a rise is an improvement.
RATE_SPEC = {
    "sensitivity": ("hit", True, +1),
    "fa_negative": ("fa", False, -1),
    "fa_positive": ("fa", True, -1),
}


class CompareRefused(ValueError):
    """The two runs cannot support a paired claim."""


def mcnemar_p(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2**n
    return min(1.0, 2 * tail)


def holm(pvalues: dict[str, float], alpha: float = ALPHA) -> dict[str, bool]:
    order = sorted(pvalues, key=lambda k: (pvalues[k], k))
    rejected = dict.fromkeys(pvalues, False)
    for step, key in enumerate(order):
        if pvalues[key] > alpha / (len(order) - step):
            break
        rejected[key] = True
    return rejected


def git_is_ancestor(older: str, newer: str) -> bool:
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", older, newer],
        capture_output=True,
        check=False,
    )
    return proc.returncode == 0


def _refuse_unless_comparable(base: dict, new: dict, change: dict) -> None:
    for label, m in (("base", base), ("new", new)):
        if m.get("partial"):
            raise CompareRefused(f"{label} run is partial")
        if not m.get("fingerprint_valid", False):
            raise CompareRefused(f"{label} run has an invalid fingerprint")
        if m["fingerprint"].get("dirty"):
            raise CompareRefused(f"{label} run was made on a dirty tree")
        if sorted(m["cases"]) != sorted(change["cases"]):
            raise CompareRefused(
                f"{label} run did not use exactly the change file's cases"
            )
    for key in FINGERPRINT_KEYS:
        if base["fingerprint"].get(key) != new["fingerprint"].get(key):
            raise CompareRefused(
                f"fingerprint mismatch on {key}: "
                f"{base['fingerprint'].get(key)!r} vs {new['fingerprint'].get(key)!r}"
            )
    old_hashes = base["fingerprint"].get("item_hashes", {})
    new_hashes = new["fingerprint"].get("item_hashes", {})
    undeclared = sorted(
        k
        for k in set(old_hashes) | set(new_hashes)
        if old_hashes.get(k) != new_hashes.get(k) and k not in change["items"]
    )
    if undeclared:
        raise CompareRefused(
            f"items changed outside the change file: {', '.join(undeclared)}"
        )


def _activated(row: dict, field: str) -> bool | None:
    """Majority vote over valid runs; None drops the case from pairing."""
    k, v = row[field], row["v"]
    if v == 0 or 2 * k == v:
        return None
    return 2 * k > v


def _paired_delta_ci(
    base: dict, new: dict, case_ids: list[str], field: str
) -> list[float]:
    clusters: dict[str, list[str]] = {}
    for cid in case_ids:
        clusters.setdefault(base["case_meta"][cid]["cluster"], []).append(cid)
    keys = sorted(clusters)
    if not keys:
        return [0.0, 0.0]
    rng = random.Random(0)
    deltas = []
    for _ in range(BOOTSTRAP_B):
        drawn = [cid for _ in keys for cid in clusters[rng.choice(keys)]]
        rates = []
        for m in (base, new):
            n = sum(m["cases"][c]["v"] for c in drawn)
            rates.append(sum(m["cases"][c][field] for c in drawn) / n if n else 0.0)
        deltas.append(rates[1] - rates[0])
    deltas.sort()
    return [
        round(deltas[int(0.025 * BOOTSTRAP_B)], 6),
        round(deltas[int(0.975 * BOOTSTRAP_B) - 1], 6),
    ]


def _rate(m: dict, case_ids: list[str], field: str) -> float | None:
    n = sum(m["cases"][c]["v"] for c in case_ids)
    return sum(m["cases"][c][field] for c in case_ids) / n if n else None


def compare(
    base: dict,
    new: dict,
    change: dict,
    *,
    is_ancestor: Callable[[str, str], bool] = git_is_ancestor,
    self_check: bool = False,
) -> dict:
    _refuse_unless_comparable(base, new, change)
    if not self_check:
        for label, m in (("base", base), ("new", new)):
            if not is_ancestor(change["declared_at"], m["fingerprint"]["commit"]):
                raise CompareRefused(
                    f"change file declared at {change['declared_at']} is not an ancestor "
                    f"of the {label} run's commit {m['fingerprint']['commit']}"
                )
    results: dict[str, dict] = {}
    for rate, (field, positive, _) in RATE_SPEC.items():
        ids = sorted(
            cid
            for cid, meta in base["case_meta"].items()
            if (meta["type"] != "negative") == positive and cid in change["cases"]
        )
        b = c = dropped = 0
        for cid in ids:
            before = _activated(base["cases"][cid], field)
            after = _activated(new["cases"][cid], field)
            if before is None or after is None:
                dropped += 1
            elif before and not after:
                b += 1
            elif after and not before:
                c += 1
        base_rate, new_rate = _rate(base, ids, field), _rate(new, ids, field)
        results[rate] = {
            "b": b,
            "c": c,
            "dropped": dropped,
            "p": mcnemar_p(b, c),
            "base": base_rate,
            "new": new_rate,
            "delta": round(new_rate - base_rate, 6)
            if None not in (base_rate, new_rate)
            else None,
            "delta_ci": _paired_delta_ci(base, new, ids, field),
        }
    rejected = holm({r: v["p"] for r, v in results.items()})
    for rate, row in results.items():
        direction = RATE_SPEC[rate][2]
        row["holm_rejected"] = rejected[rate]
        if row["b"] + row["c"] == 0:
            row["verdict"] = "no evidence of change"
        elif rejected[rate]:
            rose = row["c"] > row["b"]
            row["verdict"] = "improved" if rose == (direction > 0) else "regressed"
        elif row["b"] + row["c"] < MIN_DISCORDANT:
            row["verdict"] = "underpowered"
        else:
            row["verdict"] = "not significant"
    return {"change": change.get("id"), "self_check": self_check, "rates": results}


def _fmt(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.3f}"


def render(out: dict) -> str:
    lines = [
        f"# Comparison: {out['change']}",
        "",
        "| Rate | Base | New | Delta (95% CI) | b | c | p | Verdict |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for rate in RATES:
        r = out["rates"][rate]
        lines.append(
            f"| {rate} | {_fmt(r['base'])} | {_fmt(r['new'])} | {_fmt(r['delta'])} "
            f"({r['delta_ci'][0]:+.3f} to {r['delta_ci'][1]:+.3f}) | {r['b']} | {r['c']} "
            f"| {r['p']:.4f} | {r['verdict']} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path, help="base run metrics.json")
    parser.add_argument("new", type=Path, help="new run metrics.json")
    parser.add_argument("--change", type=Path, required=True)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)
    change = yaml.safe_load(args.change.read_text())
    try:
        out = compare(
            json.loads(args.base.read_text()),
            json.loads(args.new.read_text()),
            change,
            self_check=args.self_check,
        )
    except CompareRefused as err:
        sys.stderr.write(f"compare refused: {err}\n")
        return 2
    sys.stdout.write(render(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
