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

import re
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
