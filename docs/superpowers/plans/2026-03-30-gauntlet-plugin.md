# Gauntlet Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the gauntlet plugin that reintegrates developers
into codebases through knowledge extraction, challenge generation,
and pre-commit gates with adaptive spaced repetition.

**Architecture:** Three-layer design: knowledge extraction
(AST + AI) produces a queryable knowledge base, a challenge
engine generates six exercise types with adaptive weighting,
and integration points (pre-commit hook, commands, skills)
embed challenges into the development workflow.

**Tech Stack:** Python 3.9+, Claude Code plugin SDK (hooks,
skills, commands, agents), AST module, JSON/YAML persistence,
pytest for testing.

**Spec:** `docs/superpowers/specs/2026-03-30-gauntlet-plugin-design.md`

---

## File Structure

```
plugins/gauntlet/
├── .claude-plugin/
│   └── plugin.json
├── src/gauntlet/
│   ├── __init__.py
│   ├── models.py             # All dataclasses
│   ├── knowledge_store.py    # Knowledge base persistence + YAML annotations
│   ├── extraction.py         # Knowledge extraction from AST + files
│   ├── challenges.py         # Challenge generation (6 types)
│   ├── scoring.py            # Answer evaluation
│   ├── progress.py           # Adaptive weighting + spaced repetition
│   └── query.py              # Agent-facing query API
├── scripts/
│   ├── extractor.py        # CLI entry for extraction
│   ├── challenge_engine.py # CLI entry for challenge generation
│   ├── answer_evaluator.py # CLI entry for answer scoring
│   └── progress_tracker.py # CLI entry for progress stats
├── hooks/
│   ├── hooks.json
│   └── precommit_gate.py   # Pre-commit challenge gate
├── skills/
│   ├── extract/SKILL.md
│   ├── challenge/SKILL.md
│   ├── onboard/SKILL.md
│   └── curate/SKILL.md
├── agents/
│   └── extractor.md
├── commands/
│   ├── gauntlet.md
│   ├── extract.md
│   ├── progress.md
│   ├── onboard.md
│   └── curate.md
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   ├── test_extraction.py
│   │   ├── test_challenges.py
│   │   ├── test_scoring.py
│   │   ├── test_progress.py
│   │   ├── test_query.py
│   │   └── test_precommit.py
│   └── integration/
│       ├── __init__.py
│       └── test_end_to_end.py
├── pyproject.toml
├── Makefile
└── README.md
```

---

## Phase 1: Foundation

### Task 1: Plugin Scaffolding

**Files:**
- Create: `plugins/gauntlet/.claude-plugin/plugin.json`
- Create: `plugins/gauntlet/pyproject.toml`
- Create: `plugins/gauntlet/Makefile`
- Create: `plugins/gauntlet/src/gauntlet/__init__.py`
- Create: `plugins/gauntlet/tests/__init__.py`
- Create: `plugins/gauntlet/tests/unit/__init__.py`
- Create: `plugins/gauntlet/tests/integration/__init__.py`
- Create: `plugins/gauntlet/tests/conftest.py`

- [ ] **Step 1: Create plugin.json**

```json
{
  "name": "gauntlet",
  "version": "1.0.0",
  "description": "Codebase learning through knowledge extraction, challenges, and spaced repetition. Prevents knowledge atrophy for experienced developers and accelerates onboarding for new ones.",
  "skills": [
    {
      "name": "extract",
      "description": "Analyze a codebase and build a knowledge base of business logic, architecture, data flow, and engineering patterns.",
      "path": "skills/extract/SKILL.md"
    },
    {
      "name": "challenge",
      "description": "Run a gauntlet challenge session with adaptive difficulty. Tests codebase understanding through multiple choice, code completion, trace exercises, and more.",
      "path": "skills/challenge/SKILL.md"
    },
    {
      "name": "onboard",
      "description": "Guided onboarding path through five stages: big picture, core domain, interfaces, patterns, and hardening.",
      "path": "skills/onboard/SKILL.md"
    },
    {
      "name": "curate",
      "description": "Add or edit knowledge annotations. Capture tribal knowledge, business context, and rationale that cannot be inferred from code.",
      "path": "skills/curate/SKILL.md"
    }
  ],
  "commands": [
    {
      "name": "gauntlet",
      "description": "Run an ad-hoc gauntlet challenge session (5 questions, random scope)",
      "path": "commands/gauntlet.md"
    },
    {
      "name": "gauntlet-extract",
      "description": "Rebuild the knowledge base from the current codebase",
      "path": "commands/extract.md"
    },
    {
      "name": "gauntlet-progress",
      "description": "Show challenge accuracy stats, weak areas, and streak",
      "path": "commands/progress.md"
    },
    {
      "name": "gauntlet-onboard",
      "description": "Start or resume a guided onboarding path",
      "path": "commands/onboard.md"
    },
    {
      "name": "gauntlet-curate",
      "description": "Add or edit a knowledge annotation",
      "path": "commands/curate.md"
    }
  ],
  "agents": [
    {
      "name": "extractor",
      "description": "Autonomous knowledge extraction agent. Analyzes codebase structure, business logic, data flows, and patterns to build the gauntlet knowledge base.",
      "path": "agents/extractor.md"
    }
  ],
  "hooks": [
    "hooks/hooks.json"
  ],
  "dependencies": [],
  "keywords": [
    "learning",
    "onboarding",
    "knowledge",
    "challenges",
    "spaced-repetition",
    "pre-commit",
    "codebase-fluency"
  ],
  "author": {
    "name": "Alex Thola",
    "url": "https://github.com/athola"
  },
  "license": "MIT"
}
```

- [ ] **Step 2: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "gauntlet-dev"
version = "1.0.0"
description = "Codebase learning through knowledge extraction and spaced repetition"
authors = [
    {name = "Alex Thola", email = "alexthola@gmail.com"}
]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.9"
dependencies = [
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.14.13",
    "mypy>=1.11.0",
    "pytest>=8.0",
    "pytest-cov>=4.0",
]

[tool.hatch.build.targets.wheel]
packages = ["src/gauntlet", "scripts"]

[tool.ruff]
line-length = 88
target-version = "py39"
exclude = [".venv", ".uv-cache"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "S", "PL", "D"]
extend-ignore = ["S101", "E203", "D203", "D213", "UP017"]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = [
    "S101", "S108", "PLR2004", "D102", "D103", "D205", "D400", "D415",
    "D212", "S603", "S607", "PLW1510",
]
"scripts/**/*.py" = ["S603", "S607", "PLR0911", "PLR2004", "UP045", "S105"]
"hooks/**/*.py" = ["S603", "S607", "PLR0911", "PLR2004", "UP045", "T201"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
pythonpath = ["src", "scripts", "hooks"]
addopts = "-v --cov=src/gauntlet --cov-report=term-missing --cov-fail-under=90"
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
]

[tool.coverage.run]
source = ["src/gauntlet"]
omit = ["tests/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
fail_under = 90
```

- [ ] **Step 3: Create Makefile**

```makefile
# Gauntlet Plugin Makefile
# Codebase learning through knowledge extraction and spaced repetition

.PHONY: help deps fix check clean \
	status debug-variables \
	lint format type-check typecheck security test-unit test

# Plugin-specific variables (must be before include)
SRC_DIRS := src/gauntlet scripts hooks tests
RUFF_TARGETS := src/ scripts/ hooks/ tests/
MYPY_TARGETS := src/ scripts/
BANDIT_TARGETS := src/ scripts/ hooks/
COV_DIRS := src/gauntlet
PYTEST_TARGETS := tests/

ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
-include $(ABSTRACT_DIR)/config/make/python.mk

help: ## Show this help message
	@echo "Gauntlet Plugin - Make Targets"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

deps: ## Install dependencies
	$(UV) sync

fix: ## Auto-fix lint issues
	$(RUFF) check --fix $(RUFF_TARGETS)

test: ## Run tests
	$(PYTEST) $(PYTEST_TARGETS) -v --tb=short

check: lint type-check test ## Run all checks
	@echo "All checks passed!"

clean: ## Clean artifacts
	rm -rf .venv .uv-cache __pycache__ .mypy_cache .pytest_cache

status: ## Show project overview
	@echo "Gauntlet Plugin Status:"
	@echo "Source:   $$(find src/ -name '*.py' 2>/dev/null | wc -l)"
	@echo "Scripts:  $$(find scripts/ -name '*.py' 2>/dev/null | wc -l)"
	@echo "Hooks:    $$(find hooks/ -name '*.py' 2>/dev/null | wc -l)"
	@echo "Tests:    $$(find tests/ -name 'test_*.py' 2>/dev/null | wc -l)"

debug-variables: ## Show Makefile variable values
	@echo "=== Makefile Variables ==="
	@echo "PYTHON: $(PYTHON)"
	@echo "UV: $(UV)"
	@echo "UV_RUN: $(UV_RUN)"
	@echo "SRC_DIRS: $(SRC_DIRS)"

Makefile.local:;
-include Makefile.local

%::
	@echo "Error: Unknown target '$$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
```

- [ ] **Step 4: Create __init__.py files and conftest.py**

`plugins/gauntlet/src/gauntlet/__init__.py`:
```python
"""Gauntlet: codebase learning through knowledge extraction and spaced repetition."""

from __future__ import annotations

__version__ = "1.0.0"
```

`plugins/gauntlet/tests/__init__.py`: empty file
`plugins/gauntlet/tests/unit/__init__.py`: empty file
`plugins/gauntlet/tests/integration/__init__.py`: empty file

`plugins/gauntlet/tests/conftest.py`:
```python
"""Shared test fixtures for gauntlet plugin."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture()
def tmp_gauntlet_dir(tmp_path: Path) -> Path:
    """Create a temporary .gauntlet directory structure."""
    gauntlet_dir = tmp_path / ".gauntlet"
    gauntlet_dir.mkdir()
    (gauntlet_dir / "annotations").mkdir()
    (gauntlet_dir / "progress").mkdir()
    (gauntlet_dir / "state").mkdir()
    return gauntlet_dir


@pytest.fixture()
def sample_knowledge_base(tmp_gauntlet_dir: Path) -> Path:
    """Create a sample knowledge.json."""
    entries = [
        {
            "id": "kb-001",
            "category": "business_logic",
            "module": "src/auth/token_manager.py",
            "concept": "Token refresh before validation",
            "detail": "Tokens are refreshed before validation to prevent mid-session expiry during long API calls.",
            "related_files": ["src/auth/middleware.py", "src/api/session.py"],
            "difficulty": 3,
            "tags": ["auth", "tokens", "business-rule"],
            "extracted_at": "2026-03-30T12:00:00Z",
            "source": "automated",
            "consumers": ["both"],
        },
        {
            "id": "kb-002",
            "category": "architecture",
            "module": "src/api/router.py",
            "concept": "Router delegates to domain services",
            "detail": "The API router never contains business logic. It validates input, delegates to a domain service, and formats the response.",
            "related_files": ["src/services/user_service.py", "src/api/schemas.py"],
            "difficulty": 2,
            "tags": ["architecture", "separation-of-concerns"],
            "extracted_at": "2026-03-30T12:00:00Z",
            "source": "automated",
            "consumers": ["both"],
        },
        {
            "id": "kb-003",
            "category": "data_flow",
            "module": "src/pipeline/ingestion.py",
            "concept": "Data flows from ingestion through validation to storage",
            "detail": "Raw input enters via ingestion, passes through schema validation, gets transformed, and is persisted to the database.",
            "related_files": ["src/pipeline/validation.py", "src/pipeline/storage.py"],
            "difficulty": 4,
            "tags": ["pipeline", "data-flow"],
            "extracted_at": "2026-03-30T12:00:00Z",
            "source": "automated",
            "consumers": ["both"],
        },
    ]
    kb_path = tmp_gauntlet_dir / "knowledge.json"
    kb_path.write_text(json.dumps(entries, indent=2))
    return kb_path


@pytest.fixture()
def sample_annotation(tmp_gauntlet_dir: Path) -> Path:
    """Create a sample YAML annotation."""
    annotation = (
        "module: src/auth/token_manager.py\n"
        'concept: "Token refresh happens before validation, not after"\n'
        "why: >\n"
        "  Historical incident: users were getting logged out mid-session\n"
        "  when tokens expired during long API calls.\n"
        "related_files:\n"
        "  - src/auth/middleware.py\n"
        "  - src/api/session.py\n"
        "difficulty: 3\n"
        "tags: [auth, tokens, business-rule]\n"
    )
    path = tmp_gauntlet_dir / "annotations" / "auth-token-expiry.yaml"
    path.write_text(annotation)
    return path


@pytest.fixture()
def sample_python_file(tmp_path: Path) -> Path:
    """Create a sample Python source file for extraction testing."""
    src = tmp_path / "src" / "example.py"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text(
        'from __future__ import annotations\n'
        '\n'
        '\n'
        'def calculate_discount(price: float, tier: str) -> float:\n'
        '    """Calculate discount based on customer tier.\n'
        '\n'
        '    Business rule: premium customers get 20%%, standard get 10%%,\n'
        '    and trial customers get no discount.\n'
        '    """\n'
        '    rates = {"premium": 0.20, "standard": 0.10, "trial": 0.0}\n'
        '    rate = rates.get(tier, 0.0)\n'
        '    return round(price * (1 - rate), 2)\n'
    )
    return src
```

- [ ] **Step 5: Verify scaffolding**

Run: `cd plugins/gauntlet && ls -la .claude-plugin/plugin.json pyproject.toml Makefile src/gauntlet/__init__.py tests/conftest.py`
Expected: all files listed without error

- [ ] **Step 6: Commit scaffolding**

```bash
git add plugins/gauntlet/
git commit -m "feat(gauntlet): add plugin scaffolding

