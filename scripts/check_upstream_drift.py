#!/usr/bin/env python3
"""Gate: report drift between recorded upstream state and current reality.

This repo pins model tiers, effort levels, and harness features across
plugins, skills, commands, agents, and hooks. When Anthropic ships a
model or Claude Code ships a version, those pins rot silently, and
nothing records what upstream looked like the last time we adjusted.
Every audit then restarts from zero and re-derives the same delta by
hand.

The ledger at ``.claude/upstream-baseline.json`` is the watermark. It
records the harness version, the model roster, and the vocabularies our
other gates freeze. This script compares that record against reality
and reports four drift classes:

``harness``
    The installed ``claude --version`` differs from the ledger.

``vocabulary``
    A gate's frozen set omits a value the ledger records. This is the
    sharpest class. ``check_agent_model_matrix.py`` rejects any agent
    pinning a tier outside ``VALID_MODELS``. When a tier ships and that
    set is not widened, the guard that exists to prevent model rot has
    itself rotted, and no agent can pin the new tier.

``dated_ids``
    A file names a dated model ID such as ``claude-opus-4-6`` outside
    the surfaces ``check_agent_model_matrix.py`` already covers.

    This class counts *mentions*, not *pins*, and the difference
    matters when reading the ratchet. A lookup table keyed by legacy
    IDs is mention-heavy by construction and does not rot: to price
    Opus 4.6 you have to name Opus 4.6. What rots is a default or a
    selection, and the count cannot tell the two apart. The backlog
    rose from 44 to 51 when legacy pricing entries were added at the
    same time the live pins were removed, so the number went up while
    the risk went down. It rose again from 51 to 57 when ``docs`` was
    added to the scan, and from 57 to 60 when ``SKILL.md`` bodies
    stopped being exempt. Both surfaced pre-existing mentions rather
    than new ones. It then fell to 55, because five of the mentions
    those two changes exposed turned out to be live selections: a CLI
    default, a scaffolder's generated frontmatter, an agent template,
    and a config doc that had drifted behind the module it documents.
    That is the shape a working ratchet makes. Widening the lens raises
    the number, and reading what it exposed lowers it again. Read a
    movement here before acting on it.

``unknown_tier``
    A file references a tier absent from the ledger roster.

Harness drift is fully deterministic because the installed binary
reports its own version. Model drift is not: no local command
enumerates the current roster, so the ledger holds the last known
roster and web research establishes the current one. This script does
not research. It reports what it can prove locally and leaves the rest
to ``Skill(night-market-model-and-harness-updates)``.

Exit codes follow the house gate convention: ``0`` when no drift, ``1``
when drift is found, ``2`` on a usage or environment error.

Deterministic, read-only, and idempotent.
"""

from __future__ import annotations

import argparse
import ast
import copy
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_LEDGER = REPO_ROOT / ".claude" / "upstream-baseline.json"
DEFAULT_GATE = REPO_ROOT / "scripts" / "check_agent_model_matrix.py"
# ``docs`` is scanned because prose carries runnable examples: a guide
# that hands the reader a ``messages.create(model=...)`` snippet pins a
# model as surely as any frontmatter does, and a retired ID there is a
# 404 the reader inherits. ``scripts`` and ``tests`` stay out, because
# the only dated IDs in them are this gate's own specimens and the
# ratchet would end up measuring its own fixtures.
DEFAULT_SCAN = (
    REPO_ROOT / "plugins",
    REPO_ROOT / ".claude",
    REPO_ROOT / "docs",
)

SUPPORTED_SCHEMA_VERSION = 1

REQUIRED_TOP_LEVEL = ("schema_version", "harness", "models", "vocabularies")

# Text files worth scanning. Binary and lock files carry no pins.
SCANNED_SUFFIXES = frozenset(
    {".md", ".py", ".json", ".yaml", ".yml", ".sh", ".toml", ".txt"}
)

