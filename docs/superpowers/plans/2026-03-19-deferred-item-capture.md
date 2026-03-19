# Deferred Item Capture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unified deferred-item capture across all night-market plugins, producing GitHub issues with consistent format and labels.

**Architecture:** Standalone Python scripts per plugin (convention over shared code), two safety-net hooks in sanctum (PostToolUse + Stop), leyline skill as the contract. Each plugin bundles its own self-contained wrapper.

**Tech Stack:** Python 3.9 (stdlib only), `gh` CLI, Claude Code hook protocol (env vars)

**Spec:** `docs/superpowers/specs/2026-03-19-deferred-item-capture-design.md`

**Spec review correction:** The spec was updated to read stdin JSON for the PostToolUse hook, but the actual working pattern in `plugins/abstract/hooks/skill_execution_logger.py:326-328` uses environment variables (`CLAUDE_TOOL_NAME`, `CLAUDE_TOOL_INPUT`, `CLAUDE_TOOL_OUTPUT`). This plan uses the env var pattern (the proven, working approach).

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `plugins/leyline/skills/deferred-capture/SKILL.md` | Create | Contract: CLI interface, template, labels, compliance test |
| `plugins/sanctum/scripts/deferred_capture.py` | Create | Reference implementation (~80 lines) |
| `plugins/sanctum/tests/unit/scripts/test_deferred_capture.py` | Create | Unit tests for reference implementation |
| `plugins/sanctum/hooks/deferred_item_watcher.py` | Create | PostToolUse safety-net hook (~60 lines) |
| `plugins/sanctum/hooks/deferred_item_sweep.py` | Create | Stop hook final sweep (~50 lines) |
| `plugins/sanctum/tests/unit/hooks/test_deferred_item_watcher.py` | Create | Tests for PostToolUse hook |
| `plugins/sanctum/tests/unit/hooks/test_deferred_item_sweep.py` | Create | Tests for Stop hook |
| `plugins/sanctum/hooks/hooks.json` | Modify | Add PostToolUse + Stop hook registrations |
| `plugins/attune/scripts/deferred_capture.py` | Create | Attune wrapper (~30 lines) |
| `plugins/imbue/scripts/deferred_capture.py` | Create | Imbue wrapper (~30 lines) |
| `plugins/pensive/scripts/deferred_capture.py` | Create | Pensive wrapper (~30 lines) |
| `plugins/abstract/scripts/deferred_capture.py` | Create | Abstract wrapper (~30 lines) |
| `plugins/egregore/scripts/deferred_capture.py` | Create | Egregore wrapper (~30 lines) |
| `plugins/attune/skills/war-room/modules/deferred-capture.md` | Create | War-room deferral instructions |
| `plugins/attune/skills/project-brainstorming/modules/deferred-capture.md` | Create | Brainstorm deferral instructions |
| `plugins/imbue/skills/scope-guard/modules/github-integration.md` | Modify | Converge to shared script |
| `plugins/imbue/skills/feature-review/SKILL.md` | Modify | Add deferred capture at Phase 6 |
| `plugins/pensive/skills/unified-review/SKILL.md` | Modify | Add deferred capture at Phase 4 |
| `plugins/abstract/src/abstract/rollback_reviewer.py` | Modify:84-149 | Converge create_github_issue to shared script |
| `Makefile` | Modify | Add verify-deferred-capture target |

---

## Task 1: Leyline Contract

**Files:**
- Create: `plugins/leyline/skills/deferred-capture/SKILL.md`

- [ ] **Step 1: Create the skill directory**

Run: `mkdir -p plugins/leyline/skills/deferred-capture`

- [ ] **Step 2: Write the contract SKILL.md**

```markdown
---
name: deferred-capture
description: Contract for unified deferred-item capture across plugins. Defines CLI interface, issue template, label taxonomy, and compliance test.
---

# Deferred Capture Contract

Specification that all plugin deferred-capture wrappers implement.
Not a runtime dependency -- a convention.

## CLI Interface

Required arguments:

- `--title` (str): Concise description. Becomes issue title
  after `[Deferred]` prefix
- `--source` (str): Origin skill. One of: war-room, brainstorm,
  scope-guard, feature-review, review, regression, egregore
- `--context` (str): Why raised and why deferred

Optional arguments:

- `--labels` (str): Comma-separated additional labels beyond
  `deferred` + source
- `--session-id` (str): Session ID. Canonical source:
  `$CLAUDE_SESSION_ID` env var, fallback: UTC timestamp
  `YYYYMMDD-HHMMSS`
- `--artifact-path` (str): Absolute path or `$HOME`-based
  path to source artifact
- `--captured-by` (str): `explicit` (default) or `safety-net`
- `--dry-run` (flag): Print JSON output without creating issue

## Issue Template

Title: `[Deferred] <title>`

Labels: `deferred` + `<source>`

Body:

    ## Deferred Item

    **Source:** <source> (session <session-id>)
    **Captured:** <YYYY-MM-DD>
    **Branch:** <current git branch>
    **Captured by:** <explicit|safety-net>

    ### Context

    <context argument verbatim>

    ### Original Artifact

    <artifact-path if provided, otherwise "N/A">

    ### Next Steps

    - [ ] Evaluate feasibility in a future cycle
    - [ ] Link to related work if applicable

## Label Taxonomy

| Label | Color | Purpose |
|-------|-------|---------|
| `deferred` | `#7B61FF` | Universal query handle |
| `war-room` | `#B60205` | Source: war-room deliberation |
| `brainstorm` | `#1D76DB` | Source: brainstorming session |
| `scope-guard` | `#FBCA04` | Source: scope-guard deferral |
| `feature-review` | `#F9A825` | Source: feature-review |
| `review` | `#0E8A16` | Source: code/PR review |
| `regression` | `#D73A4A` | Source: skill regression |
| `egregore` | `#5319E7` | Source: autonomous agent |

