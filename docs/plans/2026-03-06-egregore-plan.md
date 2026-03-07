# Egregore Plugin Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan task-by-task.

**Goal:** Create the egregore plugin: an autonomous agent orchestrator
that manages full development lifecycles with zero human input,
session budget awareness, crash recovery, and overseer notifications.

**Architecture:** Orchestrator skill invokes existing night-market
skills sequentially through a pipeline (intake, build, quality,
ship). Continuation agents handle context overflow. An external
watchdog daemon relaunches sessions after rate-limit cooldowns.
State persists in `.egregore/manifest.json`.

**Tech Stack:** Python 3.9+ (hooks), Bash (watchdog, installers),
Markdown (skills, commands, agents), JSON (state files), `gh` CLI
(notifications)

**Design Doc:** `docs/plans/2026-03-06-egregore-design.md`

---

## Phase 1: Plugin Scaffold

### Task 1: Create plugin.json

**Files:**
- Create: `plugins/egregore/.claude-plugin/plugin.json`

**Step 1: Create directory structure**

Run:
```bash
mkdir -p plugins/egregore/.claude-plugin
mkdir -p plugins/egregore/{skills,commands,agents,hooks,scripts,templates,tests}
mkdir -p plugins/egregore/skills/summon/modules
mkdir -p plugins/egregore/skills/{install-watchdog,uninstall-watchdog}
mkdir -p plugins/egregore/templates/webhook-payloads
```

**Step 2: Write plugin.json**

```json
{
  "name": "egregore",
  "version": "1.6.0",
  "description": "Autonomous agent orchestrator for full development lifecycles with zero human input, session budget management, and crash recovery",
  "skills": [
    "./skills/summon",
    "./skills/install-watchdog",
    "./skills/uninstall-watchdog"
  ],
  "commands": [
    "./commands/summon.md",
    "./commands/dismiss.md",
    "./commands/status.md",
    "./commands/install-watchdog.md",
    "./commands/uninstall-watchdog.md"
  ],
  "agents": [
    "./agents/orchestrator.md",
    "./agents/sentinel.md"
  ],
  "keywords": [
    "egregore",
    "autonomous",
    "orchestrator",
    "pipeline",
    "mission",
    "watchdog",
    "session-management",
    "crash-recovery",
    "notifications",
    "ralph-wiggum"
  ],
  "author": {
    "name": "Alex Thola",
    "url": "https://github.com/athola"
  },
  "license": "MIT"
}
```

**Step 3: Commit**

```bash
git add plugins/egregore/
git commit -m "feat(egregore): scaffold plugin directory structure"
```

---

### Task 2: Create pyproject.toml and Makefile

**Files:**
- Create: `plugins/egregore/pyproject.toml`
- Create: `plugins/egregore/Makefile`

**Step 1: Write pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "egregore-dev"
version = "1.6.0"
description = "Autonomous agent orchestrator plugin for Claude Code"
authors = [
    {name = "Alex Thola", email = "alexthola@gmail.com"}
]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.9"
dependencies = []

[project.optional-dependencies]
dev = [
    "ruff>=0.14.13,<1.0",
    "mypy>=1.11.0,<2.0",
    "pytest>=8.0",
    "pytest-cov>=4.0",
]

[tool.ruff]
line-length = 88
target-version = "py39"
exclude = [".venv", ".uv-cache"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "S", "PL", "D"]
extend-ignore = ["S101", "E203", "D203", "D213"]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "PLR2004", "D103", "PLC0415"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
pythonpath = ["scripts"]
```

**Step 2: Write Makefile**

```makefile
# Egregore Plugin Makefile
# Autonomous agent orchestrator

.PHONY: check clean deps fix format help lint test type-check

ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
-include $(ABSTRACT_DIR)/config/make/python.mk

