"""Raw-text categories are scored even in a file with no prose words.

invisible_unicode is the one category scanned inside code blocks, because
a fence is where a bidi override hides (Trojan Source). A markdown file
whose only content is such a block had zero prose words, so score_text
returned before scanning and the gate printed "no prose files scanned"
and exited 0. Math review finding B5.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "slop_score.py"
# Built with chr() so this file carries no bidi character of its own.
_RLO, _LRI, _PDI = chr(0x202E), chr(0x2066), chr(0x2069)
BIDI_FENCE = f"```python\naccess = 'user{_RLO} {_LRI}# admin{_PDI} {_LRI}'\n```\n"


def _load():
    spec = importlib.util.spec_from_file_location("slop_score", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_a_hidden_override_in_a_prose_free_file_is_found() -> None:
    score = _load().score_text(BIDI_FENCE)
    assert any(f.category.endswith("invisible_unicode") for f in score.findings)
    assert score.score > 3.0


def test_the_gate_fails_a_file_that_is_only_a_trojan_fence(tmp_path: Path) -> None:
    doc = tmp_path / "only-code.md"
    doc.write_text(BIDI_FENCE)
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--threshold", "3.0", str(doc)],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )
    assert completed.returncode != 0, completed.stdout


def test_a_prose_free_file_without_hidden_characters_still_scores_zero() -> None:
    assert _load().score_text("```python\nx = 1\n```\n").score == 0.0