Plugin structure for codebase learning: plugin.json, pyproject.toml,
Makefile, test fixtures. Implements #192."
```

---

### Task 2: Data Models

**Files:**
- Create: `plugins/gauntlet/src/gauntlet/models.py`
- Create: `plugins/gauntlet/tests/unit/test_models.py`

- [ ] **Step 1: Write failing tests for data models**

`plugins/gauntlet/tests/unit/test_models.py`:
```python
"""Tests for gauntlet data models."""

from __future__ import annotations

import json

from gauntlet.models import (
    AnswerRecord,
    Challenge,
    DeveloperProgress,
    KnowledgeEntry,
    OnboardingProgress,
)


class TestKnowledgeEntry:
    def test_create_entry(self) -> None:
        entry = KnowledgeEntry(
            id="kb-001",
            category="business_logic",
            module="src/auth.py",
            concept="Token refresh before validation",
            detail="Tokens are refreshed before validation.",
            related_files=["src/middleware.py"],
            difficulty=3,
            tags=["auth"],
            extracted_at="2026-03-30T12:00:00Z",
            source="automated",
            consumers=["both"],
        )
        assert entry.id == "kb-001"
        assert entry.category == "business_logic"
        assert entry.difficulty == 3

    def test_to_dict_roundtrip(self) -> None:
        entry = KnowledgeEntry(
            id="kb-001",
            category="architecture",
            module="src/api.py",
            concept="Router pattern",
            detail="Routers delegate to services.",
            related_files=[],
            difficulty=2,
            tags=["arch"],
            extracted_at="2026-03-30T12:00:00Z",
            source="automated",
            consumers=["both"],
        )
        d = entry.to_dict()
        restored = KnowledgeEntry.from_dict(d)
        assert restored.id == entry.id
        assert restored.category == entry.category

    def test_json_serializable(self) -> None:
        entry = KnowledgeEntry(
            id="kb-001",
            category="data_flow",
            module="src/pipeline.py",
            concept="Input to output",
            detail="Data flows through pipeline.",
            related_files=["src/validate.py"],
            difficulty=4,
            tags=["pipeline"],
            extracted_at="2026-03-30T12:00:00Z",
            source="curated",
            consumers=["human"],
        )
        serialized = json.dumps(entry.to_dict())
        assert "kb-001" in serialized


class TestChallenge:
    def test_create_multiple_choice(self) -> None:
        ch = Challenge(
            id="ch-001",
            type="multiple_choice",
            knowledge_entry_id="kb-001",
            difficulty=2,
            prompt="What does calculate_discount return for premium?",
            context="def calculate_discount(price, tier): ...",
            answer="A",
            options=["20% off", "10% off", "No discount", "50% off"],
            hints=["Check the rates dict"],
            scope_files=["src/pricing.py"],
        )
        assert ch.type == "multiple_choice"
        assert len(ch.options) == 4

    def test_create_explain_why(self) -> None:
        ch = Challenge(
            id="ch-002",
            type="explain_why",
            knowledge_entry_id="kb-001",
            difficulty=3,
            prompt="Why does token refresh happen before validation?",
            context="",
            answer="Prevents mid-session expiry during long API calls",
            options=None,
            hints=[],
            scope_files=["src/auth.py"],
        )
        assert ch.type == "explain_why"
        assert ch.options is None


class TestAnswerRecord:
    def test_create_record(self) -> None:
        rec = AnswerRecord(
            challenge_id="ch-001",
            knowledge_entry_id="kb-001",
            challenge_type="multiple_choice",
            category="business_logic",
            difficulty=2,
            result="pass",
            answered_at="2026-03-30T12:00:00Z",
        )
        assert rec.result == "pass"


class TestDeveloperProgress:
    def test_empty_progress(self) -> None:
        prog = DeveloperProgress(developer_id="dev@example.com")
        assert prog.streak == 0
        assert len(prog.history) == 0
        assert prog.overall_accuracy() == 0.0

    def test_accuracy_calculation(self) -> None:
        prog = DeveloperProgress(developer_id="dev@example.com")
        prog.history = [
            AnswerRecord("c1", "k1", "multiple_choice", "business_logic", 2, "pass", "2026-03-30T12:00:00Z"),
            AnswerRecord("c2", "k2", "multiple_choice", "business_logic", 2, "fail", "2026-03-30T12:01:00Z"),
            AnswerRecord("c3", "k3", "explain_why", "architecture", 3, "partial", "2026-03-30T12:02:00Z"),
        ]
        accuracy = prog.overall_accuracy()
        # pass=1.0, fail=0.0, partial=0.5 => (1.0+0.0+0.5)/3 = 0.5
        assert accuracy == 0.5

    def test_category_accuracy(self) -> None:
        prog = DeveloperProgress(developer_id="dev@example.com")
        prog.history = [
            AnswerRecord("c1", "k1", "multiple_choice", "business_logic", 2, "pass", "2026-03-30T12:00:00Z"),
            AnswerRecord("c2", "k2", "multiple_choice", "business_logic", 2, "pass", "2026-03-30T12:01:00Z"),
            AnswerRecord("c3", "k3", "explain_why", "architecture", 3, "fail", "2026-03-30T12:02:00Z"),
        ]
        assert prog.category_accuracy("business_logic") == 1.0
        assert prog.category_accuracy("architecture") == 0.0

    def test_to_dict_roundtrip(self) -> None:
        prog = DeveloperProgress(developer_id="dev@example.com")
        prog.history = [
            AnswerRecord("c1", "k1", "multiple_choice", "business_logic", 2, "pass", "2026-03-30T12:00:00Z"),
        ]
        prog.streak = 3
        d = prog.to_dict()
        restored = DeveloperProgress.from_dict(d)
        assert restored.developer_id == "dev@example.com"
        assert restored.streak == 3
        assert len(restored.history) == 1


class TestOnboardingProgress:
    def test_initial_state(self) -> None:
        ob = OnboardingProgress(developer_id="new@example.com")
        assert ob.current_stage == 1
        assert ob.is_graduated() is False

    def test_can_advance_stage(self) -> None:
        ob = OnboardingProgress(developer_id="new@example.com")
        ob.stage_scores = {1: 0.85}
        ob.stage_challenge_count = {1: 12}
        assert ob.can_advance() is True

    def test_cannot_advance_low_accuracy(self) -> None:
        ob = OnboardingProgress(developer_id="new@example.com")
        ob.stage_scores = {1: 0.70}
        ob.stage_challenge_count = {1: 12}
        assert ob.can_advance() is False

    def test_cannot_advance_few_challenges(self) -> None:
        ob = OnboardingProgress(developer_id="new@example.com")
        ob.stage_scores = {1: 0.90}
        ob.stage_challenge_count = {1: 5}
        assert ob.can_advance() is False

    def test_graduation(self) -> None:
        ob = OnboardingProgress(developer_id="new@example.com")
        ob.current_stage = 5
        ob.stage_scores = {5: 0.85}
        ob.stage_challenge_count = {5: 12}
        assert ob.can_advance() is True
        ob.advance()
        assert ob.is_graduated() is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/gauntlet && uv run pytest tests/unit/test_models.py -v 2>&1 | head -20`
Expected: FAIL — `ModuleNotFoundError: No module named 'gauntlet.models'`

- [ ] **Step 3: Implement models**

`plugins/gauntlet/src/gauntlet/models.py`:
```python
"""Data models for the gauntlet knowledge and challenge system."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# Score values for result types
_RESULT_SCORES = {"pass": 1.0, "partial": 0.5, "fail": 0.0}

# Onboarding thresholds
_ADVANCE_ACCURACY = 0.80
_ADVANCE_MIN_CHALLENGES = 10
_FINAL_STAGE = 5


@dataclass
class KnowledgeEntry:
    """A single unit of codebase knowledge."""

    id: str
    category: str
    module: str
    concept: str
    detail: str
    related_files: list[str]
    difficulty: int
    tags: list[str]
    extracted_at: str
    source: str
    consumers: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "category": self.category,
            "module": self.module,
            "concept": self.concept,
            "detail": self.detail,
            "related_files": self.related_files,
            "difficulty": self.difficulty,
            "tags": self.tags,
            "extracted_at": self.extracted_at,
            "source": self.source,
            "consumers": self.consumers,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeEntry:
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            category=data["category"],
            module=data["module"],
            concept=data["concept"],
            detail=data["detail"],
            related_files=data.get("related_files", []),
            difficulty=data.get("difficulty", 1),
            tags=data.get("tags", []),
            extracted_at=data.get("extracted_at", ""),
            source=data.get("source", "automated"),
            consumers=data.get("consumers", ["both"]),
        )


@dataclass
class Challenge:
    """A challenge question generated from the knowledge base."""

    id: str
    type: str
    knowledge_entry_id: str
    difficulty: int
    prompt: str
    context: str
    answer: str
    options: Optional[list[str]]
    hints: list[str]
    scope_files: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "knowledge_entry_id": self.knowledge_entry_id,
            "difficulty": self.difficulty,
            "prompt": self.prompt,
            "context": self.context,
            "answer": self.answer,
            "options": self.options,
            "hints": self.hints,
            "scope_files": self.scope_files,
        }


@dataclass
class AnswerRecord:
    """Record of a developer's answer to a challenge."""

    challenge_id: str
    knowledge_entry_id: str
    challenge_type: str
    category: str
    difficulty: int
    result: str  # "pass" | "partial" | "fail"
    answered_at: str

    def score(self) -> float:
        """Numeric score: pass=1.0, partial=0.5, fail=0.0."""
        return _RESULT_SCORES.get(self.result, 0.0)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "challenge_id": self.challenge_id,
            "knowledge_entry_id": self.knowledge_entry_id,
            "challenge_type": self.challenge_type,
            "category": self.category,
            "difficulty": self.difficulty,
            "result": self.result,
            "answered_at": self.answered_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnswerRecord:
        """Deserialize from dictionary."""
        return cls(
            challenge_id=data["challenge_id"],
            knowledge_entry_id=data["knowledge_entry_id"],
            challenge_type=data["challenge_type"],
            category=data["category"],
            difficulty=data["difficulty"],
            result=data["result"],
            answered_at=data["answered_at"],
        )


@dataclass
class DeveloperProgress:
    """Tracks a developer's challenge history and adaptive state."""

    developer_id: str
    history: list[AnswerRecord] = field(default_factory=list)
    last_seen: dict[str, str] = field(default_factory=dict)
    streak: int = 0

    def overall_accuracy(self) -> float:
        """Calculate overall accuracy across all answers."""
        if not self.history:
            return 0.0
        total = sum(r.score() for r in self.history)
        return total / len(self.history)

    def category_accuracy(self, category: str) -> float:
        """Calculate accuracy for a specific knowledge category."""
        records = [r for r in self.history if r.category == category]
        if not records:
            return 0.0
        total = sum(r.score() for r in records)
        return total / len(records)

    def type_accuracy(self, challenge_type: str) -> float:
        """Calculate accuracy for a specific challenge type."""
        records = [r for r in self.history if r.challenge_type == challenge_type]
        if not records:
            return 0.0
        total = sum(r.score() for r in records)
        return total / len(records)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "developer_id": self.developer_id,
            "history": [r.to_dict() for r in self.history],
            "last_seen": self.last_seen,
            "streak": self.streak,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeveloperProgress:
        """Deserialize from dictionary."""
        prog = cls(developer_id=data["developer_id"])
        prog.history = [AnswerRecord.from_dict(r) for r in data.get("history", [])]
        prog.last_seen = data.get("last_seen", {})
        prog.streak = data.get("streak", 0)
        return prog


@dataclass
class OnboardingProgress:
    """Tracks a developer's onboarding progression."""

    developer_id: str
    current_stage: int = 1
    stage_scores: dict[int, float] = field(default_factory=dict)
    stage_challenge_count: dict[int, int] = field(default_factory=dict)
    entries_mastered: set[str] = field(default_factory=set)
    started_at: str = ""
    last_session_at: str = ""
    graduated: bool = False

    def can_advance(self) -> bool:
        """Check if the developer can advance to the next stage."""
        score = self.stage_scores.get(self.current_stage, 0.0)
        count = self.stage_challenge_count.get(self.current_stage, 0)
        return score >= _ADVANCE_ACCURACY and count >= _ADVANCE_MIN_CHALLENGES

    def advance(self) -> None:
        """Advance to the next stage, or graduate if at the final stage."""
        if self.current_stage >= _FINAL_STAGE:
            self.graduated = True
        else:
            self.current_stage += 1

    def is_graduated(self) -> bool:
        """Check if the developer has completed all stages."""
        return self.graduated

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "developer_id": self.developer_id,
            "current_stage": self.current_stage,
            "stage_scores": {str(k): v for k, v in self.stage_scores.items()},
            "stage_challenge_count": {str(k): v for k, v in self.stage_challenge_count.items()},
            "entries_mastered": list(self.entries_mastered),
            "started_at": self.started_at,
            "last_session_at": self.last_session_at,
            "graduated": self.graduated,
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/gauntlet && uv run pytest tests/unit/test_models.py -v`
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/gauntlet/src/gauntlet/models.py plugins/gauntlet/tests/unit/test_models.py
git commit -m "feat(gauntlet): add data models for knowledge, challenges, and progress

KnowledgeEntry, Challenge, AnswerRecord, DeveloperProgress,
OnboardingProgress with serialization and accuracy calculations."
```

