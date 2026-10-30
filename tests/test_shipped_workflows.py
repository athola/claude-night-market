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
    "unproven",
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

    def test_a_split_vote_with_an_unheard_lens_is_unverified(self) -> None:
        # The unheard lens could have made it two of three.
        out = _run_workflow(
            self.SCRIPT,
            self._agent(
                [
                    {"refuted": False, "reason": "r"},
                    {"refuted": True, "reason": "r"},
                    None,
                ]
            ),
            {"dimensions": ["bugs"]},
        )
        assert out["result"]["confirmed"] == []
        assert len(out["result"]["unverified"]) == 1


class TestUnprovenFindingsAreNamed:
    """A verifier that returned null leaves its finding open, not refuted."""

    def test_gate_audit_names_a_suspect_whose_proof_returned_null(self) -> None:
        out = _run_workflow(
            PLUGINS / "egregore" / "workflows" / "gate-audit.js",
            "if (opts.label.startsWith('read:'))"
            " return { gate: 'g', suspects: [{ check: 'c', why: 'w' }] };"
            "return null;",
            {"gates": ["plugins/egregore/scripts/scope.py"]},
        )
        assert out["result"]["bypasses"] == []
        assert len(out["result"]["unproven"]) == 1

    def test_skill_audit_names_a_finding_whose_verdict_returned_null(self) -> None:
        out = _run_workflow(
            PLUGINS / "abstract" / "workflows" / "skill-audit.js",
            "if (opts.label === 'audit:discovery')"
            " return { findings: [{ skill: 's', claim: 'c', evidence: 'e' }] };"
            "if (opts.label.startsWith('audit:')) return { findings: [] };"
            "return null;",
            {"skills": ["abstract:skill-authoring"]},
        )
        assert out["result"]["findings"] == []
        assert len(out["result"]["unverified"]) == 1


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


class TestSurfaceCheckSelection:
    """A surface selection that checks nothing refuses instead of passing."""

    SCRIPT = PLUGINS / "phantom" / "workflows" / "surface-check.js"
    # Dispatching any agent fails the run, so a refusal is proven to be
    # returned before the fan-out rather than after it.
    NO_DISPATCH = "throw new Error('agent dispatched for ' + opts.label);"

    def test_a_surfaces_value_that_is_not_a_list_is_refused(self) -> None:
        out = _run_workflow(self.SCRIPT, self.NO_DISPATCH, {"surfaces": "pointer"})
        assert out["result"]["started"] is False
        assert out["result"]["reason"] == "surfaces-not-a-list"
        assert out["result"]["next"]

    def test_an_empty_surface_list_is_refused(self) -> None:
        out = _run_workflow(self.SCRIPT, self.NO_DISPATCH, {"surfaces": []})
        assert out["result"]["started"] is False
        assert out["result"]["reason"] == "no-surfaces-selected"
        assert out["result"]["next"]

    def test_a_list_of_only_unknown_surfaces_is_refused_and_named(self) -> None:
        out = _run_workflow(self.SCRIPT, self.NO_DISPATCH, {"surfaces": ["screnshot"]})
        assert out["result"]["started"] is False
        assert out["result"]["reason"] == "no-surfaces-selected"
        assert out["result"]["unknown"] == ["screnshot"]

    def test_a_known_surface_in_the_list_is_the_only_one_checked(self) -> None:
        out = _run_workflow(
            self.SCRIPT,
            "return { surface: opts.label, working: true, evidence: 'seen' };",
            {"surfaces": ["pointer"]},
        )
        assert out["result"]["started"] is True
        assert [v["surface"] for v in out["result"]["verdicts"]] == ["check:pointer"]


# ---------------------------------------------------------------------------
# Every workflow, run with every agent failing.
# ---------------------------------------------------------------------------

