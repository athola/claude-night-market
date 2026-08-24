"""The night-shift handoff gate: no valid handoff, no run.

A work item may only execute unattended when four documents exist and
agree with each other. This module is the only place that judgment is
made, and it makes it without a model, because a rule a model can be
talked out of at 3am is not a rule.

The gate refuses more often than a person would. That is deliberate. A
refusal costs a one-line edit the evening before; a bad pass costs the
night.

Exit codes double as the state, worst news first:

===== ==============  ============================================
Code  State           Meaning
===== ==============  ============================================
0     ``READY``       every check passed
1     ``MISSING``     a required document is absent
2     ``MALFORMED``   frontmatter unparseable, or a required key or
                      schema version is wrong
3     ``UNSAFE``      the item asks for something no item may have
4     ``INCOHERENT``  the four documents contradict each other
===== ==============  ============================================
"""

from __future__ import annotations

import argparse
import json
import shlex
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import scope
import yaml

READY = 0
MISSING = 1
MALFORMED = 2
UNSAFE = 3
INCOHERENT = 4

_STATES = {
    READY: "READY",
    MISSING: "MISSING",
    MALFORMED: "MALFORMED",
    UNSAFE: "UNSAFE",
    INCOHERENT: "INCOHERENT",
}

#: Each required document, its schema tag, and the keys it must carry.
REQUIRED_DOCS = {
    "requirements.md": ("nightshift/requirements@1", ("item", "acceptance")),
    "design.md": ("nightshift/design@1", ("item", "risk", "traces")),
    "tasks.md": ("nightshift/tasks@1", ("item", "tasks")),
    "handoff.md": (
        "nightshift/handoff@1",
        (
            "item",
            "title",
            "base_branch",
            "branch",
            "scope",
            "commands",
            "budget",
            "implementer",
            "babysitter",
        ),
    ),
}

#: A diff larger than this needs a resolving spec reference. The number
#: is the repository's own surgical-edit threshold, not a new one.
DEFAULT_DIFF_CAP = 200

#: ``---``, the YAML block, then the body.
_FRONTMATTER_PARTS = 3

#: Substrings that bypass a quality gate or destroy work. A handoff
#: command containing any of these is refused outright, because an
#: unattended run is exactly when nobody is watching the bypass.
#: The two values ``evidence.expect`` may take. ``objective_check`` reads
#: the field as a binary, so a third spelling used to mean "check
#: nothing": a task written ``expect: Pass`` whose command exited 1
#: produced a proof row reading exit 1, expect Pass, verdict PASS.
_LEGAL_EXPECT = frozenset({"pass", "fail"})

FORBIDDEN_COMMAND_FRAGMENTS = (
    "--no-verify",
    # `git commit -n` is the short spelling of --no-verify and is named
    # alongside it in .claude/rules, but the list carried only the long
    # form, so the one an author is likelier to type went through.
    "commit -n",
    "push --force",
    "--force-with-lease",
    "push -f",
    "rm -rf",
    "SKIP=",
    "git reset --hard",
)

#: Characters that only mean something to a shell. The driver runs
#: commands as argv, so their presence is always an authoring error
#: and sometimes an injection attempt.
SHELL_METACHARACTERS = ("&", ";", "|", ">", "<", "`", "$(", "\n")


