"""Pre-commit gate hook for the gauntlet plugin.

Reads hook input from stdin (JSON), checks for a pass token, and either
allows the commit or denies it with a challenge prompt.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# Allow importing gauntlet modules when run as a hook script.
_src_path = Path(__file__).parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from gauntlet.challenges import generate_challenge, select_challenge_type
from gauntlet.knowledge_store import KnowledgeStore
from gauntlet.progress import ProgressTracker

# Graph-aware analysis (optional -- degrade gracefully)
try:
    __import__("gauntlet.blast_radius")
    __import__("gauntlet.graph")
    _GRAPH_AVAILABLE = True
except ImportError:
    _GRAPH_AVAILABLE = False

# ---------------------------------------------------------------------------
# Pass-token helpers
# ---------------------------------------------------------------------------

_TOKEN_FILENAME = "pass_token.json"  # nosec B105 - filename, not a password


def write_pass_token(
    gauntlet_dir: Path, staged_hash: str, ttl_seconds: int = 300
) -> None:
    """Write a one-time pass token to state/pass_token.json."""
    state_dir = gauntlet_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    expires_at = (
        datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(seconds=ttl_seconds)
    ).isoformat()
    token = {"staged_hash": staged_hash, "expires_at": expires_at}
    (state_dir / _TOKEN_FILENAME).write_text(json.dumps(token))


def check_pass_token(gauntlet_dir: Path, staged_hash: str) -> bool:
    """Return True if a valid token exists for *staged_hash*, then delete it.

    A token is valid when:
    - The file exists.
    - The stored hash matches *staged_hash*.
    - The token has not expired.

    The token is deleted on a successful check (one-time use).
    """
    token_path = gauntlet_dir / "state" / _TOKEN_FILENAME
    if not token_path.exists():
        return False

    try:
        data = json.loads(token_path.read_text())
    except (json.JSONDecodeError, OSError):
        return False

    if data.get("staged_hash") != staged_hash:
        return False

    expires_at_str = data.get("expires_at", "")
    try:
        expires_at = datetime.datetime.fromisoformat(expires_at_str)
    except ValueError:
        return False

    now = datetime.datetime.now(datetime.timezone.utc)
    if now >= expires_at:
        token_path.unlink(missing_ok=True)
        return False

    # Valid — consume the token.
    token_path.unlink(missing_ok=True)
    return True


# ---------------------------------------------------------------------------
# Challenge generation
# ---------------------------------------------------------------------------


def generate_challenge_for_files(
    gauntlet_dir: Path, files: list[str], developer_id: str
) -> Any | None:
    """Generate a challenge for *files* using the developer's progress.

    Returns a Challenge object, or None if no knowledge entries match.
    """
    store = KnowledgeStore(gauntlet_dir)
    entries = store.query(files=files)
    if not entries:
        return None

    tracker = ProgressTracker(gauntlet_dir)
    progress = tracker.get_or_create(developer_id)
    entry = tracker.select_entry(progress, entries)
    challenge_type = select_challenge_type(progress)
    return generate_challenge(entry, challenge_type)


# ---------------------------------------------------------------------------
# Internal helpers (patchable in tests)
# ---------------------------------------------------------------------------


def _get_gauntlet_dir() -> Path | None:
    """Return the .gauntlet directory for the current working directory."""
    cwd = Path(os.getcwd())
    candidate = cwd / ".gauntlet"
    if candidate.is_dir():
        return candidate
    return None


def _get_staged_hash() -> str:
    """Return a hash of the currently staged file tree."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        return hashlib.sha256(result.stdout.strip().encode()).hexdigest()[:12]
    except subprocess.CalledProcessError:
        return ""


def _get_developer_id() -> str:
    """Return the git user email, falling back to 'unknown'."""
    try:
        result = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() or "unknown"
    except subprocess.CalledProcessError:
        return "unknown"


