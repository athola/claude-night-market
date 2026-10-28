#!/usr/bin/env python3
"""PreToolUse hook: surface blast radius context on PR creation.

When `gh pr create` is run, analyze the blast radius of the
branch's changes and add risk context as additionalContext.

The branch's changes are everything since its merge base with the PR
base (``--base``/``-B``, else the remote default branch named by
``origin/HEAD``). At PR time the work is committed, so a diff against
HEAD would be empty.
"""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from _vendored_leyline_sibling_plugins import sibling_plugin_dir


def _find_graph_db() -> Path | None:
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / ".gauntlet" / "graph.db"
        if candidate.exists():
            return candidate
    return None


def _find_gauntlet_src() -> Path | None:
    """Find the gauntlet src directory for imports."""
    # Try via plugin directory structure
    # Beside this plugin in the repo, or the newest cached install.
    gauntlet = sibling_plugin_dir(__file__, "gauntlet")
    candidate = (gauntlet or Path(__file__).resolve().parents[2] / "gauntlet") / "src"
    if (candidate / "gauntlet").is_dir():
        return candidate
    return None


#: Per git call. hooks.json gives this hook 5s in total, and the blast
#: radius analysis still needs its own git calls after these two.
_GIT_TIMEOUT_SECONDS = 1.0


class _NoMergeBaseError(RuntimeError):
    """The PR base or its merge base with HEAD could not be determined."""


def _git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        raise _NoMergeBaseError(f"git {args[0]} could not run: {exc!r}") from exc
    if result.returncode != 0:
        msg = f"git {' '.join(args)} exited with {result.returncode}"
        raise _NoMergeBaseError(msg)
    return result.stdout.strip()


def _explicit_base(command: str) -> str | None:
    """Return the branch named by ``--base``/``-B`` in the gh command."""
    tokens = shlex.split(command)
    for i, token in enumerate(tokens):
        if token.startswith("--base="):
            return token.split("=", 1)[1]
        if token in ("--base", "-B") and i + 1 < len(tokens):
            return tokens[i + 1]
    return None


def _merge_base(command: str) -> str:
    """Return the commit the PR's changes are measured from."""
    branch = _explicit_base(command)
    if branch is None:
        base = _git("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    else:
        base = f"origin/{branch}"
    return _git("merge-base", "HEAD", base)


def _analyze(db_path: Path, base_ref: str) -> dict[str, Any] | None:
    """Run gauntlet's blast radius analysis, or None when it cannot run."""
    gauntlet_src = _find_gauntlet_src()
    if gauntlet_src and str(gauntlet_src) not in sys.path:
        sys.path.insert(0, str(gauntlet_src))

    try:
        import gauntlet.blast_radius as _br
        import gauntlet.graph as _gg

        with _gg.GraphStore(str(db_path)) as graph:
            report: dict[str, Any] = _br.analyze_changes(
                graph, base_ref=base_ref, weights=_br.load_weights(db_path.parent)
            )
    except (ImportError, ModuleNotFoundError):
        return None
    except (OSError, ValueError) as exc:
        print(f"pr_blast_radius: analysis failed: {exc}", file=sys.stderr)
        return None

    if "error" in report:
        print(f"pr_blast_radius: analysis skipped: {report['error']}", file=sys.stderr)
        return None

    return report


def main(hook_input: dict[str, Any]) -> dict[str, Any] | None:
    """Surface blast radius analysis when creating a PR."""
    tool_input = hook_input.get("tool_input", {})
    command = tool_input.get("command", "")

    if "gh pr create" not in command and "gh pr submit" not in command:
        return None

    db_path = _find_graph_db()
    if db_path is None:
        return None

    try:
        base_ref = _merge_base(command)
    except (_NoMergeBaseError, ValueError) as exc:
        # ValueError: shlex could not split an unbalanced quote.
        print(f"pr_blast_radius: no merge base: {exc}", file=sys.stderr)
        return None

    report = _analyze(db_path, base_ref)
    if report is None:
        return None

    overall = report.get("overall_risk", "none")
    total = report.get("total_affected", 0)
    untested = report.get("untested_functions", [])
    priorities = report.get("review_priorities", [])[:5]

    lines = [f"PR blast radius: {overall} risk, {total} nodes affected"]

    if priorities:
        lines.append("Top risk nodes:")
        scores = report.get("risk_scores", {})
        for node_dict in priorities:
            qn = node_dict.get("qualified_name", "?")
            short = qn.rsplit("::", 1)[-1] if "::" in qn else qn
            risk = scores.get(qn, 0)
            lines.append(f"  {risk:.2f} {short}")

    if untested:
        lines.append(f"{len(untested)} untested function(s) in blast radius")

    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": "\n".join(lines),
        }
    }


if __name__ == "__main__":
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        hook_input = {}

    output = main(hook_input)
    if output is not None:
        print(json.dumps(output))