---

## Phase 2: Knowledge Extraction

### Task 3: Knowledge Base Persistence

**Files:**
- Create: `plugins/gauntlet/src/gauntlet/knowledge_store.py`
- Create: `plugins/gauntlet/tests/unit/test_knowledge_store.py`

- [ ] **Step 1: Write failing tests**

`plugins/gauntlet/tests/unit/test_knowledge_store.py`:
```python
"""Tests for knowledge base persistence."""

from __future__ import annotations

import json
from pathlib import Path

from gauntlet.knowledge_store import KnowledgeStore
from gauntlet.models import KnowledgeEntry


class TestKnowledgeStore:
    def test_load_empty(self, tmp_gauntlet_dir: Path) -> None:
        store = KnowledgeStore(tmp_gauntlet_dir)
        entries = store.load()
        assert entries == []

    def test_save_and_load(self, tmp_gauntlet_dir: Path) -> None:
        store = KnowledgeStore(tmp_gauntlet_dir)
        entry = KnowledgeEntry(
            id="kb-001",
            category="business_logic",
            module="src/auth.py",
            concept="Token refresh",
            detail="Refresh before validation.",
            related_files=[],
            difficulty=3,
            tags=["auth"],
            extracted_at="2026-03-30T12:00:00Z",
            source="automated",
            consumers=["both"],
        )
        store.save([entry])
        loaded = store.load()
        assert len(loaded) == 1
        assert loaded[0].id == "kb-001"

    def test_load_with_annotations(
        self, tmp_gauntlet_dir: Path, sample_annotation: Path
    ) -> None:
        store = KnowledgeStore(tmp_gauntlet_dir)
        store.save([])  # Empty automated entries
        entries = store.load(include_annotations=True)
        assert len(entries) == 1
        assert entries[0].source == "curated"

    def test_merge_automated_and_curated(
        self, tmp_gauntlet_dir: Path, sample_annotation: Path
    ) -> None:
        store = KnowledgeStore(tmp_gauntlet_dir)
        automated = KnowledgeEntry(
            id="kb-auto-001",
            category="architecture",
            module="src/api.py",
            concept="Router pattern",
            detail="Routers delegate.",
            related_files=[],
            difficulty=2,
            tags=["arch"],
            extracted_at="2026-03-30T12:00:00Z",
            source="automated",
            consumers=["both"],
        )
        store.save([automated])
        entries = store.load(include_annotations=True)
        assert len(entries) == 2
        sources = {e.source for e in entries}
        assert sources == {"automated", "curated"}

    def test_query_by_files(self, sample_knowledge_base: Path) -> None:
        store = KnowledgeStore(sample_knowledge_base.parent)
        entries = store.query(files=["src/auth/middleware.py"])
        assert len(entries) >= 1
        assert all(
            "src/auth/middleware.py" in e.related_files or e.module == "src/auth/middleware.py"
            for e in entries
        )

    def test_query_by_category(self, sample_knowledge_base: Path) -> None:
        store = KnowledgeStore(sample_knowledge_base.parent)
        entries = store.query(categories=["business_logic"])
        assert len(entries) == 1
        assert entries[0].category == "business_logic"

    def test_query_by_tags(self, sample_knowledge_base: Path) -> None:
        store = KnowledgeStore(sample_knowledge_base.parent)
        entries = store.query(tags=["pipeline"])
        assert len(entries) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/gauntlet && uv run pytest tests/unit/test_knowledge_store.py -v 2>&1 | head -10`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement KnowledgeStore**

`plugins/gauntlet/src/gauntlet/knowledge_store.py`:
```python
"""Persistence layer for the gauntlet knowledge base."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from gauntlet.models import KnowledgeEntry

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


class KnowledgeStore:
    """Manages reading and writing the knowledge base and annotations."""

    def __init__(self, gauntlet_dir: Path) -> None:
        self._dir = gauntlet_dir
        self._kb_path = gauntlet_dir / "knowledge.json"
        self._annotations_dir = gauntlet_dir / "annotations"

    def load(self, include_annotations: bool = False) -> list[KnowledgeEntry]:
        """Load knowledge entries from JSON and optionally from annotations."""
        entries = self._load_automated()
        if include_annotations:
            entries.extend(self._load_annotations())
        return entries

    def save(self, entries: list[KnowledgeEntry]) -> None:
        """Save automated knowledge entries to JSON."""
        data = [e.to_dict() for e in entries]
        self._kb_path.write_text(json.dumps(data, indent=2))

    def query(
        self,
        files: Optional[list[str]] = None,
        categories: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        min_difficulty: int = 1,
        max_difficulty: int = 5,
    ) -> list[KnowledgeEntry]:
        """Query the knowledge base with filters."""
        entries = self.load(include_annotations=True)
        results = []
        for entry in entries:
            if not (min_difficulty <= entry.difficulty <= max_difficulty):
                continue
            if categories and entry.category not in categories:
                continue
            if tags and not set(tags).intersection(entry.tags):
                continue
            if files:
                entry_files = set(entry.related_files) | {entry.module}
                if not set(files).intersection(entry_files):
                    continue
            results.append(entry)
        return results

    def _load_automated(self) -> list[KnowledgeEntry]:
        """Load entries from knowledge.json."""
        if not self._kb_path.exists():
            return []
        data = json.loads(self._kb_path.read_text())
        return [KnowledgeEntry.from_dict(d) for d in data]

    def _load_annotations(self) -> list[KnowledgeEntry]:
        """Load curated entries from YAML annotation files."""
        if yaml is None or not self._annotations_dir.exists():
            return []
        entries = []
        for path in sorted(self._annotations_dir.glob("*.yaml")):
            entry = self._parse_annotation(path)
            if entry:
                entries.append(entry)
        return entries

    def _parse_annotation(self, path: Path) -> Optional[KnowledgeEntry]:
        """Parse a single YAML annotation file into a KnowledgeEntry."""
        if yaml is None:
            return None
        data = yaml.safe_load(path.read_text())
        if not isinstance(data, dict):
            return None
        stable_id = hashlib.sha256(
            f"{data.get('module', '')}:{data.get('concept', '')}".encode()
        ).hexdigest()[:12]
        return KnowledgeEntry(
            id=f"curated-{stable_id}",
            category="business_logic",
            module=data.get("module", ""),
            concept=data.get("concept", ""),
            detail=data.get("why", data.get("concept", "")),
            related_files=data.get("related_files", []),
            difficulty=data.get("difficulty", 3),
            tags=data.get("tags", []),
            extracted_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            source="curated",
            consumers=["both"],
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/gauntlet && uv run pytest tests/unit/test_knowledge_store.py -v`
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/gauntlet/src/gauntlet/knowledge_store.py plugins/gauntlet/tests/unit/test_knowledge_store.py
git commit -m "feat(gauntlet): add knowledge base persistence with YAML annotations

KnowledgeStore loads/saves JSON entries, parses YAML annotations,
and supports filtered queries by files, categories, and tags."
```

---

### Task 4: AST-Based Knowledge Extraction

**Files:**
- Create: `plugins/gauntlet/src/gauntlet/extraction.py`
- Create: `plugins/gauntlet/tests/unit/test_extraction.py`

- [ ] **Step 1: Write failing tests**

`plugins/gauntlet/tests/unit/test_extraction.py`:
```python
"""Tests for AST-based knowledge extraction."""

from __future__ import annotations

from pathlib import Path

from gauntlet.extraction import extract_from_file, extract_from_directory


class TestExtractFromFile:
    def test_extracts_functions(self, sample_python_file: Path) -> None:
        entries = extract_from_file(sample_python_file)
        assert len(entries) >= 1
        func_entry = next(
            (e for e in entries if "calculate_discount" in e.concept), None
        )
        assert func_entry is not None
        assert func_entry.module == str(sample_python_file)

    def test_extracts_docstring_as_detail(self, sample_python_file: Path) -> None:
        entries = extract_from_file(sample_python_file)
        func_entry = next(
            (e for e in entries if "calculate_discount" in e.concept), None
        )
        assert func_entry is not None
        assert "premium" in func_entry.detail.lower() or "discount" in func_entry.detail.lower()

    def test_assigns_difficulty(self, sample_python_file: Path) -> None:
        entries = extract_from_file(sample_python_file)
        for entry in entries:
            assert 1 <= entry.difficulty <= 5

    def test_nonexistent_file_returns_empty(self, tmp_path: Path) -> None:
        entries = extract_from_file(tmp_path / "nonexistent.py")
        assert entries == []

    def test_syntax_error_file_returns_empty(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("def foo(:\n  pass")
        entries = extract_from_file(bad_file)
        assert entries == []


class TestExtractFromDirectory:
    def test_extracts_from_multiple_files(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "a.py").write_text(
            "def func_a():\n"
            '    """Does A."""\n'
            "    return 1\n"
        )
        (src / "b.py").write_text(
            "def func_b():\n"
            '    """Does B."""\n'
            "    return 2\n"
        )
        entries = extract_from_directory(src)
        concepts = [e.concept for e in entries]
        assert any("func_a" in c for c in concepts)
        assert any("func_b" in c for c in concepts)

    def test_assigns_unique_ids(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "a.py").write_text(
            "def func_a():\n"
            '    """Does A."""\n'
            "    return 1\n"
        )
        entries = extract_from_directory(src)
        ids = [e.id for e in entries]
        assert len(ids) == len(set(ids))

    def test_skips_non_python_files(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "readme.md").write_text("# Hello")
        (src / "a.py").write_text("def func_a(): pass\n")
        entries = extract_from_directory(src)
        modules = [e.module for e in entries]
        assert not any("readme.md" in m for m in modules)

    def test_detects_imports_as_dependencies(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "a.py").write_text(
            "from b import helper\n"
            "\n"
            "def func_a():\n"
            '    """Uses helper from b."""\n'
            "    return helper()\n"
        )
        entries = extract_from_directory(src)
        func_entry = next(
            (e for e in entries if "func_a" in e.concept), None
        )
        assert func_entry is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/gauntlet && uv run pytest tests/unit/test_extraction.py -v 2>&1 | head -10`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement extraction**

`plugins/gauntlet/src/gauntlet/extraction.py`:
```python
"""AST-based knowledge extraction from Python source files."""

from __future__ import annotations

import ast
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from gauntlet.models import KnowledgeEntry

logger = logging.getLogger(__name__)

# Difficulty heuristics
_DIFFICULTY_THRESHOLDS = {
    "lines": [(10, 1), (30, 2), (60, 3), (100, 4)],
    "complexity_bonus": 1,  # Added when function has branches
}


def extract_from_file(file_path: Path) -> list[KnowledgeEntry]:
    """Extract knowledge entries from a single Python file."""
    if not file_path.exists() or not file_path.suffix == ".py":
        return []

    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError):
        logger.debug("Could not parse %s", file_path)
        return []

    entries: list[KnowledgeEntry] = []
    imports = _extract_imports(tree)
    module_str = str(file_path)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            entry = _function_to_entry(node, module_str, imports, now)
            if entry:
                entries.append(entry)
        elif isinstance(node, ast.ClassDef):
            entry = _class_to_entry(node, module_str, imports, now)
            if entry:
                entries.append(entry)

    return entries


def extract_from_directory(
    directory: Path,
    exclude_patterns: Optional[list[str]] = None,
) -> list[KnowledgeEntry]:
    """Extract knowledge entries from all Python files in a directory."""
    exclude = set(exclude_patterns or [])
    entries: list[KnowledgeEntry] = []

    for py_file in sorted(directory.rglob("*.py")):
        if any(pat in str(py_file) for pat in exclude):
            continue
        if py_file.name.startswith("__"):
            continue
        entries.extend(extract_from_file(py_file))

    return entries


def _extract_imports(tree: ast.Module) -> list[str]:
    """Extract import module names from an AST."""
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def _get_docstring(node: ast.AST) -> str:
    """Extract docstring from a function or class node."""
    if (
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    ):
        return node.body[0].value.value.strip()
    return ""


def _estimate_difficulty(node: ast.AST) -> int:
    """Estimate difficulty 1-5 based on function/class complexity."""
    if not hasattr(node, "body"):
        return 1

    line_count = 0
    has_branches = False
    for child in ast.walk(node):
        if hasattr(child, "lineno"):
            line_count += 1
        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
            has_branches = True

    difficulty = 1
    for threshold, level in _DIFFICULTY_THRESHOLDS["lines"]:
        if line_count >= threshold:
            difficulty = level

    if has_branches:
        difficulty = min(difficulty + _DIFFICULTY_THRESHOLDS["complexity_bonus"], 5)

    return difficulty


def _stable_id(module: str, name: str) -> str:
    """Generate a stable ID from module path and name."""
    raw = f"{module}:{name}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _function_to_entry(
    node: ast.FunctionDef,
    module: str,
    imports: list[str],
    timestamp: str,
) -> Optional[KnowledgeEntry]:
    """Convert a function AST node to a KnowledgeEntry."""
    if node.name.startswith("_") and node.name != "__init__":
        return None

    docstring = _get_docstring(node)
    detail = docstring if docstring else f"Function {node.name} in {module}"

    return KnowledgeEntry(
        id=_stable_id(module, node.name),
        category=_infer_category(node, docstring, imports),
        module=module,
        concept=f"Function: {node.name}",
        detail=detail,
        related_files=[],
        difficulty=_estimate_difficulty(node),
        tags=_extract_tags(node, docstring),
        extracted_at=timestamp,
        source="automated",
        consumers=["both"],
    )