#: Arguments that make each script fan out, and the text that must name
#: what was dropped when no agent answers. A new workflow fails
#: ``test_every_workflow_has_a_dead_agent_case`` until it is listed here.
_DEAD_AGENT_CASES: dict[str, tuple[dict, str]] = {
    "abstract": ({"skills": ["abstract:skill-audit"]}, "no audit from discovery"),
    "archetypes": (
        {"candidates": ["hexagonal", "layered"], "requirements": "a small API"},
        "no score for hexagonal, layered",
    ),
    "attune": (
        {"topics": [{"name": "deploy", "brief": "how deploys run"}]},
        "0 of 1 skills authored",
    ),
    "cartograph": (
        {"root": ".", "lenses": ["architecture"]},
        "no diagram from architecture",
    ),
    "conjure": ({"providers": ["gemini"]}, "no verdict from gemini"),
    "conserve": ({"areas": ["plugins/conserve"]}, "no scan from plugins/conserve"),
    "egregore": ({"gates": ["quality"]}, "no reading for quality"),
    "gauntlet": (
        {"subsystems": ["plugins/gauntlet"]},
        "no corpus from plugins/gauntlet",
    ),
    "herald": ({"claim": "done", "evidence": "tests pass"}, "no judge returned"),
    "hookify": ({"root": ".", "categories": ["git"]}, "no sweep from git"),
    "imbue": ({"claims": ["tests pass"]}, "not checked: tests pass"),
    "leyline": ({"plugins": ["leyline"]}, "no report from leyline"),
    "memory-palace": ({"question": "q", "palaces": ["p"]}, "no result from p"),
    "minister": ({"milestones": ["v1"], "repo": "o/r"}, "no pulse from v1"),
    "oracle": ({"skills": ["a:b"]}, "no score for a:b"),
    "parseltongue": (
        {"paths": ["x.py"], "lenses": ["lint"]},
        "no report from lint",
    ),
    "pensive": ({}, "no review from bugs"),
    "phantom": ({"surfaces": ["screenshot"]}, "no verdict for screenshot"),
    "sanctum": ({"slice": "s"}, "failed: recreate"),
    "scribe": ({"docs": ["README.md"]}, "no report from critical"),
    "scry": ({"flows": [{"name": "f", "steps": ["open"]}]}, "no result for f"),
    "spec-kit": (
        {"spec": "spec.md", "constitution": "c.md"},
        "no reading from testability",
    ),
    "tome": ({"topic": "t", "channels": ["code"]}, "0 of 1 channels"),
}


def test_every_workflow_has_a_dead_agent_case() -> None:
    """A workflow added without a dead-agent case would go unexercised."""
    plugins = {script.parent.parent.name for script in _workflow_scripts()}
    assert plugins == set(_DEAD_AGENT_CASES)


@pytest.mark.parametrize("plugin", sorted(_DEAD_AGENT_CASES))
def test_a_workflow_whose_agents_all_fail_says_what_it_dropped(plugin: str) -> None:
    """Every agent returning nothing is reported, not passed off as a result.

    GIVEN a workflow run with arguments that make it fan out
    WHEN every agent call returns null
    THEN the script finishes without throwing
    AND its log, or its result's failed stage, names what went unanswered

    The regex check above reads a script's text. This runs it, which is
    the only way the branch that reports a dropped agent ever executes.
    """
    args, expected = _DEAD_AGENT_CASES[plugin]
    (script,) = (PLUGINS / plugin / "workflows").glob("*.js")

    out = _run_workflow(script, "return null;", args)

    result = out["result"] if isinstance(out["result"], dict) else {}
    reported = list(out["log"]) + [f"failed: {result.get('failed')}"]
    assert any(expected in line for line in reported), reported


# ---------------------------------------------------------------------------
# Selections, labels and synthesis stages (B1 review, 2026-10-28).
# ---------------------------------------------------------------------------


def _script(plugin: str) -> Path:
    (script,) = (PLUGINS / plugin / "workflows").glob("*.js")
    return script


_NO_DISPATCH = "throw new Error('agent dispatched for ' + opts.label);"

#: plugin -> (the arg that narrows its roster, the other args it needs)
_SELECTIONS: dict[str, tuple[str, dict]] = {
    "parseltongue": ("lenses", {"paths": ["x.py"]}),
    "cartograph": ("lenses", {"root": "."}),
    "pensive": ("dimensions", {}),
    "hookify": ("categories", {"root": "."}),
    "conjure": ("providers", {}),
    "archetypes": ("candidates", {"requirements": "a small API"}),
}


class TestRosterSelection:
    """A selection that runs nothing refuses rather than reading as clean.

    A misspelled lens used to dispatch zero agents and return empty
    findings with an empty missing list, which is a clean review.
    """

    @pytest.mark.parametrize("plugin", sorted(_SELECTIONS))
    def test_a_selection_that_is_not_a_list_is_refused(self, plugin: str) -> None:
        key, extra = _SELECTIONS[plugin]
        out = _run_workflow(_script(plugin), _NO_DISPATCH, {**extra, key: "a,b"})
        assert out["result"]["started"] is False
        assert out["result"]["reason"] == f"{key}-not-a-list"
        assert out["result"]["next"]

    @pytest.mark.parametrize("plugin", sorted(_SELECTIONS))
    def test_an_empty_selection_is_refused(self, plugin: str) -> None:
        key, extra = _SELECTIONS[plugin]
        out = _run_workflow(_script(plugin), _NO_DISPATCH, {**extra, key: []})
        assert out["result"]["started"] is False
        assert out["result"]["reason"] == f"no-{key}-selected"

    @pytest.mark.parametrize("plugin", sorted(_SELECTIONS))
    def test_only_unknown_names_are_refused_and_named(self, plugin: str) -> None:
        key, extra = _SELECTIONS[plugin]
        out = _run_workflow(_script(plugin), _NO_DISPATCH, {**extra, key: ["nosuch"]})
        assert out["result"]["started"] is False
        assert out["result"]["reason"] == f"no-{key}-selected"
        assert out["result"]["unknown"] == ["nosuch"]


