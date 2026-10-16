"""Guard that `make test` in a plugin never rewrites the source tree.

`scripts/run-plugin-tests.sh` runs each plugin through `make test`, and so
does CI. abstract's `test` target listed `format` as a prerequisite, and
`format` runs `ruff format` and `ruff check --fix`. Running the test suite
therefore rewrote abstract's working tree, including uncommitted work that
another session had in flight. A test run must report on the tree, not
change it.

The invariant: no target that `test` depends on, directly, is one of the
rewriting targets. A plugin that wants a formatting gate in `test` uses a
check-only target such as `format-check`.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = REPO_ROOT / "plugins"

#: Targets whose recipes write to the source tree.
REWRITING_TARGETS = {"format", "fmt", "fix", "lint-fix", "format-fix"}


def _test_prerequisites(makefile_text: str) -> set[str]:
    """Direct prerequisites of the `test:` rule, or empty when it has none."""
    match = re.search(r"^test:([^#\n]*)", makefile_text, re.MULTILINE)
    if not match:
        return set()
    return set(match.group(1).split())


@pytest.mark.parametrize(
    "makefile",
    sorted(PLUGINS_DIR.glob("*/Makefile")),
    ids=lambda p: p.parent.name,
)
def test_plugin_test_target_does_not_rewrite_source(makefile: Path) -> None:
    rewriting = _test_prerequisites(makefile.read_text()) & REWRITING_TARGETS

    assert not rewriting, (
        f"{makefile.relative_to(REPO_ROOT)}: `test` depends on {sorted(rewriting)}, "
        "which rewrite files; depend on a check-only target instead"
    )


def test_rewriting_prerequisite_is_detected() -> None:
    text = "test: format lint test-unit ## Run all quality checks\n\t@echo ok\n"

    assert _test_prerequisites(text) & REWRITING_TARGETS == {"format"}


def test_check_only_prerequisite_passes() -> None:
    text = "test: format-check lint test-unit ## Run all quality checks\n"

    assert _test_prerequisites(text) & REWRITING_TARGETS == set()


def test_makefile_without_test_target_has_no_prerequisites() -> None:
    assert _test_prerequisites("lint:\n\truff check .\n") == set()
