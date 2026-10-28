"""The night-shift handoff gate: the rule that no valid handoff, no run.

A work item may only execute unattended when four documents exist and
agree with each other. This module is the only place that judgment is
made, and it makes it without a model, because a rule a model can be
talked out of at 3am is not a rule.

``night_run.main`` calls ``check_item`` before it walks anything and
reads the admitted documents back through ``load_item``, so the rule
above is the rule that guards a run.

The gate refuses more often than a person would. That is deliberate. A
refusal costs a one-line edit the evening before; a bad pass costs the
night.

Exit codes double as the state, worst news first:

===== ==============  ============================================
Code  State           Meaning
===== ==============  ============================================
0     ``READY``       every check passed
1     ``MISSING``     a required document is absent
2     ``MALFORMED``   frontmatter unparseable, or a required key,
                      document key type or schema version is wrong
3     ``UNSAFE``      the item asks for something no item may have
4     ``INCOHERENT``  the four documents contradict each other
===== ==============  ============================================
"""

from __future__ import annotations

import argparse
import json
import shlex
from collections.abc import Callable, Mapping, Sequence
from dataclasses import MISSING as NO_DEFAULT
from dataclasses import dataclass, fields
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


@dataclass(frozen=True)
class Handoff:
    """The handoff document, parsed once at the boundary the runner reads.

    The runner reads typed fields rather than the raw mapping, so an
    absent ``branch`` is refused here instead of reaching
    ``git worktree add -b`` as the string ``"None"``. Every field without
    a default is required, and ``REQUIRED_DOCS`` takes its handoff keys
    from here so the gate and the runner cannot disagree about what
    "required" means.
    """

    item: str
    title: str
    base_branch: str
    branch: str
    scope: Mapping[str, Any]
    commands: Mapping[str, Any]
    budget: Mapping[str, Any]
    implementer: Mapping[str, Any]
    babysitter: Mapping[str, Any]
    worktree: str | None = None

    @classmethod
    def from_frontmatter(cls, data: Mapping[str, Any]) -> Handoff:
        """Build from parsed frontmatter, naming the first bad key."""
        values: dict[str, Any] = {}
        for spec in fields(cls):
            if spec.name not in data:
                if spec.default is NO_DEFAULT:
                    raise ValueError(
                        f"handoff.md: required key {spec.name!r} is absent"
                    )
                continue
            value = data[spec.name]
            expected = dict if spec.name in _HANDOFF_SECTIONS else str
            optional = spec.default is not NO_DEFAULT and value is None
            if not optional and not isinstance(value, expected):
                raise ValueError(
                    f"handoff.md: {spec.name!r} must be a {expected.__name__}, "
                    f"got {type(value).__name__}"
                )
            values[spec.name] = value
        return cls(**values)


#: Handoff keys holding a nested mapping rather than a single string.
_HANDOFF_SECTIONS = frozenset(
    {"scope", "commands", "budget", "implementer", "babysitter"}
)

#: The handoff keys the gate refuses to admit an item without.
HANDOFF_REQUIRED_KEYS = tuple(
    spec.name for spec in fields(Handoff) if spec.default is NO_DEFAULT
)

#: Each required document, its schema tag, and the keys it must carry.
REQUIRED_DOCS = {
    "requirements.md": ("nightshift/requirements@1", ("item", "acceptance")),
    "design.md": ("nightshift/design@1", ("item", "risk", "traces")),
    "tasks.md": ("nightshift/tasks@1", ("item", "tasks")),
    "handoff.md": ("nightshift/handoff@1", HANDOFF_REQUIRED_KEYS),
}

#: A diff larger than this needs a resolving spec reference. The number
#: is the repository's own surgical-edit threshold, not a new one.
DEFAULT_DIFF_CAP = 200

#: ``---``, the YAML block, then the body.
_FRONTMATTER_PARTS = 3

#: The two values ``evidence.expect`` may take. ``objective_check`` reads
#: the field as a binary, so the gate admits no third spelling: a task
#: written ``expect: Pass`` whose command exited 1 would otherwise produce
#: a proof row reading exit 1, expect Pass, verdict PASS.
_LEGAL_EXPECT = frozenset({"pass", "fail"})

