"""Every ``make`` target a workflow asset cites must exist somewhere.

`.claude/rules/slop-scan-for-docs.md` Layer 0 makes a cited thing that
does not resolve a P0 defect. ``test_cited_paths_resolve.py`` enforces
that for backticked file paths and for ``plugin:name`` capabilities. A
``make`` target slips between both: it carries no slash, so the path
gate does not recognize it as a token, and no colon, so the capability
gate ignores it too.

That gap was found by following ``sanctum:git-workspace-review`` step 3,
which told the reader to run ``make format && make lint``. There is no
root ``format`` target, so the step stopped at "No rule to make target"
before it checked anything. Seven more phantom targets were cited across
skills and commands: ``fmt``, ``build``, ``docs-update``,
``validate-skill``, ``test-checkpoint``, and others that had never
existed in any Makefile in the repository.

A citation resolves against the root Makefile, the root's generated
``<plugin>`` and ``<plugin>-<target>`` delegation, or the Makefile of
the plugin the document itself lives in. That last clause is what makes
the gate useful rather than decorative: a plugin's skill legitimately
documents commands run from its own directory, but citing a target only
some *other* plugin defines is the ``make format`` bug exactly. Two
plugins define ``format``, so an "exists in some Makefile" check would
have called the citation that started this fine.

Two forms are checked, both of which read as commands rather than prose,
which is what keeps "make sure" and "make it clear" out of the results:

``make <target>`` inside backticks
    The way a sentence names a command mid-prose.

``make <target>`` starting a line inside a fenced block
    The way a runnable snippet spells one out.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Directories whose markdown an agent consumes as instructions. Kept
# identical to test_cited_paths_resolve.ASSET_GLOBS so the two gates
# always agree on what counts as an instruction.
ASSET_GLOBS = (
    "plugins/*/skills/**/*.md",
    "plugins/*/commands/**/*.md",
    "plugins/*/agents/**/*.md",
    ".claude/rules/*.md",
)

# `make foo`, `make foo BAR=1`, `$ make foo` -- the target is the first
# word after make, and must look like a target rather than a flag.
_TARGET = r"(?P<target>[a-z][a-z0-9_.-]*)"
BACKTICKED = re.compile(r"`[^`\n]*?\bmake\s+" + _TARGET + r"[^`\n]*`")
FENCED_LINE = re.compile(r"^\s*(?:\$\s*)?make\s+" + _TARGET)

# Targets named inside a worked example, where the Makefile being
# described belongs to the project the example is about rather than to
# this repository. Same bar as test_cited_paths_resolve.ALLOWLIST: a
# target earns a place by being illustrative, never by being missing.
ALLOWLIST = {
    # pr-template.md walks through a PR description for a *sample*
    # web project (it references /api/resume and that project's #481).
    # Its test plan cites that project's targets, not ours.
    "serve",
    "ps",
    # session-to-post shows a VHS tape recording someone's app build.
    "play",
    # 5-validate.md quotes an [E2] evidence line from a past run in a
    # plugin that does define memory-profile, as an example of what
    # proof-of-work evidence looks like. Seven plugins define it; sanctum
    # is not one, and the line is a quotation rather than an instruction.
    "memory-profile",
}


_RULE = re.compile(r"^([a-zA-Z][a-zA-Z0-9_.-]*)\s*:(?!=)")


def _targets_in(makefile: Path) -> set[str]:
    """Targets one Makefile defines."""
    if not makefile.exists():
        return set()
    text = makefile.read_text(encoding="utf-8", errors="replace")
    return {m.group(1) for m in (_RULE.match(line) for line in text.splitlines()) if m}


def _plugin_target_map() -> dict[str, set[str]]:
    """Each plugin's own targets, keyed by plugin name."""
    return {m.parent.name: _targets_in(m) for m in REPO_ROOT.glob("plugins/*/Makefile")}


def _owning_plugin(asset: Path) -> str | None:
    """The plugin a document lives in, if any.

    A document inside ``plugins/<name>/`` may name that plugin's own
    targets, because the commands it describes run from there.
    """
    parts = asset.relative_to(REPO_ROOT).parts
    if len(parts) >= 2 and parts[0] == "plugins":
        return parts[1]
    return None


def _tracked() -> frozenset[str]:
    """Paths git tracks, so a sibling worktree's checkout is not scanned."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return frozenset(result.stdout.splitlines())


ROOT_TARGETS = _targets_in(REPO_ROOT / "Makefile")
PLUGIN_TARGETS = _plugin_target_map()
PLUGINS = set(PLUGIN_TARGETS)
TRACKED = _tracked()


def _iter_assets() -> list[Path]:
    """Tracked instruction markdown across every asset directory."""
    found: list[Path] = []
    for glob in ASSET_GLOBS:
        for path in REPO_ROOT.glob(glob):
            if path.is_file() and str(path.relative_to(REPO_ROOT)) in TRACKED:
                found.append(path)
    return sorted(set(found))


def _citations(text: str) -> set[str]:
    """Targets named as commands, in backticks or as a fenced line."""
    found: set[str] = set()
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            fenced = FENCED_LINE.match(line)
            if fenced:
                found.add(fenced.group("target"))
        for match in BACKTICKED.finditer(line):
            found.add(match.group("target"))
    return found


def _resolves(target: str, asset: Path) -> bool:
    """Report whether this document may name this target."""
    if target in ROOT_TARGETS or target in PLUGINS or target in ALLOWLIST:
        return True
    owner = _owning_plugin(asset)
    if owner and target in PLUGIN_TARGETS.get(owner, set()):
        return True
    # The root's generated delegation: `make <plugin>-<target>`.
    head, _, tail = target.partition("-")
    return bool(tail) and head in PLUGINS and tail in PLUGIN_TARGETS.get(head, set())


ASSETS = _iter_assets()


def test_assets_are_discovered() -> None:
    """The globs match something, so a green run is not an empty one."""
    assert len(ASSETS) > 100, f"only {len(ASSETS)} assets discovered"


def test_cited_make_targets_resolve() -> None:
    """No instruction names a make target that exists in no Makefile."""
    phantoms: list[str] = []
    for asset in ASSETS:
        text = asset.read_text(encoding="utf-8", errors="replace")
        for target in sorted(_citations(text)):
            if not _resolves(target, asset):
                phantoms.append(f"{asset.relative_to(REPO_ROOT)}: make {target}")

    assert not phantoms, (
        "instructions cite make targets that no Makefile defines; the reader "
        "gets 'No rule to make target' instead of the check they were told to "
        "run:\n  " + "\n  ".join(phantoms)
    )


def test_allowlist_entries_are_still_unresolvable() -> None:
    """An allowlisted target that now exists must leave the allowlist.

    Otherwise the list silently grows into a place where real phantoms
    hide behind entries that stopped being exceptions.
    """
    redundant = sorted(t for t in ALLOWLIST if t in ROOT_TARGETS or t in PLUGINS)
    assert not redundant, (
        f"these are defined now and no longer need allowlisting: {redundant}"
    )