def test_rule_sweep_default_roster_is_every_catalog_category() -> None:
    """The header promises every rule in the catalog."""
    on_disk = sorted(
        p.name
        for p in (PLUGINS / "hookify" / "skills" / "rule-catalog" / "rules").iterdir()
        if p.is_dir()
    )
    out = _run_workflow(
        _script("hookify"),
        "return { category: 'x', stale: [] };",
        {"root": "."},
    )
    assert sorted(out["result"]["coverage"]["swept"]) == on_disk


def test_paradigm_panel_accepts_short_names_and_reads_the_real_skill() -> None:
    """`hexagonal` must reach Skill(archetypes:architecture-paradigm-hexagonal)."""
    out = _run_workflow(
        _script("archetypes"),
        "globalThis.p = globalThis.p || []; globalThis.p.push(prompt);"
        "if (opts.label === 'compare') return 'c';"
        "return { paradigm: 'x', score: 5, fits: [], costs: [], prompts: globalThis.p };",
        {"requirements": "r", "candidates": ["hexagonal"]},
    )
    ranked = out["result"]["ranked"]
    assert ranked[0]["paradigm"] == "hexagonal"
    assert (
        "Skill(archetypes:architecture-paradigm-hexagonal)" in ranked[0]["prompts"][0]
    )


def test_paradigm_panel_known_list_matches_the_skills_on_disk() -> None:
    names = sorted(
        p.name.removeprefix("architecture-paradigm-")
        for p in (PLUGINS / "archetypes" / "skills").iterdir()
        if p.name.startswith("architecture-paradigm-")
    )
    content = _script("archetypes").read_text(encoding="utf-8")
    block = re.search(r"const PARADIGMS = \[(.*?)\]", content, re.DOTALL)
    assert block, "paradigm-panel.js must list PARADIGMS"
    assert sorted(re.findall(r"'([\w-]+)'", block.group(1))) == names


#: One stage-1 answer every fan-out schema accepts. Every label field
#: holds WRONG, the string an agent invents, so a script that trusts the
#: agent's label instead of its own roster shows it.
_UNIVERSAL = {
    "lens": "WRONG",
    "layer": "WRONG",
    "area": "WRONG",
    "subsystem": "WRONG",
    "plugin": "WRONG",
    "palace": "WRONG",
    "milestone": "WRONG",
    "skill": "WRONG",
    "paradigm": "WRONG",
    "category": "WRONG",
    "provider": "WRONG",
    "findings": [
        {
            "location": "a.py:1",
            "problem": "p",
            "doc": "d",
            "requirement": "r",
            "kind": "dead-code",
            "evidence": "e",
            "blocking": True,
            "lines": 3,
        },
        {
            "location": "b.py:2",
            "problem": "q",
            "doc": "d",
            "requirement": "s",
            "kind": "duplication",
            "evidence": "f",
            "blocking": False,
            "lines": 9,
        },
    ],
    "entries": [{"concept": "c", "whatItDoes": "w", "whyItExists": "y"}],
    "violations": [],
    "satisfied": ["s"],
    "stale": [],
    "hits": [{"note": "n", "relevance": 1, "excerpt": "e"}],
    "openIssues": 1,
    "closedIssues": 0,
    "risk": "at-risk",
    "score": 5,
    "basis": "b",
    "source": "oracle",
    "fits": [],
    "costs": ["c"],
    "mermaid": "m",
    "nodes": ["n"],
    "callable": True,
    "cause": "ready",
}

#: plugin -> (args that reach the synthesis stage, its agent label)
_SYNTHESIS: dict[str, tuple[dict, str]] = {
    "archetypes": ({"requirements": "r", "candidates": ["layered"]}, "compare"),
    "cartograph": ({"root": "."}, "reconcile"),
    "conserve": ({"areas": ["a"]}, "consolidate"),
    "gauntlet": ({"subsystems": ["a", "b"]}, "merge"),
    "leyline": ({"plugins": ["a", "b"]}, "contracts"),
    "memory-palace": ({"question": "q", "palaces": ["p"]}, "rank"),
    "minister": ({"milestones": ["v1"]}, "roll-up"),
    "oracle": ({"skills": ["a/SKILL.md"]}, "calibrate"),
    "parseltongue": ({"paths": ["x.py"]}, "merge"),
    "scribe": ({"docs": ["README.md"]}, "rank"),
    "spec-kit": ({"spec": "s.md"}, "gaps"),
}


