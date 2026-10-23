"""The learnings hooks keep aggregating when leyline is not installed.

ADR-0001: a plugin that misses a peer turns that feature off and keeps
the rest. post_learnings_to_discussions imported leyline unguarded, and
both learnings hooks import it in the same try block as the aggregator,
so a missing leyline (or one the old repo-only path could not find in the
install cache) switched aggregation and the insight engine off too.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[2]

_PROBE = """
import importlib.abc
import importlib.util
import sys


class _Block(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in ("leyline", "yaml"):
            raise ModuleNotFoundError(f"No module named {name!r}")
        return None


sys.meta_path.insert(0, _Block())
sys.path.insert(0, sys.argv[1].rsplit("/", 1)[0])
spec = importlib.util.spec_from_file_location("probe_target", sys.argv[1])
module = importlib.util.module_from_spec(spec)
sys.modules["probe_target"] = module
spec.loader.exec_module(module)
print(" ".join(str(getattr(module, n)) for n in sys.argv[2:]))
"""


def _probe(relative: str, *names: str) -> str:
    proc = subprocess.run(
        [sys.executable, "-c", _PROBE, str(PLUGIN / relative), *names],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


@pytest.mark.unit
def test_daily_hook_keeps_aggregation_without_leyline() -> None:
    assert _probe("hooks/aggregate_learnings_daily.py", "_HAS_SCRIPTS") == "True"


@pytest.mark.unit
def test_stop_hook_keeps_insight_engine_without_leyline() -> None:
    assert (
        _probe("hooks/post_learnings_stop.py", "_HAS_SCRIPTS", "_HAS_INSIGHT_ENGINE")
        == "True True"
    )


@pytest.mark.unit
def test_posting_fails_cleanly_without_leyline() -> None:
    """Posting raises the RuntimeError its callers already handle."""
    probe = _PROBE.replace(
        'print(" ".join(str(getattr(module, n)) for n in sys.argv[2:]))',
        "try:\n    module.run_gh_graphql('{ viewer { login } }')\n"
        "except RuntimeError as exc:\n    print('RuntimeError', exc)",
    )
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            probe,
            str(PLUGIN / "scripts/post_learnings_to_discussions.py"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.startswith("RuntimeError")
    assert "leyline" in proc.stdout


@pytest.mark.unit
def test_fallback_gh_error_does_not_catch_unrelated_runtime_errors() -> None:
    """Without leyline, `except _GhError` still catches only gh failures."""
    probe = _PROBE.replace(
        'print(" ".join(str(getattr(module, n)) for n in sys.argv[2:]))',
        "try:\n    raise RuntimeError('unrelated')\n"
        "except module._GhError:\n    print('caught')\n"
        "except RuntimeError:\n    print('not caught')",
    )
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            probe,
            str(PLUGIN / "scripts/post_learnings_to_discussions.py"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "not caught"
