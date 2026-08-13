"""Test: `make lint` never rewrites tracked markdown.

Ruff 0.16 began formatting Python code blocks inside Markdown. The
Makefile's `lint` target runs `ruff format --config pyproject.toml
plugins/`, so the upgrade silently turned a read-only quality gate into
a repo-wide markdown rewriter: one run touched 197 tracked `.md` files
across every plugin, changing only cosmetics inside fences (a trailing
comma added to `metadata={"files": 10}`, and so on).

That matters beyond the noise. `make lint` is a prerequisite step in
`sanctum:git-workspace-review`, `sanctum:pr-prep`, and the pre-commit
workflow, and `pr-prep` Step 2.5 asks reviewers to reject "formatting
changes mixed with logic changes". The gate was manufacturing the
defect its own checklist screens for.

Ruff also does not own markdown here. `.claude/rules/markdown-formatting.md`
sets this repo's markdown conventions (80-column prose wrapping, ATX
headings), and skill documentation deliberately shows illustrative and
sometimes deliberately-wrong snippets that a formatter should leave
alone.

Feature: ruff formats Python, and leaves documentation to the docs rules.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"

# A snippet ruff would reformat if it looked at markdown at all: the
# call is split across lines without a magic trailing comma, which is
# exactly the edit that appeared in all 197 churned files.
UNFORMATTED_MARKDOWN = """# Probe

Prose above the fence.

```python
logger.log_usage(
    tokens=5000,
    success=True
)
```

Prose below the fence.
"""


@pytest.fixture
def markdown_probe(tmp_path: Path) -> Path:
    """A throwaway markdown file holding reformattable Python."""
    probe = tmp_path / "probe.md"
    probe.write_text(UNFORMATTED_MARKDOWN, encoding="utf-8")
    return probe


def _ruff_format(target: Path) -> subprocess.CompletedProcess[str]:
    """Run the repo's exact format command against one path."""
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "format",
            "--config",
            str(PYPROJECT),
            str(target),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )


def test_ruff_format_leaves_markdown_untouched(markdown_probe: Path) -> None:
    """GIVEN a markdown file whose fenced Python is unformatted
    WHEN the repo's own `ruff format --config pyproject.toml` runs on it
    THEN the file is byte-identical afterwards
    AND `make lint` therefore cannot rewrite tracked documentation.
    """
    before = markdown_probe.read_text(encoding="utf-8")
    result = _ruff_format(markdown_probe)
    after = markdown_probe.read_text(encoding="utf-8")

    assert after == before, (
        "ruff reformatted a markdown file. `make lint` runs this exact "
        "command over plugins/, so this rewrites every tracked .md in the "
        "repo (197 files when ruff 0.16 shipped markdown support). Keep "
        "*.md in the ruff `extend-exclude` list in pyproject.toml. "
        f"ruff said: {result.stdout.strip() or result.stderr.strip()}"
    )


def test_pyproject_excludes_markdown_from_ruff() -> None:
    """GIVEN pyproject.toml configures ruff for the whole repo
    WHEN the markdown exclusion is removed from it
    THEN this fails, since the behavioural test above depends on a
    config setting that is easy to drop during an unrelated edit.
    """
    config = PYPROJECT.read_text(encoding="utf-8")
    assert '"*.md"' in config, (
        'pyproject.toml no longer excludes "*.md" from ruff. Without it, '
        "`make lint` reformats Python inside every markdown fence in "
        "plugins/, mixing cosmetic churn into unrelated changes."
    )


def test_python_formatting_still_works(tmp_path: Path) -> None:
    """GIVEN the markdown exclusion could be written too broadly
    WHEN a genuinely unformatted .py file is passed to ruff format
    THEN it is still reformatted, proving the exclusion narrowed the
    file types ruff touches rather than disabling formatting outright.
    """
    probe = tmp_path / "probe.py"
    probe.write_text("x = {'a':1,   'b':2}\n", encoding="utf-8")
    before = probe.read_text(encoding="utf-8")

    _ruff_format(probe)

    assert probe.read_text(encoding="utf-8") != before, (
        "ruff stopped formatting Python files. The markdown exclusion "
        "was written too broadly and disabled the gate it was meant to "
        "narrow."
    )