def _class_to_entry(
    node: ast.ClassDef,
    module: str,
    imports: list[str],
    timestamp: str,
) -> Optional[KnowledgeEntry]:
    """Convert a class AST node to a KnowledgeEntry."""
    if node.name.startswith("_"):
        return None

    docstring = _get_docstring(node)
    detail = docstring if docstring else f"Class {node.name} in {module}"
    method_count = sum(
        1 for child in node.body
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
    )

    return KnowledgeEntry(
        id=_stable_id(module, node.name),
        category="architecture",
        module=module,
        concept=f"Class: {node.name} ({method_count} methods)",
        detail=detail,
        related_files=[],
        difficulty=_estimate_difficulty(node),
        tags=_extract_tags(node, docstring),
        extracted_at=timestamp,
        source="automated",
        consumers=["both"],
    )


def _infer_category(
    node: ast.AST,
    docstring: str,
    imports: list[str],
) -> str:
    """Infer the knowledge category from context clues."""
    doc_lower = docstring.lower()

    # Business logic indicators
    business_keywords = [
        "business", "rule", "policy", "calculate", "validate",
        "discount", "price", "tier", "permission", "rate",
    ]
    if any(kw in doc_lower for kw in business_keywords):
        return "business_logic"

    # Data flow indicators
    flow_keywords = ["pipeline", "transform", "ingest", "process", "flow", "stream"]
    if any(kw in doc_lower for kw in flow_keywords):
        return "data_flow"

    # API indicators
    api_keywords = ["endpoint", "route", "handler", "request", "response", "api"]
    if any(kw in doc_lower for kw in api_keywords):
        return "api_contract"

    # Error handling indicators
    error_keywords = ["error", "exception", "retry", "fallback", "recover"]
    if any(kw in doc_lower for kw in error_keywords):
        return "error_handling"

    return "architecture"


def _extract_tags(node: ast.AST, docstring: str) -> list[str]:
    """Extract searchable tags from the node and docstring."""
    tags: list[str] = []
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        tags.append(node.name)
        if isinstance(node, ast.AsyncFunctionDef):
            tags.append("async")
    elif isinstance(node, ast.ClassDef):
        tags.append(node.name)
        for base in node.bases:
            if isinstance(base, ast.Name):
                tags.append(base.id)
    return tags
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/gauntlet && uv run pytest tests/unit/test_extraction.py -v`
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/gauntlet/src/gauntlet/extraction.py plugins/gauntlet/tests/unit/test_extraction.py
git commit -m "feat(gauntlet): add AST-based knowledge extraction

Extracts functions, classes, docstrings, imports, and infers
categories and difficulty from Python source files."
```

---

## Phase 3: Challenge Engine

### Task 5: Challenge Generation

**Files:**
- Create: `plugins/gauntlet/src/gauntlet/challenges.py`
- Create: `plugins/gauntlet/tests/unit/test_challenges.py`

- [ ] **Step 1: Write failing tests**

`plugins/gauntlet/tests/unit/test_challenges.py`:
```python
"""Tests for challenge generation."""

from __future__ import annotations

from gauntlet.challenges import generate_challenge, select_challenge_type, CHALLENGE_TYPES
from gauntlet.models import DeveloperProgress, KnowledgeEntry


def _make_entry(
    id: str = "kb-001",
    category: str = "business_logic",
    difficulty: int = 3,
) -> KnowledgeEntry:
    return KnowledgeEntry(
        id=id,
        category=category,
        module="src/example.py",
        concept="Example concept",
        detail="Detailed explanation of the concept for testing.",
        related_files=["src/related.py"],
        difficulty=difficulty,
        tags=["test"],
        extracted_at="2026-03-30T12:00:00Z",
        source="automated",
        consumers=["both"],
    )


class TestChallengeTypes:
    def test_all_types_registered(self) -> None:
        expected = {
            "multiple_choice",
            "code_completion",
            "trace",
            "explain_why",
            "spot_bug",
            "dependency_map",
        }
        assert set(CHALLENGE_TYPES.keys()) == expected


class TestSelectChallengeType:
    def test_returns_valid_type(self) -> None:
        progress = DeveloperProgress(developer_id="dev@test.com")
        ct = select_challenge_type(progress)
        assert ct in CHALLENGE_TYPES

    def test_weights_toward_weak_types(self) -> None:
        from gauntlet.models import AnswerRecord

        progress = DeveloperProgress(developer_id="dev@test.com")
        # Make multiple_choice very strong, everything else unseen
        progress.history = [
            AnswerRecord("c1", "k1", "multiple_choice", "business_logic", 2, "pass", "2026-03-30T12:00:00Z"),
            AnswerRecord("c2", "k2", "multiple_choice", "business_logic", 2, "pass", "2026-03-30T12:01:00Z"),
            AnswerRecord("c3", "k3", "multiple_choice", "business_logic", 2, "pass", "2026-03-30T12:02:00Z"),
        ]
        # Over many selections, should occasionally pick non-MC types
        types_seen = set()
        for _ in range(100):
            types_seen.add(select_challenge_type(progress))
        assert len(types_seen) > 1


class TestGenerateChallenge:
    def test_generates_multiple_choice(self) -> None:
        entry = _make_entry()
        ch = generate_challenge(entry, "multiple_choice")
        assert ch.type == "multiple_choice"
        assert ch.options is not None
        assert len(ch.options) == 4
        assert ch.knowledge_entry_id == "kb-001"

    def test_generates_explain_why(self) -> None:
        entry = _make_entry()
        ch = generate_challenge(entry, "explain_why")
        assert ch.type == "explain_why"
        assert ch.options is None
        assert ch.prompt != ""

    def test_generates_trace(self) -> None:
        entry = _make_entry(category="data_flow")
        ch = generate_challenge(entry, "trace")
        assert ch.type == "trace"

    def test_generates_spot_bug(self) -> None:
        entry = _make_entry()
        ch = generate_challenge(entry, "spot_bug")
        assert ch.type == "spot_bug"

    def test_generates_dependency_map(self) -> None:
        entry = _make_entry(category="dependency")
        ch = generate_challenge(entry, "dependency_map")
        assert ch.type == "dependency_map"

    def test_generates_code_completion(self) -> None:
        entry = _make_entry()
        ch = generate_challenge(entry, "code_completion")
        assert ch.type == "code_completion"

    def test_difficulty_matches_entry(self) -> None:
        entry = _make_entry(difficulty=4)
        ch = generate_challenge(entry, "multiple_choice")
        assert ch.difficulty == 4

    def test_scope_files_populated(self) -> None:
        entry = _make_entry()
        ch = generate_challenge(entry, "multiple_choice")
        assert "src/example.py" in ch.scope_files or "src/related.py" in ch.scope_files
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/gauntlet && uv run pytest tests/unit/test_challenges.py -v 2>&1 | head -10`
Expected: FAIL

- [ ] **Step 3: Implement challenge generation**

`plugins/gauntlet/src/gauntlet/challenges.py`:
```python
"""Challenge generation from knowledge base entries."""

from __future__ import annotations

import hashlib
import random
from typing import Callable

from gauntlet.models import Challenge, DeveloperProgress, KnowledgeEntry

# Registry of challenge type generators
CHALLENGE_TYPES: dict[str, Callable[[KnowledgeEntry], Challenge]] = {}


def _register(name: str) -> Callable:
    """Decorator to register a challenge type generator."""
    def decorator(func: Callable[[KnowledgeEntry], Challenge]) -> Callable:
        CHALLENGE_TYPES[name] = func
        return func
    return decorator


def _challenge_id(entry_id: str, challenge_type: str) -> str:
    """Generate a stable challenge ID."""
    raw = f"{entry_id}:{challenge_type}:{random.random()}"
    return f"ch-{hashlib.sha256(raw.encode()).hexdigest()[:10]}"


def _scope_files(entry: KnowledgeEntry) -> list[str]:
    """Build the scope files list from an entry."""
    files = [entry.module]
    files.extend(entry.related_files)
    return files


def select_challenge_type(progress: DeveloperProgress) -> str:
    """Select a challenge type weighted toward the developer's weaknesses."""
    types = list(CHALLENGE_TYPES.keys())

    if not progress.history:
        return random.choice(types)

    # Build weights: lower accuracy = higher weight
    weights: list[float] = []
    for ct in types:
        accuracy = progress.type_accuracy(ct)
        # Unseen types (accuracy 0.0 from no history) get high weight
        records = [r for r in progress.history if r.challenge_type == ct]
        if not records:
            weights.append(3.0)
        else:
            weights.append(max(0.5, 2.0 - accuracy * 2.0))

    return random.choices(types, weights=weights, k=1)[0]


def generate_challenge(
    entry: KnowledgeEntry,
    challenge_type: str,
) -> Challenge:
    """Generate a challenge of the specified type from a knowledge entry."""
    generator = CHALLENGE_TYPES[challenge_type]
    return generator(entry)


@_register("multiple_choice")
def _gen_multiple_choice(entry: KnowledgeEntry) -> Challenge:
    """Generate a multiple choice challenge."""
    correct = entry.detail[:80] if len(entry.detail) > 80 else entry.detail
    distractors = [
        f"This is unrelated to {entry.concept}",
        f"The opposite behavior of {entry.concept}",
        f"A deprecated version of {entry.concept}",
    ]
    options = [correct] + distractors
    random.shuffle(options)
    correct_idx = options.index(correct)
    answer_letter = chr(ord("A") + correct_idx)

    return Challenge(
        id=_challenge_id(entry.id, "multiple_choice"),
        type="multiple_choice",
        knowledge_entry_id=entry.id,
        difficulty=entry.difficulty,
        prompt=f"What best describes '{entry.concept}' in {entry.module}?",
        context="",
        answer=answer_letter,
        options=options,
        hints=[f"Look at {entry.module}", f"Related to: {', '.join(entry.tags)}"],
        scope_files=_scope_files(entry),
    )


@_register("explain_why")
def _gen_explain_why(entry: KnowledgeEntry) -> Challenge:
    """Generate an explain-the-why challenge."""
    return Challenge(
        id=_challenge_id(entry.id, "explain_why"),
        type="explain_why",
        knowledge_entry_id=entry.id,
        difficulty=entry.difficulty,
        prompt=f"Explain why {entry.concept} works the way it does in {entry.module}.",
        context="",
        answer=entry.detail,
        options=None,
        hints=[f"Think about the purpose of {entry.module}"],
        scope_files=_scope_files(entry),
    )


@_register("trace")
def _gen_trace(entry: KnowledgeEntry) -> Challenge:
    """Generate a trace exercise challenge."""
    files_str = ", ".join(entry.related_files[:3]) if entry.related_files else entry.module
    return Challenge(
        id=_challenge_id(entry.id, "trace"),
        type="trace",
        knowledge_entry_id=entry.id,
        difficulty=entry.difficulty,
        prompt=f"Trace the data flow through {files_str} as it relates to '{entry.concept}'.",
        context="",
        answer=entry.detail,
        options=None,
        hints=[f"Start from {entry.module}"],
        scope_files=_scope_files(entry),
    )


@_register("spot_bug")
def _gen_spot_bug(entry: KnowledgeEntry) -> Challenge:
    """Generate a spot-the-bug challenge."""
    return Challenge(
        id=_challenge_id(entry.id, "spot_bug"),
        type="spot_bug",
        knowledge_entry_id=entry.id,
        difficulty=entry.difficulty,
        prompt=(
            f"A change was made to {entry.module} that breaks '{entry.concept}'. "
            "What could go wrong if this concept is violated?"
        ),
        context="",
        answer=entry.detail,
        options=None,
        hints=[f"Consider what {entry.concept} protects against"],
        scope_files=_scope_files(entry),
    )


@_register("dependency_map")
def _gen_dependency_map(entry: KnowledgeEntry) -> Challenge:
    """Generate a dependency mapping challenge."""
    return Challenge(
        id=_challenge_id(entry.id, "dependency_map"),
        type="dependency_map",
        knowledge_entry_id=entry.id,
        difficulty=entry.difficulty,
        prompt=f"Which modules depend on or are affected by '{entry.concept}' in {entry.module}?",
        context="",
        answer=", ".join(entry.related_files) if entry.related_files else "None identified",
        options=None,
        hints=[f"Check imports in {entry.module}"],
        scope_files=_scope_files(entry),
    )


@_register("code_completion")
def _gen_code_completion(entry: KnowledgeEntry) -> Challenge:
    """Generate a code completion challenge."""
    return Challenge(
        id=_challenge_id(entry.id, "code_completion"),
        type="code_completion",
        knowledge_entry_id=entry.id,
        difficulty=entry.difficulty,
        prompt=(
            f"Complete the implementation of '{entry.concept}' in {entry.module}. "
            "What is the key logic that makes this work?"
        ),
        context="",
        answer=entry.detail,
        options=None,
        hints=[f"The function is in {entry.module}", f"Tags: {', '.join(entry.tags)}"],
        scope_files=_scope_files(entry),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/gauntlet && uv run pytest tests/unit/test_challenges.py -v`
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/gauntlet/src/gauntlet/challenges.py plugins/gauntlet/tests/unit/test_challenges.py
git commit -m "feat(gauntlet): add challenge generation engine with 6 types

Multiple choice, code completion, trace, explain-why, spot-bug,
and dependency map. Adaptive type selection weighted by weakness."
```

---

### Task 6: Answer Scoring

**Files:**
- Create: `plugins/gauntlet/src/gauntlet/scoring.py`
- Create: `plugins/gauntlet/tests/unit/test_scoring.py`

- [ ] **Step 1: Write failing tests**

`plugins/gauntlet/tests/unit/test_scoring.py`:
```python
"""Tests for answer evaluation."""