help: ## Show this help message
	@echo "Egregore Plugin - Make Targets"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / \
	  {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' Makefile

deps: ## Install dependencies
	uv sync

lint: ## Run linting
	uv run ruff check scripts/ tests/

format: ## Format code
	uv run ruff format scripts/ tests/

fix: ## Auto-fix lint issues
	uv run ruff check --fix scripts/ tests/

type-check: ## Run type checking
	uv run mypy scripts/

test: ## Run tests
	uv run pytest tests/ -v --tb=short

check: lint type-check test ## Run all checks
	@echo "All checks passed!"

clean: ## Clean artifacts
	rm -rf .venv .uv-cache __pycache__ .mypy_cache .pytest_cache

Makefile.local:;
-include Makefile.local

%::
	@echo "Error: Unknown target '$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
```

**Step 3: Commit**

```bash
git add plugins/egregore/pyproject.toml plugins/egregore/Makefile
git commit -m "feat(egregore): add pyproject.toml and Makefile"
```

---

## Phase 2: State Management

### Task 3: Create manifest schema and helpers

**Files:**
- Create: `plugins/egregore/scripts/manifest.py`
- Create: `plugins/egregore/tests/test_manifest.py`

**Step 1: Write the failing test**

```python
"""Tests for egregore manifest state management."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from manifest import (
    Manifest,
    WorkItem,
    load_manifest,
    save_manifest,
)


def test_create_empty_manifest():
    m = Manifest()
    assert m.work_items == []
    assert m.project_dir is not None


def test_add_work_item_from_prompt():
    m = Manifest()
    item = m.add_work_item(source="prompt", source_ref="Build a REST API")
    assert item.id.startswith("wrk_")
    assert item.source == "prompt"
    assert item.status == "active"
    assert item.pipeline_stage == "intake"
    assert item.pipeline_step == "parse"


def test_add_work_item_from_issue():
    m = Manifest()
    item = m.add_work_item(source="github-issue", source_ref="#42")
    assert item.source == "github-issue"
    assert item.source_ref == "#42"


def test_advance_pipeline_step():
    m = Manifest()
    item = m.add_work_item(source="prompt", source_ref="test")
    m.advance(item.id)
    assert item.pipeline_step == "validate"
    m.advance(item.id)
    assert item.pipeline_step == "prioritize"
    m.advance(item.id)
    assert item.pipeline_stage == "build"
    assert item.pipeline_step == "brainstorm"


def test_mark_failed_after_max_attempts():
    m = Manifest()
    item = m.add_work_item(source="prompt", source_ref="test")
    item.attempts = 3
    item.max_attempts = 3
    m.fail_current_step(item.id, reason="test failure")
    assert item.status == "failed"


def test_save_and_load_manifest(tmp_path):
    m = Manifest(project_dir=str(tmp_path))
    m.add_work_item(source="prompt", source_ref="Build X")
    save_manifest(m, tmp_path / ".egregore" / "manifest.json")

    loaded = load_manifest(tmp_path / ".egregore" / "manifest.json")
    assert len(loaded.work_items) == 1
    assert loaded.work_items[0].source_ref == "Build X"


def test_next_active_item():
    m = Manifest()
    item1 = m.add_work_item(source="prompt", source_ref="first")
    item2 = m.add_work_item(source="prompt", source_ref="second")
    assert m.next_active_item().id == item1.id
    item1.status = "completed"
    assert m.next_active_item().id == item2.id


def test_next_active_item_none_when_all_done():
    m = Manifest()
    item = m.add_work_item(source="prompt", source_ref="only")
    item.status = "completed"
    assert m.next_active_item() is None


def test_record_decision():
    m = Manifest()
    item = m.add_work_item(source="prompt", source_ref="test")
    m.record_decision(
        item.id, step="brainstorm", chose="Express", why="simplicity"
    )
    assert len(item.decisions) == 1
    assert item.decisions[0]["chose"] == "Express"
```

**Step 2: Run test to verify it fails**

Run: `cd plugins/egregore && uv run pytest tests/test_manifest.py -v`
Expected: FAIL (manifest module not found)

**Step 3: Write manifest.py**

```python
"""Egregore manifest: persistent state for work items and pipeline."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


PIPELINE = {
    "intake": ["parse", "validate", "prioritize"],
    "build": ["brainstorm", "specify", "blueprint", "execute"],
    "quality": [
        "code-review",
        "unbloat",
        "code-refinement",
        "update-tests",
        "update-docs",
    ],
    "ship": ["prepare-pr", "pr-review", "fix-pr", "merge"],
}

STAGE_ORDER = ["intake", "build", "quality", "ship"]


@dataclass
class WorkItem:
    id: str
    source: str
    source_ref: str
    branch: str = ""
    pipeline_stage: str = "intake"
    pipeline_step: str = "parse"
    started_at: str = ""
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    attempts: int = 0
    max_attempts: int = 3
    status: str = "active"
    failure_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "source_ref": self.source_ref,
            "branch": self.branch,
            "pipeline_stage": self.pipeline_stage,
            "pipeline_step": self.pipeline_step,
            "started_at": self.started_at,
            "decisions": self.decisions,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "status": self.status,
            "failure_reason": self.failure_reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WorkItem:
        return cls(**{
            k: v for k, v in data.items()
            if k in cls.__dataclass_fields__
        })


def _next_id(items: List[WorkItem]) -> str:
    n = len(items) + 1
    return f"wrk_{n:03d}"


def _slugify(text: str, max_len: int = 30) -> str:
    slug = text.lower().strip()
    slug = "".join(c if c.isalnum() or c == " " else "" for c in slug)
    slug = "-".join(slug.split())
    return slug[:max_len]


@dataclass
class Manifest:
    work_items: List[WorkItem] = field(default_factory=list)
    project_dir: str = field(default_factory=lambda: os.getcwd())
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    session_count: int = 0
    continuation_count: int = 0

    def add_work_item(
        self, source: str, source_ref: str
    ) -> WorkItem:
        item_id = _next_id(self.work_items)
        slug = _slugify(source_ref)
        branch = f"egregore/{item_id}-{slug}" if slug else f"egregore/{item_id}"
        item = WorkItem(
            id=item_id,
            source=source,
            source_ref=source_ref,
            branch=branch,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self.work_items.append(item)
        return item

    def _get_item(self, item_id: str) -> WorkItem:
        for item in self.work_items:
            if item.id == item_id:
                return item
        raise KeyError(f"No work item with id {item_id}")

    def advance(self, item_id: str) -> None:
        item = self._get_item(item_id)
        stage = item.pipeline_stage
        steps = PIPELINE[stage]
        idx = steps.index(item.pipeline_step)

        if idx + 1 < len(steps):
            item.pipeline_step = steps[idx + 1]
        else:
            stage_idx = STAGE_ORDER.index(stage)
            if stage_idx + 1 < len(STAGE_ORDER):
                next_stage = STAGE_ORDER[stage_idx + 1]
                item.pipeline_stage = next_stage
                item.pipeline_step = PIPELINE[next_stage][0]
            else:
                item.status = "completed"
        item.attempts = 0

    def fail_current_step(
        self, item_id: str, reason: str
    ) -> None:
        item = self._get_item(item_id)
        if item.attempts >= item.max_attempts:
            item.status = "failed"
            item.failure_reason = reason
        else:
            item.attempts += 1

    def next_active_item(self) -> Optional[WorkItem]:
        for item in self.work_items:
            if item.status == "active":
                return item
        return None

    def record_decision(
        self,
        item_id: str,
        step: str,
        chose: str,
        why: str,
    ) -> None:
        item = self._get_item(item_id)
        item.decisions.append({
            "at": datetime.now(timezone.utc).isoformat(),
            "step": step,
            "chose": chose,
            "why": why,
        })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_dir": self.project_dir,
            "created_at": self.created_at,
            "session_count": self.session_count,
            "continuation_count": self.continuation_count,
            "work_items": [w.to_dict() for w in self.work_items],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Manifest:
        items_data = data.pop("work_items", [])
        m = cls(**{
            k: v for k, v in data.items()
            if k in cls.__dataclass_fields__
        })
        m.work_items = [WorkItem.from_dict(w) for w in items_data]
        return m


def save_manifest(manifest: Manifest, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest.to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )


def load_manifest(path: Path) -> Manifest:
    data = json.loads(path.read_text(encoding="utf-8"))
    return Manifest.from_dict(data)
```

**Step 4: Run tests to verify they pass**

Run: `cd plugins/egregore && uv run pytest tests/test_manifest.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add plugins/egregore/scripts/manifest.py \
       plugins/egregore/tests/test_manifest.py
git commit -m "feat(egregore): add manifest state management with pipeline"
```

---

### Task 4: Create config and budget helpers

**Files:**
- Create: `plugins/egregore/scripts/config.py`
- Create: `plugins/egregore/scripts/budget.py`
- Create: `plugins/egregore/tests/test_config.py`
- Create: `plugins/egregore/tests/test_budget.py`

**Step 1: Write failing tests for config**

```python
"""Tests for egregore config management."""
from __future__ import annotations

import json
from pathlib import Path

from config import EgregorConfig, load_config, save_config, default_config


def test_default_config():
    cfg = default_config()
    assert cfg.overseer.method == "github-repo-owner"
    assert cfg.alerts.on_crash is True
    assert cfg.alerts.on_rate_limit is True
    assert cfg.alerts.on_watchdog_relaunch is True
    assert cfg.pipeline.max_attempts_per_step == 3
    assert cfg.pipeline.auto_merge is False
    assert cfg.budget.window_type == "5h"
    assert cfg.budget.cooldown_padding_minutes == 10


def test_save_and_load_config(tmp_path):
    cfg = default_config()
    cfg.overseer.webhook_url = "https://hooks.slack.com/test"
    path = tmp_path / "config.json"
    save_config(cfg, path)

    loaded = load_config(path)
    assert loaded.overseer.webhook_url == "https://hooks.slack.com/test"


def test_load_missing_config_returns_default(tmp_path):
    path = tmp_path / "nonexistent.json"
    cfg = load_config(path)
    assert cfg.overseer.method == "github-repo-owner"
```

**Step 2: Write failing tests for budget**

```python
"""Tests for egregore token budget tracking."""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from budget import Budget, load_budget, save_budget, is_in_cooldown


def test_new_budget():
    b = Budget(window_type="5h")
    assert b.session_count == 0
    assert b.cooldown_until is None


def test_record_rate_limit():
    b = Budget(window_type="5h")
    b.record_rate_limit(cooldown_minutes=60)
    assert b.cooldown_until is not None
    assert b.last_rate_limit_at is not None


def test_is_in_cooldown_true():
    b = Budget(window_type="5h")
    future = (
        datetime.now(timezone.utc) + timedelta(hours=1)
    ).isoformat()
    b.cooldown_until = future
    assert is_in_cooldown(b) is True


def test_is_in_cooldown_false():
    b = Budget(window_type="5h")
    past = (
        datetime.now(timezone.utc) - timedelta(hours=1)
    ).isoformat()
    b.cooldown_until = past
    assert is_in_cooldown(b) is False


def test_is_in_cooldown_none():
    b = Budget(window_type="5h")
    assert is_in_cooldown(b) is False


def test_save_and_load_budget(tmp_path):
    b = Budget(window_type="7d")
    b.session_count = 5
    path = tmp_path / "budget.json"
    save_budget(b, path)
    loaded = load_budget(path)
    assert loaded.window_type == "7d"
    assert loaded.session_count == 5
```

**Step 3: Run tests to verify they fail**

Run: `cd plugins/egregore && uv run pytest tests/test_config.py tests/test_budget.py -v`
Expected: FAIL (modules not found)

**Step 4: Write config.py**

```python
"""Egregore configuration management."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class OverseerConfig:
    method: str = "github-repo-owner"
    email: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_format: str = "generic"


@dataclass
class AlertsConfig:
    on_crash: bool = True
    on_rate_limit: bool = True
    on_pipeline_failure: bool = True
    on_completion: bool = True
    on_watchdog_relaunch: bool = True


@dataclass
class PipelineConfig:
    max_attempts_per_step: int = 3
    skip_brainstorm_for_issues: bool = True
    auto_merge: bool = False


@dataclass
class BudgetConfig:
    window_type: str = "5h"
    cooldown_padding_minutes: int = 10


@dataclass
class EgregorConfig:
    overseer: OverseerConfig = field(
        default_factory=OverseerConfig
    )
    alerts: AlertsConfig = field(default_factory=AlertsConfig)
    pipeline: PipelineConfig = field(
        default_factory=PipelineConfig
    )
    budget: BudgetConfig = field(default_factory=BudgetConfig)


def default_config() -> EgregorConfig:
    return EgregorConfig()


def save_config(cfg: EgregorConfig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(cfg), indent=2) + "\n",
        encoding="utf-8",
    )


def load_config(path: Path) -> EgregorConfig:
    if not path.exists():
        return default_config()
    data = json.loads(path.read_text(encoding="utf-8"))
    return EgregorConfig(
        overseer=OverseerConfig(**data.get("overseer", {})),
        alerts=AlertsConfig(**data.get("alerts", {})),
        pipeline=PipelineConfig(**data.get("pipeline", {})),
        budget=BudgetConfig(**data.get("budget", {})),
    )
```

**Step 5: Write budget.py**

```python
"""Egregore token budget tracking."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional


@dataclass
class Budget:
    window_type: str = "5h"
    window_started_at: Optional[str] = None
    estimated_tokens_used: int = 0
    session_count: int = 0
    last_rate_limit_at: Optional[str] = None
    cooldown_until: Optional[str] = None

    def record_rate_limit(
        self, cooldown_minutes: int = 60
    ) -> None:
        now = datetime.now(timezone.utc)
        self.last_rate_limit_at = now.isoformat()
        self.cooldown_until = (
            now + timedelta(minutes=cooldown_minutes)
        ).isoformat()

    def increment_session(self) -> None:
        self.session_count += 1
        if self.window_started_at is None:
            self.window_started_at = (
                datetime.now(timezone.utc).isoformat()
            )


def is_in_cooldown(budget: Budget) -> bool:
    if budget.cooldown_until is None:
        return False
    now = datetime.now(timezone.utc)
    # Parse ISO format with timezone
    cooldown = datetime.fromisoformat(budget.cooldown_until)
    if cooldown.tzinfo is None:
        cooldown = cooldown.replace(tzinfo=timezone.utc)
    return now < cooldown


def save_budget(budget: Budget, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(budget), indent=2) + "\n",
        encoding="utf-8",
    )


def load_budget(path: Path) -> Budget:
    if not path.exists():
        return Budget()
    data = json.loads(path.read_text(encoding="utf-8"))
    return Budget(**data)
```

**Step 6: Run tests to verify they pass**

Run: `cd plugins/egregore && uv run pytest tests/test_config.py tests/test_budget.py -v`
Expected: All PASS

**Step 7: Commit**

```bash
git add plugins/egregore/scripts/config.py \
       plugins/egregore/scripts/budget.py \
       plugins/egregore/tests/test_config.py \
       plugins/egregore/tests/test_budget.py
git commit -m "feat(egregore): add config and budget state management"
```

---

### Task 5: Create notification system

**Files:**
- Create: `plugins/egregore/scripts/notify.py`
- Create: `plugins/egregore/tests/test_notify.py`

**Step 1: Write failing tests**

```python
"""Tests for egregore notification system."""
from __future__ import annotations

import json
import subprocess
from unittest.mock import patch, MagicMock

from notify import (
    build_issue_body,
    create_github_alert,
    send_webhook,
    AlertEvent,
)


def test_build_issue_body_crash():
    body = build_issue_body(
        event=AlertEvent.CRASH,
        work_item_id="wrk_001",
        work_item_ref="Build REST API",
        stage="quality",
        step="code-refinement",
        detail="exit code 137",
    )
    assert "wrk_001" in body
    assert "Build REST API" in body
    assert "crash" in body.lower() or "Crash" in body


def test_build_issue_body_completion():
    body = build_issue_body(
        event=AlertEvent.COMPLETION,
        work_item_id="wrk_001",
        work_item_ref="Build REST API",
        detail="3 items completed",
    )
    assert "completed" in body.lower() or "Complete" in body


def test_build_issue_body_rate_limit():
    body = build_issue_body(
        event=AlertEvent.RATE_LIMIT,
        detail="Cooldown until 2026-03-06T15:00:00Z",
    )
    assert "cooldown" in body.lower() or "Cooldown" in body


@patch("notify.subprocess.run")
def test_create_github_alert(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    create_github_alert(
        title="[egregore] Test alert",
        body="Test body",
        labels=["egregore/alert"],
    )
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "gh" in cmd
    assert "issue" in cmd
    assert "create" in cmd


@patch("notify.subprocess.run")
def test_send_webhook_generic(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    send_webhook(
        url="https://example.com/hook",
        event=AlertEvent.CRASH,
        detail="test crash",
        webhook_format="generic",
    )
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "curl" in " ".join(cmd)
```

**Step 2: Run to verify failure**

Run: `cd plugins/egregore && uv run pytest tests/test_notify.py -v`
Expected: FAIL

**Step 3: Write notify.py**

```python
"""Egregore notification system: GitHub issues + webhooks."""
from __future__ import annotations

import enum
import json
import subprocess
from typing import List, Optional


class AlertEvent(enum.Enum):
    CRASH = "crash"
    RATE_LIMIT = "rate_limit"
    PIPELINE_FAILURE = "pipeline_failure"
    COMPLETION = "completion"
    WATCHDOG_RELAUNCH = "watchdog_relaunch"


def build_issue_body(
    event: AlertEvent,
    work_item_id: str = "",
    work_item_ref: str = "",
    stage: str = "",
    step: str = "",
    detail: str = "",
) -> str:
    lines = ["## Egregore Alert", ""]
    lines.append(f"**Event:** {event.value}")

    if work_item_id:
        lines.append(f"**Work item:** {work_item_id}")
    if work_item_ref:
        lines.append(f"**Reference:** {work_item_ref}")
    if stage:
        lines.append(f"**Pipeline stage:** {stage} / {step}")
    if detail:
        lines.append(f"**Detail:** {detail}")

    lines.append("")
    lines.append("### Action Required")

    if event == AlertEvent.CRASH:
        lines.append(
            "Egregore will attempt to resume automatically "
            "via the watchdog."
        )
    elif event == AlertEvent.RATE_LIMIT:
        lines.append(
            "Token window exhausted. Egregore will resume "
            "after the cooldown period."
        )
    elif event == AlertEvent.COMPLETION:
        lines.append("All work items have been completed.")
    elif event == AlertEvent.PIPELINE_FAILURE:
        lines.append(
            "Work item failed after max attempts. "
            "Egregore moved on to the next item."
        )
    elif event == AlertEvent.WATCHDOG_RELAUNCH:
        lines.append(
            "The watchdog detected a dead session and "
            "relaunched egregore."
        )

    lines.append("")
    lines.append(
        "To cancel egregore: run `/egregore:dismiss` "
        "or close this issue."
    )
    return "\n".join(lines)


def create_github_alert(
    title: str,
    body: str,
    labels: Optional[List[str]] = None,
) -> None:
    cmd = ["gh", "issue", "create", "--title", title, "--body", body]
    if labels:
        for label in labels:
            cmd.extend(["--label", label])
    subprocess.run(cmd, check=False, capture_output=True)


def send_webhook(
    url: str,
    event: AlertEvent,
    detail: str = "",
    webhook_format: str = "generic",
) -> None:
    if webhook_format == "slack":
        payload = json.dumps({
            "text": f"[egregore] {event.value}: {detail}"
        })
    elif webhook_format == "discord":
        payload = json.dumps({
            "content": f"[egregore] {event.value}: {detail}"
        })
    else:
        payload = json.dumps({
            "event": event.value,
            "detail": detail,
            "source": "egregore",
        })

    cmd = [
        "curl", "-s", "-X", "POST",
        "-H", "Content-Type: application/json",
        "-d", payload,
        url,
    ]
    subprocess.run(cmd, check=False, capture_output=True)


def alert(
    event: AlertEvent,
    overseer_method: str = "github-repo-owner",
    webhook_url: Optional[str] = None,
    webhook_format: str = "generic",
    work_item_id: str = "",
    work_item_ref: str = "",
    stage: str = "",
    step: str = "",
    detail: str = "",
) -> None:
    title = f"[egregore] {event.value}"
    if work_item_id:
        title += f" on {work_item_id}"

    body = build_issue_body(
        event=event,
        work_item_id=work_item_id,
        work_item_ref=work_item_ref,
        stage=stage,
        step=step,
        detail=detail,
    )

    if overseer_method in ("github-repo-owner", "github-issue"):
        create_github_alert(
            title=title,
            body=body,
            labels=["egregore/alert"],
        )

    if webhook_url:
        send_webhook(
            url=webhook_url,
            event=event,
            detail=detail,
            webhook_format=webhook_format,
        )
```

**Step 4: Run tests**

Run: `cd plugins/egregore && uv run pytest tests/test_notify.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add plugins/egregore/scripts/notify.py \
       plugins/egregore/tests/test_notify.py
git commit -m "feat(egregore): add notification system (GitHub issues + webhooks)"
```

---

## Phase 3: Skills

### Task 6: Create summon skill with modules

**Files:**
- Create: `plugins/egregore/skills/summon/SKILL.md`
- Create: `plugins/egregore/skills/summon/modules/pipeline.md`
- Create: `plugins/egregore/skills/summon/modules/budget.md`
- Create: `plugins/egregore/skills/summon/modules/intake.md`
- Create: `plugins/egregore/skills/summon/modules/decisions.md`

**Step 1: Write SKILL.md**

The summon skill is the core orchestrator. It reads the manifest,
picks the next work item, and invokes specialist skills for each
pipeline step. Write the YAML frontmatter and full skill content
following the pattern in
`plugins/conserve/skills/clear-context/SKILL.md`.

Key frontmatter fields:
```yaml
---
name: summon
description: >
  Autonomous orchestrator that manages full development lifecycles.
  Reads the egregore manifest, picks the next active work item,
  and invokes specialist skills for each pipeline step. Handles
  context overflow via continuation agents and token budget via
  graceful shutdown.
category: orchestration
tags:
  - autonomous
  - pipeline
  - orchestrator
  - mission
dependencies:
  - attune:project-brainstorming
  - attune:project-specification
  - attune:project-planning
  - attune:project-execution
  - pensive:code-refinement
  - conserve:bloat-detector
  - sanctum:pr-prep
  - sanctum:pr-review
  - sanctum:commit-messages
  - conserve:clear-context
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Task
  - Skill
progressive_loading: true
modules:
  - modules/pipeline.md
  - modules/budget.md
  - modules/intake.md
  - modules/decisions.md
---
```

Content sections: Overview, When To Use, Orchestration Loop
(read manifest, pick item, map step to skill, invoke, advance,
check budget, repeat), Pipeline-to-Skill Mapping (table mapping
each step to the existing skill/command it invokes), Context
Overflow Protocol, Token Budget Protocol, Failure Handling,
Module Reference.

**Pipeline-to-Skill Mapping** (critical table for SKILL.md):

| Stage | Step | Skill/Action |
|-------|------|--------------|
| intake | parse | Parse prompt or fetch issue via `gh issue view` |
| intake | validate | Validate requirements are actionable |
| intake | prioritize | Order by complexity (single item = skip) |
| build | brainstorm | `Skill(attune:project-brainstorming)` |
| build | specify | `Skill(attune:project-specification)` |
| build | blueprint | `Skill(attune:project-planning)` |
| build | execute | `Skill(attune:project-execution)` |
| quality | code-review | `Skill(pensive:code-refinement)` |
| quality | unbloat | `Skill(conserve:bloat-detector)` |
| quality | code-refinement | `Skill(pensive:code-refinement)` |
| quality | update-tests | `Skill(sanctum:test-updates)` |
| quality | update-docs | `Skill(sanctum:doc-updates)` |
| ship | prepare-pr | `Skill(sanctum:pr-prep)` |
| ship | pr-review | `Skill(sanctum:pr-review)` |
| ship | fix-pr | `Skill(sanctum:pr-review)` + apply fixes |
| ship | merge | `gh pr merge` (if auto_merge enabled) |

**Step 2: Write pipeline.md module**

Stage definitions, step ordering, transition rules.
Include the PIPELINE dict and STAGE_ORDER list as reference.
Document idempotency: each step checks for existing artifacts
before re-doing work.

**Step 3: Write budget.md module**

Token window management protocol. When to check budget,
how to detect rate limits (catch error output from claude),
how to trigger graceful shutdown and write budget.json.

**Step 4: Write intake.md module**

How to parse prompts vs GitHub issues. For prompts: extract
requirements, create branch name. For issues: fetch via
`gh issue view --json`, extract title/body/labels, determine
if brainstorm can be skipped.

**Step 5: Write decisions.md module**

Autonomous decision framework. When facing ambiguity: prefer
simpler approach, log the decision with rationale, never block.
Decision log format and how to write to manifest.

**Step 6: Commit**

```bash
git add plugins/egregore/skills/
git commit -m "feat(egregore): add summon skill with pipeline/budget/intake/decisions modules"
```

---

### Task 7: Create install-watchdog and uninstall-watchdog skills

**Files:**
- Create: `plugins/egregore/skills/install-watchdog/SKILL.md`
- Create: `plugins/egregore/skills/uninstall-watchdog/SKILL.md`

**Step 1: Write install-watchdog SKILL.md**

```yaml
---
name: install-watchdog
description: >
  Install the egregore watchdog daemon using the OS-native
  scheduler. Creates a launchd plist (macOS) or systemd timer
  (Linux) that checks every 5 minutes if egregore needs
  relaunching.
category: setup
tools:
  - Bash
  - Write
  - Read
---
```

Content: detect OS, run appropriate installer script, verify
installation, show how to uninstall.

**Step 2: Write uninstall-watchdog SKILL.md**

```yaml
---
name: uninstall-watchdog
description: >
  Remove the egregore watchdog daemon and clean up all
  associated files.
category: setup
tools:
  - Bash
---
```

Content: detect OS, unload/disable service, remove plist/unit,
clean up pidfile and watchdog log.

**Step 3: Commit**

```bash
git add plugins/egregore/skills/install-watchdog/ \
       plugins/egregore/skills/uninstall-watchdog/
git commit -m "feat(egregore): add watchdog install/uninstall skills"
```

---

## Phase 4: Agents

### Task 8: Create orchestrator agent

**Files:**
- Create: `plugins/egregore/agents/orchestrator.md`

**Step 1: Write orchestrator.md**

Follow the pattern in
`plugins/conserve/agents/continuation-agent.md`.

```yaml
---
name: orchestrator
description: |
  The egregore's autonomous will. Reads the manifest, picks
  the next active work item, invokes specialist skills for each
  pipeline step, and manages the full development lifecycle.

  This agent:
  1. Reads .egregore/manifest.json
  2. Picks the next active work item
  3. Invokes the skill mapped to the current pipeline step
  4. Advances the pipeline on success
  5. Handles failures (retry or mark failed)
  6. Monitors context budget via continuation agents
  7. Monitors token budget via graceful shutdown
  8. Alerts overseer on events via GitHub issues/webhooks
  9. Repeats until all work items are completed or failed
model_preference: default
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Skill
  - Task
  - TodoRead
  - TodoWrite
---
```

Content sections:
- CRITICAL: You Must NOT Stop Early (same pattern as
  continuation-agent - persist until ALL work is done)
- Your First Action (read manifest.json, load config)
- Orchestration Loop (pick item, map step to skill, invoke,
  advance, check budget)
- Context Overflow (at 80%, save manifest, invoke
  clear-context, continuation agent reads manifest on boot)
- Token Budget (detect rate limit errors, save budget.json
  with cooldown, alert overseer, exit cleanly)
- Failure Handling (retry up to max_attempts, then mark
  failed, alert overseer, move to next item)
- Completion (all items done, alert overseer, exit)
- Decision Making (always prefer simpler approach, log
  decisions, never block on ambiguity)

**Step 2: Commit**

```bash
git add plugins/egregore/agents/orchestrator.md
git commit -m "feat(egregore): add orchestrator agent"
```

---

### Task 9: Create sentinel agent

**Files:**
- Create: `plugins/egregore/agents/sentinel.md`

**Step 1: Write sentinel.md**

```yaml
---
name: sentinel
description: |
  Monitors egregore's resource budget and handles graceful
  shutdown when token windows are exhausted. Lightweight
  agent spawned by the orchestrator to check budget status.
model_preference: default
tools:
  - Read
  - Write
  - Bash
---
```

Content: read budget.json, check if approaching limits,
signal orchestrator to save state and exit. This is a
lightweight agent focused solely on budget monitoring.

**Step 2: Commit**

```bash
git add plugins/egregore/agents/sentinel.md
git commit -m "feat(egregore): add sentinel agent for budget monitoring"
```

---

## Phase 5: Hooks

### Task 10: Create Stop hook

**Files:**
- Create: `plugins/egregore/hooks/stop_hook.py`
- Create: `plugins/egregore/hooks/hooks.json`
- Create: `plugins/egregore/tests/test_stop_hook.py`

**Step 1: Write failing test**

```python
"""Tests for egregore stop hook."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

# Must be 3.9 compatible - no union types, no match


def test_stop_hook_blocks_when_work_remains(tmp_path):
    """Stop hook should block exit when manifest has active items."""
    manifest = {
        "project_dir": str(tmp_path),
        "work_items": [
            {"id": "wrk_001", "status": "active",
             "source": "prompt", "source_ref": "test",
             "pipeline_stage": "build", "pipeline_step": "execute"}
        ],
    }
    manifest_path = tmp_path / ".egregore" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps(manifest))

    # Simulate the hook by importing and calling main
    # The hook reads manifest from CWD/.egregore/manifest.json
    # and outputs JSON with decision to block or allow


def test_stop_hook_allows_when_all_done(tmp_path):
    """Stop hook should allow exit when all items completed."""
    manifest = {
        "project_dir": str(tmp_path),
        "work_items": [
            {"id": "wrk_001", "status": "completed",
             "source": "prompt", "source_ref": "test",
             "pipeline_stage": "ship", "pipeline_step": "merge"}
        ],
    }
    manifest_path = tmp_path / ".egregore" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps(manifest))


def test_stop_hook_allows_when_no_manifest(tmp_path):
    """Stop hook should allow exit when no manifest exists."""
    pass  # No manifest = not an egregore session
```

**Step 2: Run to verify failure**

Run: `cd plugins/egregore && uv run pytest tests/test_stop_hook.py -v`

**Step 3: Write stop_hook.py**

This is the intelligent ralph-wiggum equivalent. MUST be
Python 3.9 compatible.

```python
#!/usr/bin/env python3
"""Egregore Stop hook: blocks exit when work remains.

Like ralph-wiggum's stop hook but state-aware. Reads the
egregore manifest to decide whether to block the exit and
re-inject the orchestration prompt.

IMPORTANT: Must use Python 3.9 compatible syntax.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def find_manifest() -> Path:
    """Find manifest.json in CWD or parent directories."""
    cwd = Path(os.getcwd())
    for directory in [cwd] + list(cwd.parents):
        candidate = directory / ".egregore" / "manifest.json"
        if candidate.exists():
            return candidate
    return cwd / ".egregore" / "manifest.json"


def has_active_work(manifest_path: Path) -> bool:
    """Check if manifest has active or paused work items."""
    if not manifest_path.exists():
        return False
    try:
        data = json.loads(manifest_path.read_text())
        items = data.get("work_items", [])
        return any(
            item.get("status") in ("active", "paused")
            for item in items
        )
    except (json.JSONDecodeError, OSError):
        return False


def main() -> None:
    """Stop hook entry point."""
    # Read stop payload from stdin
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    manifest_path = find_manifest()

    if not has_active_work(manifest_path):
        # No active work: allow exit
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)

    # Active work remains: block exit and re-inject prompt
    relaunch_prompt_path = manifest_path.parent / "relaunch-prompt.md"
    if relaunch_prompt_path.exists():
        reason = relaunch_prompt_path.read_text()
    else:
        reason = (
            "Egregore has active work items. "
            "Read .egregore/manifest.json and continue "
            "the pipeline from the current step. "
            "Invoke Skill(egregore:summon) to resume."
        )

    output = {
        "decision": "block",
        "reason": reason,
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
```

**Step 4: Write hooks.json**

```json
{
  "hooks": {
    "Stop": [
      {
        "_comment": "Block exit when egregore has active work items",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/stop_hook.py",
            "timeout": 2
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "_comment": "Resume egregore orchestration on session start",
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/session_start_hook.py",
            "timeout": 2
          }
        ]
      }
    ]
  }
}
```

**Step 5: Complete and run tests**

Run: `cd plugins/egregore && uv run pytest tests/test_stop_hook.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add plugins/egregore/hooks/
git commit -m "feat(egregore): add Stop hook (state-aware ralph-wiggum)"
```

---

### Task 11: Create SessionStart hook

**Files:**
- Create: `plugins/egregore/hooks/session_start_hook.py`
- Create: `plugins/egregore/tests/test_session_start_hook.py`

**Step 1: Write session_start_hook.py**

Reads the manifest on session start. If active work exists,
injects context telling claude to invoke `Skill(egregore:summon)`
to resume. MUST be Python 3.9 compatible.

```python
#!/usr/bin/env python3
"""Egregore SessionStart hook: resumes orchestration on boot.

When a session starts (or resumes after crash/relaunch),
this hook checks for an active egregore manifest and injects
context to resume the pipeline.

IMPORTANT: Must use Python 3.9 compatible syntax.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def find_manifest() -> Path:
    cwd = Path(os.getcwd())
    for directory in [cwd] + list(cwd.parents):
        candidate = directory / ".egregore" / "manifest.json"
        if candidate.exists():
            return candidate
    return cwd / ".egregore" / "manifest.json"


def main() -> None:
    # Read hook input
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    manifest_path = find_manifest()
    if not manifest_path.exists():
        sys.exit(0)

    try:
        data = json.loads(manifest_path.read_text())
    except (json.JSONDecodeError, OSError):
        sys.exit(0)

    items = data.get("work_items", [])
    active = [
        i for i in items
        if i.get("status") in ("active", "paused")
    ]

    if not active:
        sys.exit(0)

    current = active[0]
    summary = (
        f"Egregore session resuming. "
        f"{len(active)} active work item(s). "
        f"Current: {current.get('id', '?')} at "
        f"{current.get('pipeline_stage', '?')}/"
        f"{current.get('pipeline_step', '?')}. "
        f"Invoke Skill(egregore:summon) to continue."
    )

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": summary,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
```

**Step 2: Write tests, run, verify**

Run: `cd plugins/egregore && uv run pytest tests/test_session_start_hook.py -v`

**Step 3: Commit**

```bash
git add plugins/egregore/hooks/session_start_hook.py \
       plugins/egregore/tests/test_session_start_hook.py
git commit -m "feat(egregore): add SessionStart hook for auto-resume"
```

---

## Phase 6: Watchdog

### Task 12: Create watchdog script

**Files:**
- Create: `plugins/egregore/scripts/watchdog.sh`

**Step 1: Write watchdog.sh**

```bash
#!/usr/bin/env bash
# egregore-watchdog.sh
#
# Checks if egregore needs relaunching. Run via launchd or
# systemd timer every 5 minutes. Pure shell, no network calls,
# fully auditable.
set -euo pipefail

EGREGORE_DIR="${EGREGORE_DIR:-.egregore}"
MANIFEST="$EGREGORE_DIR/manifest.json"
BUDGET="$EGREGORE_DIR/budget.json"
PIDFILE="$EGREGORE_DIR/pid"
LOG="$EGREGORE_DIR/watchdog.log"

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ): $*" >> "$LOG"; }

# No manifest = nothing to do
if [[ ! -f "$MANIFEST" ]]; then
    exit 0
fi

# Check if work remains
if ! command -v jq &>/dev/null; then
    log "ERROR: jq not installed, cannot parse manifest"
    exit 1
fi

remaining=$(jq '[.work_items[] | select(.status == "active" or .status == "paused")] | length' "$MANIFEST" 2>/dev/null || echo "0")
if [[ "$remaining" -eq 0 ]]; then
    log "No active work items, exiting"
    exit 0
fi

# Check cooldown
if [[ -f "$BUDGET" ]]; then
    cooldown=$(jq -r '.cooldown_until // empty' "$BUDGET" 2>/dev/null)
    if [[ -n "$cooldown" ]]; then
        now=$(date +%s)
        if [[ "$(uname)" == "Darwin" ]]; then
            until_ts=$(date -jf "%Y-%m-%dT%H:%M:%S" "${cooldown%%.*}" +%s 2>/dev/null || echo "0")
        else
            until_ts=$(date -d "$cooldown" +%s 2>/dev/null || echo "0")
        fi
        if [[ "$now" -lt "$until_ts" ]]; then
            log "In cooldown until $cooldown, waiting"
            exit 0
        fi
    fi
fi

# Check if session already running
if [[ -f "$PIDFILE" ]]; then
    pid=$(cat "$PIDFILE")
    if kill -0 "$pid" 2>/dev/null; then
        exit 0  # session alive
    fi
    log "Stale pid $pid detected (crash). Cleaning up."
    rm -f "$PIDFILE"
fi

# Read project dir from manifest
project_dir=$(jq -r '.project_dir' "$MANIFEST" 2>/dev/null)
if [[ -z "$project_dir" || "$project_dir" == "null" ]]; then
    project_dir="$(pwd)"
fi

# Relaunch
log "Relaunching egregore session ($remaining active items)"
cd "$project_dir"

relaunch_prompt="$EGREGORE_DIR/relaunch-prompt.md"
if [[ -f "$relaunch_prompt" ]]; then
    prompt_arg="-p"
    prompt_content="$(cat "$relaunch_prompt")"
else
    prompt_arg="-p"
    prompt_content="Egregore resuming. Read .egregore/manifest.json and invoke Skill(egregore:summon) to continue the pipeline."
fi

nohup claude "$prompt_arg" "$prompt_content" \
    >> "$LOG" 2>&1 &
echo $! > "$PIDFILE"
log "Launched with PID $!"
```

**Step 2: Make executable**

Run: `chmod +x plugins/egregore/scripts/watchdog.sh`

**Step 3: Commit**

```bash
git add plugins/egregore/scripts/watchdog.sh
git commit -m "feat(egregore): add watchdog script for session relaunching"
```

---

### Task 13: Create OS-specific installers

**Files:**
- Create: `plugins/egregore/scripts/install_launchd.sh`
- Create: `plugins/egregore/scripts/install_systemd.sh`

**Step 1: Write install_launchd.sh (macOS)**

```bash
#!/usr/bin/env bash
# Install egregore watchdog as a macOS launchd agent
set -euo pipefail

INTERVAL="${1:-300}"  # Default: 5 minutes
WATCHDOG_SCRIPT="$(cd "$(dirname "$0")" && pwd)/watchdog.sh"
WORKING_DIR="${2:-$(pwd)}"
PLIST_NAME="com.egregore.watchdog"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

if [[ ! -f "$WATCHDOG_SCRIPT" ]]; then
    echo "Error: watchdog.sh not found at $WATCHDOG_SCRIPT"
    exit 1
fi

cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${WATCHDOG_SCRIPT}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${WORKING_DIR}</string>
    <key>StartInterval</key>
    <integer>${INTERVAL}</integer>
    <key>StandardOutPath</key>
    <string>${WORKING_DIR}/.egregore/watchdog-launchd.log</string>
    <key>StandardErrorPath</key>
    <string>${WORKING_DIR}/.egregore/watchdog-launchd.log</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF

launchctl load "$PLIST_PATH"
echo "Installed: $PLIST_PATH"
echo "Checking every ${INTERVAL}s in ${WORKING_DIR}"
echo "To uninstall: launchctl unload $PLIST_PATH && rm $PLIST_PATH"
```

**Step 2: Write install_systemd.sh (Linux)**

```bash
#!/usr/bin/env bash
# Install egregore watchdog as a systemd user timer
set -euo pipefail

INTERVAL="${1:-5}"  # Default: 5 minutes
WATCHDOG_SCRIPT="$(cd "$(dirname "$0")" && pwd)/watchdog.sh"
WORKING_DIR="${2:-$(pwd)}"
UNIT_DIR="$HOME/.config/systemd/user"
SERVICE_NAME="egregore-watchdog"

mkdir -p "$UNIT_DIR"

cat > "$UNIT_DIR/${SERVICE_NAME}.service" << EOF
[Unit]
Description=Egregore Watchdog Service

[Service]
Type=oneshot
WorkingDirectory=${WORKING_DIR}
ExecStart=${WATCHDOG_SCRIPT}
EOF

cat > "$UNIT_DIR/${SERVICE_NAME}.timer" << EOF
[Unit]
Description=Egregore Watchdog Timer

[Timer]
OnBootSec=${INTERVAL}min
OnUnitActiveSec=${INTERVAL}min

[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now "${SERVICE_NAME}.timer"
echo "Installed: ${SERVICE_NAME}.timer"
echo "Checking every ${INTERVAL}min in ${WORKING_DIR}"
echo "To uninstall: systemctl --user disable --now ${SERVICE_NAME}.timer"
```

**Step 3: Make executable and commit**

```bash
chmod +x plugins/egregore/scripts/install_launchd.sh
chmod +x plugins/egregore/scripts/install_systemd.sh
git add plugins/egregore/scripts/install_launchd.sh \
       plugins/egregore/scripts/install_systemd.sh
git commit -m "feat(egregore): add launchd and systemd watchdog installers"
```

---

## Phase 7: Commands

### Task 14: Create summon command

**Files:**
- Create: `plugins/egregore/commands/summon.md`

**Step 1: Write summon.md**

```yaml
---
name: summon
description: >
  Summon the egregore to autonomously process work items
  through the full development lifecycle
usage: >
  /egregore:summon "<prompt>" [--window 5h|7d]
  [--indefinite] [--issues N,N] [--issues-label LABEL]
---
```

Content: When To Use, When NOT To Use, Usage examples,
Options table, What Happens (intake, build, quality, ship),
Configuration reference, See Also.

The command invokes `Skill(egregore:summon)` with the
parsed arguments.

**Step 2: Commit**

```bash
git add plugins/egregore/commands/summon.md
git commit -m "feat(egregore): add /egregore:summon command"
```

---

### Task 15: Create dismiss and status commands

**Files:**
- Create: `plugins/egregore/commands/dismiss.md`
- Create: `plugins/egregore/commands/status.md`

**Step 1: Write dismiss.md**

```yaml
---
name: dismiss
description: Stop egregore gracefully, saving all state
usage: /egregore:dismiss
---
```

Content: marks all active items as paused, saves manifest,
removes pidfile, watchdog sees no active work and stays idle.

**Step 2: Write status.md**

```yaml
---
name: status
description: Show current egregore state and progress
usage: /egregore:status
---
```

Content: reads manifest.json, budget.json, config.json.
Displays work item summary, current pipeline position,
budget status, session/continuation counts, decision log
tail.

**Step 3: Commit**

```bash
git add plugins/egregore/commands/dismiss.md \
       plugins/egregore/commands/status.md
git commit -m "feat(egregore): add /egregore:dismiss and /egregore:status commands"
```

---

### Task 16: Create watchdog commands

**Files:**
- Create: `plugins/egregore/commands/install-watchdog.md`
- Create: `plugins/egregore/commands/uninstall-watchdog.md`

**Step 1: Write install-watchdog.md**

```yaml
---
name: install-watchdog
description: Install the egregore watchdog daemon
usage: /egregore:install-watchdog [--window 5h|7d]
---
```

**Step 2: Write uninstall-watchdog.md**

```yaml
---
name: uninstall-watchdog
description: Remove the egregore watchdog daemon
usage: /egregore:uninstall-watchdog
---
```

**Step 3: Commit**

```bash
git add plugins/egregore/commands/install-watchdog.md \
       plugins/egregore/commands/uninstall-watchdog.md
git commit -m "feat(egregore): add watchdog install/uninstall commands"
```

---

## Phase 8: Templates

### Task 17: Create relaunch prompt and alert templates

**Files:**
- Create: `plugins/egregore/templates/relaunch-prompt.md`
- Create: `plugins/egregore/templates/alert-crash.md`
- Create: `plugins/egregore/templates/alert-completion.md`
- Create: `plugins/egregore/templates/webhook-payloads/slack.json`
- Create: `plugins/egregore/templates/webhook-payloads/discord.json`
- Create: `plugins/egregore/templates/webhook-payloads/generic.json`

**Step 1: Write relaunch-prompt.md**

This is the prompt the watchdog feeds to claude on relaunch:

```markdown
You are the egregore, an autonomous agent orchestrator.
A previous session ended (crash, rate limit, or context
overflow). You must resume work.

1. Read `.egregore/manifest.json` to understand current state
2. Read `.egregore/config.json` for configuration
3. Read `.egregore/budget.json` for token budget status
4. Invoke `Skill(egregore:summon)` to continue the pipeline

Do NOT ask for human input. Make autonomous decisions.
Do NOT stop until all work items are completed or failed.
```

**Step 2: Write alert templates**

Templates for GitHub issue bodies. Use `{{variables}}`
for substitution by notify.py.

**Step 3: Write webhook payload templates**

JSON templates for Slack, Discord, and generic webhook
formats.

**Step 4: Commit**

```bash
git add plugins/egregore/templates/
git commit -m "feat(egregore): add relaunch prompt and alert templates"
```

---

## Phase 9: Integration

### Task 18: Create conftest.py and integration test

**Files:**
- Create: `plugins/egregore/tests/conftest.py`
- Create: `plugins/egregore/tests/test_integration.py`

**Step 1: Write conftest.py**

```python
"""Shared test fixtures for egregore plugin."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def egregore_dir(tmp_path):
    """Create a temporary .egregore directory."""
    d = tmp_path / ".egregore"
    d.mkdir()
    return d


@pytest.fixture
def sample_manifest(egregore_dir):
    """Create a sample manifest with one active work item."""
    manifest = {
        "project_dir": str(egregore_dir.parent),
        "created_at": "2026-03-06T10:00:00Z",
        "session_count": 1,
        "continuation_count": 0,
        "work_items": [
            {
                "id": "wrk_001",
                "source": "prompt",
                "source_ref": "Build a REST API",
                "branch": "egregore/wrk-001-build-a-rest-api",
                "pipeline_stage": "build",
                "pipeline_step": "execute",
                "started_at": "2026-03-06T10:00:00Z",
                "decisions": [],
                "attempts": 0,
                "max_attempts": 3,
                "status": "active",
                "failure_reason": "",
            }
        ],
    }
    path = egregore_dir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2))
    return path
