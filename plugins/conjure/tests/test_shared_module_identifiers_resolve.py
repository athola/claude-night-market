"""Every identifier the shared module cites must exist in conjure's code.

``shared-shell-execution.md`` is loaded by six provider skills, so a
backticked name that resolves to nothing is read as an instruction by
whichever agent follows it. ``.claude/rules/slop-scan-for-docs.md``
Layer 0 makes an unresolvable backticked identifier a categorical fail.

This gate exists because the class recurred. NB1 (discussion #675) found
the module documenting three classes and a method nobody wrote. The
commit that fixed it, ``cecc79c8``, added ``Delegator._select_service``
-- another name that existed nowhere -- and that survived to be found
again as B11 (discussion #697). A doc-only repair cannot stop a doc-only
regression; only a gate reads the file on every commit.

Scope is deliberately the whole ``plugins/conjure/scripts/`` tree rather
than ``delegation_executor.py`` alone, because the module legitimately
cites ``install_command_for`` and ``usage_logger`` from sibling modules.
"""

from __future__ import annotations

import re
from pathlib import Path

CONJURE_ROOT = Path(__file__).resolve().parent.parent
SHARED_MODULE = (
    CONJURE_ROOT / "skills" / "delegation-core" / "shared-shell-execution.md"
)
SCRIPTS_ROOT = CONJURE_ROOT / "scripts"

# Backticked tokens that look like Python: they carry an underscore or a
# dotted path. Bare lowercase words are prose or CLI names, and bare
# CamelCase is ambiguous enough to leave to the reader.
_IDENTIFIER_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)`")

# Names owned by something outside this repository. ``GOOGLE_CLOUD_PROJECT``
# is quoted from the Gemini CLI's own error text, so it is a real name
# that correctly appears in no file we author.
_EXTERNAL_NAMES = frozenset({"GOOGLE_CLOUD_PROJECT"})


def _cited_identifiers() -> set[str]:
    text = SHARED_MODULE.read_text(encoding="utf-8")
    return {
        name
        for name in _IDENTIFIER_RE.findall(text)
        if ("_" in name or "." in name) and name not in _EXTERNAL_NAMES
    }


def _conjure_source() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(SCRIPTS_ROOT.rglob("*.py"))
    )


def test_every_cited_identifier_exists_in_conjure_scripts() -> None:
    """Reject a backticked identifier that resolves to nothing.

    Scenario: The shared module names a function, class, or constant
    Given six provider skills load this module as instruction
    When each backticked Python-shaped identifier is looked up
    Then every one resolves to a name defined under scripts/

    A dotted citation is checked on its final segment. ``Delegator.
    _ordered_candidates`` passes when ``_ordered_candidates`` is defined,
    which is the claim a reader acts on: that the method is there to call.
    """
    source = _conjure_source()
    phantoms = sorted(
        name
        for name in _cited_identifiers()
        if not re.search(rf"\b{re.escape(name.split('.')[-1])}\b", source)
    )
    assert not phantoms, (
        f"{SHARED_MODULE.name} cites {len(phantoms)} identifier(s) that "
        f"exist nowhere under plugins/conjure/scripts/: {', '.join(phantoms)}"
    )