## Duplicate Detection

Search: `gh issue list --search "<title> in:title"
--state open --json number,title`

Compare: exact title match after stripping `[Deferred]`
prefix and normalizing to lowercase.

Only open issues are checked. Re-filing a closed deferred
item is intentional.

## Output (JSON to stdout)

Created: `{"status": "created", "issue_url": "...", "number": 42}`
Duplicate: `{"status": "duplicate", "existing_url": "...", "number": 17}`
Error: `{"status": "error", "message": "..."}`

## Compliance Test

Any wrapper can verify conformance with:

    python3 scripts/deferred_capture.py \
      --title "Test: compliance check" \
      --source test \
      --context "Automated compliance verification" \
      --dry-run

Must output valid JSON with a `status` field.
```

- [ ] **Step 3: Commit**

```bash
git add plugins/leyline/skills/deferred-capture/SKILL.md
git commit -m "feat(leyline): add deferred-capture contract skill"
```

---

## Task 2: Sanctum Reference Script + Tests

**Files:**
- Create: `plugins/sanctum/scripts/deferred_capture.py`
- Create: `plugins/sanctum/tests/unit/scripts/test_deferred_capture.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for deferred_capture.py reference implementation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "deferred_capture.py"


def run_script(*args: str) -> subprocess.CompletedProcess:
    """Run deferred_capture.py with given arguments."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=10,
    )


class TestDryRun:
    """Dry-run mode outputs JSON without calling gh."""

    def test_dry_run_outputs_valid_json(self):
        result = run_script(
            "--title", "Test item",
            "--source", "test",
            "--context", "Test context",
            "--dry-run",
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "dry_run"
        assert "[Deferred] Test item" in data["title"]

    def test_dry_run_includes_all_fields(self):
        result = run_script(
            "--title", "Test item",
            "--source", "war-room",
            "--context", "Some context",
            "--session-id", "20260319-143022",
            "--artifact-path", "/tmp/test.md",
            "--captured-by", "explicit",
            "--dry-run",
        )
        data = json.loads(result.stdout)
        assert data["source"] == "war-room"
        assert data["session_id"] == "20260319-143022"
        assert "explicit" in data["body"]

    def test_dry_run_with_extra_labels(self):
        result = run_script(
            "--title", "Labeled item",
            "--source", "scope-guard",
            "--context", "Context",
            "--labels", "enhancement,high-priority",
            "--dry-run",
        )
        data = json.loads(result.stdout)
        assert "deferred" in data["labels"]
        assert "scope-guard" in data["labels"]
        assert "enhancement" in data["labels"]


class TestArgParsing:
    """Argument validation and defaults."""

    def test_missing_required_args_fails(self):
        result = run_script("--dry-run")
        assert result.returncode != 0

    def test_title_gets_deferred_prefix(self):
        result = run_script(
            "--title", "My feature",
            "--source", "brainstorm",
            "--context", "Not selected",
            "--dry-run",
        )
        data = json.loads(result.stdout)
        assert data["title"] == "[Deferred] My feature"

    def test_title_not_double_prefixed(self):
        result = run_script(
            "--title", "[Deferred] Already prefixed",
            "--source", "brainstorm",
            "--context", "Not selected",
            "--dry-run",
        )
        data = json.loads(result.stdout)
        assert data["title"] == "[Deferred] Already prefixed"
        assert not data["title"].startswith("[Deferred] [Deferred]")

    def test_session_id_defaults_to_env_or_timestamp(self):
        result = run_script(
            "--title", "Test",
            "--source", "test",
            "--context", "Context",
            "--dry-run",
        )
        data = json.loads(result.stdout)
        assert data["session_id"]  # not empty


class TestBodyTemplate:
    """Issue body follows the leyline contract template."""

    def test_body_contains_required_sections(self):
        result = run_script(
            "--title", "Test",
            "--source", "war-room",
            "--context", "My context here",
            "--dry-run",
        )
        data = json.loads(result.stdout)
        body = data["body"]
        assert "## Deferred Item" in body
        assert "**Source:** war-room" in body
        assert "**Captured by:**" in body
        assert "### Context" in body
        assert "My context here" in body
        assert "### Next Steps" in body
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/sanctum && python -m pytest tests/unit/scripts/test_deferred_capture.py -v`
Expected: FAIL (script does not exist yet)

- [ ] **Step 3: Write the reference implementation**

```python
#!/usr/bin/env python3
"""Deferred-item capture -- sanctum reference implementation.