```

**Step 2: Write integration test**

```python
"""Integration tests for egregore pipeline flow."""
from __future__ import annotations

import json
from pathlib import Path

from manifest import Manifest, save_manifest, load_manifest
from config import default_config, save_config, load_config
from budget import Budget, save_budget, load_budget


def test_full_pipeline_advancement():
    """Test advancing a work item through the entire pipeline."""
    m = Manifest()
    item = m.add_work_item(
        source="prompt", source_ref="test project"
    )

    steps_seen = []
    while item.status == "active":
        steps_seen.append(
            f"{item.pipeline_stage}/{item.pipeline_step}"
        )
        m.advance(item.id)

    assert item.status == "completed"
    assert steps_seen[0] == "intake/parse"
    assert steps_seen[-1] == "ship/merge"
    assert len(steps_seen) == 16  # total pipeline steps


def test_roundtrip_all_state(tmp_path):
    """Test saving and loading all state files."""
    egregore_dir = tmp_path / ".egregore"
    egregore_dir.mkdir()

    # Manifest
    m = Manifest(project_dir=str(tmp_path))
    m.add_work_item(source="prompt", source_ref="test")
    save_manifest(m, egregore_dir / "manifest.json")
    loaded_m = load_manifest(egregore_dir / "manifest.json")
    assert len(loaded_m.work_items) == 1

    # Config
    cfg = default_config()
    save_config(cfg, egregore_dir / "config.json")
    loaded_cfg = load_config(egregore_dir / "config.json")
    assert loaded_cfg.alerts.on_crash is True

    # Budget
    b = Budget(window_type="7d")
    save_budget(b, egregore_dir / "budget.json")
    loaded_b = load_budget(egregore_dir / "budget.json")
    assert loaded_b.window_type == "7d"