def _load_config(gauntlet_dir: Path) -> dict[str, Any]:
    """Load config.yaml (preferred) or config.json from the gauntlet directory."""
    try:
        from yaml import (
            YAMLError,
            safe_load,
        )
    except ImportError:
        pass
    else:
        yaml_path = gauntlet_dir / "config.yaml"
        if yaml_path.exists():
            try:
                data = safe_load(yaml_path.read_text())
                if isinstance(data, dict):
                    return data
            except (OSError, YAMLError):
                pass

    config_path = gauntlet_dir / "config.json"
    if config_path.exists():
        try:
            return json.loads(config_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _get_staged_files() -> list[str] | None:
    """Return a list of staged file paths, or None on git failure."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        return [f for f in result.stdout.strip().splitlines() if f]
    except subprocess.CalledProcessError:
        return None


# ---------------------------------------------------------------------------
# Graph-aware blast radius check
# ---------------------------------------------------------------------------


def _graph_staleness_warning(
    gauntlet_dir: Path,
    default_threshold_hours: float = 24.0,
) -> str | None:
    """Warn if graph.db is older than threshold.

    Threshold is configurable via .gauntlet/config.json:
    {"stale_threshold_hours": 12}
    """
    db_path = gauntlet_dir / "graph.db"
    if not db_path.exists():
        return None

    threshold = default_threshold_hours
    config_path = gauntlet_dir / "config.json"
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text())
            threshold = float(data.get("stale_threshold_hours", threshold))
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            pass

    try:
        mtime = db_path.stat().st_mtime
    except OSError:
        return None
    age_hours = (time.time() - mtime) / 3600

    if age_hours <= threshold:
        return None

    hours_display = int(age_hours)
    return (
        f"Graph is {hours_display}h old (threshold: {int(threshold)}h). "
        f"Run `/gauntlet-graph build` to refresh."
    )


def _graph_risk_context(gauntlet_dir: Path) -> str | None:
    """Run blast radius analysis and return context if high-risk changes found.

    Returns a warning string for high-risk commits, or None if the graph
    is unavailable or risk is low.
    """
    if not _GRAPH_AVAILABLE:
        return None

    db_path = gauntlet_dir / "graph.db"
    if not db_path.exists():
        return None

    try:
        from gauntlet.blast_radius import (
            analyze_changes as _analyze,
        )
        from gauntlet.graph import (
            GraphStore as _GS,
        )

        graph = _GS(str(db_path))
        report = _analyze(graph, base_ref="HEAD")
        graph.close()
    except Exception:
        return None

    overall = report.get("overall_risk", "none")
    if overall in ("none", "low"):
        return None

    # Build a concise warning
    lines = [f"Graph blast radius: {overall} risk"]
    priorities = report.get("review_priorities", [])[:5]
    for node_dict in priorities:
        qn = node_dict.get("qualified_name", "?")
        short = qn.rsplit("::", 1)[-1] if "::" in qn else qn
        risk = report.get("risk_scores", {}).get(qn, 0)
        lines.append(f"  {risk:.2f} {short}")

    untested = report.get("untested_functions", [])
    if untested:
        lines.append(f"  {len(untested)} untested function(s) affected")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main(hook_input: dict[str, Any]) -> dict[str, Any] | None:
    """Process a PreToolUse hook event.

    Returns:
    - None to pass through (no decision).
    - hookSpecificOutput with permissionDecision "allow" to allow.
    - hookSpecificOutput with permissionDecision "deny" to block.
    - {"additionalContext": ...} to nudge without blocking.
    """
    tool_input = hook_input.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command.startswith("git commit"):
        return None

    gauntlet_dir = _get_gauntlet_dir()
    if gauntlet_dir is None:
        return None

    config = _load_config(gauntlet_dir)
    mode = config.get("precommit", {}).get("mode", "gate")

    if mode == "off":
        return None

    staged_hash = _get_staged_hash()
    if check_pass_token(gauntlet_dir, staged_hash):
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
            }
        }

    # Graph-aware checks (non-blocking, adds context)
    risk_context = _graph_risk_context(gauntlet_dir)
    stale_warning = _graph_staleness_warning(gauntlet_dir)
    if stale_warning:
        risk_context = (
            f"{risk_context}\n{stale_warning}" if risk_context else stale_warning
        )

    # No valid token — generate a challenge.
    staged_files = _get_staged_files()
    if staged_files is None:
        if mode == "gate":
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        "Gauntlet: unable to read staged files (git failure)."
                    ),
                }
            }
        return None

    developer_id = _get_developer_id()
    challenge = generate_challenge_for_files(gauntlet_dir, staged_files, developer_id)

    if challenge is None:
        # No knowledge entries — still surface risk context if present.
        if risk_context:
            return {"additionalContext": risk_context}
        return None

    # Persist pending challenge so the skill can present it.
    state_dir = gauntlet_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "pending_challenge.json").write_text(
        json.dumps(challenge.to_dict(), indent=2)
    )

    risk_section = f"\n\n{risk_context}" if risk_context else ""
    prompt_text = (
        f"Gauntlet challenge required before commit.\n\n"
        f"{challenge.prompt}\n\n"
        f"Answer via: gauntlet answer <your response>\n"
        f"Challenge ID: {challenge.id}"
        f"{risk_section}"
    )

    if mode == "nudge":
        return {"additionalContext": prompt_text}

    # Default: gate mode — deny.
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": prompt_text,
        }
    }


# ---------------------------------------------------------------------------
# Script entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        hook_input = {}

    output = main(hook_input)
    if output is not None:
        print(json.dumps(output))