from __future__ import annotations

from gauntlet.models import Challenge
from gauntlet.scoring import evaluate_answer


def _make_mc_challenge() -> Challenge:
    return Challenge(
        id="ch-001",
        type="multiple_choice",
        knowledge_entry_id="kb-001",
        difficulty=2,
        prompt="What is X?",
        context="",
        answer="B",
        options=["Wrong", "Correct", "Wrong2", "Wrong3"],
        hints=[],
        scope_files=["src/x.py"],
    )


def _make_explain_challenge() -> Challenge:
    return Challenge(
        id="ch-002",
        type="explain_why",
        knowledge_entry_id="kb-001",
        difficulty=3,
        prompt="Why does X work this way?",
        context="",
        answer="Because tokens are refreshed before validation to prevent mid-session expiry",
        options=None,
        hints=[],
        scope_files=["src/auth.py"],
    )


class TestEvaluateMultipleChoice:
    def test_correct_answer(self) -> None:
        ch = _make_mc_challenge()
        result = evaluate_answer(ch, "B")
        assert result == "pass"

    def test_correct_answer_lowercase(self) -> None:
        ch = _make_mc_challenge()
        result = evaluate_answer(ch, "b")
        assert result == "pass"

    def test_wrong_answer(self) -> None:
        ch = _make_mc_challenge()
        result = evaluate_answer(ch, "A")
        assert result == "fail"

    def test_empty_answer(self) -> None:
        ch = _make_mc_challenge()
        result = evaluate_answer(ch, "")
        assert result == "fail"


class TestEvaluateExplainWhy:
    def test_exact_match(self) -> None:
        ch = _make_explain_challenge()
        result = evaluate_answer(ch, ch.answer)
        assert result == "pass"

    def test_contains_key_concepts(self) -> None:
        ch = _make_explain_challenge()
        result = evaluate_answer(
            ch, "The tokens get refreshed before being validated so sessions don't expire"
        )
        assert result in ("pass", "partial")

    def test_completely_wrong(self) -> None:
        ch = _make_explain_challenge()
        result = evaluate_answer(ch, "I have no idea")
        assert result == "fail"

    def test_partial_match(self) -> None:
        ch = _make_explain_challenge()
        result = evaluate_answer(ch, "Something about tokens")
        assert result in ("partial", "fail")


class TestEvaluateDependencyMap:
    def test_correct_modules(self) -> None:
        ch = Challenge(
            id="ch-003",
            type="dependency_map",
            knowledge_entry_id="kb-001",
            difficulty=3,
            prompt="Which modules?",
            context="",
            answer="src/a.py, src/b.py",
            options=None,
            hints=[],
            scope_files=["src/main.py"],
        )
        result = evaluate_answer(ch, "src/a.py, src/b.py")
        assert result == "pass"

    def test_partial_modules(self) -> None:
        ch = Challenge(
            id="ch-003",
            type="dependency_map",
            knowledge_entry_id="kb-001",
            difficulty=3,
            prompt="Which modules?",
            context="",
            answer="src/a.py, src/b.py, src/c.py",
            options=None,
            hints=[],
            scope_files=["src/main.py"],
        )
        result = evaluate_answer(ch, "src/a.py")
        assert result == "partial"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/gauntlet && uv run pytest tests/unit/test_scoring.py -v 2>&1 | head -10`
Expected: FAIL

- [ ] **Step 3: Implement scoring**

`plugins/gauntlet/src/gauntlet/scoring.py`:
```python
"""Answer evaluation for gauntlet challenges."""

from __future__ import annotations

import re
from typing import Callable

from gauntlet.models import Challenge

# Minimum word overlap ratio for text-based scoring
_PASS_THRESHOLD = 0.5
_PARTIAL_THRESHOLD = 0.2

# Evaluator registry by challenge type
_EVALUATORS: dict[str, Callable[[Challenge, str], str]] = {}


def _register(name: str) -> Callable:
    """Register an evaluator for a challenge type."""
    def decorator(func: Callable[[Challenge, str], str]) -> Callable:
        _EVALUATORS[name] = func
        return func
    return decorator


def evaluate_answer(challenge: Challenge, answer: str) -> str:
    """Evaluate an answer against a challenge.

    Returns "pass", "partial", or "fail".
    """
    evaluator = _EVALUATORS.get(challenge.type, _evaluate_text_similarity)
    return evaluator(challenge, answer)


def _normalize(text: str) -> set[str]:
    """Normalize text to a set of lowercase words."""
    return set(re.findall(r"\w+", text.lower()))


def _word_overlap(expected: str, actual: str) -> float:
    """Calculate word overlap ratio between expected and actual."""
    expected_words = _normalize(expected)
    actual_words = _normalize(actual)
    if not expected_words:
        return 0.0
    overlap = expected_words & actual_words
    return len(overlap) / len(expected_words)


@_register("multiple_choice")
def _evaluate_multiple_choice(challenge: Challenge, answer: str) -> str:
    """Evaluate a multiple choice answer (exact letter match)."""
    if not answer.strip():
        return "fail"
    if answer.strip().upper() == challenge.answer.strip().upper():
        return "pass"
    return "fail"


@_register("dependency_map")
def _evaluate_dependency_map(challenge: Challenge, answer: str) -> str:
    """Evaluate a dependency map answer (set comparison)."""
    expected_modules = {m.strip().lower() for m in challenge.answer.split(",")}
    actual_modules = {m.strip().lower() for m in answer.split(",")}

    if not actual_modules - {""}:
        return "fail"

    overlap = expected_modules & actual_modules
    if not expected_modules:
        return "pass" if not actual_modules else "fail"

    ratio = len(overlap) / len(expected_modules)
    if ratio >= 0.8:
        return "pass"
    if ratio >= 0.3:
        return "partial"
    return "fail"


@_register("explain_why")
@_register("trace")
@_register("spot_bug")
@_register("code_completion")
def _evaluate_text_similarity(challenge: Challenge, answer: str) -> str:
    """Evaluate text-based answers by word overlap with the rubric.

    This is the local fallback evaluator. In production, AI-evaluated
    types will use the active Claude model for richer assessment.
    This function handles offline and test scenarios.
    """
    if not answer.strip():
        return "fail"

    overlap = _word_overlap(challenge.answer, answer)

    if overlap >= _PASS_THRESHOLD:
        return "pass"
    if overlap >= _PARTIAL_THRESHOLD:
        return "partial"
    return "fail"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/gauntlet && uv run pytest tests/unit/test_scoring.py -v`
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/gauntlet/src/gauntlet/scoring.py plugins/gauntlet/tests/unit/test_scoring.py
git commit -m "feat(gauntlet): add answer evaluation with type-specific scoring

Exact match for multiple choice, set comparison for dependency map,
word overlap for text-based types (explain, trace, spot-bug, completion)."
```

---

### Task 7: Progress Tracking and Adaptive Weighting

**Files:**
- Create: `plugins/gauntlet/src/gauntlet/progress.py`
- Create: `plugins/gauntlet/tests/unit/test_progress.py`

- [ ] **Step 1: Write failing tests**

`plugins/gauntlet/tests/unit/test_progress.py`:
```python
"""Tests for progress tracking and persistence."""

from __future__ import annotations

import json
from pathlib import Path

from gauntlet.models import AnswerRecord, DeveloperProgress, KnowledgeEntry
from gauntlet.progress import ProgressTracker


def _make_entry(id: str = "kb-001", category: str = "business_logic") -> KnowledgeEntry:
    return KnowledgeEntry(
        id=id, category=category, module="src/x.py", concept="X",
        detail="Detail", related_files=[], difficulty=3, tags=[],
        extracted_at="2026-03-30T12:00:00Z", source="automated",
        consumers=["both"],
    )


class TestProgressTracker:
    def test_get_or_create_new(self, tmp_gauntlet_dir: Path) -> None:
        tracker = ProgressTracker(tmp_gauntlet_dir)
        prog = tracker.get_or_create("dev@test.com")
        assert prog.developer_id == "dev@test.com"
        assert prog.streak == 0

    def test_record_answer_pass(self, tmp_gauntlet_dir: Path) -> None:
        tracker = ProgressTracker(tmp_gauntlet_dir)
        prog = tracker.get_or_create("dev@test.com")
        tracker.record_answer(prog, "ch-001", "kb-001", "multiple_choice", "business_logic", 2, "pass")
        assert len(prog.history) == 1
        assert prog.streak == 1

    def test_record_answer_fail_resets_streak(self, tmp_gauntlet_dir: Path) -> None:
        tracker = ProgressTracker(tmp_gauntlet_dir)
        prog = tracker.get_or_create("dev@test.com")
        tracker.record_answer(prog, "ch-001", "kb-001", "multiple_choice", "business_logic", 2, "pass")
        tracker.record_answer(prog, "ch-002", "kb-002", "multiple_choice", "business_logic", 2, "fail")
        assert prog.streak == 0

    def test_save_and_load(self, tmp_gauntlet_dir: Path) -> None:
        tracker = ProgressTracker(tmp_gauntlet_dir)
        prog = tracker.get_or_create("dev@test.com")
        tracker.record_answer(prog, "ch-001", "kb-001", "multiple_choice", "business_logic", 2, "pass")
        tracker.save(prog)

        tracker2 = ProgressTracker(tmp_gauntlet_dir)
        loaded = tracker2.get_or_create("dev@test.com")
        assert loaded.streak == 1
        assert len(loaded.history) == 1

    def test_select_entry_prefers_unseen(self, tmp_gauntlet_dir: Path) -> None:
        tracker = ProgressTracker(tmp_gauntlet_dir)
        prog = tracker.get_or_create("dev@test.com")
        prog.last_seen = {"kb-001": "2026-03-30T12:00:00Z"}

        entries = [_make_entry("kb-001"), _make_entry("kb-002")]
        # Over many picks, kb-002 (unseen) should appear more
        picks = [tracker.select_entry(prog, entries).id for _ in range(50)]
        assert picks.count("kb-002") > picks.count("kb-001")

    def test_select_entry_prefers_weak_categories(self, tmp_gauntlet_dir: Path) -> None:
        tracker = ProgressTracker(tmp_gauntlet_dir)
        prog = tracker.get_or_create("dev@test.com")
        prog.history = [
            AnswerRecord("c1", "kb-001", "mc", "business_logic", 2, "pass", "2026-03-30T12:00:00Z"),
            AnswerRecord("c2", "kb-001", "mc", "business_logic", 2, "pass", "2026-03-30T12:01:00Z"),
            AnswerRecord("c3", "kb-002", "mc", "architecture", 2, "fail", "2026-03-30T12:02:00Z"),
        ]

        bl_entry = _make_entry("kb-003", "business_logic")
        arch_entry = _make_entry("kb-004", "architecture")
        entries = [bl_entry, arch_entry]
        picks = [tracker.select_entry(prog, entries).id for _ in range(50)]
        assert picks.count("kb-004") > picks.count("kb-003")

    def test_current_difficulty(self, tmp_gauntlet_dir: Path) -> None:
        tracker = ProgressTracker(tmp_gauntlet_dir)
        prog = tracker.get_or_create("dev@test.com")
        assert tracker.current_difficulty(prog) == 3  # default

        # Build a streak of 3
        for i in range(3):
            tracker.record_answer(prog, f"ch-{i}", f"kb-{i}", "mc", "bl", 3, "pass")
        assert tracker.current_difficulty(prog) == 4  # bumped up
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/gauntlet && uv run pytest tests/unit/test_progress.py -v 2>&1 | head -10`
Expected: FAIL

- [ ] **Step 3: Implement progress tracker**

`plugins/gauntlet/src/gauntlet/progress.py`:
```python
"""Progress tracking with spaced repetition and adaptive difficulty."""

from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from gauntlet.models import AnswerRecord, DeveloperProgress, KnowledgeEntry

_DEFAULT_DIFFICULTY = 3
_STREAK_BUMP_THRESHOLD = 3
_MAX_DIFFICULTY = 5


class ProgressTracker:
    """Manages developer progress with persistence and adaptive selection."""

    def __init__(self, gauntlet_dir: Path) -> None:
        self._progress_dir = gauntlet_dir / "progress"
        self._progress_dir.mkdir(parents=True, exist_ok=True)

    def get_or_create(self, developer_id: str) -> DeveloperProgress:
        """Load existing progress or create new."""
        path = self._path_for(developer_id)
        if path.exists():
            data = json.loads(path.read_text())
            return DeveloperProgress.from_dict(data)
        return DeveloperProgress(developer_id=developer_id)

    def save(self, progress: DeveloperProgress) -> None:
        """Persist progress to disk."""
        path = self._path_for(progress.developer_id)
        path.write_text(json.dumps(progress.to_dict(), indent=2))

    def record_answer(
        self,
        progress: DeveloperProgress,
        challenge_id: str,
        knowledge_entry_id: str,
        challenge_type: str,
        category: str,
        difficulty: int,
        result: str,
    ) -> None:
        """Record an answer and update streak."""
        record = AnswerRecord(
            challenge_id=challenge_id,
            knowledge_entry_id=knowledge_entry_id,
            challenge_type=challenge_type,
            category=category,
            difficulty=difficulty,
            result=result,
            answered_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        progress.history.append(record)
        progress.last_seen[knowledge_entry_id] = record.answered_at

        if result == "pass":
            progress.streak += 1
        else:
            progress.streak = 0

        self.save(progress)

    def select_entry(
        self,
        progress: DeveloperProgress,
        entries: list[KnowledgeEntry],
    ) -> KnowledgeEntry:
        """Select a knowledge entry weighted by spaced repetition and weakness."""
        if not entries:
            raise ValueError("No entries to select from")

        weights: list[float] = []
        for entry in entries:
            w = 1.0

            # Unseen entries get higher weight
            if entry.id not in progress.last_seen:
                w += 2.0

            # Weak categories get higher weight
            cat_accuracy = progress.category_accuracy(entry.category)
            cat_records = [r for r in progress.history if r.category == entry.category]
            if cat_records:
                w += max(0.0, 2.0 - cat_accuracy * 2.0)
            else:
                w += 1.5  # Untested category

            weights.append(w)

        return random.choices(entries, weights=weights, k=1)[0]

    def current_difficulty(self, progress: DeveloperProgress) -> int:
        """Calculate current difficulty based on streak."""
        base = _DEFAULT_DIFFICULTY
        bumps = progress.streak // _STREAK_BUMP_THRESHOLD
        return min(base + bumps, _MAX_DIFFICULTY)

    def _path_for(self, developer_id: str) -> Path:
        """Get the file path for a developer's progress."""
        safe_name = developer_id.replace("@", "_at_").replace(".", "_")
        return self._progress_dir / f"{safe_name}.json"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/gauntlet && uv run pytest tests/unit/test_progress.py -v`
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/gauntlet/src/gauntlet/progress.py plugins/gauntlet/tests/unit/test_progress.py
git commit -m "feat(gauntlet): add progress tracking with spaced repetition