def _universal_agent(dead_label: str = "") -> str:
    return (
        f"if (opts.label === {json.dumps(dead_label)}) return null;"
        f"return {json.dumps(_UNIVERSAL)};"
    )


@pytest.mark.parametrize("plugin", sorted(_SYNTHESIS))
def test_a_dead_synthesis_agent_is_named_not_skipped(plugin: str) -> None:
    """GIVEN stage one answered WHEN the synthesis agent returns null
    THEN the result names the stage as failed and the log says so.

    The deliberate skip path returns the same null, so without the name a
    dead synthesis agent reads as a run with nothing to synthesize.
    """
    args, label = _SYNTHESIS[plugin]
    out = _run_workflow(_script(plugin), _universal_agent(label), args)
    assert out["result"]["failed"] == label
    assert any(label in line for line in out["log"]), out["log"]


@pytest.mark.parametrize("plugin", sorted(_SYNTHESIS))
def test_a_live_synthesis_agent_names_no_failure(plugin: str) -> None:
    args, _ = _SYNTHESIS[plugin]
    out = _run_workflow(_script(plugin), _universal_agent(), args)
    assert out["result"]["failed"] is None


#: plugin -> (args, path to the per-item label list, the labels expected)
_LABELS: dict[str, tuple[dict, tuple[str, ...], list[str]]] = {
    "parseltongue": (
        {"paths": ["x.py"], "lenses": ["lint", "types"]},
        ("coverage", "reviewed"),
        ["lint", "types"],
    ),
    "spec-kit": (
        {"spec": "s.md"},
        ("coverage", "read"),
        ["testability", "consistency", "coverage", "constitution"],
    ),
    "hookify": (
        {"root": ".", "categories": ["git", "python"]},
        ("coverage", "swept"),
        ["git", "python"],
    ),
    "leyline": ({"plugins": ["a", "b"]}, ("coverage", "checked"), ["a", "b"]),
    "memory-palace": (
        {"question": "q", "palaces": ["p1", "p2"]},
        ("coverage", "searched"),
        ["p1", "p2"],
    ),
    "scribe": (
        {"docs": ["README.md"]},
        ("coverage", "reviewed"),
        ["critical", "economy", "audience", "sentence", "evidence"],
    ),
}


@pytest.mark.parametrize("plugin", sorted(_LABELS))
def test_labels_come_from_the_roster_not_the_agent(plugin: str) -> None:
    """`reviewed` and `missing` must share one vocabulary: the roster's."""
    args, path, expected = _LABELS[plugin]
    out = _run_workflow(_script(plugin), _universal_agent(), args)
    node = out["result"]
    for key in path:
        node = node[key]
    assert node == expected


def test_doc_sweep_counts_critical_findings_whatever_the_agent_calls_its_layer() -> (
    None
):
    out = _run_workflow(_script("scribe"), _universal_agent(), {"docs": ["README.md"]})
    assert len(out["result"]["critical"]) == 2
    assert out["log"][-1].endswith("2 critical")


def test_provider_sweep_matches_verdicts_by_roster_position() -> None:
    """A probe that writes `Gemini` is still the gemini probe."""
    out = _run_workflow(
        _script("conjure"),
        "return { provider: 'Gemini', callable: true, cause: 'ready' };",
        {"providers": ["gemini"]},
    )
    assert out["result"]["ready"] == ["gemini"]
    assert out["result"]["unreported"] == []


def test_bloat_sweep_keeps_the_area_and_ranks_by_lines_saved() -> None:
    out = _run_workflow(
        _script("conserve"),
        "if (opts.label === 'consolidate') return { duplications: [] };"
        "const lines = opts.label === 'scan:b' ? 50 : 5;"
        "return { area: 'WRONG', findings: [{ kind: 'dead-code', location: 'x', evidence: 'e', lines }] };",
        {"areas": ["a", "b"]},
    )
    findings = out["result"]["findings"]
    assert [(f["area"], f["lines"]) for f in findings] == [("b", 50), ("a", 5)]


