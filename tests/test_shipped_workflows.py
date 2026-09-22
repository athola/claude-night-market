"""Every plugin ships a workflow, and every workflow parses.

`claude-code-plugin-reference` documented `workflows/` as "the asset
type this repo does not ship yet". Four plugins had one by the time
review reached that heading, and the heading was still saying no.

Two gates here. The coverage gate says every plugin in `plugins/` ships
at least one script, because the review asked for workflows across all
of them. The format gate pins the contract a script has to satisfy
before the runtime will start it, which is worth a test precisely
because a violation fails at dispatch time rather than at author time:

- `meta` is the first statement, preceded only by comments, and is a
  pure literal carrying `name` and `description`.
- The body calls none of `Date.now()`, `Math.random()`, argless
  `new Date()` or `import()`. The first three throw, because a run has
  to be replayable from its journal on resume. `import()` fails the
  script before the run starts.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS = REPO_ROOT / "plugins"

META_START = re.compile(r"^export\s+const\s+meta\s*=", re.MULTILINE)

#: Each maps to a documented runtime failure, not a style preference.
FORBIDDEN_CALLS = (
    ("Date.now(", "throws: a run must replay identically from its journal"),
    ("Math.random(", "throws: same reason"),
    ("new Date()", "throws: pass a timestamp through args instead"),
    ("import(", "the script fails to load before the run starts"),
)


def _plugin_dirs() -> list[Path]:
    return sorted(
        p
        for p in PLUGINS.iterdir()
        if p.is_dir() and (p / ".claude-plugin" / "plugin.json").is_file()
    )


def _workflow_scripts() -> list[Path]:
    return sorted(
        script
        for plugin in _plugin_dirs()
        for script in (plugin / "workflows").glob("*.js")
    )


@pytest.mark.parametrize("plugin", _plugin_dirs(), ids=lambda p: p.name)
def test_every_plugin_ships_at_least_one_workflow(plugin: Path) -> None:
    """Coverage: the review asked for workflows across all plugins."""
    scripts = sorted((plugin / "workflows").glob("*.js"))

    assert scripts, (
        f"{plugin.name} ships no workflow. Add one under "
        f"plugins/{plugin.name}/workflows/ encoding that plugin's fan-out."
    )


@pytest.mark.parametrize(
    "script", _workflow_scripts(), ids=lambda p: f"{p.parents[1].name}/{p.name}"
)
def test_meta_is_first_and_carries_name_and_description(script: Path) -> None:
    """The runtime reads meta before running anything else."""
    content = script.read_text()
    match = META_START.search(content)

    assert match is not None, f"{script} has no `export const meta =`"

    preamble = content[: match.start()].splitlines()
    offenders = [
        line
        for line in preamble
        if line.strip() and not line.strip().startswith(("//", "/*", "*", "*/"))
    ]
    assert not offenders, (
        f"{script}: only comments may precede meta, found: {offenders[:3]}"
    )

    meta = content[match.end() : content.index("\n}\n", match.end())]
    assert "name:" in meta, f"{script}: meta has no name"
    assert "description:" in meta, f"{script}: meta has no description"


@pytest.mark.parametrize(
    "script", _workflow_scripts(), ids=lambda p: f"{p.parents[1].name}/{p.name}"
)
def test_body_avoids_calls_the_runtime_rejects(script: Path) -> None:
    """Each forbidden call maps to a documented runtime failure."""
    content = script.read_text()
    found = [f"{call} ({why})" for call, why in FORBIDDEN_CALLS if call in content]

    assert not found, f"{script} calls: {'; '.join(found)}"


@pytest.mark.parametrize(
    "script", _workflow_scripts(), ids=lambda p: f"{p.parents[1].name}/{p.name}"
)
def test_meta_name_matches_the_filename(script: Path) -> None:
    """Invocation is `/plugin:name`, where name comes from meta."""
    content = script.read_text()
    declared = re.search(r"name:\s*'([^']+)'", content)

    assert declared is not None, f"{script}: meta.name is not a string literal"
    assert declared.group(1) == script.stem, (
        f"{script.name} declares meta.name '{declared.group(1)}'. The harness "
        "invokes by meta.name, so a mismatch makes the filename a lie."
    )


#: How a script establishes that an input field may be absent: a default
#: (`||`, `??`), a ternary on the field itself, or a type test. A field
#: reached through any of these is safe to read when `args` is empty.
_GUARDED = (
    r"input\.{field}\s*(?:\|\||\?\?)",
    r"input\.{field}\s*\?[^?]",
    r"Array\.isArray\(\s*input\.{field}\s*\)",
    r"typeof\s+input\.{field}",
)

_INPUT_FIELD = re.compile(r"\binput\.(\w+)")


def _unguarded_input_fields(content: str) -> list[str]:
    """Input fields the script reads with no default and no type test.

    Whitespace is collapsed first because a ternary guard routinely sits
    on the line after the field it guards, and a line-by-line read calls
    that unguarded.
    """
    flat = " ".join(content.split())
    unguarded = []
    for field in sorted(set(_INPUT_FIELD.findall(flat))):
        if not any(
            re.search(pattern.format(field=re.escape(field)), flat)
            for pattern in _GUARDED
        ):
            unguarded.append(field)
    return unguarded


@pytest.mark.parametrize(
    "script", _workflow_scripts(), ids=lambda p: f"{p.parents[1].name}/{p.name}"
)
def test_a_script_that_cannot_start_refuses_instead_of_dispatching(
    script: Path,
) -> None:
    """GIVEN a shipped workflow that requires input to run.

    WHEN it is started without that input
    THEN it returns a refusal naming the command that would supply it

    `claude-code-plugin-reference` states this as one of two conventions
    every shipped script holds, and until now only the other one
    (forbidden calls) was gated. A convention documented and unenforced
    is the defect that put the workflow section's own heading out of
    date, so it gets a test rather than a sentence.

    The shape: return `{started: false, reason, next}` rather than fan
    out agents against nothing. `next` is the load-bearing field. A
    refusal that does not say what to run leaves the caller exactly
    where they were, and the caller here is a model that will otherwise
    improvise the missing input.

    A script with no required input has nothing to refuse. Which
    scripts those are is decided by `_unguarded_input_fields` below,
    from how the script reads its input. Deciding it from the presence
    of the `started` flag, which is what this gate did first, was
    circular: a script that needed input and forgot to refuse was
    exempted for having forgotten, and six scripts were skipped by a
    rule that could only ever agree with them.
    """
    content = script.read_text()

    if "started: false" not in content and "started: true" not in content:
        unguarded = _unguarded_input_fields(content)
        assert not unguarded, (
            f"{script.name} has no refusal branch, so it must run on no "
            "input at all, but it reads these fields without a default or "
            f"a type test: {', '.join(unguarded)}"
        )
        return

    assert "started: false" in content, (
        f"{script} tracks a started flag but has no refusal branch"
    )
    assert "reason:" in content, f"{script}: a refusal must carry a reason"
    assert "next:" in content, (
        f"{script}: a refusal must name what would supply the missing input, "
        "or the caller improvises it"
    )


@pytest.mark.parametrize(
    "script", _workflow_scripts(), ids=lambda p: f"{p.parents[1].name}/{p.name}"
)
def test_every_workflow_has_a_row_in_the_capabilities_reference(
    script: Path,
) -> None:
    """GIVEN a workflow script shipped under a plugin.

    WHEN a reader looks it up in the capabilities reference
    THEN a row names it and its plugin

    Adding the table without this gate would trade one drift surface
    for another: the reference already carries skills, commands, agents
    and hooks, and each of those is kept honest by a check. A workflow
    absent from the table is invisible to anyone who reads the table
    rather than the directory, which is most people.
    """
    reference = (
        REPO_ROOT / "book" / "src" / "reference" / "capabilities-reference.md"
    ).read_text()
    name = re.search(r"name:\s*'([^']+)'", script.read_text()).group(1)
    plugin = script.parents[1].name

    assert f"| `{name}` | [{plugin}]" in reference, (
        f"{plugin}:{name} ships but has no row in capabilities-reference.md"
    )


@pytest.mark.unit
def test_doc_sweep_accepts_python_as_a_review_target() -> None:
    """Scenario: the sweep says what a .py target means.

    `scripts/slop_score.py` reads a Python path as its comments and
    docstrings, so the workflow can review one. A reviewer told only
    "documents" will either skip the file or review its code, and the
    second is worse: notation in a docstring is code that happens to
    sit in prose, and flagging it wastes the reader's time.
    """
    script = (
        Path(__file__).resolve().parents[1]
        / "plugins"
        / "scribe"
        / ("workflows/doc-sweep.js")
    )
    content = script.read_text(encoding="utf-8")

    assert ".py" in content, (
        "doc-sweep must say that a .py file is a valid review target"
    )
    assert "docstrings" in content, (
        "doc-sweep must say a .py document is its comments and docstrings"
    )
    assert "notation" in content.lower(), (
        "doc-sweep must tell the sentence reviewer to leave notation alone"
    )


_AGENT_TYPE_LITERAL = re.compile(
    r"""agentType:\s*(['"])([A-Za-z0-9_-]+):([a-z0-9-]+)\1"""
)


@pytest.mark.parametrize(
    "script", _workflow_scripts(), ids=lambda p: p.parent.parent.name
)
def test_every_literal_agent_type_names_a_shipped_agent(script: Path) -> None:
    """Every ``agentType: 'plugin:name'`` literal resolves to an agent file.

    tome pinned its own workflow table to its agent files after finding
    the table was a fifth copy of the channel-to-agent mapping (ADR-0024).
    Eleven scripts name plugin agents and nothing checked any of them: a
    renamed agent degrades the dispatch to the default agent and the
    workflow still reports success. Variable references such as
    ``agentType: d.agentType`` are not literals and are not checked, and
    neither are the harness's own types (``general-purpose``, ``Explore``),
    which carry no ``plugin:`` prefix and so never match the pattern.
    """
    content = script.read_text(encoding="utf-8")
    for _, plugin, agent in _AGENT_TYPE_LITERAL.findall(content):
        agent_file = PLUGINS / plugin / "agents" / f"{agent}.md"
        assert agent_file.is_file(), (
            f"{script.relative_to(REPO_ROOT)} dispatches {plugin}:{agent} but "
            f"{agent_file.relative_to(REPO_ROOT)} does not exist"
        )


def test_the_agent_type_guard_sees_the_scripts_that_name_agents() -> None:
    """The guard is only worth having if it matches the roster it protects."""
    naming = [
        s
        for s in _workflow_scripts()
        if _AGENT_TYPE_LITERAL.search(s.read_text(encoding="utf-8"))
    ]
    assert len(naming) >= 10, [s.parent.parent.name for s in naming]


#: A fan-out result whose nulls are removed. ``filter(Boolean)`` is the
#: common spelling; tome writes ``filter((r) => r && r.result)``, and the
#: guard used to see only the first, so the exemplar it cited was skipped.
_NULL_DROP = re.compile(
    r"\.filter\(\s*Boolean\s*\)"
    r"|\.filter\(\s*\(?(\w+)\)?\s*=>\s*(?:!!)?\1\s*(?:\)|&&|!==?\s*null)"
    r"|\?\?\s*\[\]"
)
#: ADR-0025 Decision 1 vocabulary: the names a workflow gives to what it
#: dropped. ``unchecked`` is in the ADR and was missing here.
_DROP_NAMES = (
    "failed",
    "missing",
    "unread",
    "unreported",
    "dropped",
    "unscored",
    "unchecked",
    "unreviewed",
    "unheard",
    "unverified",
)
#: The name must be assigned or returned as a key, not merely present:
#: "failed" inside a prompt string is how three scripts passed the old guard.
_NAMED_DROP = re.compile(
    r"\b(?:const|let)\s+(" + "|".join(_DROP_NAMES) + r")\b"
    r"|(?<![\w.'\"])(" + "|".join(_DROP_NAMES) + r")\s*:(?!:)"
)


def _null_drop_sites(content: str) -> int:
    return len(_NULL_DROP.findall(content))


def _named_drops(content: str) -> set[str]:
    return {a or b for a, b in _NAMED_DROP.findall(content)}


@pytest.mark.parametrize(
    "script", _workflow_scripts(), ids=lambda p: p.parent.parent.name
)
def test_a_script_that_drops_null_agents_reports_which_ones(script: Path) -> None:
    """Every null-drop site must have a named list of what it dropped.

    A subagent that dies returns null, and dropping nulls makes it
    indistinguishable from one that ran and found nothing. In a review
    workflow that turns a document that fails outright into a clean
    pass; in herald's panel it moved the verdict (ADR-0025). One name
    per drop site: attune's inner lens fan-out passed the old guard on
    the outer fan-out's ``failed`` while dropping reviews unnamed.
    """
    content = script.read_text(encoding="utf-8")
    sites = _null_drop_sites(content)
    if sites == 0:
        assert "agent(" not in content or "parallel(" not in content, (
            f"{script.relative_to(REPO_ROOT)} fans out agents but the guard "
            "found no null-drop site; add its idiom to _NULL_DROP"
        )
        pytest.skip("script has no fan-out and never filters null agent results")
    names = _named_drops(content)
    assert len(names) >= sites, (
        f"{script.relative_to(REPO_ROOT)} drops null agent results at {sites} "
        f"site(s) but names only {sorted(names) or 'nothing'} "
        f"(one of {', '.join(_DROP_NAMES)} assigned or returned per site)"
    )


class TestDropGuardSelfCheck:
    """The guard is only worth having if it rejects the idioms it claims to."""

    def test_tome_idiom_without_a_name_is_rejected(self) -> None:
        synthetic = (
            "const kept = returned.filter((r) => r && r.result)\nreturn { kept }\n"
        )
        assert _null_drop_sites(synthetic) == 1
        assert _named_drops(synthetic) == set()

    def test_a_drop_word_inside_a_prompt_does_not_count(self) -> None:
        synthetic = "agent('report what failed')\nconst v = checked.filter(Boolean)\n"
        assert _null_drop_sites(synthetic) == 1
        assert _named_drops(synthetic) == set()

    def test_assigned_and_returned_names_count(self) -> None:
        synthetic = (
            "const v = checked.filter(Boolean)\nconst missing = a.filter((x, i) => !checked[i])\n"
            "return { v, unheard: 2 }\n"
        )
        assert _named_drops(synthetic) == {"missing", "unheard"}

    def test_every_shipped_fan_out_is_seen(self) -> None:
        seen = [
            s
            for s in _workflow_scripts()
            if _null_drop_sites(s.read_text(encoding="utf-8"))
        ]
        assert len(seen) >= 20, [s.parent.parent.name for s in seen]


# ---------------------------------------------------------------------------
# Running a script for real, under node, with the runtime stubbed.
# ---------------------------------------------------------------------------

_RUNTIME_SHIM = """
const __log = [];
const log = (m) => __log.push(String(m));
const phase = () => {};
const parallel = async (thunks) => Promise.all(thunks.map((t) => t()));
const pipeline = async (items, first, second) => {
  const out = [];
  for (const item of items) {
    const r = await first(item);
    out.push(await second(r, item));
  }
  return out;
};
"""


def _run_workflow(script: Path, agent_js: str, args: dict) -> dict:
    """Execute a workflow script under node with ``agent`` supplied by the test.

    ``agent_js`` is the body of ``async (prompt, opts) => { ... }``. The
    script's ``export`` is stripped and its body wrapped in an async
    function, which is the shape the Workflow runtime gives it.
    """
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    body = script.read_text(encoding="utf-8").replace(
        "export const meta", "const meta", 1
    )
    program = (
        _RUNTIME_SHIM
        + f"const args = {json.dumps(args)};\n"
        + f"const agent = async (prompt, opts) => {{ {agent_js} }};\n"
        + "(async () => {\n"
        + body
        + "\n})().then((result) => console.log(JSON.stringify({ result, log: __log })))"
        + ".catch((e) => { console.error(e && e.stack || e); process.exit(3); });\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "workflow.mjs"
        path.write_text(program, encoding="utf-8")
        run = subprocess.run(
            [node, str(path)], capture_output=True, text=True, timeout=60, check=False
        )
    assert run.returncode == 0, run.stderr
    return json.loads(run.stdout)


class TestUnifiedReviewVerification:
    """Two dead lenses must not let the third confirm a finding alone."""

    SCRIPT = PLUGINS / "pensive" / "workflows" / "unified-review.js"
    FINDING = {"title": "t", "file": "a.py", "line": 1, "severity": "minor", "why": "w"}

    def _agent(self, verify_returns: list) -> str:
        return (
            f"const finding = {json.dumps(self.FINDING)};"
            f"const verdicts = {json.dumps(verify_returns)};"
            "globalThis.__n = globalThis.__n || 0;"
            "if (opts.label.startsWith('review:')) return { findings: [finding] };"
            "return verdicts[globalThis.__n++ % verdicts.length];"
        )

    def test_a_finding_heard_by_one_of_three_lenses_is_unverified(self) -> None:
        out = _run_workflow(
            self.SCRIPT,
            self._agent([None, None, {"refuted": False, "reason": "r"}]),
            {"dimensions": ["bugs"]},
        )
        assert out["result"]["confirmed"] == []
        unverified = out["result"]["unverified"]
        assert len(unverified) == 1
        assert unverified[0]["unheard"] == 2

    def test_a_majority_of_the_roster_confirms(self) -> None:
        out = _run_workflow(
            self.SCRIPT,
            self._agent(
                [
                    {"refuted": False, "reason": "r"},
                    {"refuted": False, "reason": "r"},
                    {"refuted": True, "reason": "r"},
                ]
            ),
            {"dimensions": ["bugs"]},
        )
        assert len(out["result"]["confirmed"]) == 1
        assert out["result"]["unverified"] == []


class TestNullAgentsAreNamed:
    """A capture or surface agent that returns null is listed, not lost."""

    def test_scry_names_the_flow_whose_agent_returned_null(self) -> None:
        out = _run_workflow(
            PLUGINS / "scry" / "workflows" / "capture-set.js",
            "if (opts.label === 'capture:dead') return null;"
            "return { captured: true, asset: opts.label + '.gif', reason: '' };",
            {"flows": [{"name": "live"}, {"name": "dead"}]},
        )
        assert out["result"]["dropped"] == ["dead"]
        assert out["result"]["failed"] == []
        assert out["result"]["assets"] == ["capture:live.gif"]

    def test_phantom_names_the_surface_whose_agent_returned_null(self) -> None:
        out = _run_workflow(
            PLUGINS / "phantom" / "workflows" / "surface-check.js",
            "if (opts.label === 'check:screenshot') return null;"
            "return { working: true, detail: '' };",
            {},
        )
        assert "screenshot" in out["result"]["missing"]
        assert out["result"]["broken"] == []