# Directories that never hold authored pins.
#
# ``worktrees`` and ``context-archive`` duplicate the tree, so scanning
# them double-counts every finding. ``staging`` holds memory-palace web
# captures, which are external text we never authored and must not
# rewrite. All three were found by running this gate against the real
# repo, where they produced the bulk of the noise.
SKIPPED_DIRS = frozenset(
    {
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        ".uv-cache",
        ".worktrees",
        "worktrees",
        "staging",
        "context-archive",
        # Migration reports document what shipped and what was retired,
        # so they name dated IDs by necessity. Counting them makes the
        # ratchet climb once per run forever, driven by this workflow's
        # own output. Historical records are exempt here for the same
        # reason the repo's prose rules exempt changelog entries.
        "migrations",
        # Tool caches and vendored packages are build output. 80 of the
        # first 124 counted findings were .mypy_cache entries for the
        # anthropic SDK's model type stubs, so the ratchet was tracking
        # whether someone had rerun mypy.
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".eggs",
        "site-packages",
        "htmlcov",
    }
)

# A dated model ID, in either of the two naming conventions Anthropic
# has used. Claude 4 onward puts the version after the family name
# (``claude-sonnet-4-6``); Claude 3.x and earlier put it before
# (``claude-3-5-sonnet-20241022``), and ``claude-2.1`` carries no family
# at all. Encoding only the later shape left every retired 3.x ID
# invisible to this ratchet, which is how a ``claude-3-5-sonnet-20241022``
# call sat in a docs example past its 2025-10-28 retirement until an
# outside contributor read the line by hand.
#
# The family list stays explicit for the post-4 branch so a hyphenated
# product name cannot be read as a model. The pre-4 branch cannot use one:
# the version comes first, so there is nothing to anchor on but the digit.
DATED_ID_RE = re.compile(
    r"claude-(?:(?:opus|sonnet|haiku|fable)-)?\d[\w.-]*|claude-instant[\w.-]*"
)

# A ``model:`` frontmatter assignment naming a tier alias.
MODEL_LINE_RE = re.compile(r"^[ \t]*model:[ \t]*([A-Za-z][\w.-]*)[ \t]*$", re.MULTILINE)

# The leading YAML block of a markdown file. Tier pins are read only
# from here. A bare ``model:`` line elsewhere is either prose showing
# the reader what to write, or a Python annotation such as
# ``model: str`` in a dataclass. Both produced false positives before
# this narrowing.
FRONTMATTER_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL)

# Vocabularies the ledger records, mapped to the gate symbol that must
# be able to express them.
VOCABULARY_BINDINGS = (
    ("model tier", "VALID_MODELS", ("models", "tiers")),
    ("effort level", "VALID_EFFORTS", ("vocabularies", "effort_levels")),
)


@dataclass(frozen=True)
class Drift:
    """One reported difference between the ledger and reality."""

    kind: str
    detail: str
    location: str


# --------------------------------------------------------------------
# Ledger
# --------------------------------------------------------------------


def load_ledger(path: Path) -> dict:
    """Read the ledger.

    Raises ``FileNotFoundError`` when absent rather than returning an
    empty default. A missing watermark is a condition to fix, not one
    to paper over: silently treating it as "nothing recorded yet" would
    make a first run indistinguishable from a deleted ledger.
    """
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_ledger(path: Path, data: dict) -> None:
    """Write the ledger so it diffs cleanly in review."""
    text = json.dumps(data, indent=2, sort_keys=False) + "\n"
    Path(path).write_text(text, encoding="utf-8")