Creates GitHub issues for deferred items using a unified format.
Contract: plugins/leyline/skills/deferred-capture/SKILL.md

Python 3.9 compatible. No external dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_session_id(override: str | None = None) -> str:
    """Resolve session ID: explicit > env var > timestamp."""
    if override:
        return override
    env_id = os.environ.get("CLAUDE_SESSION_ID", "")
    if env_id:
        return env_id
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def get_current_branch() -> str:
    """Get current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "unknown"


def build_title(raw_title: str) -> str:
    """Add [Deferred] prefix if not already present."""
    if raw_title.startswith("[Deferred]"):
        return raw_title
    return f"[Deferred] {raw_title}"


def build_labels(source: str, extra: str | None) -> list[str]:
    """Build label list: always deferred + source + extras."""
    labels = ["deferred", source]
    if extra:
        labels.extend(l.strip() for l in extra.split(",") if l.strip())
    return list(dict.fromkeys(labels))  # dedupe, preserve order


def build_body(
    source: str,
    session_id: str,
    branch: str,
    captured_by: str,
    context: str,
    artifact_path: str | None,
) -> str:
    """Build issue body from leyline contract template."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    artifact = artifact_path or "N/A"
    return f"""## Deferred Item

**Source:** {source} (session {session_id})
**Captured:** {today}
**Branch:** {branch}
**Captured by:** {captured_by}

### Context

{context}

### Original Artifact

{artifact}

### Next Steps

- [ ] Evaluate feasibility in a future cycle
- [ ] Link to related work if applicable"""