Adaptive entry selection weighted by unseen entries and weak
categories. Streak-based difficulty scaling. JSON persistence."
```

---

## Phase 4: Query API

### Task 8: Agent-Facing Query API

**Files:**
- Create: `plugins/gauntlet/src/gauntlet/query.py`
- Create: `plugins/gauntlet/tests/unit/test_query.py`

- [ ] **Step 1: Write failing tests**

`plugins/gauntlet/tests/unit/test_query.py`:
```python
"""Tests for the agent-facing query API."""

from __future__ import annotations

from pathlib import Path

from gauntlet.query import get_context_for_files, query_knowledge, validate_understanding


class TestQueryKnowledge:
    def test_query_all(self, sample_knowledge_base: Path) -> None:
        results = query_knowledge(sample_knowledge_base.parent)
        assert len(results) == 3

    def test_query_by_file(self, sample_knowledge_base: Path) -> None:
        results = query_knowledge(
            sample_knowledge_base.parent,
            files=["src/auth/middleware.py"],
        )
        assert len(results) >= 1

    def test_query_by_category(self, sample_knowledge_base: Path) -> None:
        results = query_knowledge(
            sample_knowledge_base.parent,
            categories=["data_flow"],
        )
        assert len(results) == 1
        assert results[0].category == "data_flow"

    def test_query_empty_dir(self, tmp_gauntlet_dir: Path) -> None:
        results = query_knowledge(tmp_gauntlet_dir)
        assert results == []


class TestGetContextForFiles:
    def test_returns_markdown(self, sample_knowledge_base: Path) -> None:
        md = get_context_for_files(
            sample_knowledge_base.parent,
            files=["src/auth/token_manager.py"],
        )
        assert "Token refresh" in md
        assert "##" in md  # Has markdown headings

    def test_no_matching_files(self, sample_knowledge_base: Path) -> None:
        md = get_context_for_files(
            sample_knowledge_base.parent,
            files=["nonexistent.py"],
        )
        assert "No knowledge entries" in md


class TestValidateUnderstanding:
    def test_accurate_claim(self, sample_knowledge_base: Path) -> None:
        result = validate_understanding(
            sample_knowledge_base.parent,
            files=["src/auth/token_manager.py"],
            claim="Tokens are refreshed before validation to prevent mid-session expiry",
        )
        assert result["score"] >= 0.5

    def test_wrong_claim(self, sample_knowledge_base: Path) -> None:
        result = validate_understanding(
            sample_knowledge_base.parent,
            files=["src/auth/token_manager.py"],
            claim="This module handles database migrations",
        )
        assert result["score"] < 0.3

    def test_returns_gaps(self, sample_knowledge_base: Path) -> None:
        result = validate_understanding(
            sample_knowledge_base.parent,
            files=["src/auth/token_manager.py"],
            claim="Something about auth",
        )
        assert "gaps" in result
        assert isinstance(result["gaps"], list)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/gauntlet && uv run pytest tests/unit/test_query.py -v 2>&1 | head -10`
Expected: FAIL

- [ ] **Step 3: Implement query API**

`plugins/gauntlet/src/gauntlet/query.py`:
```python
"""Agent-facing query API for the gauntlet knowledge base."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from gauntlet.knowledge_store import KnowledgeStore
from gauntlet.models import KnowledgeEntry


def query_knowledge(
    gauntlet_dir: Path,
    files: Optional[list[str]] = None,
    categories: Optional[list[str]] = None,
    tags: Optional[list[str]] = None,
    min_difficulty: int = 1,
    max_difficulty: int = 5,
) -> list[KnowledgeEntry]:
    """Query the knowledge base with filters."""
    store = KnowledgeStore(gauntlet_dir)
    return store.query(
        files=files,
        categories=categories,
        tags=tags,
        min_difficulty=min_difficulty,
        max_difficulty=max_difficulty,
    )


def get_context_for_files(
    gauntlet_dir: Path,
    files: list[str],
) -> str:
    """Return a markdown summary of knowledge entries for the given files.

    Designed for injection into agent context before code modification.
    """
    entries = query_knowledge(gauntlet_dir, files=files)

    if not entries:
        return "No knowledge entries found for the specified files."

    lines = ["## Gauntlet Knowledge Context", ""]
    for entry in entries:
        lines.append(f"### {entry.concept}")
        lines.append(f"**Module:** `{entry.module}`")
        lines.append(f"**Category:** {entry.category}")
        lines.append(f"**Difficulty:** {entry.difficulty}/5")
        lines.append("")
        lines.append(entry.detail)
        if entry.related_files:
            lines.append("")
            lines.append("**Related:** " + ", ".join(f"`{f}`" for f in entry.related_files))
        lines.append("")

    return "\n".join(lines)


def validate_understanding(
    gauntlet_dir: Path,
    files: list[str],
    claim: str,
) -> dict[str, Any]:
    """Score a claim about files against the knowledge base.

    Returns {score: float, gaps: list[str]}.
    """
    entries = query_knowledge(gauntlet_dir, files=files)

    if not entries:
        return {"score": 0.0, "gaps": ["No knowledge entries for these files"]}

    claim_words = set(re.findall(r"\w+", claim.lower()))
    total_overlap = 0.0
    gaps: list[str] = []

    for entry in entries:
        entry_words = set(re.findall(r"\w+", entry.detail.lower()))
        if not entry_words:
            continue
        overlap = len(claim_words & entry_words) / len(entry_words)
        total_overlap += overlap

        if overlap < 0.3:
            gaps.append(f"Missing: {entry.concept} ({entry.category})")

    score = total_overlap / len(entries) if entries else 0.0

    return {"score": min(score, 1.0), "gaps": gaps}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd plugins/gauntlet && uv run pytest tests/unit/test_query.py -v`
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/gauntlet/src/gauntlet/query.py plugins/gauntlet/tests/unit/test_query.py
git commit -m "feat(gauntlet): add agent-facing query API

query_knowledge(), get_context_for_files(), validate_understanding()
for cross-plugin integration with abstract, pensive, sanctum."
```

---

## Phase 5: Pre-commit Hook

### Task 9: Pre-commit Gate Hook

**Files:**
- Create: `plugins/gauntlet/hooks/hooks.json`
- Create: `plugins/gauntlet/hooks/precommit_gate.py`
- Create: `plugins/gauntlet/tests/unit/test_precommit.py`

- [ ] **Step 1: Write failing tests**

`plugins/gauntlet/tests/unit/test_precommit.py`:
```python
"""Tests for the pre-commit gate hook."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

from precommit_gate import (
    check_pass_token,
    generate_challenge_for_files,
    write_pass_token,
    main,
)


class TestPassToken:
    def test_write_and_check(self, tmp_gauntlet_dir: Path) -> None:
        staged_hash = "abc123"
        write_pass_token(tmp_gauntlet_dir, staged_hash)
        assert check_pass_token(tmp_gauntlet_dir, staged_hash) is True

    def test_wrong_hash_fails(self, tmp_gauntlet_dir: Path) -> None:
        write_pass_token(tmp_gauntlet_dir, "abc123")
        assert check_pass_token(tmp_gauntlet_dir, "def456") is False

    def test_expired_token_fails(self, tmp_gauntlet_dir: Path) -> None:
        write_pass_token(tmp_gauntlet_dir, "abc123", ttl_seconds=0)
        time.sleep(0.1)
        assert check_pass_token(tmp_gauntlet_dir, "abc123") is False

    def test_missing_token_fails(self, tmp_gauntlet_dir: Path) -> None:
        assert check_pass_token(tmp_gauntlet_dir, "abc123") is False


class TestGenerateChallengeForFiles:
    def test_generates_from_knowledge_base(
        self, tmp_gauntlet_dir: Path, sample_knowledge_base: Path
    ) -> None:
        challenge = generate_challenge_for_files(
            tmp_gauntlet_dir,
            ["src/auth/token_manager.py"],
            developer_id="dev@test.com",
        )
        assert challenge is not None
        assert challenge.prompt != ""

    def test_no_knowledge_returns_none(self, tmp_gauntlet_dir: Path) -> None:
        challenge = generate_challenge_for_files(
            tmp_gauntlet_dir,
            ["nonexistent.py"],
            developer_id="dev@test.com",
        )
        assert challenge is None


class TestMainHook:
    def test_allows_when_valid_token(self, tmp_gauntlet_dir: Path) -> None:
        write_pass_token(tmp_gauntlet_dir, "abc123")
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {"command": "git commit -m 'test'"},
        }
        with patch("precommit_gate._get_gauntlet_dir", return_value=tmp_gauntlet_dir):
            with patch("precommit_gate._get_staged_hash", return_value="abc123"):
                output = main(hook_input)
        # Should not deny
        decision = output.get("hookSpecificOutput", {}).get("permissionDecision")
        assert decision != "deny"

    def test_denies_when_no_token(self, tmp_gauntlet_dir: Path, sample_knowledge_base: Path) -> None:
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {"command": "git commit -m 'test'"},
        }
        with patch("precommit_gate._get_gauntlet_dir", return_value=tmp_gauntlet_dir):
            with patch("precommit_gate._get_staged_hash", return_value="abc123"):
                with patch("precommit_gate._get_staged_files", return_value=["src/auth/token_manager.py"]):
                    output = main(hook_input)
        decision = output.get("hookSpecificOutput", {}).get("permissionDecision")
        assert decision == "deny"

    def test_non_commit_command_passes(self, tmp_gauntlet_dir: Path) -> None:
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {"command": "git status"},
        }
        with patch("precommit_gate._get_gauntlet_dir", return_value=tmp_gauntlet_dir):
            output = main(hook_input)
        decision = output.get("hookSpecificOutput", {}).get("permissionDecision")
        assert decision != "deny"

    def test_gauntlet_off_passes(self, tmp_gauntlet_dir: Path) -> None:
        config = {"precommit": {"mode": "off"}}
        config_path = tmp_gauntlet_dir / "config.yaml"
        # Write as JSON since yaml might not be available
        config_path.write_text(json.dumps(config))
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {"command": "git commit -m 'test'"},
        }
        with patch("precommit_gate._get_gauntlet_dir", return_value=tmp_gauntlet_dir):
            with patch("precommit_gate._load_config", return_value=config):
                output = main(hook_input)
        decision = output.get("hookSpecificOutput", {}).get("permissionDecision")
        assert decision != "deny"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd plugins/gauntlet && uv run pytest tests/unit/test_precommit.py -v 2>&1 | head -10`
Expected: FAIL

- [ ] **Step 3: Create hooks.json**

`plugins/gauntlet/hooks/hooks.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "if": "Bash(git commit*)",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/precommit_gate.py",
            "timeout": 2
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 4: Implement precommit_gate.py**