def validate_ledger(data: dict) -> list[str]:
    """Return a list of schema errors, empty when the ledger is sound."""
    errors: list[str] = []

    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            errors.append(f"missing required key: {key}")
    if errors:
        return errors

    version = data["schema_version"]
    if version != SUPPORTED_SCHEMA_VERSION:
        errors.append(
            f"unsupported schema_version {version!r}; "
            f"this script understands {SUPPORTED_SCHEMA_VERSION}"
        )

    models = data["models"]
    tiers = models.get("tiers", [])
    ids = models.get("ids", {})
    for tier in tiers:
        if tier not in ids:
            errors.append(f"tier {tier!r} has no model ID recorded in models.ids")

    ratchets = data.get("ratchets", {})
    if not isinstance(ratchets, dict):
        errors.append("ratchets must be an object")
    else:
        for key, value in ratchets.items():
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                errors.append(f"ratchet {key!r} must be a non-negative integer")

    return errors


def snapshot_state(ledger: dict) -> dict:
    """Capture the comparable state of a ledger as a detached copy.

    Call this before mutating the ledger for a run, then hand the result
    to ``record_migration`` as ``from_state``. The copy is deliberate:
    a live view would track the mutations and record a no-op delta.
    """
    return {
        "harness": ledger["harness"]["version"],
        "model_tiers": list(ledger["models"]["tiers"]),
    }


def record_migration(
    ledger: dict,
    migration: dict,
    from_state: dict | None = None,
) -> dict:
    """Return a ledger with a new migration recorded.

    ``migration`` carries ``id``, ``trigger``, ``assets_changed``, and
    ``report``. The previous ``last_migration`` is appended to
    ``history`` and never rewritten.

    ``from_state`` is the ledger state as it stood when the run began,
    captured with ``snapshot_state``. Omitting it records ``from`` equal
    to ``to``, which is correct only for a run that changed nothing.

    An earlier version derived ``from`` off the previous migration's
    ``to``. That silently recorded a no-op whenever the previous record
    over-claimed or the ledger was corrected out of band, which is
    exactly what happened on the first real run: a 140-version harness
    gap was recorded as 2.1.220 to 2.1.220. The state the run actually
    started from is the only honest source for ``from``.
    """
    updated = copy.deepcopy(ledger)
    previous = updated.get("last_migration")

    if previous is not None:
        updated.setdefault("history", []).append(copy.deepcopy(previous))
    else:
        updated.setdefault("history", [])

    start = from_state if from_state is not None else snapshot_state(updated)

    updated["last_migration"] = {
        "id": migration["id"],
        "trigger": migration["trigger"],
        "from": {
            "harness": start.get("harness"),
            "model_tiers": list(start.get("model_tiers", [])),
        },
        "to": snapshot_state(updated),
        "assets_changed": migration["assets_changed"],
        "report": migration["report"],
    }
    return updated


# --------------------------------------------------------------------
# Drift class: harness
# --------------------------------------------------------------------


def detect_harness_version() -> str | None:
    """Return the installed Claude Code version, or None if unknown."""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    match = re.search(r"\d+\.\d+\.\d+", result.stdout)
    return match.group(0) if match else None


def detect_harness_drift(ledger: dict, current: str | None) -> list[Drift]:
    """Compare the installed harness version against the ledger."""
    recorded = ledger["harness"]["version"]

    if current is None:
        return [
            Drift(
                kind="harness",
                detail=(
                    "could not determine the installed Claude Code version; "
                    f"ledger records {recorded}"
                ),
                location="claude --version",
            )
        ]

    if current != recorded:
        return [
            Drift(
                kind="harness",
                detail=f"ledger records {recorded}, installed harness is {current}",
                location="claude --version",
            )
        ]

    return []


# --------------------------------------------------------------------
# Drift class: vocabulary
# --------------------------------------------------------------------