@dataclass(frozen=True)
class GateResult:
    """The verdict on one work item.

    ``code`` is checked at construction rather than when ``state`` is
    read. The property is reached from the CLI's JSON path, where an
    unrecognized code used to surface as a ``KeyError`` from inside a
    property: a traceback naming the lookup, at the point of
    formatting, rather than the caller that invented the code.
    """

    code: int
    problems: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Refuse a code no state name covers."""
        if self.code not in _STATES:
            raise ValueError(
                f"unknown gate code {self.code!r}; expected one of {sorted(_STATES)}"
            )

    @property
    def state(self) -> str:
        """Human-readable name of the verdict."""
        return _STATES[self.code]


def parse_frontmatter(text: str) -> dict[str, Any]:
    """Return the YAML frontmatter of a document.

    Raises ``ValueError`` when the document has no frontmatter block or
    the block is not a YAML mapping. The caller turns that into
    ``MALFORMED``; nothing here guesses at a partial document.
    """
    if not text.startswith("---"):
        raise ValueError("no frontmatter block")
    parts = text.split("---", 2)
    if len(parts) < _FRONTMATTER_PARTS:
        raise ValueError("unterminated frontmatter block")
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        raise ValueError(f"unparseable frontmatter: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("frontmatter is not a mapping")
    return data


def _load_documents(item_dir: Path) -> tuple[dict[str, Any], list[str], int]:
    """Load and structurally validate the four documents."""
    absent = [name for name in REQUIRED_DOCS if not (item_dir / name).is_file()]
    if absent:
        return {}, [f"{name} is absent" for name in sorted(absent)], MISSING

    docs: dict[str, Any] = {}
    problems: list[str] = []
    for name, (schema_tag, required_keys) in REQUIRED_DOCS.items():
        try:
            data = parse_frontmatter((item_dir / name).read_text())
        except ValueError as exc:
            problems.append(f"{name}: {exc}")
            continue
        if data.get("schema") != schema_tag:
            problems.append(
                f"{name}: schema is {data.get('schema')!r}, expected {schema_tag!r}"
            )
            continue
        for key in required_keys:
            if key not in data:
                problems.append(f"{name}: required key {key!r} is absent")
        docs[name] = data

    if problems:
        return docs, problems, MALFORMED

    item_ids = {name: doc["item"] for name, doc in docs.items()}
    expected = item_ids["handoff.md"]
    mismatched = [
        f"{name}: item is {value!r}, handoff.md says {expected!r}"
        for name, value in item_ids.items()
        if value != expected
    ]
    if mismatched:
        return docs, mismatched, MALFORMED

    return docs, [], READY


def _check_unsafe(docs: dict[str, Any]) -> list[str]:
    """Refuse anything no work item may ask for, whatever its author wrote."""
    handoff = docs["handoff.md"]
    problems: list[str] = []
    item_scope = handoff.get("scope") or {}
    allow_paths = item_scope.get("allow_paths") or []

    if not allow_paths:
        problems.append("scope.allow_paths is empty; an item must name its files")

    for path in allow_paths:
        if str(path).strip() in {".", "/", "./"}:
            problems.append(f"scope.allow_paths contains the repository root: {path!r}")
        elif scope.is_denied(str(path)):
            problems.append(
                f"scope.allow_paths names a denied path: {path!r}. "
                "The denylist is not overridable by a handoff."
            )

    cap = item_scope.get("max_diff_lines", DEFAULT_DIFF_CAP)
    if not _is_plain_int(cap):
        problems.append(
            f"scope.max_diff_lines is {cap!r}, which is not a number. A cap "
            "that cannot be read is not an absent cap."
        )
    elif cap > DEFAULT_DIFF_CAP and not item_scope.get("spec_ref"):
        problems.append(
            f"scope.max_diff_lines is {cap} (over {DEFAULT_DIFF_CAP}) with no "
            "scope.spec_ref to justify it"
        )

    max_tasks = (handoff.get("budget") or {}).get("max_tasks")
    if max_tasks is not None and not _is_plain_int(max_tasks):
        problems.append(
            f"budget.max_tasks is {max_tasks!r}, which is not a number. A "
            "budget that cannot be read is not an absent budget."
        )

    for task in docs["tasks.md"].get("tasks") or []:
        expect = (task.get("evidence") or {}).get("expect", "pass")
        if expect not in _LEGAL_EXPECT:
            problems.append(
                f"task {task.get('id')} declares evidence.expect={expect!r}; "
                f"the only legal values are {' and '.join(sorted(_LEGAL_EXPECT))}"
            )

    for label, command in _executable_commands(docs):
        problems += _check_command(label, command)
    return problems


def _is_plain_int(value: object) -> bool:
    """Return True for an int that is not a bool.

    The guards these replace were ``isinstance(x, int)``, which skips the
    check on anything else rather than rejecting it, while the driver
    reads the same fields through ``int(...)`` and accepts a string. Two
    quote characters therefore lifted the surgical-edit ceiling on an
    unattended run. ``bool`` is excluded because it is an int subclass:
    ``max_diff_lines: true`` passed an isinstance check and then made the
    downstream cap 1.
    """
    return isinstance(value, int) and not isinstance(value, bool)


def _executable_commands(docs: dict[str, Any]) -> list[tuple[str, str]]:
    """Every string the driver will execute, with a label for the message.

    One generator so the command gate cannot be applied to some of them.
    ``_check_command`` used to be reached from a single call site over
    ``handoff["commands"]`` while a task's ``evidence.command`` was
    checked for non-emptiness and then run by the driver as plain argv --
    which is all ``rm -rf``, ``git reset --hard`` and ``git push --force``
    need. The gate refused a string on one path and ran the identical
    string on the other.
    """
    handoff = docs["handoff.md"]
    commands = [
        (f"commands.{name}", str(command))
        for name, command in (handoff.get("commands") or {}).items()
    ]
    commands += [
        (f"task {task.get('id')} evidence.command", str(command))
        for task in docs["tasks.md"].get("tasks") or []
        if (command := (task.get("evidence") or {}).get("command"))
    ]
    return commands


def _check_command(name: str, command: str) -> list[str]:
    """Refuse a command the driver could not run safely as argv.

    Every handoff command is executed with ``subprocess`` in list form
    and no shell, so a metacharacter is not merely risky, it would not
    do what its author expected. Refusing here means the driver never
    has to judge a string at 3am.

    Use a tool's own directory flag rather than ``cd X &&``: for example
    ``uv run --directory plugins/conjure pytest -q``.
    """
    problems: list[str] = []
    # Normalized before matching. The fragments were tested against the
    # raw string, so ordinary spacing variants walked straight through:
    # `git  reset  --hard` with two spaces, and `git push  -f`, were both
    # allowed while their single-spaced forms were refused.
    normalized = " ".join(command.split())
    for fragment in FORBIDDEN_COMMAND_FRAGMENTS:
        if fragment in normalized:
            problems.append(
                f"{name} contains {fragment!r}, which bypasses a "
                "quality gate or destroys work"
            )

    found = [ch for ch in SHELL_METACHARACTERS if ch in command]
    if found:
        problems.append(
            f"{name} contains shell metacharacters {found}. Commands "
            "run as argv with no shell. Use a tool's own directory flag "
            "instead of 'cd X &&'."
        )
        return problems

    try:
        if not shlex.split(command):
            problems.append(f"{name} is empty")
    except ValueError as exc:
        problems.append(f"{name} is not a parseable shell word list: {exc}")
    return problems


def _find_cycle(tasks: Sequence[dict[str, Any]]) -> list[str]:
    """Return a dependency cycle as a list of task ids, or an empty list."""
    graph: dict[str, list[str]] = {
        str(t.get("id")): [str(d) for d in (t.get("depends_on") or [])] for t in tasks
    }
    visiting: set = set()
    done: set = set()
    trail: list[str] = []

    def walk(node: str) -> list[str]:
        if node in done:
            return []
        if node in visiting:
            return trail[trail.index(node) :] + [node]
        visiting.add(node)
        trail.append(node)
        for nxt in graph.get(node, []):
            if nxt in graph:
                found = walk(nxt)
                if found:
                    return found
        trail.pop()
        visiting.discard(node)
        done.add(node)
        return []

    for node in graph:
        found = walk(node)
        if found:
            return found
    return []


def _check_tasks(
    tasks: Sequence[dict[str, Any]], allow_paths: Sequence[str]
) -> list[str]:
    """Check each task against the allowlist and against its siblings."""
    problems: list[str] = []
    task_ids = {t.get("id") for t in tasks}

    for task in tasks:
        tid = task.get("id")
        for path in task.get("files") or []:
            if not any(scope.within(a, str(path)) for a in allow_paths if a):
                problems.append(
                    f"task {tid} touches {path!r}, which is outside scope.allow_paths"
                )
        if not (task.get("evidence") or {}).get("command"):
            problems.append(
                f"task {tid} has no evidence.command; nothing could prove it"
            )
        for dep in task.get("depends_on") or []:
            if dep not in task_ids:
                problems.append(f"task {tid} depends on unknown task {dep!r}")

    cycle = _find_cycle(tasks)
    if cycle:
        problems.append(f"dependency cycle among tasks: {' -> '.join(cycle)}")
    return problems


def _check_iron_law(tasks: Sequence[dict[str, Any]]) -> list[str]:
    """Require at least one check declared to fail before anything passes."""
    if any((t.get("evidence") or {}).get("expect") == "fail" for t in tasks):
        return []
    return [
        "no task declares 'expect: fail'; without a failing check first, a "
        "later green proves nothing"
    ]


def _check_traceability(
    acceptance: Sequence[dict[str, Any]],
    traces: dict[str, Any],
    task_ids: set,
) -> list[str]:
    """Require every acceptance criterion to reach a real task."""
    problems: list[str] = []
    for criterion in acceptance:
        acid = str(criterion.get("id"))
        traced = traces.get(acid) or []
        if not traced:
            problems.append(f"acceptance criterion {acid} is traced to no task")
            continue
        unknown = [t for t in traced if t not in task_ids]
        if unknown:
            problems.append(
                f"acceptance criterion {acid} traces to unknown tasks: {unknown}"
            )
    return problems


def _check_incoherent(docs: dict[str, Any]) -> list[str]:
    """Check the four documents against each other."""
    handoff = docs["handoff.md"]
    tasks = docs["tasks.md"].get("tasks") or []
    allow_paths = (handoff.get("scope") or {}).get("allow_paths") or []

    problems: list[str] = []
    # Annotated because it comes from parsed YAML: the value is whatever
    # the author wrote, and _is_plain_int is what decides it is readable.
    max_tasks: Any = (handoff.get("budget") or {}).get("max_tasks")
    if _is_plain_int(max_tasks) and len(tasks) > max_tasks:
        problems.append(
            f"tasks.md declares {len(tasks)} tasks, over budget.max_tasks={max_tasks}"
        )

    problems += _check_tasks(tasks, allow_paths)
    problems += _check_iron_law(tasks)
    problems += _check_traceability(
        docs["requirements.md"].get("acceptance") or [],
        docs["design.md"].get("traces") or {},
        {t.get("id") for t in tasks},
    )
    return problems


def check_item(item_dir: Path) -> GateResult:
    """Judge one work-item directory.

    Checks run worst-news-first and stop at the first failing tier, so a
    reader fixes the structural problem before the semantic one that may
    only exist because of it.
    """
    docs, problems, code = _load_documents(Path(item_dir))
    if code != READY:
        return GateResult(code=code, problems=tuple(problems))

    unsafe = _check_unsafe(docs)
    if unsafe:
        return GateResult(code=UNSAFE, problems=tuple(unsafe))

    incoherent = _check_incoherent(docs)
    if incoherent:
        return GateResult(code=INCOHERENT, problems=tuple(incoherent))

    return GateResult(code=READY)


def main(argv: Sequence[str] | None = None) -> int:
    """Check one item directory and report the verdict."""
    parser = argparse.ArgumentParser(description="Night-shift handoff gate")
    parser.add_argument("--item-dir", required=True, help="Path to the item directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args(argv)

    result = check_item(Path(args.item_dir))
    if args.json:
        print(
            json.dumps(
                {
                    "state": result.state,
                    "code": result.code,
                    "problems": list(result.problems),
                },
                indent=2,
            )
        )
    else:
        print(f"{result.state} ({result.code})")
        for problem in result.problems:
            print(f"  - {problem}")
    return result.code


if __name__ == "__main__":
    raise SystemExit(main())
