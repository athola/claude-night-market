"""The night-run driver: one task at a time, evidence before advancing.

This is the deterministic half of the harness. It is Python rather than
a ``Workflow`` script for two reasons, both checked against the harness
contract rather than assumed:

- A ``Workflow`` script has no filesystem or subprocess access, so it
  could not run a test suite or read a diff. Ground truth would have to
  come from an agent's report, which is the thing this design exists to
  avoid.
- A ``Workflow`` run does not outlive its session. The documentation is
  explicit that exiting Claude Code starts the next run fresh. A night
  is longer than a session is guaranteed to be.

A plain process, in contrast, is something a watchdog can restart.

The order of operations is the contract:

1. Dispatch the implementer off-plan, through conjure's delegation
   executor. Its output goes to a log and is read by nothing.
2. Read the changed file list, and revert anything out of scope
   **before** any judge is invoked. A judge that never sees the
   violation cannot be argued into permitting it.
3. Run the task's own evidence command and keep the exit code and the
   raw output.
4. Ask the babysitter for a verdict, showing it only the diff and the
   captured output.
5. Reconcile: the deterministic reading may tighten the babysitter's
   verdict but never loosen it. See ``scripts/verdict.py``.

Every command runs as argv with no shell. The gate refuses any handoff
command containing a shell metacharacter, so by the time the driver sees
one it is already a plain word list.
"""

from __future__ import annotations

import re
import shlex
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:  # pragma: no cover
    from budget import Budget

import budget as budget_mod
import verdict as verdict_mod
import window as window_mod

#: Marker the delegation executor emits when no provider answered.
PROVIDERS_EXHAUSTED = "providers_exhausted"

#: Repository-relative path to conjure's delegation entry point.
CONJURE_EXECUTOR = "plugins/conjure/scripts/delegation_executor.py"

#: Exit code used when a command exceeds its timeout, matching the
#: convention `timeout(1)` uses so logs read consistently.
TIMEOUT_EXIT = 124

#: `git diff --numstat` emits added and removed counts before the path.
_NUMSTAT_COUNT_FIELDS = 2


@dataclass
class Completed:
    """The result of one command."""

    returncode: int
    output: str = ""


class Runner(Protocol):
    """Anything that can run a command and report what happened."""

    def run(self, command: str, cwd: Path | None = None, timeout: int = 0) -> Completed:
        """Run ``command`` and return its exit code and combined output."""
        ...