```

**Step 3: Run all tests**

Run: `cd plugins/egregore && uv run pytest tests/ -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add plugins/egregore/tests/
git commit -m "feat(egregore): add integration tests and conftest"
```

---

### Task 19: Create README.md

**Files:**
- Create: `plugins/egregore/README.md`

**Step 1: Write README**

Follow the pattern of existing plugin READMEs. Include:
- What egregore is (the concept, the plugin)
- Quick start (`/egregore:summon "prompt" --window 5h`)
- Commands reference table
- Configuration reference
- Watchdog setup
- Architecture overview (3-layer diagram)
- Comparison with ralph-wiggum
- Future roadmap (Approach C features)

**Step 2: Commit**

```bash
git add plugins/egregore/README.md
git commit -m "docs(egregore): add plugin README"
```

---

### Task 20: Create future GitHub issues for Approach C evolution

**Files:** None (GitHub issues only)

**Step 1: Create issues**

```bash
gh issue create --title "[egregore] Parallel work items via worktrees" \
  --label "enhancement,egregore" \
  --body "Process multiple work items concurrently using git worktrees."

gh issue create --title "[egregore] Parallel pipeline stages" \
  --label "enhancement,egregore" \
  --body "Run independent quality gates in parallel (code-review + update-docs + unbloat)."

gh issue create --title "[egregore] Agent specialization" \
  --label "enhancement,egregore" \
  --body "Dedicated long-lived agents for specific pipeline stages."

gh issue create --title "[egregore] Cross-item learning" \
  --label "enhancement,egregore" \
  --body "Decision log from completed items informs strategy on future items."

gh issue create --title "[egregore] Multi-repo support" \
  --label "enhancement,egregore" \
  --body "Single egregore instance managing work across multiple repositories."
```

**Step 2: Verify issues created**

Run: `gh issue list --label egregore`

---

## Execution Notes

- **Python version**: All hook scripts MUST be 3.9 compatible
  (use `from __future__ import annotations`, no `X | Y` unions,
  no `match/case`, no `datetime.UTC`)
- **Plugin version**: 1.6.0 (matching current release branch)
- **State files**: All in `.egregore/` directory (add to
  `.gitignore`)
- **Testing**: Run `cd plugins/egregore && uv run pytest tests/ -v`
  after each phase
- **Pre-commit**: Existing hooks will validate plugin structure
  automatically on commit
