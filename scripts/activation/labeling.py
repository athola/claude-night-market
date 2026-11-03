"""FR-2 creation: draft and pre-label prompts with models not under test.

The measured models must never write their own answer key, so the
writer and judge are the first configured candidates whose resolved
model id differs from every arm's. Labeling fails closed when a model
was not resolved. Prompts are drafted from item bodies, never from
descriptions, and the judge reads body excerpts of the router's
shortlist, so neither proposer copies the text the model routes on.
Body wording often repeats the description anyway; reports state that
echo risk rather than claim it is gone.

Usage (uv run python -m scripts.activation.<command>):
  labeling resolve           probe each configured model once (spends ~$0.05 each)
  labeling draft             write labels/<plugin>.yaml and adjudicate.yaml
  labeling queue             list prompts still awaiting adjudication
"""

from __future__ import annotations

import json
import random
import re
import subprocess
import sys
from pathlib import Path

import yaml

from .inventory import _FRONTMATTER, Item, build_inventory
from .labels import Case
from .router import Router, evaluate

BODY_CHARS = 3000
SHORTLIST = 8
BATCH = 8
AUDIT_SHARE = 0.10
NEGATIVE_SOURCES = (
    "refactoring a Python function",
    "fixing a failing unit test",
    "explaining a compiler error",
    "writing a SQL query",
    "renaming variables across a file",
    "general programming concept questions",
    "editing a YAML config value",
    "small frontend CSS fixes",
    "reading a stack trace",
    "writing a regular expression",
    "shell one-liners",
    "data structure choice",
)
NEGATIVES_PER_SOURCE = 5


class BudgetExceeded(RuntimeError):
    """The labeling session reached label_max_cost_usd."""


class LabelingRefused(RuntimeError):
    """Configuration would let a measured model shape its own labels."""


def claude_call(model: str | None, prompt: str) -> tuple[str, float]:
    cmd = ["claude", "-p", "--output-format", "json"]
    if model:
        cmd += ["--model", model]
    proc = subprocess.run([*cmd, prompt], capture_output=True, text=True, check=True)
    out = json.loads(proc.stdout)
    return out, float(out.get("total_cost_usd") or 0.0)


def resolved_model(result: dict) -> str:
    """The model that answered, from the result's per-model usage."""
    usage = result.get("modelUsage") or {}
    if not usage:
        raise LabelingRefused(
            "probe result carries no modelUsage; cannot resolve the model"
        )
    return max(usage, key=lambda m: usage[m].get("outputTokens", 0))


def resolve(config: dict, call=claude_call) -> dict:
    wanted = {**{f"arm:{k}": v for k, v in config["arms"].items()}}
    for alias in [*config["writer_models"], *config["judge_models"]]:
        wanted[alias] = alias
    resolved = {}
    for key, model in wanted.items():
        result, _ = call(model, "Reply with the single word ok.")
        resolved[key] = resolved_model(result)
    return resolved


def pick_roles(config: dict) -> dict[str, str]:
    resolved = config.get("resolved") or {}
    arm_ids = set()
    for arm in config["arms"]:
        if f"arm:{arm}" not in resolved:
            raise LabelingRefused(
                f"arm {arm} is unresolved; run `uv run python -m scripts.activation.labeling resolve`"
            )
        arm_ids.add(resolved[f"arm:{arm}"])
    roles = {}
    for role in ("writer", "judge"):
        for alias in config[f"{role}_models"]:
            if alias not in resolved:
                raise LabelingRefused(
                    f"{alias} is unresolved; run `uv run python -m scripts.activation.labeling resolve`"
                )
            if resolved[alias] not in arm_ids:
                roles[role] = alias
                break
        else:
            raise LabelingRefused(
                f"every {role} candidate resolves to a measured arm ({sorted(arm_ids)}); "
                f"add a candidate to {role}_models"
            )
    return roles


class Budget:
    def __init__(self, call, ceiling: float):
        self.call, self.ceiling, self.spent = call, ceiling, 0.0

    def __call__(self, model: str | None, prompt: str) -> str:
        if self.spent >= self.ceiling:
            raise BudgetExceeded(f"spent ${self.spent:.2f} of ${self.ceiling:.2f}")
        result, cost = self.call(model, prompt)
        self.spent += cost
        return result.get("result", "") if isinstance(result, dict) else str(result)


def item_body(root: Path, item: Item) -> str:
    source = (root / item.path).read_text(encoding="utf-8")
    if item.kind == "workflow":
        source = re.sub(r"\b(description|whenToUse):\s*'(?:[^'\\]|\\.)*',?", "", source)
    else:
        match = _FRONTMATTER.match(source)
        source = source[match.end() :] if match else source
    return source.strip()[:BODY_CHARS]


