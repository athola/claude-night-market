"""Every attune scaffold path picks the same default Python version.

``attune init`` defaulted to 3.9 (C-001) while ``arch-init``, ``upgrade``
and the template variables used 3.10, so the same request scaffolded two
different baselines depending on the command.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from attune_init import _build_parser  # noqa: E402 - after sys.path insert
from template_engine import get_default_variables  # noqa: E402 - after sys.path insert

COMMAND_DOC = Path(__file__).parent.parent / "commands" / "project-init.md"


def _template_default() -> str:
    return inspect.signature(get_default_variables).parameters["python_version"].default


def test_init_cli_default_matches_the_template_default() -> None:
    """The init CLI and the template variables agree."""
    assert _build_parser().get_default("python_version") == _template_default()


def test_project_init_doc_states_the_default_the_cli_uses() -> None:
    """/attune:project-init names the default the CLI applies."""
    expected = f"Python version (default: {_template_default()})"
    assert expected in COMMAND_DOC.read_text(encoding="utf-8")
