"""Regression tests for the make plugin-check dogfooding harness.

Feature: The dogfooding harness must not silently hang or mask failures

As a maintainer
I want plugin-check to surface real defects instead of hiding them
So that a green run is trustworthy

These are invariant-encoding tests (test-updates Phase 2.5). Each one
encodes a fix from the 2026-06-28 dogfooding pass, distilled in
docs/quality-gates.md ("Dogfooding Harness Lessons"). If one fails,
someone reverted a fix: read that section before changing the assertion.

Coverage of that pass's findings, stated exactly rather than implied:

============  =========================================================
F-A, F-B      Guarded. Generalized to "every path a plugin Makefile
              names must exist", which covers the two stale paths that
              were found and the next one nobody has typed yet.
F-C           Guarded. Generalized to "no plugin Makefile may collapse
              a failing test run into a success message".
F-G           Guarded, twice: the non-fetching probe and the per-plugin
              timeout that bounds the loop.
F-D, F-E      Not guarded. Both were reported with a proposed fix that
              was never implemented, so there is no invariant to hold.
              F-D is mission-state evidence going stale against a
              changing index; F-E is the root coverage.xml reporting 0%
              on 17 modules that are simply out of its scope.
F-F           Not guarded, and never will be. It records that no
              browser surface exists in this repo, so the Playwright
              track has no target here. An observation about the
              environment is not a defect and has nothing to regress.
============  =========================================================

The first three tests were literal-string canaries: they asserted one
exact substring was present or absent. A canary catches the specific
typo somebody already fixed. It does not catch the same defect
reintroduced with different wording, which is what happened to F-C --
the canary watched for "No tests found", that string went away, and ten
targets kept masking pytest failures behind "Not applicable" instead.
Each canary is now the invariant it was standing in for.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PLUGINS = REPO / "plugins"


def _read(rel: str) -> str:
    return (REPO / rel).read_text()


def _plugin_makefiles() -> list[Path]:
    return sorted(PLUGINS.glob("*/Makefile"))


def _logical_lines(text: str) -> list[str]:
    """Join backslash continuations so one recipe reads as one line."""
    return re.sub(r"\\\n\s*", " ", text).splitlines()


# A relative path token: ../ followed by one or more segments. Excludes
# tokens carrying a make variable or a glob, which cannot be resolved
# statically, and anchors on the left so ../../plugins/ is read whole
# rather than as a bare ../plugins/.
_RELATIVE_PATH = re.compile(r"(?<![\w$*/])(\.\.(?:/[\w.-]+)+/?)")

# A path handed to a linter or type checker inside a plugin Makefile.
_TOOL_PATH = re.compile(r"\b(?:ruff (?:check|format)|mypy|bandit -r)\s+([\w./-]+/)")

# A test run whose failure is swallowed by an `|| echo`. `|| true` on a
# `rm -rf` in a clean target is a different thing and is not matched:
# the pattern requires a pytest invocation on the same logical line.
_MASKED_TEST_RUN = re.compile(r"pytest\b[^\n]*\|\|\s*(?:\\\s*)?echo")


class TestHarnessFilesExist:
    """The scans below are vacuous if they match no files."""

    @pytest.mark.unit
    def test_plugin_makefiles_are_found(self) -> None:
        """
        GIVEN the plugins directory
        WHEN scanning for Makefiles
        THEN several are found

        Without this, every scan in this module passes on an empty list.
        """
        makefiles = _plugin_makefiles()
        assert len(makefiles) > 5, f"expected many plugin Makefiles, got {makefiles}"


class TestReferencedPathsExist:
    """Scenario: a Makefile may not name a path that is not there (F-A, F-B).

    Both original findings were one stale path each: ``../conservation/``
    in conserve (the directory is ``conserve``) and ``parseltongue/`` in
    parseltongue (the source is under ``src/``). Both exited clean by
    printing a benign message, so the harness reported a skip where there
    was a defect. Asserting the two literals catches those two typos;
    asserting that referenced paths resolve catches the class.
    """

    @pytest.mark.unit
    def test_sibling_paths_resolve(self) -> None:
        """
        GIVEN a plugin Makefile referencing a path outside its directory
        WHEN the path is resolved against that Makefile's directory
        THEN it must exist
        """
        missing = [
            f"{makefile.relative_to(REPO)}: {token}"
            for makefile in _plugin_makefiles()
            for token in _RELATIVE_PATH.findall(makefile.read_text())
            if not (makefile.parent / token).exists()
        ]
        assert not missing, (
            "plugin Makefiles reference paths that do not exist:\n  "
            + ("\n  ".join(missing))
        )

    @pytest.mark.unit
    def test_lint_and_typecheck_targets_resolve(self) -> None:
        """
        GIVEN a plugin Makefile handing a directory to ruff, mypy or bandit
        WHEN that directory is resolved against the plugin root
        THEN it must exist

        This is F-B's class: a linter pointed at a missing directory
        reports nothing and exits clean, which reads exactly like clean
        code.
        """
        missing = [
            f"{makefile.relative_to(REPO)}: {target}"
            for makefile in _plugin_makefiles()
            for target in _TOOL_PATH.findall(makefile.read_text())
            if "$" not in target and not (makefile.parent / target).exists()
        ]
        assert not missing, "lint or typecheck targets point at missing paths:\n  " + (
            "\n  ".join(missing)
        )


class TestFailuresAreNotMasked:
    """Scenario: a failing test run may not be reported as a skip (F-C)."""

    @pytest.mark.unit
    def test_no_makefile_collapses_a_failing_test_run_into_a_message(self) -> None:
        """
        GIVEN a plugin Makefile target that runs pytest
        WHEN the run fails
        THEN the failure must propagate, not become an echoed message

        `pytest ... || echo "Not applicable"` exits 0 on a real failure.
        To skip when nothing matched, branch on pytest's exit code 5
        ("no tests collected") and re-raise every other status.
        """
        masked = [
            f"{makefile.relative_to(REPO)}: {line.strip()[:90]}"
            for makefile in _plugin_makefiles()
            for line in _logical_lines(makefile.read_text())
            if not line.lstrip().startswith("#") and _MASKED_TEST_RUN.search(line)
        ]
        assert not masked, (
            "these targets turn a failing test run into a success message; "
            "branch on exit code 5 instead:\n  " + "\n  ".join(masked)
        )


class TestHarnessCannotStall:
    """Scenario: no step in the harness may hang unbounded (F-G)."""

    @pytest.mark.unit
    def test_scry_playwright_probe_does_not_hang_offline(self) -> None:
        """
        GIVEN scry checks playwright availability in its dependency probe
        WHEN the probe runs via npx
        THEN it must use --no-install so an absent package fails fast,
        not a bare npx fetch that hangs offline

        Stated as the literal flag because the flag is the mechanism:
        --no-install is what makes npm exec refuse to reach the network.
        """
        assert "npx --no-install playwright" in _read("plugins/scry/Makefile"), (
            "npx --no-install dropped from scry playwright probe (finding F-G)"
        )

    @pytest.mark.unit
    def test_root_plugin_check_bounds_each_plugin(self) -> None:
        """
        GIVEN make plugin-check iterates every plugin in sequence
        WHEN one plugin's check hangs
        THEN a per-plugin timeout must bound it so the run cannot stall
        """
        # Assert the invariant (each per-plugin check is time-bounded), not
        # the specific number: ``timeout 240`` would still satisfy it. The
        # pattern binds the timeout to the per-plugin make invocation.
        assert re.search(
            r"timeout \d+ \$\(MAKE\) -C \$\$plugin plugin-check", _read("Makefile")
        ), "per-plugin timeout removed from root plugin-check loop (finding F-G)"
