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
  labeling repair            fill short items, re-judge rows the judge never saw
  labeling requeue           rebuild adjudicate.yaml from the labels, no spend
  labeling queue             list prompts still awaiting adjudication
"""

from __future__ import annotations

import json
import random
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import yaml

from .inventory import _FRONTMATTER, Item, build_inventory
from .labels import Case, coverage_gaps
from .router import Router, evaluate

BODY_CHARS = 3000
SHORTLIST = 8
BATCH = 8
JUDGE_BATCH = 10
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


def claude_call(model: str | None, prompt: str) -> tuple[dict, float]:
    """One headless call with no tools, skills or saved session.

    It runs from an empty temporary directory so the repository's
    CLAUDE.md and project settings stay out of the prompt. Labeling
    needs text in and text out, and every loaded token is paid for on
    each of several hundred calls.
    """
    cmd = [
        "claude",
        "-p",
        "--output-format",
        "json",
        "--tools",
        "",
        "--disable-slash-commands",
        "--no-session-persistence",
    ]
    if model:
        cmd += ["--model", model]
    with tempfile.TemporaryDirectory(prefix="activation-label-") as cwd:
        proc = subprocess.run(
            [*cmd, prompt], capture_output=True, text=True, check=True, cwd=cwd
        )
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


def write_resolved(config_path: Path, resolved: dict) -> None:
    """Replace only the ``resolved:`` block, keeping the file's comments."""
    lines = config_path.read_text().splitlines()
    start = next(n for n, line in enumerate(lines) if line.startswith("resolved:"))
    end = start + 1
    while end < len(lines) and lines[end].startswith((" ", "\t")):
        end += 1
    block = ["resolved:"] + [f"  {key}: {value}" for key, value in resolved.items()]
    config_path.write_text("\n".join(lines[:start] + block + lines[end:]) + "\n")


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
    """Caps spend and records failed calls.

    A failed ``claude -p`` call (non-zero exit or unparseable output)
    loses one batch, which the coverage gate then reports as missing
    prompts. Stopping the whole session on it would discard every batch
    already paid for.
    """

    def __init__(self, call, ceiling: float):
        self.call, self.ceiling, self.spent = call, ceiling, 0.0
        self.failures: list[str] = []

    def __call__(self, model: str | None, prompt: str) -> str:
        if self.spent >= self.ceiling:
            raise BudgetExceeded(f"spent ${self.spent:.2f} of ${self.ceiling:.2f}")
        try:
            result, cost = self.call(model, prompt)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as err:
            detail = getattr(err, "stderr", None) or str(err)
            self.failures.append(str(detail).strip()[:200])
            sys.stderr.write(
                f"labeling: call failed, batch skipped: {self.failures[-1]}\n"
            )
            return ""
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
    by_id = {i.id: i for i in build_inventory(root)}  # neighbors may lie outside items
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


def judge_batch(root: Path, router: Router, by_id: dict, ask, prompts: list) -> list:
    """Judge picks for several (prompt, target) pairs in one call.

    Candidates are the router's top 8 plus the writer's target, sorted by
    id. Without the target the judge could only disagree whenever the
    router ranked it low: the first full draft (2026-11-03) lost 328 of
    628 positive labels that way. Returns (pick, runner_up) per prompt,
    None where the judge named nothing valid.
    """
    shortlists = []
    for prompt, target in prompts:
        short = {i for i, _ in router.rank(prompt)[:SHORTLIST]}
        if target:
            short.add(target)
        shortlists.append(sorted(short))
    shown = sorted({cid for short in shortlists for cid in short})
    tools = "\n\n".join(
        f"### {cid}\n{item_body(root, by_id[cid])[:800]}" for cid in shown
    )
    asks = "\n".join(
        f"PROMPT {n}: {p}\nCANDIDATES {n}: {', '.join(short)}"
        for n, ((p, _), short) in enumerate(zip(prompts, shortlists))
    )
    text = ask(
        "Each PROMPT below was typed by a developer to a coding assistant that can "
        "invoke the tools described at the end. For each, pick the tool from its "
        "CANDIDATES that should handle it and a runner-up, or none when the assistant "
        "should answer directly. Return only JSON: "
        '[{"n": <number>, "pick": "<id or none>", "runner_up": "<id or none>"}].\n\n'
        f"{asks}\n\n{tools}"
    )
    out: list = [(None, None)] * len(prompts)
    for row in parse_json_list(text):
        if not isinstance(row, dict) or not isinstance(row.get("n"), int):
            continue
        n = row["n"]
        if 0 <= n < len(prompts):
            valid = set(shortlists[n])
            pick, runner = row.get("pick"), row.get("runner_up")
            out[n] = (
                pick if pick in valid else None,
                runner if runner in valid else None,
            )
    return out