`plugins/gauntlet/hooks/precommit_gate.py`:
```python
#!/usr/bin/env python3
"""Pre-commit gate hook for gauntlet challenges.

Blocks git commit commands until the developer answers a challenge
about the code they're committing. Uses a pass-token mechanism:
on correct answer, a time-limited token is written that allows
the next commit.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_DEFAULT_TTL = 300  # 5 minutes

# Add src to path for gauntlet imports
_plugin_root = Path(__file__).resolve().parent.parent
_src_path = _plugin_root / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from gauntlet.challenges import generate_challenge, select_challenge_type  # noqa: E402
from gauntlet.knowledge_store import KnowledgeStore  # noqa: E402
from gauntlet.models import Challenge  # noqa: E402
from gauntlet.progress import ProgressTracker  # noqa: E402


def _get_gauntlet_dir() -> Optional[Path]:
    """Find the .gauntlet directory in the current working directory."""
    cwd = Path.cwd()
    gauntlet_dir = cwd / ".gauntlet"
    if gauntlet_dir.exists():
        return gauntlet_dir
    return None


def _load_config(gauntlet_dir: Path) -> dict[str, Any]:
    """Load gauntlet configuration."""
    config_path = gauntlet_dir / "config.yaml"
    if not config_path.exists():
        return {}
    try:
        import yaml
        return yaml.safe_load(config_path.read_text()) or {}
    except ImportError:
        # Fallback: try JSON
        try:
            return json.loads(config_path.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return {}


def _get_staged_files() -> list[str]:
    """Get list of staged files from git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def _get_staged_hash() -> str:
    """Get a hash of the current staged content."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--stat"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        return hashlib.sha256(result.stdout.encode()).hexdigest()[:16]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def _get_developer_id() -> str:
    """Get developer identity from git config."""
    try:
        result = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        return result.stdout.strip() or "unknown"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return "unknown"


def write_pass_token(
    gauntlet_dir: Path,
    staged_hash: str,
    ttl_seconds: int = _DEFAULT_TTL,
) -> None:
    """Write a pass token allowing the next commit."""
    state_dir = gauntlet_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    token = {
        "staged_hash": staged_hash,
        "expires_at": time.time() + ttl_seconds,
    }
    (state_dir / "pass_token.json").write_text(json.dumps(token))


def check_pass_token(gauntlet_dir: Path, staged_hash: str) -> bool:
    """Check if a valid pass token exists for this staged content."""
    token_path = gauntlet_dir / "state" / "pass_token.json"
    if not token_path.exists():
        return False

    try:
        token = json.loads(token_path.read_text())
    except (json.JSONDecodeError, OSError):
        return False

    if token.get("staged_hash") != staged_hash:
        return False

    if time.time() > token.get("expires_at", 0):
        token_path.unlink(missing_ok=True)
        return False

    # Valid token — consume it (one-time use)
    token_path.unlink(missing_ok=True)
    return True


def generate_challenge_for_files(
    gauntlet_dir: Path,
    files: list[str],
    developer_id: str,
) -> Optional[Challenge]:
    """Generate a challenge scoped to the given files."""
    store = KnowledgeStore(gauntlet_dir)
    entries = store.query(files=files)

    if not entries:
        return None

    tracker = ProgressTracker(gauntlet_dir)
    progress = tracker.get_or_create(developer_id)
    entry = tracker.select_entry(progress, entries)
    challenge_type = select_challenge_type(progress)

    return generate_challenge(entry, challenge_type)


def _format_challenge(challenge: Challenge) -> str:
    """Format a challenge for display in additionalContext."""
    lines = [
        "## Gauntlet Challenge",
        "",
        f"**Type:** {challenge.type.replace('_', ' ').title()}",
        f"**Difficulty:** {'*' * challenge.difficulty}",
        "",
        challenge.prompt,
    ]

    if challenge.context:
        lines.extend(["", "```", challenge.context, "```"])

    if challenge.options:
        lines.append("")
        for i, opt in enumerate(challenge.options):
            letter = chr(ord("A") + i)
            lines.append(f"  {letter}) {opt}")

    lines.extend([
        "",
        "Answer in the conversation. On correct answer, the commit will proceed.",
    ])

    return "\n".join(lines)


def main(hook_input: dict[str, Any]) -> dict[str, Any]:
    """Hook entry point."""
    empty_output = {"hookSpecificOutput": {"hookEventName": "PreToolUse"}}

    # Only act on git commit commands
    tool_input = hook_input.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command.startswith("git commit"):
        return empty_output

    gauntlet_dir = _get_gauntlet_dir()
    if gauntlet_dir is None:
        return empty_output

    # Check config
    config = _load_config(gauntlet_dir)
    precommit_config = config.get("precommit", {})
    mode = precommit_config.get("mode", "gate")

    if mode == "off":
        return empty_output

    # Check for valid pass token
    staged_hash = _get_staged_hash()
    if check_pass_token(gauntlet_dir, staged_hash):
        return empty_output

    # No valid token — generate a challenge
    staged_files = _get_staged_files()
    if not staged_files:
        return empty_output

    developer_id = _get_developer_id()
    challenge = generate_challenge_for_files(gauntlet_dir, staged_files, developer_id)

    if challenge is None:
        # No knowledge entries for these files — allow commit
        return empty_output

    # Block the commit with a challenge
    challenge_text = _format_challenge(challenge)

    # Save pending challenge for later evaluation
    state_dir = gauntlet_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    pending = {
        "challenge": challenge.to_dict(),
        "staged_hash": staged_hash,
        "developer_id": developer_id,
    }
    (state_dir / "pending_challenge.json").write_text(json.dumps(pending, indent=2))

    if mode == "nudge":
        # Nudge mode: show challenge but don't block
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": challenge_text,
            }
        }

    # Gate mode: block the commit
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "additionalContext": challenge_text,
        }
    }


if __name__ == "__main__":
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        hook_input = {}

    output = main(hook_input)
    print(json.dumps(output))
    sys.exit(0)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd plugins/gauntlet && uv run pytest tests/unit/test_precommit.py -v`
Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add plugins/gauntlet/hooks/ plugins/gauntlet/tests/unit/test_precommit.py
git commit -m "feat(gauntlet): add pre-commit gate hook with pass-token mechanism

Blocks git commit until challenge answered correctly. Pass token
is one-time-use, hash-bound, and expires after 5 minutes.
Supports gate, nudge, and off modes."
```

---

## Phase 6: Skills & Commands

### Task 10: Skills

**Files:**
- Create: `plugins/gauntlet/skills/extract/SKILL.md`
- Create: `plugins/gauntlet/skills/challenge/SKILL.md`
- Create: `plugins/gauntlet/skills/onboard/SKILL.md`
- Create: `plugins/gauntlet/skills/curate/SKILL.md`

- [ ] **Step 1: Create extract skill**

`plugins/gauntlet/skills/extract/SKILL.md`:
```markdown
---
name: extract
description: >
  Analyze a codebase and build a knowledge base of business logic,
  architecture, data flow, and engineering patterns. The foundation
  for gauntlet challenges and agent integration.
model_hint: standard
---

# Extract Codebase Knowledge

Build or rebuild the `.gauntlet/knowledge.json` knowledge base.

## Steps

1. **Identify target directory**: use the current working
   directory or a user-specified path

2. **Run AST extraction**: invoke the extractor script
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/extractor.py <target-dir>
   ```

3. **AI enrichment**: for each extracted entry, enhance the
   `detail` field with natural language explanation of:
   - Business logic and domain rules
   - Data flow through the module
   - Architectural role and responsibilities
   - Why this code exists (not just what it does)

4. **Cross-reference**: link related entries across modules
   by matching imports, shared types, and data flow paths

5. **Merge with annotations**: preserve any existing curated
   entries in `.gauntlet/annotations/`

6. **Save**: write the enriched knowledge base to
   `.gauntlet/knowledge.json`

7. **Report**: show summary statistics
   - Total entries by category
   - Coverage gaps (modules with no entries)
   - Difficulty distribution

## Category Priority

Extract in this order (highest priority first):

1. business_logic (weight 7)
2. architecture (weight 6)
3. data_flow (weight 5)
4. api_contract (weight 4)
5. pattern (weight 3)
6. dependency (weight 2)
7. error_handling (weight 1)
```

- [ ] **Step 2: Create challenge skill**

`plugins/gauntlet/skills/challenge/SKILL.md`:
```markdown
---
name: challenge
description: >
  Run a gauntlet challenge session with adaptive difficulty.
  Tests codebase understanding through multiple choice, code
  completion, trace exercises, and more.
model_hint: standard
---

# Run Gauntlet Challenge

Present challenges from the knowledge base and evaluate answers.

## Steps

1. **Load state**: read `.gauntlet/knowledge.json` and
   developer progress from `.gauntlet/progress/`

2. **Check for pending challenge**: if
   `.gauntlet/state/pending_challenge.json` exists, evaluate
   the developer's most recent message as an answer to that
   challenge before generating a new one

3. **Generate challenge**: use adaptive weighting to select
   a knowledge entry and challenge type

4. **Present challenge**: show the question with appropriate
   context (code snippets, module excerpts)

5. **Evaluate answer**: score the developer's response
   - Multiple choice: exact letter match
   - Text-based: check key concepts against the rubric
   - Dependency map: set comparison of modules

6. **Record result**: update developer progress and streak

7. **On pass**: write a pass token if this was triggered by
   a pre-commit gate. Show encouragement and next challenge
   if in a session.

8. **On fail**: show the correct answer with explanation.
   Present a new challenge.

## Scoring

| Result | Score | Streak |
|--------|-------|--------|
| Pass | 1.0 | +1 |
| Partial | 0.5 | reset |
| Fail | 0.0 | reset |
```

- [ ] **Step 3: Create onboard skill**

`plugins/gauntlet/skills/onboard/SKILL.md`:
```markdown
---
name: onboard
description: >
  Guided onboarding path through five stages: big picture,
  core domain, interfaces, patterns, and hardening.
model_hint: standard
---

# Guided Onboarding

Walk a new developer through the codebase in structured stages.

## Stages

| Stage | Focus | Categories | Difficulty |
|-------|-------|-----------|------------|
| 1 | Big picture | architecture, data_flow | 1-2 |
| 2 | Core domain | business_logic | 2-3 |
| 3 | Interfaces | api_contract, data_flow | 3 |
| 4 | Patterns | pattern, dependency | 3-4 |
| 5 | Hardening | error_handling, business_logic | 4-5 |

## Steps

1. **Load onboarding progress** from
   `.gauntlet/progress/<developer>_onboarding.json`

2. **Show current stage** and progress summary

3. **Present 5 challenges** from the current stage's
   categories and difficulty range

4. **Enable hints** on first attempt for each challenge

5. **Track mastery**: mark knowledge entries as mastered
   when answered correctly twice

6. **Check advancement**: 80% accuracy across 10+
   challenges advances to the next stage

7. **Report progress**: "Stage 2: Core Domain --
   7/15 concepts mastered, 73% accuracy"

## Graduation

After stage 5, the developer enters the regular gauntlet.
Answer history carries over for adaptive weighting.
```

- [ ] **Step 4: Create curate skill**

`plugins/gauntlet/skills/curate/SKILL.md`:
```markdown
---
name: curate
description: >
  Add or edit knowledge annotations. Capture tribal knowledge,
  business context, and rationale that cannot be inferred from code.
model_hint: standard
---

# Curate Knowledge

Add developer-authored annotations to the knowledge base.

## Steps

1. **Identify the module** the developer wants to annotate

2. **Ask for the concept**: what is the key insight or rule?

3. **Ask for the why**: what is the rationale, history, or
   context behind this?

4. **Generate YAML annotation** file:
   ```yaml
   module: <module-path>
   concept: "<one-line concept>"
   why: >
     <multi-line explanation>
   related_files:
     - <file1>
     - <file2>
   difficulty: <1-5>
   tags: [<tag1>, <tag2>]
   ```

5. **Save** to `.gauntlet/annotations/<slug>.yaml`

6. **Confirm** the annotation was saved and will be
   included in future challenges
```

- [ ] **Step 5: Commit skills**

```bash
git add plugins/gauntlet/skills/
git commit -m "feat(gauntlet): add skills for extract, challenge, onboard, curate

Four skills covering the core gauntlet workflow: knowledge extraction,
challenge sessions, guided onboarding, and knowledge curation."
```

---

### Task 11: Commands

**Files:**
- Create: `plugins/gauntlet/commands/gauntlet.md`
- Create: `plugins/gauntlet/commands/extract.md`
- Create: `plugins/gauntlet/commands/progress.md`
- Create: `plugins/gauntlet/commands/onboard.md`
- Create: `plugins/gauntlet/commands/curate.md`

- [ ] **Step 1: Create all command files**

`plugins/gauntlet/commands/gauntlet.md`:
```markdown
---
description: Run an ad-hoc gauntlet challenge session (5 questions, random scope)
model_hint: standard
---

# Gauntlet Challenge Session

Invoke `Skill(gauntlet:challenge)` to run a 5-question session.

Arguments:
- No args: random scope, 5 questions
- `--count N`: run N questions
- `--scope <file-or-dir>`: limit to specific files
- `--type <type>`: force a specific challenge type
```

`plugins/gauntlet/commands/extract.md`:
```markdown
---
description: Rebuild the knowledge base from the current codebase
model_hint: standard
---

# Extract Knowledge

Invoke `Skill(gauntlet:extract)` to analyze the codebase and
rebuild `.gauntlet/knowledge.json`.

Arguments:
- No args: extract from current directory
- `<path>`: extract from specific directory
```

`plugins/gauntlet/commands/progress.md`:
```markdown
---
description: Show challenge accuracy stats, weak areas, and streak
model_hint: fast
---

# Gauntlet Progress

Show the developer's challenge statistics.

## Steps

1. Get developer ID from `git config user.email`
2. Load progress from `.gauntlet/progress/<developer>.json`
3. Display:
   - Overall accuracy
   - Current streak
   - Accuracy by category (highlight weakest)
   - Accuracy by challenge type
   - Total challenges answered
   - Last session date
```

`plugins/gauntlet/commands/onboard.md`:
```markdown
---
description: Start or resume a guided onboarding path
model_hint: standard
---

# Onboarding

Invoke `Skill(gauntlet:onboard)` to start or resume the
guided onboarding path.

Arguments:
- No args: resume from current stage
- `--stage N`: jump to stage N
- `--reset`: restart from stage 1
```

`plugins/gauntlet/commands/curate.md`:
```markdown
---
description: Add or edit a knowledge annotation
model_hint: standard
---

# Curate Knowledge

Invoke `Skill(gauntlet:curate)` to add a developer-authored
annotation to the knowledge base.

Arguments:
- No args: interactive annotation workflow
- `<module-path>`: annotate a specific module
```

- [ ] **Step 2: Commit commands**

```bash
git add plugins/gauntlet/commands/
git commit -m "feat(gauntlet): add slash commands

/gauntlet, /gauntlet-extract, /gauntlet-progress,
/gauntlet-onboard, /gauntlet-curate."
```