def parse_json_list(text: str) -> list:
    start, end = text.find("["), text.rfind("]")
    if start < 0 or end < start:
        return []
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _writer_prompt(blocks: list[str], ask: str) -> str:
    return (
        "You write test prompts for a skill router. A user types each prompt to a coding "
        "assistant. Write prompts the way a developer would, naming their task, not the tool. "
        "Never quote or paraphrase a heading from the material.\n\n"
        f"{ask}\n\nReturn only a JSON array of objects, no prose.\n\n"
        + "\n\n".join(blocks)
    )


def draft_plain(root, items, writer, model) -> dict[str, list[str]]:
    drafted: dict[str, list[str]] = {}
    for start in range(0, len(items), BATCH):
        batch = items[start : start + BATCH]
        blocks = [f"### ITEM {i.id}\n{item_body(root, i)}" for i in batch]
        text = writer(
            model,
            _writer_prompt(
                blocks,
                "For each ITEM write 2 prompts its material would serve. Objects: "
                '{"item": "<id>", "prompt": "<text>"}.',
            ),
        )
        for row in parse_json_list(text):
            if isinstance(row, dict) and row.get("item") in {i.id for i in batch}:
                drafted.setdefault(row["item"], []).append(str(row["prompt"]))
    return {k: v[:2] for k, v in drafted.items()}


def draft_near_misses(
    root, items, neighbors, writer, model
) -> dict[str, tuple[str, str]]:
    by_id = {i.id: i for i in items}
    out = {}
    pending = [i for i in items if neighbors.get(i.id)]
    for start in range(0, len(pending), BATCH):
        batch = pending[start : start + BATCH]
        blocks = [
            f"### ITEM {i.id}\n{item_body(root, i)[:1500]}\n### NEIGHBOR {neighbors[i.id][0]}\n"
            f"{item_body(root, by_id[neighbors[i.id][0]])[:1000]}"
            for i in batch
        ]
        text = writer(
            model,
            _writer_prompt(
                blocks,
                "For each ITEM write 1 prompt that ITEM serves but that a hasty reader "
                "could send to its NEIGHBOR. Objects: "
                '{"item": "<id>", "prompt": "<text>"}.',
            ),
        )
        for row in parse_json_list(text):
            if (
                isinstance(row, dict)
                and row.get("item") in neighbors
                and row["item"] not in out
            ):
                out[row["item"]] = (str(row["prompt"]), neighbors[row["item"]][0])
    return out


def draft_negatives(writer, model) -> list[tuple[str, str]]:
    text = writer(
        model,
        _writer_prompt(
            [],
            f"For each of these sources write {NEGATIVES_PER_SOURCE} everyday coding requests "
            "that need no special workflow, review, or plugin: "
            + "; ".join(NEGATIVE_SOURCES)
            + '. Objects: {"source": "<source>", "prompt": "<text>"}.',
        ),
    )
    rows = parse_json_list(text)
    return [
        (str(r["source"]), str(r["prompt"]))
        for r in rows
        if isinstance(r, dict) and r.get("source") in NEGATIVE_SOURCES
    ]


def judge_pick(
    root: Path, router: Router, by_id: dict, ask, prompt: str
) -> tuple[str | None, str | None]:
    """Judge picks among the router's shortlist, shown bodies only."""
    shortlist = [i for i, _ in router.rank(prompt)[:SHORTLIST]]
    blocks = [f"### {cid}\n{item_body(root, by_id[cid])[:800]}" for cid in shortlist]
    text = ask(
        (
            "A developer typed the PROMPT below to a coding assistant that can invoke the tools "
            "listed. Pick the tool that should handle it, and a runner-up, or none when the "
            "assistant should answer directly. Return only JSON: "
            '[{"pick": "<id or none>", "runner_up": "<id or none>"}].\n\n'
            f"PROMPT: {prompt}\n\n" + "\n\n".join(blocks)
        ),
    )
    rows = parse_json_list(text)
    if not rows or not isinstance(rows[0], dict):
        return None, None
    pick, runner = rows[0].get("pick"), rows[0].get("runner_up")
    valid = set(shortlist)
    return (pick if pick in valid else None), (runner if runner in valid else None)


def _slug(item_id: str) -> str:
    return item_id.replace(":", ".").lower()