def test_quality_bench_keeps_an_unavailable_score_out_of_the_distribution() -> None:
    out = _run_workflow(
        _script("oracle"),
        "return { skill: 's', basis: 'daemon not running', source: 'unavailable' };",
        {"skills": ["a/SKILL.md"]},
    )
    assert out["result"]["scores"] == []
    assert out["result"]["unscored"] == ["a/SKILL.md"]
    assert out["result"]["calibration"] is None


def test_capture_set_moves_a_capture_with_no_asset_to_failed() -> None:
    out = _run_workflow(
        _script("scry"),
        "return { flow: opts.label, captured: true };",
        {"flows": [{"name": "f"}]},
    )
    assert out["result"]["assets"] == []
    assert len(out["result"]["failed"]) == 1


class TestSanctumAnalysisBranches:
    """A dead analyst and an empty answer are different outcomes."""

    RECREATION = {"steps": ["s"], "friction": ["f"], "components": []}

    def _agent(self, analysis: object) -> str:
        return (
            f"if (opts.label === 'recreate') return {json.dumps(self.RECREATION)};"
            f"if (opts.label === 'analyse') return {json.dumps(analysis)};"
            "return null;"
        )

    def test_a_dead_analyst_says_re_run(self) -> None:
        out = _run_workflow(_script("sanctum"), self._agent(None), {"slice": "s"})
        assert out["result"]["failed"] == "analyse"
        assert "Re-run" in out["result"]["next"]

    def test_no_options_says_the_slice_may_not_need_one(self) -> None:
        out = _run_workflow(
            _script("sanctum"), self._agent({"options": []}), {"slice": "s"}
        )
        assert out["result"]["failed"] == "analyse"
        assert "may not need one" in out["result"]["next"]


_ARGS_IN_PROSE = re.compile(r"\bargs\.(\w+)")


@pytest.mark.parametrize(
    "script", _workflow_scripts(), ids=lambda p: p.parent.parent.name
)
def test_every_arg_when_to_use_advertises_is_read(script: Path) -> None:
    """The skill listing shows whenToUse to the model verbatim.

    An advertised arg that no code reads is passed and silently ignored.
    """
    content = script.read_text(encoding="utf-8")
    when = re.search(r"whenToUse:\s*\n?\s*(['\"`])(.*?)(?<!\\)\1", content, re.DOTALL)
    assert when, f"{script}: no whenToUse"
    advertised = set(_ARGS_IN_PROSE.findall(when.group(2)))
    read = set(_INPUT_FIELD.findall(content))
    assert advertised <= read, sorted(advertised - read)


# ---------------------------------------------------------------------------
# PR #992 review: result shapes and argument guards (G6).
# ---------------------------------------------------------------------------


def test_paradigm_panel_names_the_score_stage_when_every_scorer_died() -> None:
    """The early return carries `failed` like the final one does."""
    out = _run_workflow(
        _script("archetypes"),
        "return null;",
        {"candidates": ["layered"], "requirements": "a small API"},
    )
    assert out["result"]["failed"] == "score"
    assert out["result"]["unscored"] == ["layered"]


class TestQualityBenchSeparatesDeadScorersFromADownDaemon:
    """A dead scorer agent must not send the operator to fix the daemon."""

    def test_dead_scorers_are_dropped_and_the_daemon_is_not_blamed(self) -> None:
        out = _run_workflow(_script("oracle"), "return null;", {"skills": ["a:b"]})
        assert out["result"]["dropped"] == ["a:b"]
        assert out["result"]["unavailable"] == []
        assert not any("daemon" in line for line in out["log"]), out["log"]

    def test_an_unavailable_daemon_is_named(self) -> None:
        out = _run_workflow(
            _script("oracle"),
            "return { skill: 's', basis: 'down', source: 'unavailable' };",
            {"skills": ["a:b"]},
        )
        assert out["result"]["unavailable"] == ["a:b"]
        assert out["result"]["dropped"] == []
        assert any("daemon" in line for line in out["log"]), out["log"]


@pytest.mark.parametrize("lenses", [0, -1, 4, 1.5, "2"])
def test_unified_review_refuses_a_lens_count_outside_the_roster(lenses) -> None:
    """`lenses: 0` verified nothing and reported zero surviving findings."""
    out = _run_workflow(_script("pensive"), _NO_DISPATCH, {"lenses": lenses})
    assert out["result"]["started"] is False
    assert out["result"]["reason"] == "lenses-out-of-range"
    assert out["result"]["next"]


def test_unified_review_runs_with_one_lens() -> None:
    out = _run_workflow(_script("pensive"), "return { findings: [] };", {"lenses": 1})
    assert out["result"].get("started") is not False
    assert any("1 of 3 lenses" in line for line in out["log"]), out["log"]