#: Git options that come before the subcommand and take the next word as
#: their value, so the subcommand is found by skipping both.
_GIT_GLOBAL_OPTIONS_WITH_VALUE = frozenset(
    {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env"}
)

#: ``git -c`` keys that change what a later word means: an alias renames
#: a forbidden subcommand, and ``core.hooksPath`` disables the hooks.
_GIT_CONFIG_BYPASS_KEYS = ("alias.", "core.hookspath")

#: ``git commit`` short options that consume the rest of their bundle as
#: a value, so ``-mn`` is the message "n" and not ``--no-verify``.
_COMMIT_VALUE_SHORTS = "mFCctu"

#: Characters that only mean something to a shell. The driver runs
#: commands as argv, so their presence is always an authoring error
#: and sometimes an injection attempt.
SHELL_METACHARACTERS = ("&", ";", "|", ">", "<", "`", "$(", "\n")

#: Budget fields the driver reads through ``int()``. Zero is refused too:
#: ``claude_token_ceiling: 0`` reads as "no ceiling" downstream, the
#: opposite of what its author meant.
_BUDGET_NUMBERS = (
    "max_tasks",
    "max_attempts_per_task",
    "implementer_timeout_s",
    "claude_token_ceiling",
)

#: Shells that run a string passed with ``-c``, bundled or not.
_SHELLS = frozenset({"sh", "bash", "zsh", "dash", "ksh", "fish"})

#: The flag that hands each interpreter its code as a string.
_CODE_FLAGS = {"node": "-e", "perl": "-e", "ruby": "-e"}


@dataclass(frozen=True)
class GateResult:
    """The verdict on one work item.

    ``code`` is checked at construction rather than when ``state`` is
    read, so an unrecognized code raises in the caller that invented it.
    The property is reached from the CLI's JSON path, where a lookup
    failure would name the formatting step instead.
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
        missing = [key for key in required_keys if key not in data]
        problems += [f"{name}: required key {key!r} is absent" for key in missing]
        if name == "handoff.md" and not missing:
            try:
                Handoff.from_frontmatter(data)
            except ValueError as exc:
                problems.append(str(exc))
        elif not missing:
            problems += _shape_problems(name, data)
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


def _shape_problems(name: str, data: Mapping[str, Any]) -> list[str]:
    """Check a planning document holds the shapes the later checks read.

    Those checks read every entry through ``.get``, so a scalar where a
    mapping belongs would raise out of ``check_item`` rather than refuse
    the item. An empty list is refused as well: an item with no
    acceptance criterion or no task has nothing to prove.
    """
    if name == "design.md":
        traces = data["traces"]
        if isinstance(traces, dict) and all(
            isinstance(ids, list) and all(isinstance(i, str) for i in ids)
            for ids in traces.values()
        ):
            return []
        return [f"{name}: 'traces' must map each criterion id to a list of task ids"]

    key = "acceptance" if name == "requirements.md" else "tasks"
    entries = data[key]
    if not (
        isinstance(entries, list)
        and entries
        and all(isinstance(entry, dict) for entry in entries)
    ):
        return [f"{name}: {key!r} must be a non-empty list of mappings"]
    if key == "tasks":
        untyped = [e.get("id") for e in entries if not isinstance(e.get("id"), str)]
        if untyped:
            return [f"{name}: every task id must be a string, got {untyped!r}"]
    return [
        f"{name}: task {entry.get('id')} 'evidence' must be a mapping"
        for entry in entries
        if not isinstance(entry.get("evidence") or {}, dict)
    ]


def _check_unsafe(docs: dict[str, Any]) -> list[str]:
    """Refuse anything no work item may ask for, whatever its author wrote."""
    handoff = docs["handoff.md"]
    problems: list[str] = []
    item_scope = handoff.get("scope") or {}
    allow_paths = item_scope.get("allow_paths") or []

    if not allow_paths:
        problems.append("scope.allow_paths is empty; an item must name its files")
    elif not (
        isinstance(allow_paths, list) and all(isinstance(p, str) for p in allow_paths)
    ):
        problems.append(
            f"scope.allow_paths must be a list of paths, got {allow_paths!r}"
        )
        allow_paths = []

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

    budget = handoff.get("budget") or {}
    for key in _BUDGET_NUMBERS:
        number = budget.get(key)
        if number is not None and not (_is_plain_int(number) and number > 0):
            problems.append(
                f"budget.{key} is {number!r}, which is not a positive number. "
                "A budget that cannot be read is not an absent budget."
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

    A numeric field that fails this is refused, not skipped: the driver
    reads the same fields through ``int(...)``, which accepts a string,
    so a quoted cap would otherwise lift the surgical-edit ceiling on an
    unattended run. ``bool`` is excluded because it is an int subclass,
    and ``max_diff_lines: true`` would make the downstream cap 1.
    """
    return isinstance(value, int) and not isinstance(value, bool)


def _executable_commands(docs: dict[str, Any]) -> list[tuple[str, str]]:
    """Every string the driver will execute, with a label for the message.

    One generator so the command gate cannot be applied to some of them:
    ``handoff["commands"]`` and every task's ``evidence.command`` both
    reach the driver as argv, so a string refused on one path must be
    refused on the other.
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
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        return [f"{name} is not a parseable shell word list: {exc}"]

    problems = [
        f"{name} contains {offender!r}, which bypasses a quality gate or destroys work"
        for offender in _command_bypasses(argv)
    ]
    interpreter = _inline_code(argv)
    if interpreter:
        problems.append(
            f"{name} runs code given as a string ({interpreter!r}), which the "
            "bypass checks cannot read. Put the code in a script and run that."
        )
    found = [ch for ch in SHELL_METACHARACTERS if ch in command]
    if found:
        problems.append(
            f"{name} contains shell metacharacters {found}. Commands "
            "run as argv with no shell. Use a tool's own directory flag "
            "instead of 'cd X &&'."
        )
    elif not argv:
        problems.append(f"{name} is empty")
    return problems


def _inline_code(argv: Sequence[str]) -> str | None:
    """Return the interpreter in ``argv`` that is handed code as a string.

    ``sh -c "git push --force"`` is one word to ``_command_bypasses``, so
    whatever the string says is never judged. Only options before the
    first operand count: ``python -m pytest -c pytest.ini`` passes ``-c``
    to pytest, not to python.
    """
    for index, word in enumerate(argv):
        tool = word.rsplit("/", 1)[-1]
        options = []
        for option in argv[index + 1 :]:
            if not option.startswith("-"):
                break
            options.append(option)
        if tool == "env" and any(
            o == "-S" or o.startswith("--split-string") for o in options
        ):
            return word
        if tool in _SHELLS and any(
            not o.startswith("--") and "c" in o[1:] for o in options
        ):
            return word
        flag = "-c" if tool.startswith("python") else _CODE_FLAGS.get(tool)
        if flag and any(o.startswith(flag) for o in options):
            return word
    return None


def _command_bypasses(argv: Sequence[str]) -> list[str]:
    """Return what in ``argv`` bypasses a quality gate or destroys work.

    Judged on words, not text, so flag order, spacing and short-option
    bundling cannot change the answer. ``git`` and ``rm`` are looked for
    at every position because wrappers (``uv run``, ``env``) put them
    anywhere. An unattended run is exactly when nobody is watching the
    bypass, so an ambiguous word is refused rather than admitted.
    """
    found = [
        word
        for word in argv
        if word.startswith("SKIP=") or word.split("=", 1)[0] == "--no-verify"
    ]
    for index, word in enumerate(argv):
        tool = word.rsplit("/", 1)[-1]
        if tool == "git":
            found += _git_bypasses(argv[index + 1 :])
        elif tool == "rm":
            found += _rm_bypasses(argv[index + 1 :])
    return list(dict.fromkeys(found))


def _long_option(word: str, option: str) -> bool:
    """Match ``option`` or an abbreviation of it.

    git and GNU getopt both accept an unambiguous prefix of a long
    option, so ``--forc`` is ``--force``. An ambiguous prefix matches
    too, which only refuses a command git would reject anyway.
    """
    name = word.split("=", 1)[0]
    return len(name) > len("--") and name.startswith("--") and option.startswith(name)


def _git_bypasses(args: Sequence[str]) -> list[str]:
    """Judge one git invocation, given the words after ``git``."""
    found: list[str] = []
    index = 0
    while index < len(args) and args[index].startswith("-"):
        option, _, attached = args[index].partition("=")
        takes_value = option in _GIT_GLOBAL_OPTIONS_WITH_VALUE and not attached
        value = attached
        if takes_value and index + 1 < len(args):
            value = args[index + 1]
        if option in {"-c", "--config-env"} and value.lower().startswith(
            _GIT_CONFIG_BYPASS_KEYS
        ):
            found.append(f"{option} {value}")
        index += 2 if takes_value else 1
    if index >= len(args):
        return found

    subcommand, rest = args[index], args[index + 1 :]
    judge = _GIT_SUBCOMMAND_BYPASSES.get(subcommand)
    return found + judge(rest) if judge else found


def _short_letters(word: str, value_letters: str = "") -> str:
    """Return the letters of a short-option bundle, or "" for any other word.

    Reading stops at the first letter in ``value_letters``, because that
    option takes the rest of the bundle as its value.
    """
    if not word.startswith("-") or word.startswith("--"):
        return ""
    letters = word[1:]
    for index, letter in enumerate(letters):
        if letter in value_letters:
            return letters[: index + 1]
    return letters


def _push_bypasses(args: Sequence[str]) -> list[str]:
    """Force or delete in any spelling, including ``+ref`` and ``:ref``."""
    long_forms = (
        "--force",
        "--force-with-lease",
        "--no-verify",
        "--mirror",
        "--delete",
        "--prune",
    )
    return [
        word
        for word in args
        if set(_short_letters(word, "o")) & {"f", "d"}
        or any(_long_option(word, option) for option in long_forms)
        or word.startswith(("+", ":"))
    ]


def _commit_bypasses(args: Sequence[str]) -> list[str]:
    """``--no-verify`` in any spelling, including ``n`` in a short bundle."""
    found: list[str] = []
    for word in args:
        if word == "--":
            break
        if _long_option(word, "--no-verify") or "n" in _short_letters(
            word, _COMMIT_VALUE_SHORTS
        ):
            found.append(word)
    return found


def _reset_bypasses(args: Sequence[str]) -> list[str]:
    """``--hard`` discards the worktree."""
    return [word for word in args if _long_option(word, "--hard")]


def _clean_bypasses(args: Sequence[str]) -> list[str]:
    """Any forced clean deletes untracked files; ``-n`` alone is a dry run."""
    return [
        word
        for word in args
        if "f" in _short_letters(word, "e") or _long_option(word, "--force")
    ]


def _checkout_bypasses(args: Sequence[str]) -> list[str]:
    """Refuse ``--`` pathspecs, ``.``, force, or ``-B``: each overwrites work."""
    found: list[str] = []
    for index, word in enumerate(args):
        if word == "--":
            found += [f"-- {path}" for path in args[index + 1 :]]
            break
        if (
            word == "."
            or any(letter in _short_letters(word, "bB") for letter in "fB")
            or _long_option(word, "--force")
        ):
            found.append(word)
    return found


def _restore_bypasses(args: Sequence[str]) -> list[str]:
    """Refuse any restore that writes the worktree rather than only the index."""
    staged = worktree = False
    for word in args:
        if word == "--":
            break
        letters = _short_letters(word, "s")
        staged = staged or "S" in letters or _long_option(word, "--staged")
        worktree = worktree or "W" in letters or _long_option(word, "--worktree")
    if staged and not worktree:
        return []
    return ["restore " + " ".join(args)]


def _stash_bypasses(args: Sequence[str]) -> list[str]:
    """``drop`` and ``clear`` delete stashed work."""
    if args and args[0] in {"drop", "clear"}:
        return [f"stash {args[0]}"]
    return []


def _branch_bypasses(args: Sequence[str]) -> list[str]:
    """Refuse deleting an unmerged branch, or renaming or copying over one.

    ``-D`` is ``-d --force``; ``-M`` and ``-C`` are ``-m``/``-c`` with
    ``--force``, which replace an existing branch of the target name.
    """
    letters = "".join(_short_letters(word) for word in args)
    force = "f" in letters or any(_long_option(w, "--force") for w in args)
    overwrites = any(
        letter in letters or any(_long_option(w, long) for w in args)
        for letter, long in (("d", "--delete"), ("m", "--move"), ("c", "--copy"))
    )
    if any(letter in letters for letter in "DMC") or (overwrites and force):
        return ["branch " + " ".join(w for w in args if w.startswith("-"))]
    return []


#: The judge for each git subcommand that can bypass a gate or lose work.
_GIT_SUBCOMMAND_BYPASSES: dict[str, Callable[[Sequence[str]], list[str]]] = {
    "push": _push_bypasses,
    "commit": _commit_bypasses,
    "reset": _reset_bypasses,
    "clean": _clean_bypasses,
    "checkout": _checkout_bypasses,
    "restore": _restore_bypasses,
    "stash": _stash_bypasses,
    "branch": _branch_bypasses,
}


def _rm_bypasses(args: Sequence[str]) -> list[str]:
    """Recursive plus force, however the two flags are split or combined."""
    flags: set[str] = set()
    for word in args:
        if word == "--":
            break
        if _long_option(word, "--recursive"):
            flags.add("r")
        elif _long_option(word, "--force"):
            flags.add("f")
        elif word.startswith("-") and not word.startswith("--"):
            flags.update(word[1:].replace("R", "r"))
    if {"r", "f"} <= flags:
        return ["rm " + " ".join(w for w in args if w.startswith("-"))]
    return []


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
        evidence = task.get("evidence") or {}
        if not evidence.get("command"):
            problems.append(
                f"task {tid} has no evidence.command; nothing could prove it"
            )
        # pytest exits 4 on a usage error and 5 on no tests collected, so
        # a nonzero exit alone does not show the guard went red.
        if evidence.get("expect") == "fail" and not evidence.get("match"):
            problems.append(
                f"task {tid} declares expect: fail with no evidence.match; "
                "a nonzero exit alone includes a check that never ran"
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


def load_item(item_dir: Path) -> tuple[Handoff, list[dict[str, Any]]]:
    """Return the handoff and task list of an item the gate admits.

    Callers run ``check_item`` first. A directory the structural checks
    refuse raises, so a runner cannot walk half a handoff by accident.
    """
    docs, problems, code = _load_documents(Path(item_dir))
    if code != READY:
        raise ValueError("; ".join(problems))
    handoff = Handoff.from_frontmatter(docs["handoff.md"])
    return handoff, list(docs["tasks.md"].get("tasks") or [])


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