def draft(root: Path, config: dict, call=claude_call) -> dict:
    roles = pick_roles(config)
    budget = Budget(call, float(config["label_max_cost_usd"]))
    items = build_inventory(root)
    router = Router(items)
    writer, judge = roles["writer"], roles["judge"]
    by_id = {i.id: i for i in items}

    def ask_judge(prompt: str) -> str:
        return budget(judge, prompt)

    plain = draft_plain(root, items, budget, writer)
    plain_cases = [
        Case(id=f"{_slug(t)}.p{n + 1}", type="positive", prompt=p, target=t, cluster=t)
        for t, prompts in plain.items()
        for n, p in enumerate(prompts)
    ]
    neighbors = evaluate(router, plain_cases)["neighbors"]
    near = draft_near_misses(root, items, neighbors, budget, writer)
    negatives = draft_negatives(budget, writer)
    rows, disagreements = [], []
    for case in plain_cases:
        top = router.rank(case.prompt)[0][0]
        pick, _ = judge_pick(root, router, by_id, ask_judge, case.prompt)
        proposers = [
            n for n, who in (("router", top), ("judge", pick)) if who == case.target
        ]
        row = case.to_dict() | {"proposers": proposers or ["writer"]}
        if top != case.target or pick != case.target:
            row["notes"] = f"router: {top}; judge: {pick}"
            disagreements.append(row["id"])
        rows.append(row)
    for target, (prompt, neighbor) in sorted(near.items()):
        ranking = [i for i, _ in router.rank(prompt)]
        pick, runner = judge_pick(root, router, by_id, ask_judge, prompt)
        competitor = (
            runner
            if runner and runner != target
            else next(i for i in ranking if i != target)
        )
        cid = f"{_slug(target)}.p3"
        row = Case(
            id=cid,
            type="near_miss",
            prompt=prompt,
            target=target,
            competitor=competitor,
            cluster=target,
            proposers=("writer",),
        ).to_dict()
        row["proposers"] = [
            n for n, who in (("router", ranking[0]), ("judge", pick)) if who == target
        ] or ["writer"]
        row["notes"] = (
            f"aimed at {neighbor}; router: {ranking[0]}; judge: {pick}/{runner}"
        )
        if ranking[0] != target or pick != target or competitor != neighbor:
            disagreements.append(cid)
        rows.append(row)
    for n, (source, prompt) in enumerate(negatives):
        top = router.rank(prompt)[0]
        pick, _ = judge_pick(root, router, by_id, ask_judge, prompt)
        rows.append(
            Case(
                id=f"neg.{n + 1:03d}",
                type="negative",
                prompt=prompt,
                target=None,
                cluster=source,
                proposers=("writer",),
                notes=f"router top: {top[0]} ({top[1]:.2f}); judge: {pick}",
            ).to_dict()
        )
        if pick is not None:
            disagreements.append(f"neg.{n + 1:03d}")
    agreed = sorted({r["id"] for r in rows} - set(disagreements))
    audit = (
        sorted(random.Random(0).sample(agreed, round(AUDIT_SHARE * len(agreed))))
        if agreed
        else []
    )
    labels_dir = root / "evals/activation/labels"
    labels_dir.mkdir(parents=True, exist_ok=True)
    by_file: dict[str, list[dict]] = {}
    for row in rows:
        name = row["target"].split(":")[0] if row["target"] else "_negatives"
        by_file.setdefault(name, []).append(row)
    for name, file_rows in by_file.items():
        (labels_dir / f"{name}.yaml").write_text(
            yaml.safe_dump(
                {"schema_version": 1, "cases": file_rows},
                sort_keys=False,
                allow_unicode=True,
            )
        )
    queue = {
        "disagreements": sorted(set(disagreements)),
        "audit_sample": audit,
        "writer": writer,
        "judge": judge,
        "spent_usd": round(budget.spent, 4),
    }
    (root / "evals/activation/adjudicate.yaml").write_text(
        yaml.safe_dump(queue, sort_keys=False)
    )
    return queue


def pending(root: Path) -> list[str]:
    queue = yaml.safe_load((root / "evals/activation/adjudicate.yaml").read_text())
    wanted = set(queue["disagreements"]) | set(queue["audit_sample"])
    done = set()
    for path in (root / "evals/activation/labels").glob("*.yaml"):
        for row in yaml.safe_load(path.read_text()).get("cases") or []:
            if row.get("adjudicated"):
                done.add(row["id"])
    return sorted(wanted - done)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    root = Path.cwd()
    config_path = root / "evals/activation/config.yaml"
    config = yaml.safe_load(config_path.read_text())
    command = argv[0] if argv else ""
    try:
        if command == "resolve":
            config["resolved"] = resolve(config)
            config_path.write_text(yaml.safe_dump(config, sort_keys=False))
            sys.stdout.write(json.dumps(config["resolved"], indent=1) + "\n")
        elif command == "draft":
            queue = draft(root, config)
            sys.stdout.write(
                f"drafted labels; {len(queue['disagreements'])} disagreements and "
                f"{len(queue['audit_sample'])} audit cases to adjudicate; "
                f"spent ${queue['spent_usd']:.2f}\n"
            )
        elif command == "queue":
            remaining = pending(root)
            sys.stdout.write(
                "\n".join(remaining) + ("\n" if remaining else "nothing pending\n")
            )
            return 1 if remaining else 0
        else:
            sys.stderr.write(__doc__)
            return 2
    except (LabelingRefused, BudgetExceeded) as err:
        sys.stderr.write(f"labeling stopped: {err}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