def judge_all(root, router, by_id, ask, prompts: list) -> tuple[list, str | None]:
    """Judge in batches; on budget exhaustion keep what was judged.

    Unjudged prompts come back as "unjudged" and land in the
    adjudication queue, so a budget stop costs review time, not labels.
    """
    picks: list = []
    for start in range(0, len(prompts), JUDGE_BATCH):
        try:
            picks += judge_batch(
                root, router, by_id, ask, prompts[start : start + JUDGE_BATCH]
            )
        except BudgetExceeded as err:
            picks += [("unjudged", None)] * (len(prompts) - len(picks))
            return picks, str(err)
    return picks, None


def _slug(item_id: str) -> str:
    return item_id.replace(":", ".").lower()


def apply_judgment(row: dict, pick, runner, router: Router) -> dict:
    """Record each proposer's answer on a row and derive its proposers.

    ``proposals`` keeps what the router and the judge named, so the
    queue can be recomputed later without parsing prose notes.
    """
    proposals = dict(row.get("proposals") or {})
    if row["type"] == "negative":
        top, score = router.rank(row["prompt"])[0]
        proposals.update(router=top, router_score=round(score, 2), judge=pick)
        row["proposals"] = proposals
        row["notes"] = f"router top: {top} ({score:.2f}); judge: {pick}"
        return row
    ranking = [i for i, _ in router.rank(row["prompt"])]
    target = row["target"]
    proposals.update(router=ranking[0], judge=pick, judge_runner_up=runner)
    if row["type"] == "near_miss":
        row["competitor"] = (
            runner
            if runner and runner != target
            else next(i for i in ranking if i != target)
        )
    row["proposals"] = proposals
    row["proposers"] = [
        name for name in ("router", "judge") if proposals[name] == target
    ] or ["writer"]
    aimed = f"aimed at {proposals['aimed_at']}; " if proposals.get("aimed_at") else ""
    row["notes"] = f"{aimed}router: {ranking[0]}; judge: {pick}/{runner}"
    return row


def _none(value: str | None) -> str | None:
    return None if value in (None, "None", "none") else value


def backfill_proposals(row: dict) -> dict:
    """Recover ``proposals`` for rows written before the field existed.

    The first draft wrote notes only where a proposer disagreed, so an
    empty note on a positive means router and judge both named the
    target.
    """
    if "proposals" in row:
        return row
    notes = row.get("notes") or ""
    proposals: dict = {}
    if row["type"] == "negative":
        found = re.match(r"router top: (\S+) \(([\d.]+)\); judge: (\S+)", notes)
        if found:
            proposals = {
                "router": found.group(1),
                "router_score": float(found.group(2)),
                "judge": _none(found.group(3)),
            }
    elif row["type"] == "near_miss":
        found = re.match(r"aimed at (\S+); router: (\S+); judge: ([^/]+)/(\S+)", notes)
        if found:
            proposals = {
                "aimed_at": found.group(1),
                "router": found.group(2),
                "judge": _none(found.group(3)),
                "judge_runner_up": _none(found.group(4)),
            }
    elif not notes:
        proposals = {"router": row["target"], "judge": row["target"]}
    else:
        found = re.match(r"router: (\S+); judge: (\S+)", notes)
        if found:
            proposals = {"router": found.group(1), "judge": _none(found.group(2))}
    row["proposals"] = proposals
    return row


