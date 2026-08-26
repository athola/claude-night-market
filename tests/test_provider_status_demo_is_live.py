"""Guard that a target labelled ``(LIVE)`` actually runs something.

``tests/test_makefile_probe_integrity.py`` guards Makefile ``python -c``
probes against importing modules that do not exist. This guard covers the
neighbouring failure: a ``demo-*`` target that advertises itself as LIVE
and whose every recipe line is an ``@echo``.

conjure had both halves of the defect. ``demo-status`` is echo-only::

    demo-status: ## Demo status command (LIVE)
        @echo "=== status Demo (LIVE) ==="
        @echo "This demonstrates status usage."
        @echo "Execute manually in Claude Code for full functionality."

So is ``demo-plugin``. And the aggregate that exists to run the demos
depended on exactly those two::

    demo-conjure-commands: demo-plugin demo-status

So ``make demo-conjure-commands`` printed "Demo Complete" having executed
no plugin code at all, while three separate lines claimed LIVE.

This matters more for conjure than it would elsewhere. PR #662 made the
provider contract the thing that decides whether a service can be
registered, authenticated and still never selected. ``delegate-setup``
already runs ``delegation_setup.py --status`` and prints the table that
shows it working, with a row per provider and its install and auth state.
The demo surface simply did not point at it.

Two properties are asserted:

1. The demo aggregate reaches at least one target that runs real code,
   so the aggregate cannot go green having run nothing.
2. No target advertises ``(LIVE)`` in its help text while its recipe is
   echo-only. The label is the part that misleads: an informational
   target is fine, an informational target claiming to be live is not.

Both are static reads of the Makefile, so neither spawns a provider CLI.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONJURE_MAKEFILE = REPO_ROOT / "plugins" / "conjure" / "Makefile"
AGGREGATE = "demo-conjure-commands"

# A recipe line that does real work: it runs something other than echo.
_INERT = re.compile(r"^\t@?(echo\b|#|@#|$)")


def _targets(makefile: Path) -> dict[str, tuple[str, list[str]]]:
    """Map target name to its help text and recipe lines."""
    out: dict[str, tuple[str, list[str]]] = {}
    lines = makefile.read_text().splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^([A-Za-z0-9_-]+):(?![=])([^#]*)(?:##\s*(.*))?$", line)
        if not m:
            continue
        name, help_text = m.group(1), (m.group(3) or "")
        body: list[str] = []
        for nxt in lines[i + 1 :]:
            if nxt.startswith("\t"):
                body.append(nxt)
            elif nxt.strip() == "":
                continue
            else:
                break
        out[name] = (help_text, body)
    return out


def _deps(makefile: Path, target: str) -> list[str]:
    """Prerequisites declared for one target."""
    for line in makefile.read_text().splitlines():
        m = re.match(rf"^{re.escape(target)}:([^#]*)", line)
        if m:
            return m.group(1).split()
    return []


def _does_real_work(body: list[str]) -> bool:
    """True when at least one recipe line runs something beyond echo."""
    return any(not _INERT.match(ln) for ln in body)


def test_the_demo_aggregate_runs_at_least_one_real_target() -> None:
    """`make demo-conjure-commands` must execute plugin code."""
    targets = _targets(CONJURE_MAKEFILE)
    assert AGGREGATE in targets, f"{AGGREGATE} is not defined"

    reached = _deps(CONJURE_MAKEFILE, AGGREGATE)
    assert reached, f"{AGGREGATE} has no prerequisites"

    live = [d for d in reached if d in targets and _does_real_work(targets[d][1])]
    assert live, (
        f"{AGGREGATE} depends only on echo-only targets ({reached}), so it "
        "reports success having run no plugin code. Point it at a target "
        "that runs real code, such as delegate-setup."
    )


PLUGIN_MAKEFILES = sorted((REPO_ROOT / "plugins").glob("*/Makefile"))


@pytest.mark.parametrize("makefile", PLUGIN_MAKEFILES, ids=lambda p: p.parent.name)
def test_no_target_claims_live_while_only_echoing(makefile: Path) -> None:
    """A `(LIVE)` label must be backed by a recipe that runs something.

    Scoped to every plugin rather than to conjure. The first version of
    this guard read one Makefile, so the fix it certified held in one
    plugin while 61 targets across ten others went on advertising LIVE
    over recipes that were nothing but ``@echo``. A guard that reads one
    instance of a repo-wide claim reports the claim as kept.
    """
    liars = [
        name
        for name, (help_text, body) in _targets(makefile).items()
        if "LIVE" in help_text and body and not _does_real_work(body)
    ]
    assert not liars, (
        f"In {makefile.parent.name}, these targets advertise (LIVE) but "
        f"only echo: {liars}. Either run the feature or drop the label; a "
        "false LIVE claim is what let conjure's broken demo-delegation "
        "stay invisible."
    )