def ensure_label_exists(label: str, color: str) -> None:
    """Create label if it doesn't exist. Ignore errors."""
    try:
        subprocess.run(
            ["gh", "label", "create", label,
             "--color", color,
             "--description", f"Deferred items: {label}"],
            capture_output=True, text=True, timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass  # best-effort


LABEL_COLORS = {
    "deferred": "7B61FF",
    "war-room": "B60205",
    "brainstorm": "1D76DB",
    "scope-guard": "FBCA04",
    "feature-review": "F9A825",
    "review": "0E8A16",
    "regression": "D73A4A",
    "egregore": "5319E7",
}


def find_duplicate(title: str) -> dict | None:
    """Check for existing open issue with same title."""
    search_title = title.replace("[Deferred] ", "").lower()
    try:
        result = subprocess.run(
            ["gh", "issue", "list",
             "--search", f"{search_title} in:title",
             "--state", "open",
             "--json", "number,title,url"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            return None
        issues = json.loads(result.stdout)
        for issue in issues:
            existing = issue["title"].replace("[Deferred] ", "").lower()
            if existing == search_title:
                return issue
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def create_issue(title: str, body: str, labels: list[str]) -> dict:
    """Create GitHub issue via gh CLI. Returns result dict."""
    # Ensure labels exist
    for label in labels:
        if label in LABEL_COLORS:
            ensure_label_exists(label, LABEL_COLORS[label])

    cmd = ["gh", "issue", "create", "--title", title, "--body", body]
    for label in labels:
        cmd.extend(["--label", label])

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            # Extract issue number from URL
            number = int(url.rstrip("/").split("/")[-1])
            return {"status": "created", "issue_url": url, "number": number}
        sys.stderr.write(
            f"deferred_capture: gh issue create failed "
            f"(exit {result.returncode}): {result.stderr.strip()}\n"
        )
        return {"status": "error", "message": result.stderr.strip()}
    except FileNotFoundError:
        return {"status": "error", "message": "gh CLI not found"}
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "gh issue create timed out"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture deferred items as GitHub issues")
    parser.add_argument("--title", required=True, help="Issue title")
    parser.add_argument("--source", required=True, help="Origin skill")
    parser.add_argument("--context", required=True, help="Why deferred")
    parser.add_argument("--labels", default=None, help="Extra labels (comma-sep)")
    parser.add_argument("--session-id", default=None, help="Session ID")
    parser.add_argument("--artifact-path", default=None, help="Source artifact path")
    parser.add_argument("--captured-by", default="explicit", choices=["explicit", "safety-net"])
    parser.add_argument("--dry-run", action="store_true", help="Print without creating")
    args = parser.parse_args()

    title = build_title(args.title)
    session_id = get_session_id(args.session_id)
    branch = get_current_branch()
    labels = build_labels(args.source, args.labels)
    body = build_body(
        args.source, session_id, branch,
        args.captured_by, args.context, args.artifact_path,
    )

    if args.dry_run:
        print(json.dumps({
            "status": "dry_run",
            "title": title,
            "source": args.source,
            "session_id": session_id,
            "labels": labels,
            "body": body,
        }))
        return

    # Check for duplicates
    dup = find_duplicate(title)
    if dup:
        print(json.dumps({
            "status": "duplicate",
            "existing_url": dup.get("url", ""),
            "number": dup["number"],
        }))
        return

    # Create issue
    result = create_issue(title, body, labels)
    print(json.dumps(result))
    if result["status"] != "created":
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/sanctum && python -m pytest tests/unit/scripts/test_deferred_capture.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/sanctum/scripts/deferred_capture.py \
       plugins/sanctum/tests/unit/scripts/test_deferred_capture.py
git commit -m "feat(sanctum): add deferred_capture.py reference implementation"
```

---

## Task 3: PostToolUse Safety-Net Hook

**Files:**
- Create: `plugins/sanctum/hooks/deferred_item_watcher.py`
- Create: `plugins/sanctum/tests/unit/hooks/test_deferred_item_watcher.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for deferred_item_watcher.py PostToolUse hook."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

# Import after sys.path manipulation
import importlib
import sys

HOOK_DIR = Path(__file__).resolve().parents[3] / "hooks"
sys.path.insert(0, str(HOOK_DIR))


class TestWatchList:
    """Hook only processes watched skills."""

    def test_non_skill_tool_exits_silently(self):
        """Non-Skill tools should be ignored."""
        env = {"CLAUDE_TOOL_NAME": "Bash", "CLAUDE_TOOL_INPUT": "{}"}
        with patch.dict(os.environ, env, clear=False):
            import deferred_item_watcher as mod
            # Should not raise, should exit early
            assert mod.should_process() is False

    def test_unwatched_skill_exits_silently(self):
        """Skills not in watch list should be ignored."""
        env = {
            "CLAUDE_TOOL_NAME": "Skill",
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": "leyline:markdown-formatting"}),
        }
        with patch.dict(os.environ, env, clear=False):
            import deferred_item_watcher as mod
            assert mod.should_process() is False

    def test_watched_skill_is_processed(self):
        """War-room skill should be processed."""
        env = {
            "CLAUDE_TOOL_NAME": "Skill",
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": "attune:war-room"}),
        }
        with patch.dict(os.environ, env, clear=False):
            import deferred_item_watcher as mod
            assert mod.should_process() is True


class TestDeferralDetection:
    """Pattern matching for deferral signals."""

    def test_detects_deferred_marker(self):
        from deferred_item_watcher import scan_for_deferrals
        assert scan_for_deferrals("[Deferred] Some feature")

    def test_detects_out_of_scope(self):
        from deferred_item_watcher import scan_for_deferrals
        assert scan_for_deferrals("This is out of scope for the current work")

    def test_ignores_normal_output(self):
        from deferred_item_watcher import scan_for_deferrals
        assert not scan_for_deferrals("Task completed successfully")


class TestLedger:
    """Session ledger read/write operations."""

    def test_write_and_read_entry(self, tmp_path):
        from deferred_item_watcher import write_ledger_entry, read_ledger
        ledger_path = tmp_path / "deferred-items-session.json"
        entry = {"title": "Test", "source": "test", "filed": False}
        write_ledger_entry(ledger_path, entry)
        entries = read_ledger(ledger_path)
        assert len(entries) == 1
        assert entries[0]["title"] == "Test"

    def test_update_entry_filed_status(self, tmp_path):
        from deferred_item_watcher import (
            write_ledger_entry, update_ledger_entry, read_ledger,
        )
        ledger_path = tmp_path / "deferred-items-session.json"
        write_ledger_entry(ledger_path, {
            "title": "Test", "source": "test", "filed": False,
        })
        update_ledger_entry(ledger_path, "Test", filed=True, issue_number=42)
        entries = read_ledger(ledger_path)
        assert entries[0]["filed"] is True
        assert entries[0]["issue_number"] == 42
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/sanctum && python -m pytest tests/unit/hooks/test_deferred_item_watcher.py -v`
Expected: FAIL (hook does not exist)

- [ ] **Step 3: Write the PostToolUse hook**

```python
#!/usr/bin/env python3
"""PostToolUse safety-net hook for deferred-item capture.

Watches Skill tool invocations for deferral signals in
high-value skills. Creates GitHub issues for uncaptured
deferrals via the deferred_capture.py script.

Uses two-phase ledger write: writes filed=false before
calling gh, updates to filed=true on success.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

WATCH_LIST = {
    "war-room", "brainstorm", "scope-guard",
    "feature-review", "unified-review", "rollback-reviewer",
}

DEFERRAL_PATTERNS = re.compile(
    r"\[Deferred\]|out of scope|not yet applicable|future cycle",
    re.IGNORECASE,
)

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"


def get_ledger_path() -> Path:
    """Session-scoped ledger for dedup."""
    claude_dir = Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude"))
    return claude_dir / "deferred-items-session.json"


def read_ledger(path: Path) -> list[dict]:
    """Read ledger entries."""
    if not path.exists():
        return []
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return []


def write_ledger_entry(path: Path, entry: dict) -> None:
    """Append entry to ledger."""
    entries = read_ledger(path)
    entries.append(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(entries, f, indent=2)


def update_ledger_entry(
    path: Path, title: str, filed: bool = True,
    issue_number: int | None = None,
) -> None:
    """Update an existing ledger entry by title."""
    entries = read_ledger(path)
    for entry in entries:
        if entry.get("title") == title:
            entry["filed"] = filed
            if issue_number is not None:
                entry["issue_number"] = issue_number
            break
    with open(path, "w") as f:
        json.dump(entries, f, indent=2)


def should_process() -> bool:
    """Check if this invocation should be processed."""
    tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
    if tool_name != "Skill":
        return False
    tool_input_str = os.environ.get("CLAUDE_TOOL_INPUT", "{}")
    try:
        tool_input = json.loads(tool_input_str)
    except json.JSONDecodeError:
        return False
    skill_ref = tool_input.get("skill", "")
    # Extract skill name after colon (e.g., "attune:war-room" -> "war-room")
    skill_name = skill_ref.split(":", 1)[-1] if ":" in skill_ref else skill_ref
    return skill_name in WATCH_LIST


def scan_for_deferrals(text: str) -> bool:
    """Scan text for deferral signal patterns."""
    return bool(DEFERRAL_PATTERNS.search(text))


def extract_deferred_titles(text: str) -> list[str]:
    """Extract deferred item titles from [Deferred] markers."""
    titles = re.findall(r"\[Deferred\]\s*(.+?)(?:\n|$)", text)
    return titles if titles else ["Untitled deferred item"]


def main() -> None:
    """PostToolUse hook entry point."""
    if not should_process():
        return

    tool_output = os.environ.get("CLAUDE_TOOL_OUTPUT", "")
    if not tool_output or not scan_for_deferrals(tool_output):
        return

    # Extract deferred items
    titles = extract_deferred_titles(tool_output)
    ledger_path = get_ledger_path()
    existing = {e["title"] for e in read_ledger(ledger_path)}

    tool_input = json.loads(os.environ.get("CLAUDE_TOOL_INPUT", "{}"))
    skill_ref = tool_input.get("skill", "unknown")
    source = skill_ref.split(":", 1)[-1] if ":" in skill_ref else skill_ref

    for title in titles:
        if title in existing:
            continue

        # Phase 1: write filed=false
        entry = {
            "title": title,
            "source": source,
            "filed": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        write_ledger_entry(ledger_path, entry)

        # Phase 2: call deferred_capture.py
        script = SCRIPT_DIR / "deferred_capture.py"
        try:
            result = subprocess.run(
                [sys.executable, str(script),
                 "--title", title,
                 "--source", source,
                 "--context", f"Detected by safety-net hook from {skill_ref}",
                 "--captured-by", "safety-net"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                update_ledger_entry(
                    ledger_path, title, filed=True,
                    issue_number=data.get("number"),
                )
        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
            pass  # entry remains filed=false for Stop hook


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # hooks must never crash the session
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/sanctum && python -m pytest tests/unit/hooks/test_deferred_item_watcher.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/sanctum/hooks/deferred_item_watcher.py \
       plugins/sanctum/tests/unit/hooks/test_deferred_item_watcher.py
git commit -m "feat(sanctum): add PostToolUse deferred-item watcher hook"
```

---

## Task 4: Stop Hook (Final Sweep)

**Files:**
- Create: `plugins/sanctum/hooks/deferred_item_sweep.py`
- Create: `plugins/sanctum/tests/unit/hooks/test_deferred_item_sweep.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for deferred_item_sweep.py Stop hook."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import sys
HOOK_DIR = Path(__file__).resolve().parents[3] / "hooks"
sys.path.insert(0, str(HOOK_DIR))


class TestLedgerProcessing:
    """Stop hook processes unfiled ledger entries."""

    def test_skips_filed_entries(self, tmp_path):
        from deferred_item_sweep import process_ledger
        ledger = tmp_path / "deferred-items-session.json"
        ledger.write_text(json.dumps([
            {"title": "Filed", "source": "test", "filed": True, "issue_number": 1},
        ]))
        with patch("deferred_item_sweep.call_capture_script") as mock:
            stats = process_ledger(ledger)
        mock.assert_not_called()
        assert stats["already_filed"] == 1

    def test_retries_unfiled_entries(self, tmp_path):
        from deferred_item_sweep import process_ledger
        ledger = tmp_path / "deferred-items-session.json"
        ledger.write_text(json.dumps([
            {"title": "Unfiled", "source": "war-room", "filed": False},
        ]))
        mock_result = {"status": "created", "issue_url": "https://...", "number": 99}
        with patch("deferred_item_sweep.call_capture_script", return_value=mock_result):
            stats = process_ledger(ledger)
        assert stats["filed"] == 1

    def test_empty_ledger_is_noop(self, tmp_path):
        from deferred_item_sweep import process_ledger
        ledger = tmp_path / "deferred-items-session.json"
        ledger.write_text("[]")
        stats = process_ledger(ledger)
        assert stats["filed"] == 0
        assert stats["already_filed"] == 0

    def test_missing_ledger_is_noop(self, tmp_path):
        from deferred_item_sweep import process_ledger
        ledger = tmp_path / "nonexistent.json"
        stats = process_ledger(ledger)
        assert stats["filed"] == 0

    def test_ledger_preserved_when_entries_remain_unfiled(self, tmp_path):
        from deferred_item_sweep import process_ledger
        ledger = tmp_path / "deferred-items-session.json"
        ledger.write_text(json.dumps([
            {"title": "Stuck", "source": "test", "filed": False},
        ]))
        mock_err = {"status": "error", "message": "gh timeout"}
        with patch("deferred_item_sweep.call_capture_script", return_value=mock_err):
            stats = process_ledger(ledger)
        assert stats["failed"] == 1
        assert ledger.exists()  # NOT deleted

    def test_ledger_deleted_when_all_filed(self, tmp_path):
        from deferred_item_sweep import process_ledger
        ledger = tmp_path / "deferred-items-session.json"
        ledger.write_text(json.dumps([
            {"title": "Done", "source": "test", "filed": True, "issue_number": 1},
        ]))
        with patch("deferred_item_sweep.call_capture_script"):
            stats = process_ledger(ledger)
        assert not ledger.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/sanctum && python -m pytest tests/unit/hooks/test_deferred_item_sweep.py -v`
Expected: FAIL

- [ ] **Step 3: Write the Stop hook**

```python
#!/usr/bin/env python3
"""Stop hook: final sweep for unfiled deferred items.

Reads the session ledger, retries any entries where
filed=false, prints summary, cleans up.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"


def get_ledger_path() -> Path:
    """Session-scoped ledger path."""
    claude_dir = Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude"))
    return claude_dir / "deferred-items-session.json"


def call_capture_script(title: str, source: str) -> dict:
    """Call deferred_capture.py for a single item."""
    script = SCRIPT_DIR / "deferred_capture.py"
    try:
        result = subprocess.run(
            [sys.executable, str(script),
             "--title", title,
             "--source", source,
             "--context", f"Captured by Stop hook sweep (originally from {source})",
             "--captured-by", "safety-net"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {"status": "error", "message": result.stderr.strip()}
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as e:
        return {"status": "error", "message": str(e)}


def process_ledger(ledger_path: Path) -> dict:
    """Process ledger entries. Returns stats dict."""
    stats = {"filed": 0, "already_filed": 0, "failed": 0, "duplicates": 0}

    if not ledger_path.exists():
        return stats

    try:
        with open(ledger_path) as f:
            entries = json.load(f)
    except (OSError, json.JSONDecodeError):
        return stats

    if not entries:
        ledger_path.unlink(missing_ok=True)
        return stats

    all_filed = True
    for entry in entries:
        if entry.get("filed"):
            stats["already_filed"] += 1
            continue

        result = call_capture_script(entry["title"], entry.get("source", "unknown"))
        if result["status"] == "created":
            entry["filed"] = True
            entry["issue_number"] = result.get("number")
            stats["filed"] += 1
        elif result["status"] == "duplicate":
            entry["filed"] = True
            entry["issue_number"] = result.get("number")
            stats["duplicates"] += 1
        else:
            stats["failed"] += 1
            all_filed = False

    if all_filed:
        ledger_path.unlink(missing_ok=True)
    else:
        # Preserve ledger for manual inspection
        with open(ledger_path, "w") as f:
            json.dump(entries, f, indent=2)
        sys.stderr.write(
            f"deferred_item_sweep: {stats['failed']} items remain unfiled. "
            f"Ledger preserved at {ledger_path}\n"
        )

    return stats


def main() -> None:
    """Stop hook entry point."""
    ledger_path = get_ledger_path()
    stats = process_ledger(ledger_path)

    total = stats["filed"] + stats["duplicates"]
    if total > 0 or stats["failed"] > 0:
        sys.stderr.write(
            f"Deferred items: {total} filed, "
            f"{stats['duplicates']} duplicate, "
            f"{stats['failed']} failed\n"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # hooks must never crash the session
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/sanctum && python -m pytest tests/unit/hooks/test_deferred_item_sweep.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/sanctum/hooks/deferred_item_sweep.py \
       plugins/sanctum/tests/unit/hooks/test_deferred_item_sweep.py
git commit -m "feat(sanctum): add Stop hook for deferred-item sweep"
```

---

## Task 5: Register Hooks in hooks.json

**Files:**
- Modify: `plugins/sanctum/hooks/hooks.json`

- [ ] **Step 1: Add PostToolUse and update Stop entries**

Add a new `PostToolUse` section and append to existing `Stop` hooks:

```json
"PostToolUse": [
  {
    "matcher": "Skill",
    "hooks": [
      {
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/hooks/deferred_item_watcher.py",
        "timeout": 2
      }
    ]
  }
],
```

In the existing `Stop` section, add after `session_complete_notify.py`:

```json
{
  "type": "command",
  "command": "${CLAUDE_PLUGIN_ROOT}/hooks/deferred_item_sweep.py",
  "timeout": 5
}
```

Note: Stop sweep gets timeout 5 (not 1) because it may retry `gh` calls.

- [ ] **Step 2: Validate JSON syntax**

Run: `python3 -c "import json; json.load(open('plugins/sanctum/hooks/hooks.json'))"`
Expected: No error

- [ ] **Step 3: Commit**

```bash
git add plugins/sanctum/hooks/hooks.json
git commit -m "feat(sanctum): register deferred-item hooks in hooks.json"
```

---

## Task 6: Plugin Wrappers

**Files:**
- Create: `plugins/attune/scripts/deferred_capture.py`
- Create: `plugins/imbue/scripts/deferred_capture.py`
- Create: `plugins/pensive/scripts/deferred_capture.py`
- Create: `plugins/abstract/scripts/deferred_capture.py`
- Create: `plugins/egregore/scripts/deferred_capture.py`

Each wrapper is a self-contained script (~30 lines) that implements the leyline contract with plugin-specific defaults. All share the same structure:

1. Argparse with same interface as reference
2. Plugin-specific default source and label
3. Plugin-specific context enrichment
4. Same `gh issue create` pattern, same JSON output

- [ ] **Step 1: Write attune wrapper**

`plugins/attune/scripts/deferred_capture.py` -- defaults to `war-room` source, enriches context with strategeion session path.

- [ ] **Step 2: Write imbue wrapper**

`plugins/imbue/scripts/deferred_capture.py` -- defaults to `scope-guard` source, enriches context with worthiness score breakdown.

- [ ] **Step 3: Write pensive wrapper**

`plugins/pensive/scripts/deferred_capture.py` -- defaults to `review` source, enriches context with review dimension.

- [ ] **Step 4: Write abstract wrapper**

`plugins/abstract/scripts/deferred_capture.py` -- defaults to `regression` source, enriches context with stability gap metrics.

- [ ] **Step 5: Write egregore wrapper**

`plugins/egregore/scripts/deferred_capture.py` -- defaults to `egregore` source, enriches context with pipeline step info.

- [ ] **Step 6: Verify all wrappers pass compliance test**

Run for each:
```bash
for plugin in attune imbue pensive abstract egregore; do
  echo "=== $plugin ==="
  python3 plugins/$plugin/scripts/deferred_capture.py \
    --title "Test: compliance" \
    --source test \
    --context "Compliance check" \
    --dry-run
done
```
Expected: All output valid JSON with `status` field.

- [ ] **Step 7: Commit**

```bash
git add plugins/attune/scripts/deferred_capture.py \
       plugins/imbue/scripts/deferred_capture.py \
       plugins/pensive/scripts/deferred_capture.py \
       plugins/abstract/scripts/deferred_capture.py \
       plugins/egregore/scripts/deferred_capture.py
git commit -m "feat: add deferred_capture.py wrappers for all plugins"
```

---

## Task 7: Skill Integration Modules

**Files:**
- Create: `plugins/attune/skills/war-room/modules/deferred-capture.md`
- Create: `plugins/attune/skills/project-brainstorming/modules/deferred-capture.md`
- Modify: `plugins/imbue/skills/scope-guard/modules/github-integration.md`
- Modify: `plugins/imbue/skills/feature-review/SKILL.md`
- Modify: `plugins/pensive/skills/unified-review/SKILL.md`

These are documentation changes that instruct each skill when and how to call its plugin's `deferred_capture.py`.

- [ ] **Step 1: Create war-room deferred-capture module**

`plugins/attune/skills/war-room/modules/deferred-capture.md`:

Instructs the war-room skill to iterate rejected COAs after Phase 5 (Voting + Narrowing) and call `scripts/deferred_capture.py` for each COA that received at least one Borda vote. Context includes the COA summary and Supreme Commander's rejection rationale.

- [ ] **Step 2: Create brainstorm deferred-capture module**

`plugins/attune/skills/project-brainstorming/modules/deferred-capture.md`:

Instructs the brainstorming skill to offer capture of non-selected approaches after Phase 5 (Decision + Rationale). Prompts user: `"N non-selected approaches have merit. Capture as deferred items? [Y/n/select]"`. Only captures on user confirmation.

- [ ] **Step 3: Update scope-guard github-integration.md**

Replace the bespoke `gh issue create` command block (lines ~19-57 of `github-integration.md`) with a call to `scripts/deferred_capture.py`. The worthiness score and breakdown go into `--context`. Remove the old `scope-guard-deferred` label reference. Add the label migration note.

- [ ] **Step 4: Update feature-review SKILL.md**

Add a note at Phase 6 (GitHub Integration) to call `scripts/deferred_capture.py` for suggestions scored > 2.5 that aren't acted on. RICE/WSJF score goes into `--context`.

- [ ] **Step 5: Update unified-review SKILL.md**

Add a note at Phase 4 (Action Plan) to call `scripts/deferred_capture.py` for findings triaged to backlog. Review dimension goes into `--context`.

- [ ] **Step 6: Commit**

```bash
git add plugins/attune/skills/war-room/modules/deferred-capture.md \
       plugins/attune/skills/project-brainstorming/modules/deferred-capture.md \
       plugins/imbue/skills/scope-guard/modules/github-integration.md \
       plugins/imbue/skills/feature-review/SKILL.md \
       plugins/pensive/skills/unified-review/SKILL.md
git commit -m "feat: add deferred-capture integration to war-room, brainstorm, scope-guard, feature-review, unified-review"
```

---

## Task 8: Converge Rollback Reviewer

**Files:**
- Modify: `plugins/abstract/src/abstract/rollback_reviewer.py:84-149`

- [ ] **Step 1: Replace create_github_issue method body**

Replace the bespoke `gh issue create` subprocess call with a call to `plugins/abstract/scripts/deferred_capture.py`. Pass regression metrics (stability gap, improvement diff, rollback command) into `--context`. Keep the same return type (`str | None` for issue URL).

- [ ] **Step 2: Run existing rollback reviewer tests**

Run: `cd plugins/abstract && python -m pytest tests/ -k rollback -v`
Expected: PASS (behavior unchanged, just different codepath)

- [ ] **Step 3: Commit**

```bash
git add plugins/abstract/src/abstract/rollback_reviewer.py
git commit -m "refactor(abstract): converge rollback_reviewer to shared deferred_capture script"
```

---

## Task 9: Makefile Compliance Target

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Add verify-deferred-capture target**

```makefile
.PHONY: verify-deferred-capture
verify-deferred-capture:  ## Verify all deferred_capture.py wrappers conform to leyline contract
	@echo "Verifying deferred_capture.py compliance..."
	@for plugin in sanctum attune imbue pensive abstract egregore; do \
		echo "  $$plugin..."; \
		python3 plugins/$$plugin/scripts/deferred_capture.py \
			--title "Test: compliance" \
			--source test \
			--context "Automated compliance check" \
			--dry-run | python3 -c "import json,sys; d=json.load(sys.stdin); assert 'status' in d, 'Missing status field'" \
		|| { echo "  FAIL: $$plugin"; exit 1; }; \
	done
	@echo "All wrappers compliant."
```

- [ ] **Step 2: Run it**

Run: `make verify-deferred-capture`
Expected: All wrappers compliant.

- [ ] **Step 3: Commit**

```bash
git add Makefile
git commit -m "build: add verify-deferred-capture compliance target"
```

---

## Task 10: Label Creation + Migration

- [ ] **Step 1: Create new labels**

```bash
gh label create deferred --color "7B61FF" --description "Deferred items from plugin workflows" --force
gh label create war-room --color "B60205" --description "Source: war-room deliberation" --force
gh label create brainstorm --color "1D76DB" --description "Source: brainstorming session" --force
gh label create feature-review --color "F9A825" --description "Source: feature-review suggestions" --force
gh label create regression --color "D73A4A" --description "Source: skill regression" --force
gh label create egregore --color "5319E7" --description "Source: autonomous agent" --force
```

Note: `scope-guard` and `review` labels likely exist already. Check first.

- [ ] **Step 2: Migrate existing scope-guard-deferred issues (if any)**

```bash
gh issue list --label scope-guard-deferred --json number --jq '.[].number' | \
  xargs -I{} gh issue edit {} --add-label deferred --add-label scope-guard
```

- [ ] **Step 3: Commit (no files, just document the migration)**

No file changes. This is a runtime operation against the GitHub API.