def disagrees(row: dict) -> bool:
    """Whether a label goes to a person.

    The judge decides: it reads item bodies, while the router only
    matches words and its rank-1 missed 319 of 628 judge-confirmed
    positives on the first full draft. A router-only mismatch is kept in
    ``proposals`` and reported as echo risk, not queued. A near-miss
    competitor only feeds the report breakdown, so it never queues.
    """
    judge = (row.get("proposals") or {}).get("judge")
    if row["type"] == "negative":
        return judge is not None
    return judge != row["target"]


def _write_labels(root: Path, rows: list[dict], meta: dict) -> dict:
    disagreements = sorted(r["id"] for r in rows if disagrees(r))
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
    for name, file_rows in sorted(by_file.items()):
        (labels_dir / f"{name}.yaml").write_text(
            yaml.safe_dump(
                {
                    "schema_version": 1,
                    "cases": sorted(file_rows, key=lambda r: r["id"]),
                },
                sort_keys=False,
                allow_unicode=True,
            )
        )
    queue = {"disagreements": disagreements, "audit_sample": audit, **meta}
    (root / "evals/activation/adjudicate.yaml").write_text(
        yaml.safe_dump(queue, sort_keys=False)
    )
    return queue


def _new_rows(root, session, items, all_cases) -> list[dict]:
    """Draft 2 plain prompts and 1 near-miss for each of ``items``."""
    budget, writer, router = session.budget, session.roles["writer"], session.router
    taken = {c.id for c in all_cases}
    plain = draft_plain(root, items, budget, writer)
    rows, plain_cases = [], []
    for target, prompts in sorted(plain.items()):
        for n, prompt in enumerate(prompts):
            cid = f"{_slug(target)}.p{n + 1}"
            while cid in taken:
                cid += "x"
            taken.add(cid)
            case = Case(
                id=cid, type="positive", prompt=prompt, target=target, cluster=target
            )
            plain_cases.append(case)
            rows.append(case.to_dict() | {"proposers": ["writer"]})
    neighbors = evaluate(router, [*all_cases, *plain_cases])["neighbors"]
    near = draft_near_misses(root, items, neighbors, budget, writer)
    for target, (prompt, neighbor) in sorted(near.items()):
        cid = f"{_slug(target)}.p3"
        while cid in taken:
            cid += "x"
        taken.add(cid)
        row = Case(
            id=cid,
            type="near_miss",
            prompt=prompt,
            target=target,
            competitor=neighbor,
            cluster=target,
            proposers=("writer",),
        ).to_dict()
        row["proposals"] = {"aimed_at": neighbor}
        rows.append(row)
    return rows


def _judge_rows(root, rows, router, by_id, ask) -> str | None:
    picks, stopped = judge_all(
        root, router, by_id, ask, [(r["prompt"], r["target"]) for r in rows]
    )
    for row, (pick, runner) in zip(rows, picks):
        apply_judgment(row, pick, runner, router)
    return stopped


def _session(root: Path, config: dict, call) -> SimpleNamespace:
    roles = pick_roles(config)
    budget = Budget(call, float(config["label_max_cost_usd"]))
    items = build_inventory(root)

    def ask_judge(prompt: str) -> str:  # one batch of prompts per call
        return budget(roles["judge"], prompt)

    return SimpleNamespace(
        roles=roles,
        budget=budget,
        items=items,
        by_id={i.id: i for i in items},
        router=Router(items),
        ask_judge=ask_judge,
    )


def draft(root: Path, config: dict, call=claude_call) -> dict:
    ses = _session(root, config, call)
    roles, budget = ses.roles, ses.budget
    rows = _new_rows(root, ses, ses.items, [])
    # A writer reply that does not parse yields no rows for its whole batch:
    # the first full draft lost 11 items that way. Redraft them once, then
    # record what is still short rather than leave it to the coverage gate.
    # One item per retry call, so an item whose reply never parses cannot
    # take its batch-mates down with it a second time.
    for item_id in _short_items(rows, ses.items):
        cases = [Case.from_dict(r) for r in rows]
        rows += _new_rows(root, ses, [ses.by_id[item_id]], cases)
    for n, (source, prompt) in enumerate(draft_negatives(budget, roles["writer"])):
        rows.append(
            Case(
                id=f"neg.{n + 1:03d}",
                type="negative",
                prompt=prompt,
                target=None,
                cluster=source,
                proposers=("writer",),
            ).to_dict()
        )
    stopped = _judge_rows(root, rows, ses.router, ses.by_id, ses.ask_judge)
    return _write_labels(
        root,
        rows,
        {
            "writer": roles["writer"],
            "judge": roles["judge"],
            "spent_usd": round(budget.spent, 4),
            "stopped": stopped,
            "failed_calls": budget.failures,
            "unfilled_items": _short_items(rows, ses.items),
        },
    )