class SubprocessRunner:
    """The real runner.

    Splits the command into argv and runs it without a shell, so a
    metacharacter that slipped past the gate would fail loudly as a
    literal argument rather than quietly executing. Stderr is merged into
    stdout because a crash is evidence too, and a filter that only reads
    stdout is silent on exactly the runs worth waking up for.
    """

    def run(self, command: str, cwd: Path | None = None, timeout: int = 0) -> Completed:
        """Run ``command`` as argv and capture everything it printed."""
        argv = shlex.split(command)
        if not argv:
            return Completed(returncode=1, output="empty command")
        try:
            proc = subprocess.run(
                argv,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout or None,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return Completed(
                returncode=TIMEOUT_EXIT, output=f"timed out after {timeout}s"
            )
        except OSError as exc:
            return Completed(returncode=127, output=f"could not run {argv[0]!r}: {exc}")
        return Completed(returncode=proc.returncode, output=proc.stdout + proc.stderr)


#: A babysitter takes the captured facts and answers with
#: ``(verdict, reason, next_instruction)``.
Babysitter = Callable[..., "tuple[str, str, str]"]


@dataclass
class TaskResult:
    """Everything the morning review needs about one task."""

    task_id: str
    verdict: str
    reason: str
    attempts: int = 0
    dissent: bool = False
    ledger: list[dict[str, Any]] = field(default_factory=list)


def _diff_line_count(runner: Runner, workdir: Path) -> int:
    """Count added and removed lines in the working tree."""
    result = runner.run("git diff --numstat", cwd=workdir)
    total = 0
    for line in result.output.splitlines():
        parts = line.split()
        if len(parts) >= _NUMSTAT_COUNT_FIELDS:
            total += int(parts[0]) if parts[0].isdigit() else 0
            total += int(parts[1]) if parts[1].isdigit() else 0
    return total


def _changed_files(runner: Runner, workdir: Path) -> list[str]:
    """List the tracked files the implementer modified."""
    result = runner.run("git diff --name-only", cwd=workdir)
    return [line.strip() for line in result.output.splitlines() if line.strip()]


def _touched_files(runner: Runner, workdir: Path) -> list[str]:
    """Every path the implementer wrote, created ones included.

    ``git diff --name-only`` lists tracked modifications only, so an
    implementer that creates a file produced an empty list and the scope
    fence was handed nothing to judge. The denylist's own headline entry
    is ``.github/**``, named as a path where an unattended overnight edit
    changes the rules the harness runs under -- and creating a workflow
    file is precisely that, so the case the fence exists for was the case
    it could not see.
    """
    return _changed_files(runner, workdir) + _untracked(runner, workdir)


def _dispatch_implementer(
    runner: Runner,
    handoff: Mapping[str, Any],
    task: Mapping[str, Any],
    workdir: Path,
    steer: str,
) -> Completed:
    """Hand the task to a non-Anthropic provider and log whatever it says."""
    provider = (handoff.get("implementer") or {}).get("provider", "auto")
    timeout = int((handoff.get("budget") or {}).get("implementer_timeout_s", 900))
    files = [str(f) for f in task.get("files") or []]
    prompt = (
        f"Task {task.get('id')}: {task.get('title')}.\n"
        f"Change: {task.get('change')}\n"
        f"Touch only these files: {', '.join(files)}.\n"
        f"{steer}"
    )
    argv = [
        "python3",
        CONJURE_EXECUTOR,
        provider,
        prompt,
        "--timeout",
        str(timeout),
    ]
    if files:
        argv += ["--files", *files]
    return runner.run(shlex.join(argv), cwd=workdir, timeout=timeout)


def _record(
    result: TaskResult,
    attempt: int,
    evidence: Mapping[str, Any],
    observed: Completed,
    final: verdict_mod.Verdict,
) -> None:
    """Append one row to the proof ledger. Only this function writes it."""
    result.ledger.append(
        {
            "task": result.task_id,
            "attempt": attempt,
            "command": evidence.get("command", ""),
            "exit": observed.returncode,
            "expect": evidence.get("expect", "pass"),
            "output": observed.output,
            "verdict": final.verdict,
        }
    )
    result.verdict = final.verdict
    result.reason = final.reason
    result.dissent = final.dissent


def run_task(
    task: Mapping[str, Any],
    handoff: Mapping[str, Any],
    workdir: Path,
    runner: Runner,
    *,
    babysitter: Babysitter,
    budget: Budget | None = None,
) -> TaskResult:
    """Drive one task to a verdict, retrying up to the item's budget.

    ``budget`` is egregore's own :class:`budget.Budget`. When it is in
    cooldown the task stops before anything is dispatched, so the night
    shift respects the same rate-limit window ``watchdog.sh`` reads. A
    second cooldown file would be a second source of truth.
    """
    limits = handoff.get("budget") or {}
    item_scope = handoff.get("scope") or {}
    max_attempts = int(limits.get("max_attempts_per_task", 3))
    allow_paths: Sequence[str] = item_scope.get("allow_paths") or []
    cap = int(item_scope.get("max_diff_lines", 200))
    evidence = task.get("evidence") or {}
    allow_fallback = bool(
        (handoff.get("implementer") or {}).get("allow_on_plan_fallback", False)
    )

    result = TaskResult(task_id=str(task.get("id")), verdict="FAIL", reason="")
    steer = ""

    if budget is not None and budget_mod.is_in_cooldown(budget):
        result.verdict = "BLOCKED"
        result.reason = (
            f"cooldown active until {budget.cooldown_until}; the night shift "
            "waits out the same rate-limit window the watchdog reads"
        )
        return result

    for attempt in range(1, max_attempts + 1):
        result.attempts = attempt

        dispatched = _dispatch_implementer(runner, handoff, task, workdir, steer)
        if PROVIDERS_EXHAUSTED in dispatched.output and not allow_fallback:
            result.verdict = "BLOCKED"
            result.reason = (
                f"{PROVIDERS_EXHAUSTED}: no delegation provider answered, and this "
                "item does not set implementer.allow_on_plan_fallback"
            )
            return result

        scope_result = verdict_mod.check_scope(
            allow_paths, _touched_files(runner, workdir)
        )
        if not scope_result.ok:
            offenders = scope_result.violating
            unreverted = _revert_offenders(runner, workdir, offenders)
            if unreverted:
                steer = (
                    "Your last attempt edited files outside the task's scope "
                    f"({', '.join(offenders)}). Reverting "
                    f"{', '.join(unreverted)} failed, so those edits are still "
                    "in the tree. Touch only the files the task names."
                )
                result.verdict = "BLOCKED"
                result.reason = (
                    f"out of scope ({scope_result.reason}): {offenders}; "
                    f"{unreverted} could not be reverted"
                )
                return result
            steer = (
                "Your last attempt edited files outside the task's scope "
                f"({', '.join(offenders)}). Those edits were reverted. Touch "
                "only the files the task names."
            )
            result.verdict = "FAIL"
            result.reason = f"out of scope ({scope_result.reason}): {offenders}"
            continue

        observed = runner.run(str(evidence.get("command", "")), cwd=workdir)
        _raise_if_usage_limited(observed)
        objective = verdict_mod.objective_check(
            evidence,
            exit_code=observed.returncode,
            output=observed.output,
            diff_lines=_diff_line_count(runner, workdir),
            cap=cap,
            implementer_output=dispatched.output,
        )

        if objective.blocking:
            final = verdict_mod.reconcile("BLOCKED", objective)
        else:
            sitter_verdict, sitter_reason, next_instruction = babysitter(
                task=task,
                diff=runner.run("git diff --unified=0", cwd=workdir).output,
                test_output=observed.output,
                test_exit=observed.returncode,
            )
            final = verdict_mod.reconcile(sitter_verdict, objective, sitter_reason)
            steer = next_instruction or steer

        _record(result, attempt, evidence, observed, final)
        if final.verdict in {"PASS", "BLOCKED"}:
            return result

    return result


def render_proof(result: TaskResult) -> str:
    """Render the proof ledger as the table a morning review reads."""
    header = (
        "| Task | Attempt | Evidence command | Exit | Expect | Verdict |\n"
        "|------|---------|------------------|------|--------|---------|\n"
    )
    rows = "".join(
        f"| {row['task']} | {row['attempt']} | `{row['command']}` | "
        f"{row['exit']} | {row['expect']} | {row['verdict']} |\n"
        for row in result.ledger
    )
    return header + rows


#: Rough characters-per-token divisor used to estimate on-plan spend.
#: This is an estimate, not a measurement. It exists so the ceiling trips
#: on the right order of magnitude. When the real babysitter reports usage
#: from ``claude --output-format json``, prefer that number over this.
CHARS_PER_TOKEN = 4


#: Characters of the discarded diff kept in the proof. The same bound
#: the babysitter uses: enough to see what was attempted, not enough to
#: turn a ledger into a dump.
DISCARD_DIFF_CHARS = 4000


@dataclass
class Discarded:
    """What the working tree held when the item parked.

    ``files`` were reverted. ``untracked`` were left where they are: a
    blind ``git clean -fd`` would take the setup artifacts with them and
    make the resume pay for setup a second time.
    """

    files: list[str] = field(default_factory=list)
    untracked: list[str] = field(default_factory=list)
    diff: str = ""


@dataclass
class ItemResult:
    """The outcome of walking one work item to a stopping point."""

    item: str
    status: str
    reason: str = ""
    committed: list[str] = field(default_factory=list)
    tasks: list[TaskResult] = field(default_factory=list)
    full_suite: dict[str, Any] | None = None
    estimated_tokens: int = 0
    discarded: Discarded | None = None


def estimate_tokens(text: str) -> int:
    """Estimate the on-plan tokens a string costs. See ``CHARS_PER_TOKEN``."""
    return max(1, len(text) // CHARS_PER_TOKEN)


def topo_sort(tasks: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """Order tasks so every dependency precedes its dependents.

    Ties keep declared order, so a reader of ``tasks.md`` sees the same
    sequence the night ran. A cycle raises rather than picking an order:
    the gate is supposed to have caught it, and a walker that quietly
    guessed would hide the gate being wrong.
    """
    by_id = {str(t.get("id")): t for t in tasks}
    ordered: list[Mapping[str, Any]] = []
    placed: set[str] = set()
    remaining = [str(t.get("id")) for t in tasks]

    while remaining:
        ready = [
            tid
            for tid in remaining
            if all(
                dep not in by_id or dep in placed
                for dep in by_id[tid].get("depends_on") or []
            )
        ]
        if not ready:
            raise ValueError(f"dependency cycle among tasks: {sorted(remaining)}")
        for tid in ready:
            ordered.append(by_id[tid])
            placed.add(tid)
            remaining.remove(tid)
    return ordered


def _headers_in(text: str) -> dict[str, str]:
    """Pull any rate-limit headers the CLI echoed into its error output.

    The CLI does not expose response headers as data, so the only place
    they appear is the error text it prints. Reading them there is a
    scrape, and it degrades to an empty mapping rather than a wrong
    answer when the format changes.
    """
    found: dict[str, str] = {}
    for name in (*window_mod.RESET_HEADERS, "retry-after"):
        match = re.search(rf"{re.escape(name)}\s*[:=]\s*(\S+)", text, re.IGNORECASE)
        if match:
            found[name] = match.group(1)
    return found


def _git(runner: Runner, workdir: Path | None, *args: str) -> Completed:
    """Run one git command as argv."""
    return runner.run(shlex.join(["git", *args]), cwd=workdir)


def _untracked(runner: Runner, workdir: Path) -> list[str]:
    """List files git does not track yet.

    ``-uall`` because the plain form collapses a wholly-new directory to
    a single entry like ``.github/``. That happens to still match the
    denylist, but it reports a directory to the allowlist and into the
    steer message, so the implementer is told the wrong path and a
    nested allowlist entry cannot be judged at all.
    """
    result = runner.run("git status --porcelain -uall", cwd=workdir)
    return [
        line[3:].strip()
        for line in result.output.splitlines()
        if line.startswith("??") and line[3:].strip()
    ]


def _revert_offenders(
    runner: Runner, workdir: Path, offenders: Sequence[str]
) -> list[str]:
    """Undo out-of-scope edits. Returns the paths still in the tree.

    Tracked and created files need different commands: ``git checkout --``
    cannot remove a file git has never seen, and exits 1 with "pathspec
    ... did not match any file(s) known to git" while leaving it in place.

    Both exit codes are read. They used to be discarded while the steer
    text and the proof asserted the tree had been reverted, so an
    implementer worked from a false premise on every later attempt and
    the morning's proof recorded a revert that never happened.
    """
    tracked = set(_changed_files(runner, workdir))
    created = [path for path in offenders if path not in tracked]
    modified = [path for path in offenders if path in tracked]

    unreverted: list[str] = []
    if modified:
        result = _git(runner, workdir, "checkout", "--", *modified)
        if result.returncode != 0:
            unreverted += modified
    if created:
        result = _git(runner, workdir, "clean", "-fd", "--", *created)
        if result.returncode != 0:
            unreverted += created
    return unreverted


def _discard_uncommitted(runner: Runner, worktree: Path) -> Discarded | None:
    """Record what a parked task left behind, then revert it.

    The task that parked the item was dispatched before it was judged,
    so the implementer had already written something. Those edits carry
    no proof row and no commit: invisible to the morning review, and
    applied a second time on top of themselves when the task is
    dispatched again. Recording them keeps them reviewable, and
    reverting keeps the resume honest about what the diff contains.

    Returns None when there was nothing to discard, so a clean park does
    not grow an empty section.
    """
    files = _changed_files(runner, worktree)
    untracked = _untracked(runner, worktree)
    if not files and not untracked:
        return None

    diff = runner.run("git diff", cwd=worktree).output[-DISCARD_DIFF_CHARS:]
    if files:
        _git(runner, worktree, "checkout", "--", ".")
    return Discarded(files=files, untracked=untracked, diff=diff)


class BudgetExhausted(Exception):
    """Raised when a babysitter call would cross the item's token ceiling."""


class UsageLimited(Exception):
    """Raised when a run was refused for quota rather than for correctness.

    Carries the kind of refusal and the text it was read from, so the
    caller can record a real reset instant rather than a guessed one.
    """

    def __init__(self, kind: str, text: str) -> None:
        """Record which limit was hit and the response that said so."""
        super().__init__(f"{kind}: {text[:200]}")
        self.kind = kind
        self.text = text


def _raise_if_usage_limited(observed: Completed) -> None:
    """Turn a quota refusal into an exception, leaving real failures alone.

    A test that fails because the code is wrong and a test that fails
    because the account is out of tokens both exit non-zero. Only the
    second should stop the night, so the two are told apart here rather
    than by the retry loop, which would otherwise burn its attempts on a
    limit no retry can lift.
    """
    if observed.returncode == 0:
        return
    kind = window_mod.classify(observed.output)
    if kind in ("rate_limit", "spend_limit"):
        raise UsageLimited(kind, observed.output)


def _metered_babysitter(
    babysitter: Babysitter,
    spend: list[int],
    budget: Budget | None,
    ceiling: int | None,
) -> Babysitter:
    """Wrap a babysitter so its cost is counted, and capped, before it runs.

    The check happens here rather than between tasks because this is
    where the spend happens. Checking between tasks lets a run overshoot
    by a whole task's cost, and a ceiling that can be exceeded is not a
    ceiling. ``spend`` is a one-element list so the count survives across
    calls without a class.
    """

    def metered(**kwargs: Any) -> tuple[str, str, str]:
        shown = str(kwargs.get("diff", "")) + str(kwargs.get("test_output", ""))
        cost = estimate_tokens(shown)
        if ceiling is not None and spend[0] + cost > ceiling:
            raise BudgetExhausted(
                f"this check would cost about {cost} on-plan tokens, taking the "
                f"run to {spend[0] + cost} against a ceiling of {ceiling}"
            )
        spend[0] += cost
        if budget is not None:
            budget.estimated_tokens_used += cost
        return babysitter(**kwargs)

    return metered


def run_item(
    handoff: Mapping[str, Any],
    tasks: Sequence[Mapping[str, Any]],
    root: Path,
    runner: Runner,
    *,
    babysitter: Babysitter,
    budget: Budget | None = None,
) -> ItemResult:
    """Walk one item's tasks to a stopping point, committing as it goes.

    Stops at the first task that does not pass, at the on-plan token
    ceiling, or at the end of the list. In every case the tasks that
    already passed stay committed. A stop is not a rollback: a task with
    a proof row is reviewable work whatever happened after it.
    """
    item = str(handoff.get("item"))
    limits = handoff.get("budget") or {}
    ceiling = int(limits.get("claude_token_ceiling", 0)) or None
    worktree = root / str(handoff.get("worktree") or f".egregore/worktrees/{item}")

    result = ItemResult(item=item, status="ready")

    _git(
        runner,
        root,
        "worktree",
        "add",
        "-b",
        str(handoff.get("branch")),
        str(worktree),
        str(handoff.get("base_branch")),
    )
    setup = (handoff.get("commands") or {}).get("setup")
    if setup:
        runner.run(str(setup), cwd=worktree)

    spend = [0]
    for task in topo_sort(tasks):
        tid = str(task.get("id"))

        try:
            task_result = run_task(
                task,
                handoff,
                worktree,
                runner,
                babysitter=_metered_babysitter(babysitter, spend, budget, ceiling),
                budget=budget,
            )
        except BudgetExhausted as exhausted:
            result.status = "parked_budget"
            result.reason = f"stopped at {tid}: {exhausted}"
            break
        except UsageLimited as limited:
            result.status = f"parked_{limited.kind}"
            resume_at = window_mod.record_reset(
                budget if budget is not None else budget_mod.Budget(),
                window_mod.parse_reset(_headers_in(limited.text), limited.text),
            )
            result.reason = (
                f"stopped at {tid}: {limited.kind}. Capacity is expected back "
                f"at {resume_at.isoformat()}; the watchdog resumes then."
            )
            break
        result.tasks.append(task_result)

        if task_result.verdict != "PASS":
            result.status = "parked_task"
            result.reason = f"{tid} ended {task_result.verdict}: {task_result.reason}"
            break

        _git(runner, worktree, "add", "-A")
        _git(runner, worktree, "commit", "-m", f"{tid}: {task.get('title')}")
        result.committed.append(tid)

    result.estimated_tokens = spend[0]

    if result.status != "ready":
        result.discarded = _discard_uncommitted(runner, worktree)

    if result.status == "ready":
        full = (handoff.get("commands") or {}).get("full_test")
        if full:
            observed = runner.run(str(full), cwd=worktree)
            result.full_suite = {
                "command": str(full),
                "exit": observed.returncode,
                "output": observed.output,
            }
            if observed.returncode != 0:
                result.status = "full_suite_red"
                result.reason = f"the full suite exited {observed.returncode}"

    return result


def write_proof(item_dir: Path, result: ItemResult) -> Path:
    """Write the item's proof ledger. Only this function writes it."""
    lines = [
        f"# Proof: {result.item}",
        "",
        f"**Status**: {result.status}",
    ]
    if result.reason:
        lines += ["", f"**Why it stopped**: {result.reason}"]
    lines += [
        "",
        f"**Estimated on-plan tokens**: {result.estimated_tokens}",
        "",
        "## Evidence",
        "",
        "| Task | Attempt | Evidence command | Exit | Expect | Verdict |",
        "|------|---------|------------------|------|--------|---------|",
    ]
    for task_result in result.tasks:
        for row in task_result.ledger:
            lines.append(
                f"| {row['task']} | {row['attempt']} | `{row['command']}` | "
                f"{row['exit']} | {row['expect']} | {row['verdict']} |"
            )
    dissenting = [t for t in result.tasks if t.dissent]
    if dissenting:
        lines += ["", "## Babysitter dissents (the evidence was green anyway)", ""]
        lines += [f"- {t.task_id}: {t.reason}" for t in dissenting]
    if result.full_suite:
        lines += [
            "",
            "## Full suite",
            "",
            f"`{result.full_suite['command']}` exited {result.full_suite['exit']}",
        ]
    if result.discarded is not None:
        lines += [
            "",
            "## Discarded at park",
            "",
            "The task that parked this item had already been dispatched, so "
            "these edits existed with no proof row and no commit. They are "
            "recorded here and the tree was reverted, so a resume does not "
            "apply them twice.",
        ]
        if result.discarded.files:
            lines += ["", f"**Reverted**: {', '.join(result.discarded.files)}"]
        if result.discarded.untracked:
            lines += [
                "",
                "**Left in place, untracked**: "
                f"{', '.join(result.discarded.untracked)}",
            ]
        if result.discarded.diff:
            lines += ["", "```diff", result.discarded.diff.rstrip(), "```"]

    lines += ["", "## Committed", ""]
    lines += [f"- {tid}" for tid in result.committed] or ["- (nothing)"]
    lines.append("")

    item_dir.mkdir(parents=True, exist_ok=True)
    path = item_dir / "proof.md"
    path.write_text("\n".join(lines))
    return path
