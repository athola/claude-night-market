"""Everything a workflow asset cites must exist: paths, and capabilities.

`.claude/rules/slop-scan-for-docs.md` Layer 0 makes this a P0 rule:
"every cited file path ... must resolve to a real thing". Nothing
enforced it, so the same defect kept arriving through review instead of
through a gate. Discussions #604, #610, #623, and PR findings B3/B4 on
PR #417 are five instances of one bug: a SKILL.md pointing at a file
that was renamed, never written, or deleted underneath it.

A phantom citation is worse than a missing one. An agent that follows
`plugins/gauntlet/hooks/pr_blast_radius.py:52-56` for the "exact code
shape" gets nothing back and has no signal that the instruction was
wrong rather than its own lookup.

Three citation forms, three gates, one rule:

``test_cited_paths_resolve``
    Backticked repo paths, rooted at a tracked directory.

``test_cited_capabilities_resolve``
    Backticked ``plugin:name`` and ``/plugin:name`` -- the way a
    document names a sibling skill, command, or agent in prose.

``test_invoked_skills_resolve``
    ``Skill(plugin:name)`` -- the call form, which claims more than
    the prose form does. A backtick says the thing exists; a call
    says it is reachable through the Skill tool, so this arm rejects
    an agent that the prose arm accepts.

The second form was unguarded until discussion #433's sweep found 11
dangling instances. It slips between the two gates that predate it:
``scripts/check_skill_graph_drift.py`` matches only the ``Skill(...)``
call syntax, and the path gate above needs a slash to recognize a
token. Write ``conserve:resource-management`` in backticks and neither
one looks at it, which is how `conserve:resource-management`, deleted
in `54e5b4b1` on 2026-01-18, was still recommended by
`plugins/abstract/commands/plugin-review.md` almost seven months later.

Scope: skills, commands, agents, workflows, and project rules -- the documents an
agent reads as instructions. Prose docs and the changelog are excluded;
they narrate history, and history legitimately references files that no
longer exist.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Directories whose markdown an agent consumes as instructions.
ASSET_GLOBS = (
    "plugins/*/skills/**/*.md",
    "plugins/*/commands/**/*.md",
    "plugins/*/agents/**/*.md",
    ".claude/rules/*.md",
)

# Path-shaped tokens are only checked when rooted at one of these, so
# that `foo/bar` in prose and `os/path` in a docstring stay out of it.
TRACKED_ROOTS = (
    "plugins/",
    "scripts/",
    "tests/",
    "docs/",
    ".claude/",
    ".github/",
)

# A backticked token: a rooted path, optional :line or :line-line suffix.
CITATION = re.compile(
    r"`(?P<path>(?:" + "|".join(re.escape(r) for r in TRACKED_ROOTS) + r")[^`\s]+)`"
)

# Tokens carrying any of these are templates, globs, or prose, not paths.
PLACEHOLDER_CHARS = set("<>{}*?|$")

# Paths a workflow *writes* rather than reads, and paths that are worked
# examples rather than references. A citation only earns a place here by
# being one of those two things -- "it does not exist yet" is the defect
# this gate catches, not an excuse for entering it here.
#
# Directories and pytest node IDs are filtered structurally below, so
# this list holds only file paths.
ALLOWLIST = {
    # --- Artifacts the workflow creates on the user's machine ---
    # The decision journal's two logs; created on first write, and
    # lessons-learned.md is already present. See leyline:decision-journal.
    "docs/tradeoffs.md",
    # doc-consolidation routes content here; a destination, not a source.
    "docs/migration-guide.md",
    # Scaffolded into *target* projects by attune, never into this repo.
    ".github/workflows/test.yml",
    ".github/workflows/validate-hooks.yml",
    "docs/project-brief.md",
    "docs/specification.md",
    "docs/implementation-plan.md",
    "docs/quickstart.md",
    "docs/crypto-inventory.md",
    "docs/benchmarks.md",
    "docs/tutorials/quickstart.md",
    "docs/knowledge-corpus/queue/README.md",
    "docs/playbooks/release-train-health.md",
    ".claude/hookify.block-force-push.local.md",
    ".claude/hookify.dangerous-rm.local.md",
    # Runtime state written by hooks and the continuation agent.
    ".claude/scheduled_tasks.json",
    ".claude/session-state.md",
    ".claude/session-state.md.bak",
    # Per-machine permission overrides. Claude Code writes this one; the
    # repo ships .claude/settings.json and gitignores the local twin.
    ".claude/settings.local.json",
    # Deferred work captured by imbue:scope-guard, and the intake log
    # memory-palace appends to. Destinations the workflows create.
    "docs/backlog/queue.md",
    "docs/backlog/technical-debt.md",
    "docs/curation-log.md",
    "plugins/memory-palace/data/intake_queue.jsonl",
    # Config attune tells the user to add to *their* project.
    ".claude/config.md",
    # Component-level pre-commit scripts attune scaffolds downstream.
    "scripts/run-component-lint.sh",
    "scripts/run-component-tests.sh",
    "scripts/run-component-typecheck.sh",
    # --- Worked examples in authoring guides ---
    "plugins/your-plugin/skills/your-skill/SKILL.md",
    "docs/adr/0001-architecture-choice.md",
    "docs/api.md",
    "docs/specs/feature-user-authentication.md",
    "docs/plans/component-authentication.md",
    "docs/modular-skills/guide.md",
    "tests/test_foo.py",
    "tests/test_file1.py",
    "tests/conftest.py",
    "tests/integration/test_full_flow.py",
    "tests/unit/x.py",
}


# A backticked capability reference: `plugin:name` or `/plugin:name`.
# The leading slash is how the docs write a command; both forms name the
# same three-directory search, so the slash is read and not required to
# mean anything stronger. Of the 180 slash-form references, 11 resolve
# to a skill or an agent and to no command, so demanding that the slash
# imply "command" would report house style as a defect.
CAPABILITY = re.compile(r"`/?(?P<plugin>[a-z][a-z0-9-]*):(?P<name>[a-z][a-z0-9-]*)`")

# Capability references that name something outside this repo, or a
# worked example. Same bar as ALLOWLIST: "it does not exist yet" is the
# defect this gate catches, not a reason to be listed here.
CAPABILITY_ALLOWLIST: set[str] = set()


def _iter_assets() -> list[Path]:
    seen: list[Path] = []
    for pattern in ASSET_GLOBS:
        seen.extend(sorted(REPO_ROOT.glob(pattern)))
    return seen


def _strip_code_blocks(text: str) -> str:
    """Drop fenced blocks: shell examples cite paths that need not exist."""
    out, fenced = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            out.append(line)
    return "\n".join(out)


def _citations(text: str) -> set[str]:
    found = set()
    for match in CITATION.finditer(_strip_code_blocks(text)):
        raw = match.group("path")
        # Trim a trailing :12 or :12-30 line reference, then an anchor.
        path = re.sub(r":\d+(?:-\d+)?$", "", raw)
        path = path.split("#", 1)[0]
        path = path.rstrip(".,;:)")
        if PLACEHOLDER_CHARS & set(path):
            continue
        # A pytest node ID names a test, not a file to read.
        if "::" in path:
            path = path.split("::", 1)[0]
        # Directory citations are conventions ("drop reports in tests/"),
        # not instructions to open a specific document.
        if path.endswith("/"):
            continue
        if path in ALLOWLIST:
            continue
        found.add(path)
    return found


def _owning_plugin(asset: Path) -> Path | None:
    """Return the plugin root that owns ``asset``, if any."""
    rel = asset.relative_to(REPO_ROOT).parts
    if len(rel) >= 2 and rel[0] == "plugins":
        return REPO_ROOT / "plugins" / rel[1]
    return None


def _tracked_paths() -> frozenset[str]:
    """Every tracked file, plus the directory prefixes leading to one.

    Citations are checked against git's index rather than the working
    tree. Six of them -- `.claude/session-state.md`, `docs/backlog/
    queue.md`, and four more -- are gitignored runtime artifacts: the
    workflows write them, so they sit on any machine that has run the
    workflows and on no fresh checkout. Asking the filesystem meant this
    gate read the developer's machine instead of the repository, passing
    locally and failing in CI for 11 assets at once.

    The masking case is the worse half. Under a working-tree check, any
    untracked file lying at the cited path answers "yes" -- so a genuine
    phantom that happens to collide with local scratch state goes
    unreported, which is the exact defect this gate exists to catch.

    Directory prefixes are included because `_citations` only filters
    tokens ending in a slash; `docs/adr` cites a real directory without
    one, and git lists no directories of its own.
    """
    listing = subprocess.run(
        ["git", "ls-files", "-z"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=True,
    ).stdout
    known = {entry for entry in listing.split("\0") if entry}
    for entry in list(known):
        parts = entry.split("/")
        for depth in range(1, len(parts)):
            known.add("/".join(parts[:depth]))
    return frozenset(known)


TRACKED = _tracked_paths()


def _resolves(citation: str, asset: Path) -> bool:
    """A citation resolves against the repo root or its own plugin.

    Inside `plugins/foo/skills/bar/SKILL.md`, `scripts/x.py` means
    `plugins/foo/scripts/x.py` -- every plugin carries its own scripts/
    and hooks/ directories, and the docs address them unprefixed. Both
    readings are checked so the convention is not reported as a defect.
    """
    if citation in TRACKED:
        return True
    plugin = _owning_plugin(asset)
    if plugin is None:
        return False
    return (plugin / citation).relative_to(REPO_ROOT).as_posix() in TRACKED


def _phantoms(asset: Path) -> list[str]:
    text = asset.read_text(encoding="utf-8", errors="replace")
    return sorted(c for c in _citations(text) if not _resolves(c, asset))


def _capabilities(text: str) -> set[str]:
    """Backticked `plugin:name` refs whose plugin is real.

    An unknown plugin segment means the token was never a capability
    reference: `note:something`, `TODO:fix`, and every `key: value` in
    prose share the shape. Anchoring on a directory that exists keeps
    the gate to references it can actually adjudicate.
    """
    found = set()
    for match in CAPABILITY.finditer(_strip_code_blocks(text)):
        plugin, name = match.group("plugin"), match.group("name")
        if not (REPO_ROOT / "plugins" / plugin).is_dir():
            continue
        ref = f"{plugin}:{name}"
        if ref not in CAPABILITY_ALLOWLIST:
            found.add(ref)
    return found


def _capability_resolves(ref: str) -> bool:
    """A capability is a skill, command, agent, or workflow of its plugin.

    Workflows are the fifth type. A plugin shipping `workflows/name.js`
    makes `/plugin:name` invocable, so a document citing it is citing
    something real; without this arm, the first shipped workflow reads
    as a phantom.
    """
    plugin, name = ref.split(":", 1)
    root = REPO_ROOT / "plugins" / plugin
    return (
        (root / "skills" / name / "SKILL.md").exists()
        or (root / "commands" / f"{name}.md").exists()
        or (root / "agents" / f"{name}.md").exists()
        or (root / "workflows" / f"{name}.js").exists()
    )


def _phantom_capabilities(asset: Path) -> list[str]:
    text = asset.read_text(encoding="utf-8", errors="replace")
    return sorted(c for c in _capabilities(text) if not _capability_resolves(c))


ASSETS = _iter_assets()


def test_assets_are_discovered() -> None:
    """Guard the glob itself: an empty sweep would pass everything."""
    assert len(ASSETS) > 100, f"only {len(ASSETS)} workflow assets found"


def test_capability_references_are_found() -> None:
    """Guard the regex: a pattern matching nothing would pass everything.

    The path gate has ``test_assets_are_discovered`` for the same
    reason. A parametrized sweep over assets that cite no capabilities
    is vacuously green, and so is one whose regex silently stopped
    matching.
    """
    total = sum(len(_capabilities(a.read_text(errors="replace"))) for a in ASSETS)
    assert total > 300, f"only {total} capability references found"


@pytest.mark.parametrize("asset", ASSETS, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_cited_paths_resolve(asset: Path) -> None:
    """Every rooted repo path cited outside a code block must exist."""
    phantoms = _phantoms(asset)
    assert not phantoms, (
        f"{asset.relative_to(REPO_ROOT)} cites "
        f"{len(phantoms)} path(s) that do not exist: " + ", ".join(phantoms)
    )


@pytest.mark.parametrize("asset", ASSETS, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_cited_capabilities_resolve(asset: Path) -> None:
    """Every backticked `plugin:name` must be a real skill, command, or agent."""
    phantoms = _phantom_capabilities(asset)
    assert not phantoms, (
        f"{asset.relative_to(REPO_ROOT)} cites "
        f"{len(phantoms)} capability(ies) that do not exist: " + ", ".join(phantoms)
    )


# --- The third gate: the `Skill(plugin:name)` call form ---------------
#
# `test_cited_capabilities_resolve` above needs the backtick flush
# against the token, so `` `Skill(pensive:bug-review)` `` matches
# neither it nor `scripts/check_skill_graph_drift.py`, which reads the
# call syntax but globs only `plugins/*/skills/*/SKILL.md`. A command
# citing a skill by the call form was adjudicated by nothing.
#
# That gap became load-bearing on this branch. Seventeen commands were
# reduced to a delegation whose entire body is one `Skill(...)` call, so
# an unresolvable reference is no longer a stale cross-link: it is a
# command that does nothing when invoked.

SKILL_GRAPH = REPO_ROOT / "plugins" / "abstract" / "scripts" / "skill_graph.py"


def _load_skill_graph():
    """Import the classifier the drift ratchet runs, rather than copy it.

    ``KNOWN_EXTERNAL_PLUGINS`` and ``_is_placeholder`` decide which
    dangling references are defects and which are cross-marketplace
    links or template text. Two gates holding two copies of that list
    is the failure ``test_discoverability_metadata`` records: its
    private copy of the description cap outlived the rule by months
    while the live hook passed. One definition, imported.

    The module is a script, not an installed package, so it is loaded
    by path; it must be registered in ``sys.modules`` before execution
    because its ``@dataclass`` decorators resolve annotations through
    that entry.
    """
    spec = importlib.util.spec_from_file_location("skill_graph", SKILL_GRAPH)
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"cannot load the reference classifier from {SKILL_GRAPH}. "
            "scripts/check_skill_graph_drift.py runs this same module; if it "
            "has moved, that ratchet and this gate have drifted apart."
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules["skill_graph"] = module
    spec.loader.exec_module(module)
    return module


_SKILL_GRAPH = _load_skill_graph()

# A `Skill(plugin:name)` call, with or without trailing arguments:
# `Skill(abstract:skill-auditor, quiet=true)` names the same target as
# `Skill(pensive:bug-review)`. The bare form `Skill(test-updates)`,
# which omits the plugin, is a separate defect and is not adjudicated
# here -- an unqualified name has no single resolution to check.
INVOCATION = re.compile(
    r"Skill\((?P<plugin>[a-z][a-z0-9-]*):(?P<name>[a-z0-9][a-z0-9-]*)\s*[,)]"
)

# Skills are deliberately absent: `Skill(...)` inside a SKILL.md is
# already the drift ratchet's subject, and a second gate counting the
# same references would put two baselines on one rule.
# The call form reaches further than the path form: a skill invokes a
# sibling skill, and a workflow script carries `Skill(...)` into the
# prompt it hands a subagent. Both are instructions an agent executes,
# so both are in the scope this module's docstring claims.
INVOCATION_GLOBS = (
    "plugins/*/skills/**/*.md",
    "plugins/*/commands/**/*.md",
    "plugins/*/agents/**/*.md",
    "plugins/*/workflows/**/*.js",
    ".claude/rules/*.md",
)

# Losing a lane must not be silent. A single total across every lane
# hides the loss of any one of them: dropping both the agent and rule
# lanes still cleared a global floor of 150, because the command lane
# alone carries more than that. Each lane therefore answers for itself,
# at a floor set below today's count and above zero.
INVOCATION_LANE_FLOORS = {
    "plugins/*/skills/**/*.md": 250,
    "plugins/*/commands/**/*.md": 130,
    "plugins/*/agents/**/*.md": 12,
    "plugins/*/workflows/**/*.js": 1,
    ".claude/rules/*.md": 8,
}


def _iter_invocation_assets() -> list[Path]:
    seen: list[Path] = []
    for pattern in INVOCATION_GLOBS:
        seen.extend(sorted(REPO_ROOT.glob(pattern)))
    return seen


def _invocations(text: str) -> set[str]:
    """Every `plugin:name` invoked through `Skill()`, fences included.

    The path gate strips fenced blocks because a shell example cites
    paths that need not exist. This gate must not: in this repository a
    fenced `Skill(...)` line *is* the instruction. One of the three
    defects caught the first time this gate ran sat inside a fence --
    the sample output in `plugins/attune/commands/validate.md` told the
    user to run a skill that had never existed, and a fence-stripping
    gate would have read that recommendation as decoration. Measured
    across every asset below, keeping fences produced no example-shaped
    false positive.
    """
    found = set()
    for match in INVOCATION.finditer(text):
        plugin, name = match.group("plugin"), match.group("name")
        if _SKILL_GRAPH._is_placeholder(plugin, name):
            continue
        if plugin in _SKILL_GRAPH.KNOWN_EXTERNAL_PLUGINS:
            continue
        found.add(f"{plugin}:{name}")
    return found


def _invocation_resolves(ref: str) -> bool:
    """A `Skill()` target is a skill, a command, or a workflow.

    Agents are excluded on purpose, and that exclusion is the point of
    the arm. The harness lists skills, commands, and workflows to the
    Skill tool and lists agents separately to the Agent tool, so
    `Skill(abstract:skill-auditor)` names a real asset by the wrong
    verb and fails at invocation. `_capability_resolves` accepts agents
    because a backticked `plugin:name` in prose only claims the thing
    exists; a call claims it is callable this way.
    """
    plugin, name = ref.split(":", 1)
    root = REPO_ROOT / "plugins" / plugin
    return (
        (root / "skills" / name / "SKILL.md").exists()
        or (root / "commands" / f"{name}.md").exists()
        or (root / "workflows" / f"{name}.js").exists()
    )


def _phantom_invocations(asset: Path) -> list[str]:
    text = asset.read_text(encoding="utf-8", errors="replace")
    return sorted(c for c in _invocations(text) if not _invocation_resolves(c))


INVOCATION_ASSETS = _iter_invocation_assets()


@pytest.mark.parametrize("pattern", sorted(INVOCATION_LANE_FLOORS))
def test_every_invocation_lane_is_scanned(pattern: str) -> None:
    """Guard each lane separately: a lane matching nothing passes everything.

    The regex guard used to be one total over every lane, which a single
    lane could satisfy on its own. Deleting the agent and rule globs was
    therefore undetectable. Per-lane floors make each glob answer for
    its own contribution.
    """
    assert pattern in INVOCATION_GLOBS, (
        f"lane {pattern} has a floor but is not scanned; "
        "INVOCATION_GLOBS and INVOCATION_LANE_FLOORS must agree"
    )
    assets = sorted(REPO_ROOT.glob(pattern))
    assert set(assets) <= set(INVOCATION_ASSETS), (
        f"lane {pattern} matches files the scanner never collects"
    )
    found = sum(len(_invocations(a.read_text(errors="replace"))) for a in assets)
    floor = INVOCATION_LANE_FLOORS[pattern]
    assert found >= floor, (
        f"lane {pattern} yields {found} Skill() invocations across "
        f"{len(assets)} file(s), below its floor of {floor}"
    )


def test_a_skill_call_on_an_agent_does_not_resolve() -> None:
    """The agent exclusion is the point of this arm, so it is pinned here.

    `_capability_resolves` accepts an agent because backticked prose
    only claims the thing exists. A `Skill()` call claims it is callable
    that way, and the harness lists agents to the Agent tool instead.
    Collapsing this arm into the capability resolver left the whole
    suite green, so the distinction needs its own guard in both
    directions: a real agent must fail, a real skill must pass.
    """
    agent = REPO_ROOT / "plugins" / "abstract" / "agents" / "skill-auditor.md"
    assert agent.exists(), "fixture drifted: pick another real agent"
    assert not _invocation_resolves("abstract:skill-auditor")

    skill = REPO_ROOT / "plugins" / "abstract" / "skills" / "skill-authoring"
    assert (skill / "SKILL.md").exists(), "fixture drifted: pick another skill"
    assert _invocation_resolves("abstract:skill-authoring")


@pytest.mark.parametrize(
    "asset", INVOCATION_ASSETS, ids=lambda p: str(p.relative_to(REPO_ROOT))
)
def test_invoked_skills_resolve(asset: Path) -> None:
    """Every `Skill(plugin:name)` must name something callable that way."""
    phantoms = _phantom_invocations(asset)
    assert not phantoms, (
        f"{asset.relative_to(REPO_ROOT)} invokes "
        f"{len(phantoms)} target(s) that are not callable through Skill(): "
        + ", ".join(phantoms)
    )