def _short_items(rows: list[dict], items: list[Item]) -> list[str]:
    cases = [Case.from_dict(r) for r in rows]
    gaps = coverage_gaps(cases, items, min_negatives=0, min_sources=0)
    return sorted(gaps["items"])


def _load_rows(root: Path) -> list[dict]:
    rows = []
    for path in sorted((root / "evals/activation/labels").glob("*.yaml")):
        rows.extend((yaml.safe_load(path.read_text()) or {}).get("cases") or [])
    return rows


def requeue(root: Path) -> dict:
    """Rebuild adjudicate.yaml from the label files. Spends nothing."""
    rows = [backfill_proposals(r) for r in _load_rows(root)]
    previous = (
        yaml.safe_load((root / "evals/activation/adjudicate.yaml").read_text()) or {}
    )
    meta = {
        k: v for k, v in previous.items() if k not in ("disagreements", "audit_sample")
    }
    return _write_labels(root, rows, meta)


def repair(root: Path, config: dict, call=claude_call) -> dict:
    """Fill items short of coverage and re-judge rows whose target the
    judge never saw (outside the router's top 8). Adjudicated rows are
    left alone.
    """
    ses = _session(root, config, call)
    roles, budget, by_id, router = ses.roles, ses.budget, ses.by_id, ses.router
    rows = _load_rows(root)
    for row in rows:
        backfill_proposals(row)
    cases = [Case.from_dict(r) for r in rows]
    short = coverage_gaps(cases, ses.items, min_negatives=0, min_sources=0)["items"]
    fresh = _new_rows(root, ses, [by_id[i] for i in sorted(short)], cases)
    stale = [
        r
        for r in rows
        if r["type"] != "negative"
        and not r.get("adjudicated")
        and r["target"] not in [i for i, _ in router.rank(r["prompt"])[:SHORTLIST]]
    ]
    stopped = _judge_rows(root, fresh + stale, router, by_id, ses.ask_judge)
    previous = (
        yaml.safe_load((root / "evals/activation/adjudicate.yaml").read_text()) or {}
    )
    return _write_labels(
        root,
        rows + fresh,
        {
            "writer": roles["writer"],
            "judge": roles["judge"],
            "spent_usd": round(float(previous.get("spent_usd") or 0) + budget.spent, 4),
            "stopped": stopped,
            "failed_calls": budget.failures,
            "repaired": {"filled_items": sorted(short), "rejudged": len(stale)},
        },
    )


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
            write_resolved(config_path, config["resolved"])
            sys.stdout.write(json.dumps(config["resolved"], indent=1) + "\n")
        elif command == "draft":
            queue = draft(root, config)
            sys.stdout.write(
                f"drafted labels; {len(queue['disagreements'])} disagreements and "
                f"{len(queue['audit_sample'])} audit cases to adjudicate; "
                f"spent ${queue['spent_usd']:.2f}\n"
            )
        elif command == "repair":
            queue = repair(root, config)
            sys.stdout.write(
                f"repaired: filled {len(queue['repaired']['filled_items'])} items, re-judged "
                f"{queue['repaired']['rejudged']}; {len(queue['disagreements'])} disagreements "
                f"and {len(queue['audit_sample'])} audit cases; total spent ${queue['spent_usd']:.2f}\n"
            )
        elif command == "requeue":
            queue = requeue(root)
            sys.stdout.write(
                f"{len(queue['disagreements'])} disagreements and "
                f"{len(queue['audit_sample'])} audit cases queued\n"
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
