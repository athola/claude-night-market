"""Every mutmut caller pins a release that still takes its flags.

mutmut 3 removed ``--paths-to-mutate`` and ``--tests-dir``. Click exits 2
on an unknown option, and the mutation workflow read exit 2 as "survivors
found", so the weekly run went green without mutating anything. The ten
plugin ``mutation-test`` targets ran whatever mutmut was on PATH, and with
a current one they failed with a usage error.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMON_MK = REPO_ROOT / "plugins" / "abstract" / "config" / "make" / "common.mk"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "mutation-testing.yml"


def _mutmut_makefiles() -> list[Path]:
    return sorted(
        p
        for p in (REPO_ROOT / "plugins").glob("*/Makefile")
        if "mutmut" in p.read_text().lower()
    )


def test_discovery_finds_the_mutation_targets() -> None:
    assert len(_mutmut_makefiles()) >= 10


def test_the_shared_command_pins_mutmut_below_3() -> None:
    assert re.search(
        r"^MUTMUT := .*--with 'mutmut<3' mutmut$", COMMON_MK.read_text(), re.M
    )


def test_no_plugin_runs_an_unpinned_mutmut() -> None:
    bare = [
        f"{p.parent.name}: {line.strip()}"
        for p in _mutmut_makefiles()
        for line in p.read_text().splitlines()
        if re.search(r"(?<![\w$(])mutmut run", line)
    ]
    assert not bare, bare


def test_the_workflow_installs_a_pinned_mutmut() -> None:
    text = WORKFLOW.read_text()
    assert "'mutmut<3'" in text
    assert not re.search(r"pip install mutmut(?!<)", text)


def test_the_workflow_fails_a_run_that_produced_no_mutants() -> None:
    text = WORKFLOW.read_text()
    assert "junitxml" in text
    assert "no mutants" in text