---

### Task 12: Extractor Agent

**Files:**
- Create: `plugins/gauntlet/agents/extractor.md`

- [ ] **Step 1: Create the extractor agent**

`plugins/gauntlet/agents/extractor.md`:
```markdown
---
name: extractor
model: sonnet
agent: true
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
description: |
  Autonomous knowledge extraction agent. Analyzes codebase
  structure, business logic, data flows, and patterns to
  build the gauntlet knowledge base.
---

# Knowledge Extractor Agent

Analyze a codebase and produce a `.gauntlet/knowledge.json`
knowledge base.

## Workflow

1. **Discover source files**: use Glob to find all Python,
   TypeScript, and other source files in the target directory.
   Skip tests, configs, and generated files.

2. **Run AST extraction**: execute the extractor script:
   ```bash
   python3 plugins/gauntlet/scripts/extractor.py <target-dir> --output .gauntlet/knowledge.json
   ```

3. **Enrich entries**: for each extracted entry, read the
   source file and enhance the detail with:
   - Business logic explanation (why, not just what)
   - Data flow description
   - Architectural context

4. **Cross-reference**: identify entries that share files
   in their `related_files` and link them

5. **Assign categories** using priority order:
   business_logic > architecture > data_flow > api_contract >
   pattern > dependency > error_handling

6. **Validate**: ensure all entries have non-empty detail,
   valid difficulty (1-5), and at least one tag

7. **Save**: write to `.gauntlet/knowledge.json`

## Error Handling

- If a file cannot be parsed, skip it and log a warning
- If the extractor script fails, fall back to manual
  file-by-file analysis using Read + Grep
- Report partial results rather than failing entirely
```

- [ ] **Step 2: Commit agent**

```bash
git add plugins/gauntlet/agents/
git commit -m "feat(gauntlet): add knowledge extractor agent

Sonnet-level agent for autonomous codebase analysis and
knowledge base generation."
```

---

## Phase 7: CLI Scripts

### Task 13: CLI Entry Points

**Files:**
- Create: `plugins/gauntlet/scripts/extractor.py`
- Create: `plugins/gauntlet/scripts/challenge_engine.py`
- Create: `plugins/gauntlet/scripts/answer_evaluator.py`
- Create: `plugins/gauntlet/scripts/progress_tracker.py`

- [ ] **Step 1: Create extractor CLI**

`plugins/gauntlet/scripts/extractor.py`:
```python
#!/usr/bin/env python3
"""CLI entry point for knowledge extraction."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add src to path
_src = Path(__file__).resolve().parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from gauntlet.extraction import extract_from_directory
from gauntlet.knowledge_store import KnowledgeStore


def main() -> int:
    """Run knowledge extraction."""
    parser = argparse.ArgumentParser(description="Extract codebase knowledge")
    parser.add_argument("target_dir", type=Path, help="Directory to analyze")
    parser.add_argument("--output", type=Path, default=None, help="Output .gauntlet dir")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args()

    entries = extract_from_directory(args.target_dir)

    if args.output:
        gauntlet_dir = args.output
        gauntlet_dir.mkdir(parents=True, exist_ok=True)
        store = KnowledgeStore(gauntlet_dir)
        store.save(entries)
        print(f"Saved {len(entries)} entries to {gauntlet_dir / 'knowledge.json'}")
    elif args.format == "json":
        print(json.dumps([e.to_dict() for e in entries], indent=2))
    else:
        print(f"Extracted {len(entries)} knowledge entries:")
        for entry in entries:
            print(f"  [{entry.category}] {entry.concept} (difficulty {entry.difficulty})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Create challenge_engine CLI**

`plugins/gauntlet/scripts/challenge_engine.py`:
```python
#!/usr/bin/env python3
"""CLI entry point for challenge generation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_src = Path(__file__).resolve().parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from gauntlet.challenges import generate_challenge, select_challenge_type
from gauntlet.knowledge_store import KnowledgeStore
from gauntlet.progress import ProgressTracker


def main() -> int:
    """Generate a challenge."""
    parser = argparse.ArgumentParser(description="Generate a gauntlet challenge")
    parser.add_argument("gauntlet_dir", type=Path, help=".gauntlet directory")
    parser.add_argument("--developer", default="unknown", help="Developer ID")
    parser.add_argument("--files", nargs="*", help="Scope to specific files")
    parser.add_argument("--type", dest="challenge_type", help="Force challenge type")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args()

    store = KnowledgeStore(args.gauntlet_dir)
    entries = store.query(files=args.files) if args.files else store.load(include_annotations=True)

    if not entries:
        print("No knowledge entries found.", file=sys.stderr)
        return 1

    tracker = ProgressTracker(args.gauntlet_dir)
    progress = tracker.get_or_create(args.developer)
    entry = tracker.select_entry(progress, entries)
    ct = args.challenge_type or select_challenge_type(progress)
    challenge = generate_challenge(entry, ct)

    if args.format == "json":
        print(json.dumps(challenge.to_dict(), indent=2))
    else:
        print(f"[{challenge.type}] {challenge.prompt}")
        if challenge.options:
            for i, opt in enumerate(challenge.options):
                print(f"  {chr(ord('A') + i)}) {opt}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Create answer_evaluator CLI**

`plugins/gauntlet/scripts/answer_evaluator.py`:
```python
#!/usr/bin/env python3
"""CLI entry point for answer evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_src = Path(__file__).resolve().parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from gauntlet.models import Challenge
from gauntlet.scoring import evaluate_answer


def main() -> int:
    """Evaluate an answer against a challenge."""
    parser = argparse.ArgumentParser(description="Evaluate a gauntlet answer")
    parser.add_argument("challenge_json", type=Path, help="Challenge JSON file")
    parser.add_argument("answer", help="Developer's answer")
    args = parser.parse_args()

    data = json.loads(args.challenge_json.read_text())
    challenge = Challenge(**data)
    result = evaluate_answer(challenge, args.answer)

    print(json.dumps({"result": result}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Create progress_tracker CLI**

`plugins/gauntlet/scripts/progress_tracker.py`:
```python
#!/usr/bin/env python3
"""CLI entry point for progress statistics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_src = Path(__file__).resolve().parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from gauntlet.progress import ProgressTracker


def main() -> int:
    """Show developer progress statistics."""
    parser = argparse.ArgumentParser(description="Show gauntlet progress")
    parser.add_argument("gauntlet_dir", type=Path, help=".gauntlet directory")
    parser.add_argument("--developer", default="unknown", help="Developer ID")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args()

    tracker = ProgressTracker(args.gauntlet_dir)
    progress = tracker.get_or_create(args.developer)

    if args.format == "json":
        print(json.dumps(progress.to_dict(), indent=2))
    else:
        print(f"Developer: {progress.developer_id}")
        print(f"Overall accuracy: {progress.overall_accuracy():.0%}")
        print(f"Current streak: {progress.streak}")
        print(f"Total challenges: {len(progress.history)}")

        if progress.history:
            categories = set(r.category for r in progress.history)
            print("\nAccuracy by category:")
            for cat in sorted(categories):
                acc = progress.category_accuracy(cat)
                print(f"  {cat}: {acc:.0%}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Verify scripts run**

Run: `cd plugins/gauntlet && python3 scripts/extractor.py --help && python3 scripts/challenge_engine.py --help`
Expected: help text for both scripts

- [ ] **Step 6: Commit scripts**

```bash
git add plugins/gauntlet/scripts/
git commit -m "feat(gauntlet): add CLI scripts for extraction, challenges, scoring, progress

Entry points for extractor.py, challenge_engine.py,
answer_evaluator.py, and progress_tracker.py."
```

---

## Phase 8: README and Final Validation

### Task 14: README and Integration Test

**Files:**
- Create: `plugins/gauntlet/README.md`
- Create: `plugins/gauntlet/tests/integration/test_end_to_end.py`

- [ ] **Step 1: Write integration test**

`plugins/gauntlet/tests/integration/test_end_to_end.py`:
```python
"""End-to-end integration test for the gauntlet workflow."""

from __future__ import annotations

from pathlib import Path

import pytest

from gauntlet.challenges import generate_challenge, select_challenge_type
from gauntlet.extraction import extract_from_file
from gauntlet.knowledge_store import KnowledgeStore
from gauntlet.progress import ProgressTracker
from gauntlet.query import get_context_for_files, query_knowledge
from gauntlet.scoring import evaluate_answer


@pytest.mark.integration
class TestEndToEnd:
    def test_extract_challenge_score_loop(
        self,
        sample_python_file: Path,
        tmp_gauntlet_dir: Path,
    ) -> None:
        """Full loop: extract -> store -> challenge -> score -> progress."""
        # 1. Extract knowledge from a source file
        entries = extract_from_file(sample_python_file)
        assert len(entries) >= 1

        # 2. Store in knowledge base
        store = KnowledgeStore(tmp_gauntlet_dir)
        store.save(entries)
        loaded = store.load()
        assert len(loaded) == len(entries)

        # 3. Generate a challenge
        tracker = ProgressTracker(tmp_gauntlet_dir)
        progress = tracker.get_or_create("test@dev.com")
        entry = tracker.select_entry(progress, loaded)
        ct = select_challenge_type(progress)
        challenge = generate_challenge(entry, ct)
        assert challenge.prompt != ""

        # 4. Evaluate an answer
        if challenge.type == "multiple_choice":
            result = evaluate_answer(challenge, challenge.answer)
        else:
            result = evaluate_answer(challenge, entry.detail)
        assert result in ("pass", "partial", "fail")

        # 5. Record progress
        tracker.record_answer(
            progress,
            challenge.id,
            challenge.knowledge_entry_id,
            challenge.type,
            entry.category,
            entry.difficulty,
            result,
        )
        assert len(progress.history) == 1

    def test_query_api_after_extraction(
        self,
        sample_python_file: Path,
        tmp_gauntlet_dir: Path,
    ) -> None:
        """Query API works after extraction."""
        entries = extract_from_file(sample_python_file)
        store = KnowledgeStore(tmp_gauntlet_dir)
        store.save(entries)

        # Query by file
        results = query_knowledge(
            tmp_gauntlet_dir,
            files=[str(sample_python_file)],
        )
        assert len(results) >= 1

        # Get context
        context = get_context_for_files(
            tmp_gauntlet_dir,
            files=[str(sample_python_file)],
        )
        assert "##" in context
```

- [ ] **Step 2: Run integration test**

Run: `cd plugins/gauntlet && uv run pytest tests/integration/ -v -m integration`
Expected: all tests PASS

- [ ] **Step 3: Create README**

`plugins/gauntlet/README.md`:
```markdown
# Gauntlet

Codebase learning through knowledge extraction, challenges,
and spaced repetition. Prevents knowledge atrophy for
experienced developers and accelerates onboarding for new ones.

## Quick Start

```bash
# Extract knowledge from your codebase
/gauntlet-extract

# Run a challenge session
/gauntlet

# Check your progress
/gauntlet-progress

# Start guided onboarding
/gauntlet-onboard
```

## How It Works

1. **Knowledge extraction** analyzes your codebase via AST
   parsing and AI summarization to build a knowledge base
   of business logic, architecture, data flow, and patterns.

2. **Challenge engine** generates six types of exercises:
   multiple choice, code completion, trace, explain-the-why,
   spot-the-bug, and dependency mapping.

3. **Pre-commit gate** blocks commits until you answer a
   question about the code you are shipping. Configurable
   as gate (default), nudge, or off.

4. **Adaptive difficulty** uses spaced repetition to
   target your weak areas and increase difficulty as
   your streak grows.

## Configuration

Create `.gauntlet/config.yaml` in your repository:

```yaml
precommit:
  mode: gate        # gate | nudge | session | off
  scope: commit     # commit | full

difficulty:
  default: 3
  adaptive: true

onboarding:
  guided_path: true
  hints_enabled: true
```

## Knowledge Curation

Add annotations the AI cannot infer:

```yaml
# .gauntlet/annotations/my-annotation.yaml
module: src/auth/token_manager.py
concept: "Token refresh before validation"
why: >
  Historical incident caused mid-session logouts.
related_files:
  - src/auth/middleware.py
difficulty: 3
tags: [auth, business-rule]
```

## Commands

| Command | Purpose |
|---------|---------|
| `/gauntlet` | Run a challenge session |
| `/gauntlet-extract` | Rebuild knowledge base |
| `/gauntlet-progress` | Show stats and weak areas |
| `/gauntlet-onboard` | Guided onboarding path |
| `/gauntlet-curate` | Add knowledge annotations |
```

- [ ] **Step 4: Run full test suite**

Run: `cd plugins/gauntlet && uv run pytest tests/ -v --tb=short`
Expected: all tests PASS

- [ ] **Step 5: Run linting**

Run: `cd plugins/gauntlet && uv run ruff check src/ scripts/ hooks/ tests/`
Expected: no errors (or only auto-fixable style issues)

- [ ] **Step 6: Commit README and integration tests**

```bash
git add plugins/gauntlet/README.md plugins/gauntlet/tests/integration/
git commit -m "feat(gauntlet): add README and integration tests

End-to-end test covering extract -> store -> challenge -> score
-> progress loop. README with quick start and configuration."
```

- [ ] **Step 7: Final commit — all gauntlet files**

Verify nothing is unstaged:
```bash
cd plugins/gauntlet && git status
```

If any files remain, add and commit:
```bash
git add plugins/gauntlet/
git commit -m "feat(gauntlet): complete plugin structure for #192"
```
