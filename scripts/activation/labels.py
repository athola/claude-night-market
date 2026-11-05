"""FR-2: load, validate and hash the labeled answer key.

A label that names an unknown item, or a near-miss with no competitor,
does not fail at run time: it silently counts as a miss. Validation
turns each of those into an error before a run can spend money on it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .inventory import Item, _frontmatter, build_inventory

TYPES = ("positive", "near_miss", "negative")
_ID = re.compile(r"^[a-z0-9.-]+$")


class LabelError(ValueError):
    """A label file violates the FR-2 schema."""


@dataclass(frozen=True)
class Case:
    id: str
    type: str
    prompt: str
    target: str | None
    cluster: str
    competitor: str | None = None
    proposers: tuple[str, ...] = field(default_factory=tuple)
    adjudicated: bool = False
    notes: str = ""

    @classmethod
    def from_dict(cls, row: dict) -> Case:
        return cls(
            id=str(row["id"]),
            type=str(row["type"]),
            prompt=str(row["prompt"]),
            target=row.get("target"),
            cluster=str(row.get("cluster") or row.get("target") or ""),
            competitor=row.get("competitor"),
            proposers=tuple(row.get("proposers") or ()),
            adjudicated=bool(row.get("adjudicated", False)),
            notes=str(row.get("notes") or ""),
        )

    @property
    def is_positive(self) -> bool:
        """Near-misses are positives: they name a target that must fire."""
        return self.type != "negative"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "prompt": self.prompt,
            "target": self.target,
            "competitor": self.competitor,
            "cluster": self.cluster,
            "proposers": list(self.proposers),
            "adjudicated": self.adjudicated,
            "notes": self.notes,
        }


def load_cases(labels_dir: Path) -> list[Case]:
    cases = []
    for path in sorted(labels_dir.glob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if doc.get("schema_version") != 1:
            raise LabelError(f"{path}: schema_version must be 1")
        cases.extend(Case.from_dict(row) for row in doc.get("cases") or [])
    return cases


def _disabled_ids(root: Path) -> set[str]:
    disabled = set()
    for path in root.glob("plugins/*/skills/*/SKILL.md"):
        if _frontmatter(path).get("disable-model-invocation") is True:
            disabled.add(f"{path.parts[-4]}:{path.parent.name}")
    for path in root.glob("plugins/*/commands/*.md"):
        if _frontmatter(path).get("disable-model-invocation") is True:
            disabled.add(f"{path.parts[-3]}:{path.stem}")
    return disabled


def validate(cases: list[Case], items: list[Item], root: Path) -> None:
    known = {i.id for i in items}
    disabled = _disabled_ids(root)
    seen: set[str] = set()
    for case in cases:
        where = f"case {case.id!r}"
        if not _ID.match(case.id):
            raise LabelError(f"{where}: id must match {_ID.pattern}")
        if case.id in seen:
            raise LabelError(f"{where}: duplicate id")
        seen.add(case.id)
        if case.type not in TYPES:
            raise LabelError(f"{where}: type must be one of {TYPES}")
        if case.type == "negative":
            if case.target is not None:
                raise LabelError(f"{where}: negative with a target")
            if not case.cluster:
                raise LabelError(f"{where}: negative needs a cluster naming its source")
            continue
        if case.target in disabled:
            raise LabelError(
                f"{where}: target {case.target} is disable-model-invocation"
            )
        if case.target not in known:
            raise LabelError(f"{where}: unknown target {case.target!r}")
        if case.type == "near_miss":
            if not case.competitor or case.competitor == case.target:
                raise LabelError(
                    f"{where}: near_miss needs a competitor other than its target"
                )
            if case.competitor not in known:
                raise LabelError(f"{where}: unknown competitor {case.competitor!r}")


def coverage_gaps(
    cases: list[Case],
    items: list[Item],
    *,
    min_positives: int = 3,
    min_negatives: int = 50,
    min_sources: int = 10,
) -> dict:
    counts = {i.id: 0 for i in items}
    for case in cases:
        if case.is_positive and case.target in counts:
            counts[case.target] += 1
    short = {k: v for k, v in counts.items() if v < min_positives}
    negatives = [c for c in cases if c.type == "negative"]
    sources = {c.cluster for c in negatives}
    return {
        "items": short,
        "negatives": (len(negatives), min_negatives),
        "sources": (len(sources), min_sources),
        "ok": not short
        and len(negatives) >= min_negatives
        and len(sources) >= min_sources,
    }


def case_set_hash(cases: list[Case]) -> str:
    rows = sorted([c.id, c.type, c.prompt, c.target] for c in cases)
    payload = json.dumps(rows, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "coverage"])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--labels", type=Path, default=None)
    args = parser.parse_args(argv)
    labels_dir = args.labels or args.root / "evals/activation/labels"
    items = build_inventory(args.root)
    cases = load_cases(labels_dir)
    try:
        validate(cases, items, args.root)
    except LabelError as err:
        sys.stderr.write(f"labels: {err}\n")
        return 1
    if args.command == "validate":
        sys.stdout.write(
            f"{len(cases)} cases valid, case_set_hash {case_set_hash(cases)}\n"
        )
        return 0
    gaps = coverage_gaps(cases, items)
    sys.stdout.write(
        f"items short of 3 positives: {len(gaps['items'])}\n"
        f"negatives: {gaps['negatives'][0]}/{gaps['negatives'][1]}, "
        f"sources: {gaps['sources'][0]}/{gaps['sources'][1]}\n"
    )
    for item_id, count in sorted(gaps["items"].items()):
        sys.stdout.write(f"  {item_id}: {count}\n")
    return 0 if gaps["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
