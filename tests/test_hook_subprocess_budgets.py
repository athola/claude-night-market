"""A hook's own timeouts must fit inside the cap the harness enforces.

``hooks.json`` declares a ``timeout`` per hook. The harness kills the
process at that cap. A killed hook does not return a partial answer, it
returns nothing, and for a blocking hook nothing means the action
proceeds. So a subprocess budget at or above the cap converts a gate
into a no-op precisely when the work is slowest, which is when the gate
matters.

Four instances, each measured before this file was written:

``gauntlet/hooks/precommit_gate.py``
    Declares 2s. ``main`` calls ``_graph_risk_context``, which reaches
    ``blast_radius.parse_git_diff_ranges`` and its ``timeout=10``. The
    gate had already set ``_GIT_TIMEOUT_SECONDS = 1`` for its own calls,
    with the comment that a killed hook returns no deny, and then made a
    library call it did not audit.

``sanctum/hooks/deferred_item_sweep.py``
    Declares 5s on Stop. Used ``timeout=15`` per ledger entry, in a loop,
    so a single unfiled item already exceeded the cap.

``imbue/hooks/guard_package_hallucination.py``
    Declares 8s. Spent 1.5s per unresolved package with no cap on the
    count, so six unknown names exceeded it.

``memory-palace/hooks/shared/deduplication.py``
    Declares 5s. Used ``timeout=5`` on ``git add``, leaving no margin for
    the fetch, the checks and the write that ran first in the same
    invocation.

The check reads literals and simple module constants. It cannot see a
loop, so a per-item budget that fits the cap once can still exceed it
across iterations; that is what the deadline in each of the two looping
hooks above is for, and it is asserted separately in each plugin's
suite.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS = REPO_ROOT / "plugins"

# Keyword arguments that carry a wall-clock budget into a blocking call.
TIMEOUT_KEYWORDS = frozenset({"timeout"})


def _module_constants(tree: ast.Module) -> dict[str, float]:
    """Module-level names bound to a bare number."""
    constants: dict[str, float] = {}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        if not isinstance(value, ast.Constant) or not isinstance(
            value.value, (int, float)
        ):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name):
                constants[target.id] = float(value.value)
    return constants


def _declared_timeouts(source: str) -> list[tuple[int, float]]:
    """Every ``timeout=<number>`` in the file, as (line, seconds)."""
    tree = ast.parse(source)
    constants = _module_constants(tree)
    found: list[tuple[int, float]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg not in TIMEOUT_KEYWORDS:
                continue
            value = keyword.value
            if isinstance(value, ast.Constant) and isinstance(
                value.value, (int, float)
            ):
                found.append((keyword.value.lineno, float(value.value)))
            elif isinstance(value, ast.Name) and value.id in constants:
                found.append((value.lineno, constants[value.id]))
    return found


def _registered_hooks() -> list[tuple[Path, float]]:
    """Each hook script that hooks.json registers, with its tightest cap.

    A script registered under two events is held to the smaller cap: it
    has one body, and that body has to fit whichever event fires.
    """
    caps: dict[Path, float] = {}
    for manifest in sorted(PLUGINS.glob("*/hooks/hooks.json")):
        plugin_hooks = manifest.parent
        events = json.loads(manifest.read_text(encoding="utf-8")).get("hooks", {})
        for groups in events.values():
            for group in groups:
                for entry in group.get("hooks", []):
                    timeout = entry.get("timeout")
                    if not isinstance(timeout, (int, float)):
                        continue
                    if entry.get("async") is True:
                        # An async hook outlives the session, so the cap
                        # does not bound it.
                        continue
                    command = entry.get("command", "")
                    name = command.rsplit("/", 1)[-1].strip()
                    if not name.endswith((".py", ".sh")):
                        continue
                    script = plugin_hooks / name
                    if not script.is_file():
                        continue
                    caps[script] = min(caps.get(script, float("inf")), float(timeout))
    return sorted(caps.items())


def test_discovery_finds_registered_hooks() -> None:
    """An empty parametrize list would make the guard below vacuous."""
    assert len(_registered_hooks()) > 5


@pytest.mark.parametrize(
    "script,cap",
    _registered_hooks(),
    ids=lambda v: v.stem if isinstance(v, Path) else v,
)
def test_hook_subprocess_budget_fits_its_cap(script: Path, cap: float) -> None:
    """Every timeout a hook declares must be strictly under its cap."""
    if script.suffix != ".py":
        return
    relative = script.relative_to(REPO_ROOT)
    offenders = [
        (line, seconds)
        for line, seconds in _declared_timeouts(script.read_text(encoding="utf-8"))
        if seconds >= cap
    ]
    rendered = "\n".join(f"  {relative}:{line}: timeout={s}" for line, s in offenders)
    assert not offenders, (
        f"{relative} is registered with a {cap}s cap and declares a timeout "
        f"at or above it:\n{rendered}\n"
        f"The harness kills the process at the cap, and a killed hook returns "
        f"no decision at all. For a blocking hook that is the same as having "
        f"no hook, and it happens on exactly the slow runs the hook exists to "
        f"catch. Leave margin for the work that already ran in the same "
        f"invocation."
    )