def extract_frozenset(source: str, name: str) -> set[str] | None:
    """Read a module-level ``NAME = frozenset({...})`` literal.

    Parsed rather than imported. Importing a gate to read one constant
    would run its module-level code, and these gates resolve repo paths
    at import time.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if name not in targets:
            continue
        value = node.value
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "frozenset"
            and value.args
        ):
            value = value.args[0]
        try:
            literal = ast.literal_eval(value)
        except (ValueError, TypeError):
            return None
        if isinstance(literal, (set, frozenset, list, tuple)):
            return {str(item) for item in literal}
    return None


def _ledger_path(ledger: dict, path: tuple[str, ...]) -> list[str]:
    node: object = ledger
    for key in path:
        if not isinstance(node, dict):
            return []
        node = node.get(key)
    return list(node) if isinstance(node, list) else []


def detect_vocabulary_drift(ledger: dict, gate_source: str) -> list[Drift]:
    """Report ledger values a gate's frozen set cannot express.

    The ledger is a floor, not a ceiling. A gate accepting more than the
    ledger records is not drift; only values the ledger knows about and
    the gate rejects are.
    """
    drifts: list[Drift] = []

    for label, symbol, ledger_key in VOCABULARY_BINDINGS:
        accepted = extract_frozenset(gate_source, symbol)
        if accepted is None:
            continue
        recorded = _ledger_path(ledger, ledger_key)
        missing = [value for value in recorded if value not in accepted]
        if missing:
            drifts.append(
                Drift(
                    kind="vocabulary",
                    detail=(
                        f"{symbol} cannot express {label}(s) "
                        f"{', '.join(sorted(missing))} recorded in the ledger"
                    ),
                    location=symbol,
                )
            )

    return drifts


# --------------------------------------------------------------------
# File scanning
# --------------------------------------------------------------------


def _is_gated_surface(path: Path) -> bool:
    """True when check_agent_model_matrix.py already covers this file.

    Only agent definitions qualify. ``SKILL.md`` does not: the matrix
    gate reads a skill's ``model:`` frontmatter field and nothing else,
    so its body is nobody's territory unless this gate takes it. See
    ``_scannable_text``.
    """
    return "agents" in path.parts


def _scannable_text(path: Path) -> str:
    """Return the part of a file this gate owns.

    For ``SKILL.md`` that is the body: the matrix gate owns the
    ``model:`` field in the frontmatter, and counting it here would
    double-report one violation. Everything else is scanned whole.
    """
    text = _read(path)
    if path.name == "SKILL.md":
        return FRONTMATTER_RE.sub("", text)
    return text


def _iter_files(roots: list[Path] | tuple[Path, ...]):
    for root in roots:
        root = Path(root)
        if root.is_file():
            yield root
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if SKIPPED_DIRS.intersection(path.parts):
                continue
            if path.suffix not in SCANNED_SUFFIXES:
                continue
            yield path


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def detect_dated_ids(
    roots: list[Path] | tuple[Path, ...],
    known_ids: set[str] | None = None,
) -> list[Drift]:
    """Report dated model IDs outside the surfaces the matrix gate covers."""
    known = known_ids or set()
    drifts: list[Drift] = []

    for path in _iter_files(roots):
        if _is_gated_surface(path):
            continue
        found = set(DATED_ID_RE.findall(_scannable_text(path))) - known
        for model_id in sorted(found):
            drifts.append(
                Drift(
                    kind="dated_ids",
                    detail=f"pins dated model ID {model_id}",
                    location=str(path),
                )
            )

    return drifts


def detect_unknown_tiers(
    ledger: dict,
    roots: list[Path] | tuple[Path, ...],
) -> list[Drift]:
    """Report ``model:`` values naming a tier absent from the ledger."""
    tiers = set(_ledger_path(ledger, ("models", "tiers")))
    drifts: list[Drift] = []

    for path in _iter_files(roots):
        if path.suffix != ".md":
            continue
        block = FRONTMATTER_RE.match(_read(path))
        if block is None:
            continue
        for value in MODEL_LINE_RE.findall(block.group(1)):
            if value.startswith("claude-"):
                continue  # a dated ID; detect_dated_ids owns that case
            if value in tiers:
                continue
            drifts.append(
                Drift(
                    kind="unknown_tier",
                    detail=f"references tier {value!r}, absent from the ledger roster",
                    location=str(path),
                )
            )

    return drifts


# --------------------------------------------------------------------
# Ratchet
# --------------------------------------------------------------------


def apply_dated_id_ratchet(found: list[Drift], backlog: int) -> list[Drift]:
    """Collapse the dated-ID findings into a ratchet verdict.

    The repo carries a pre-existing backlog of dated IDs in docs, tests,
    and historical notes, where a dated ID is often correct. Failing on
    every one would hold this gate permanently red and train everyone to
    ignore it. Instead the count is capped: the gate fails only when the
    backlog grows.
    """
    if len(found) <= backlog:
        return []
    return [
        Drift(
            kind="dated_ids",
            detail=(
                f"{len(found)} dated model IDs found, ratchet allows {backlog}. "
                f"Remove {len(found) - backlog} or justify raising the backlog."
            ),
            location="ratchets.dated_ids_backlog",
        )
    ]


def ratchet_slack(found: list[Drift], backlog: int) -> int:
    """Return how far the backlog could tighten, zero when it cannot."""
    return max(0, backlog - len(found))


# --------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report drift between the upstream ledger and reality.",
    )
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--gate", type=Path, default=DEFAULT_GATE)
    parser.add_argument("--scan", type=Path, action="append", default=None)
    parser.add_argument(
        "--harness-version",
        default=None,
        help="Override version detection; mainly for tests.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a JSON report.")
    return parser.parse_args(argv)


def _render_text(drifts: list[Drift], ledger_path: Path) -> None:
    if not drifts:
        print(f"upstream drift: none (ledger {ledger_path})")
        return

    by_kind: dict[str, list[Drift]] = {}
    for drift in drifts:
        by_kind.setdefault(drift.kind, []).append(drift)

    print(f"upstream drift: {len(drifts)} finding(s) against {ledger_path}\n")
    for kind in sorted(by_kind):
        entries = by_kind[kind]
        print(f"  {kind} ({len(entries)})")
        for drift in entries:
            print(f"    - {drift.detail}")
            print(f"      {drift.location}")
        print()
    print("Run Skill(night-market-model-and-harness-updates) to research and sweep.")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(list(argv) if argv is not None else sys.argv[1:])

    try:
        ledger = load_ledger(args.ledger)
    except FileNotFoundError:
        print(f"error: ledger not found: {args.ledger}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: ledger is not valid JSON: {exc}", file=sys.stderr)
        return 2

    errors = validate_ledger(ledger)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 2

    gate_source = _read(args.gate)
    roots = args.scan if args.scan else list(DEFAULT_SCAN)
    current = args.harness_version or detect_harness_version()
    known_ids = set(ledger.get("models", {}).get("ids", {}).values())

    backlog = ledger.get("ratchets", {}).get("dated_ids_backlog", 0)
    dated = detect_dated_ids(roots, known_ids=known_ids)

    drifts: list[Drift] = []
    drifts.extend(detect_harness_drift(ledger, current))
    drifts.extend(detect_vocabulary_drift(ledger, gate_source))
    drifts.extend(apply_dated_id_ratchet(dated, backlog))
    drifts.extend(detect_unknown_tiers(ledger, roots))

    slack = ratchet_slack(dated, backlog)

    if args.json:
        print(
            json.dumps(
                {
                    "ledger": str(args.ledger),
                    "harness_recorded": ledger["harness"]["version"],
                    "harness_current": current,
                    "drift_count": len(drifts),
                    "drifts": [asdict(d) for d in drifts],
                    "dated_ids_found": len(dated),
                    "dated_ids_backlog": backlog,
                    "ratchet_slack": slack,
                },
                indent=2,
            )
        )
    else:
        _render_text(drifts, args.ledger)
        if slack:
            print(
                f"note: dated-ID backlog can tighten by {slack} "
                f"(found {len(dated)}, allows {backlog})."
            )

    return 1 if drifts else 0


if __name__ == "__main__":
    sys.exit(main())
