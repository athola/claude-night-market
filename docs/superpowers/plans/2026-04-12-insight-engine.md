# Insight Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan
> task-by-task. Steps use checkbox (`- [ ]`) syntax for
> tracking.

**Goal:** Transform the learnings system from a repetitive
metrics reporter into a proactive insight engine with
pluggable analyzer lenses, content-hash deduplication,
and GitHub Discussions integration.

**Architecture:** Pluggable lens-based analyzer that feeds
findings through an InsightRegistry (dedup engine) into a
new "Insights" Discussion category. Four trigger points:
Stop hook (lightweight), scheduled agent (deep),
/pr-review (PR-scoped), /code-refinement (codebase-wide).

**Tech Stack:** Python 3.9+, GitHub GraphQL API via `gh`
CLI, pytest, existing abstract plugin infrastructure.

**Spec:** `docs/superpowers/specs/2026-04-12-insight-engine-design.md`

---

## Task 1: Diagnose and Fix Skill Execution Logging Gap

The logging system only captures 1 of 200+ skills
(`abstract:skill-auditor`). Without broader data, the
insight engine has nothing to analyze. This task
investigates and fixes the logging gap.

**Files:**

- Modify: `plugins/abstract/hooks/skill_execution_logger.py:308-387`
- Modify: `plugins/abstract/hooks/shared/skill_utils.py`
- Test: `plugins/abstract/tests/hooks/test_skill_execution_logger.py`

- [ ] **Step 1: Add diagnostic logging to skill_execution_logger**

Add stderr tracing to every exit path in `main()` so we
can see which skills hit the hook and where they bail out.
In `plugins/abstract/hooks/skill_execution_logger.py`,
add a debug mode controlled by env var:

```python
# At the top of main(), after the existing try:
_DEBUG = os.environ.get("SKILL_LOGGER_DEBUG", "")

def main() -> None:
    """PostToolUse hook entry point."""
    try:
        tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
        tool_input_str = os.environ.get("CLAUDE_TOOL_INPUT", "{}")
        tool_output = os.environ.get("CLAUDE_TOOL_OUTPUT", "")

        if _DEBUG:
            sys.stderr.write(
                f"[skill_logger] tool_name={tool_name} "
                f"input_preview={tool_input_str[:100]}\n"
            )

        if tool_name != "Skill":
            sys.exit(0)

        # ... rest of existing code, but add debug traces
        # at parse_skill_name, save_log_entry, etc.
```

- [ ] **Step 2: Write a test that exercises the full logging path**

In a new or existing test file, verify that `create_log_entry`
and `save_log_entry` work for various skill name formats:

```python
# plugins/abstract/tests/hooks/test_skill_execution_logger.py

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent.parent / "hooks")
)
sys.path.insert(
    0, str(Path(__file__).parent.parent.parent / "hooks" / "shared")
)

from skill_execution_logger import (
    create_log_entry,
    save_log_entry,
)


@pytest.fixture()
def log_dir(tmp_path):
    with patch(
        "skill_execution_logger.get_log_directory",
        return_value=tmp_path,
    ):
        yield tmp_path


def test_logs_fully_qualified_skill(log_dir):
    """Skills like 'abstract:skill-auditor' log correctly."""
    entry = create_log_entry(
        tool_input={"skill": "abstract:skill-auditor"},
        tool_output="Launching skill: abstract:skill-auditor",
        pre_state=None,
        evaluator=None,
    )
    save_log_entry(entry)

    log_files = list(log_dir.rglob("*.jsonl"))
    assert len(log_files) == 1
    assert "abstract" in str(log_files[0])
    assert "skill-auditor" in str(log_files[0])


def test_logs_short_name_skill(log_dir):
    """Skills like 'commit' without plugin prefix log under 'unknown'."""
    entry = create_log_entry(
        tool_input={"skill": "commit"},
        tool_output="Launching skill: commit",
        pre_state=None,
        evaluator=None,
    )
    save_log_entry(entry)

    log_files = list(log_dir.rglob("*.jsonl"))
    assert len(log_files) == 1
    assert "unknown" in str(log_files[0])


def test_outcome_detection_not_fooled_by_skill_content(log_dir):
    """Skill content mentioning 'error' shouldn't mark as failure."""
    entry = create_log_entry(
        tool_input={"skill": "sanctum:commit-msg"},
        tool_output="Launching skill: sanctum:commit-msg",
        pre_state=None,
        evaluator=None,
    )
    # The "Launching skill" output shouldn't trigger error detection
    assert entry["outcome"] == "success"
```

- [ ] **Step 3: Run the tests**

Run: `cd /home/alext/claude-night-market && python -m pytest plugins/abstract/tests/hooks/test_skill_execution_logger.py -v`
Expected: All 3 tests pass.

- [ ] **Step 4: Check if CLAUDE_TOOL_INPUT is populated for skill invocations**

Run a manual diagnostic by temporarily adding stderr output
to the main() function to capture what the hook receives
during a live session:

```python
# Temporary diagnostic at the top of main():
sys.stderr.write(
    f"[DIAG] CLAUDE_TOOL_NAME={os.environ.get('CLAUDE_TOOL_NAME', 'UNSET')} "
    f"CLAUDE_TOOL_INPUT={os.environ.get('CLAUDE_TOOL_INPUT', 'UNSET')[:200]}\n"
)
```

Use a test skill invocation (`/abstract:test-skill`) and
check stderr for the diagnostic output. This determines
whether the hook is firing but parsing incorrectly, or
not firing at all.

- [ ] **Step 5: Commit the diagnostic and test improvements**

```bash
git add plugins/abstract/hooks/skill_execution_logger.py \
       plugins/abstract/tests/hooks/test_skill_execution_logger.py
git commit -m "fix(abstract): add diagnostic tracing to skill execution logger

The logger only captures 1 of 200+ skills. Add debug mode
and tests to identify where invocations are lost."
```

---

## Task 2: Finding Dataclass and AnalysisContext

Create the core data structures that all lenses and the
registry depend on.

**Files:**

- Create: `plugins/abstract/scripts/insight_types.py`
- Test: `plugins/abstract/tests/scripts/test_insight_types.py`

- [ ] **Step 1: Write the failing test**

```python
# plugins/abstract/tests/scripts/test_insight_types.py

import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent.parent / "scripts")
)

from insight_types import (
    AnalysisContext,
    Finding,
    finding_hash,
)


def test_finding_creation():
    f = Finding(
        type="Trend",
        severity="medium",
        skill="abstract:skill-auditor",
        summary="success rate dropped from 92% to 71%",
        evidence="- 2026-03-29: 92%\n- 2026-04-12: 71%",
        recommendation="Investigate error pattern",
        source="trend_lens",
    )
    assert f.type == "Trend"
    assert f.related_files == []


def test_finding_hash_deterministic():
    f = Finding(
        type="Trend",
        severity="medium",
        skill="abstract:skill-auditor",
        summary="success rate dropped from 92% to 71%",
        evidence="different evidence",
        recommendation="different rec",
        source="different_source",
    )
    h1 = finding_hash(f)
    h2 = finding_hash(f)
    assert h1 == h2
    assert len(h1) == 12


def test_finding_hash_differs_by_type():
    base = dict(
        severity="medium",
        skill="abstract:skill-auditor",
        summary="same summary",
        evidence="",
        recommendation="",
        source="test",
    )
    f1 = Finding(type="Trend", **base)
    f2 = Finding(type="Bug Alert", **base)
    assert finding_hash(f1) != finding_hash(f2)


def test_finding_hash_ignores_evidence():
    """Hash is based on type:skill:summary, not evidence."""
    base = dict(
        type="Trend",
        severity="medium",
        skill="x:y",
        summary="same",
        recommendation="",
        source="test",
    )
    f1 = Finding(evidence="evidence A", **base)
    f2 = Finding(evidence="evidence B", **base)
    assert finding_hash(f1) == finding_hash(f2)


def test_analysis_context_creation():
    ctx = AnalysisContext(
        metrics={},
        previous_snapshot=None,
        performance_history=None,
        improvement_memory=None,
        code_paths=[],
        pr_diff=None,
        trigger="stop",
    )
    assert ctx.trigger == "stop"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/alext/claude-night-market && python -m pytest plugins/abstract/tests/scripts/test_insight_types.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'insight_types'`

- [ ] **Step 3: Write the implementation**

```python
# plugins/abstract/scripts/insight_types.py
"""Core data structures for the Insight Engine.

Finding represents a single insight produced by an analyzer
lens. AnalysisContext carries all data a lens needs to run.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Valid insight types and their title prefixes
INSIGHT_TYPES = {
    "Trend": "[Trend]",
    "Pattern": "[Pattern]",
    "Bug Alert": "[Bug Alert]",
    "Optimization": "[Optimization]",
    "Improvement": "[Improvement]",
    "PR Finding": "[PR Finding]",
    "Health Check": "[Health Check]",
}


@dataclass
class Finding:
    """A single insight produced by an analyzer lens."""

    type: str
    severity: str  # "high", "medium", "low", "info"
    skill: str  # affected skill or "" for cross-cutting
    summary: str  # one-line, used in title and hash
    evidence: str  # markdown body with data/metrics
    recommendation: str  # what to do about it
    source: str  # which lens/trigger produced this
    related_files: list[str] = field(default_factory=list)

    def title(self) -> str:
        """Generate a discussion title from this finding."""
        prefix = INSIGHT_TYPES.get(self.type, f"[{self.type}]")
        if self.skill:
            return f"{prefix} {self.skill}: {self.summary}"
        return f"{prefix} {self.summary}"


@dataclass
class AnalysisContext:
    """Data available to analyzer lenses during a run."""

    metrics: dict[str, Any]
    previous_snapshot: dict[str, Any] | None
    performance_history: Any  # PerformanceTracker or None
    improvement_memory: Any  # ImprovementMemory or None
    code_paths: list[Path] = field(default_factory=list)
    pr_diff: str | None = None
    trigger: str = "stop"


def finding_hash(finding: Finding) -> str:
    """Compute a deterministic content hash for dedup.

    Hash is based on type, skill, and summary only.
    Evidence and recommendation are excluded so that
    updated data for the same observation gets the
    same hash.
    """
    key = f"{finding.type}:{finding.skill}:{finding.summary}"
    return hashlib.sha256(key.encode()).hexdigest()[:12]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/alext/claude-night-market && python -m pytest plugins/abstract/tests/scripts/test_insight_types.py -v`
Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/abstract/scripts/insight_types.py \
       plugins/abstract/tests/scripts/test_insight_types.py
git commit -m "feat(abstract): add Finding and AnalysisContext data structures

Core types for the insight engine. Finding represents a
single insight with type, severity, evidence, and
recommendation. finding_hash() provides content-based
dedup keyed on type:skill:summary."
```

---

## Task 3: InsightRegistry with Content-Hash Dedup

The registry accepts findings, deduplicates them via
content hashing with staleness expiry, and decides
whether to post, link, or skip.

**Files:**

- Create: `plugins/abstract/scripts/insight_registry.py`
- Test: `plugins/abstract/tests/scripts/test_insight_registry.py`

- [ ] **Step 1: Write the failing test**

```python
# plugins/abstract/tests/scripts/test_insight_registry.py

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent.parent / "scripts")
)

from insight_registry import InsightRegistry
from insight_types import Finding


def _make_finding(**overrides) -> Finding:
    defaults = dict(
        type="Trend",
        severity="medium",
        skill="abstract:skill-auditor",
        summary="success rate dropped",
        evidence="data here",
        recommendation="investigate",
        source="trend_lens",
    )
    defaults.update(overrides)
    return Finding(**defaults)


@pytest.fixture()
def registry(tmp_path):
    return InsightRegistry(state_path=tmp_path / "insights_posted.json")


def test_new_finding_is_not_duplicate(registry):
    f = _make_finding()
    result = registry.check_local(f)
    assert result == "create"


def test_same_finding_is_duplicate(registry):
    f = _make_finding()
    registry.record_posted(f, "https://example.com/1")
    result = registry.check_local(f)
    assert result == "skip"


def test_different_finding_is_not_duplicate(registry):
    f1 = _make_finding(summary="dropped 92 to 71")
    f2 = _make_finding(summary="dropped 71 to 50")
    registry.record_posted(f1, "https://example.com/1")
    result = registry.check_local(f2)
    assert result == "create"


def test_stale_finding_can_repost(registry):
    f = _make_finding()
    registry.record_posted(f, "https://example.com/1")
    # Manually age the entry to 31 days
    from insight_types import finding_hash
    h = finding_hash(f)
    registry._state["posted_hashes"][h]["posted_at"] = "2026-03-01"
    registry._save()
    result = registry.check_local(f)
    assert result == "create"


def test_state_persists_to_disk(tmp_path):
    path = tmp_path / "insights_posted.json"
    r1 = InsightRegistry(state_path=path)
    f = _make_finding()
    r1.record_posted(f, "https://example.com/1")

    r2 = InsightRegistry(state_path=path)
    assert r2.check_local(f) == "skip"


def test_snapshot_save_and_load(registry):
    snapshot = {"abstract:skill-auditor": {"success_rate": 40.0}}
    registry.save_snapshot(snapshot)
    loaded = registry.load_snapshot()
    assert loaded == snapshot
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/alext/claude-night-market && python -m pytest plugins/abstract/tests/scripts/test_insight_registry.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'insight_registry'`

- [ ] **Step 3: Write the implementation**

```python
# plugins/abstract/scripts/insight_registry.py
"""Insight deduplication registry.

Accepts findings from any source, deduplicates via
content hashing with 30-day staleness expiry, and
persists state to disk.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from insight_types import Finding, finding_hash

STALENESS_DAYS = 30


class InsightRegistry:
    """Tracks posted insights and prevents duplicates."""

    def __init__(self, state_path: Path | None = None):
        self._path = state_path or (
            Path.home()
            / ".claude"
            / "skills"
            / "discussions"
            / "insights_posted.json"
        )
        self._state: dict = {"posted_hashes": {}, "last_snapshot": {}}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                self._state = json.loads(self._path.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        # Ensure required keys
        self._state.setdefault("posted_hashes", {})
        self._state.setdefault("last_snapshot", {})

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._state, indent=2))

    def check_local(self, finding: Finding) -> str:
        """Check if a finding is a local duplicate.

        Returns:
            "skip" if already posted and not stale,
            "create" if new or stale.
        """
        h = finding_hash(finding)
        entry = self._state["posted_hashes"].get(h)
        if entry is None:
            return "create"

        posted_at = entry.get("posted_at", "")
        if self._is_stale(posted_at):
            return "create"

        return "skip"

    def record_posted(self, finding: Finding, url: str) -> None:
        """Record that a finding was posted."""
        h = finding_hash(finding)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._state["posted_hashes"][h] = {
            "url": url,
            "posted_at": today,
            "type": finding.type,
            "summary": finding.summary,
        }
        self._save()

    def save_snapshot(self, snapshot: dict) -> None:
        """Save a metrics snapshot for delta comparison."""
        self._state["last_snapshot"] = snapshot
        self._save()

    def load_snapshot(self) -> dict:
        """Load the last metrics snapshot."""
        return self._state.get("last_snapshot", {})

    @staticmethod
    def _is_stale(posted_at: str, max_age_days: int = STALENESS_DAYS) -> bool:
        if not posted_at:
            return True
        try:
            posted_date = datetime.strptime(posted_at, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
            age = (datetime.now(timezone.utc) - posted_date).days
            return age > max_age_days
        except ValueError:
            return True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/alext/claude-night-market && python -m pytest plugins/abstract/tests/scripts/test_insight_registry.py -v`
Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/abstract/scripts/insight_registry.py \
       plugins/abstract/tests/scripts/test_insight_registry.py
git commit -m "feat(abstract): add InsightRegistry with content-hash dedup

Tracks posted insights via content hashing (type:skill:summary).
Includes 30-day staleness expiry so persistent problems get
re-surfaced. Persists state to insights_posted.json."
```

---

## Task 4: GitHub Semantic Dedup (Layer 4)

Extend the InsightRegistry to query existing GitHub
Discussions and compare findings using Jaccard similarity
on normalized terms.

**Files:**

- Modify: `plugins/abstract/scripts/insight_registry.py`
- Test: `plugins/abstract/tests/scripts/test_insight_registry.py`

- [ ] **Step 1: Write the failing tests**

Add to `test_insight_registry.py`:

```python
from insight_registry import (
    DedupResult,
    normalize_terms,
    jaccard_similarity,
)


def test_normalize_terms():
    text = "skill-auditor: 40.0% success rate dropped to 35.2%"
    terms = normalize_terms(text)
    assert "skill-auditor" in terms
    assert "success" in terms
    assert "rate" in terms
    # Numbers normalized to ranges
    assert "30-40%" in terms or "40-50%" in terms


def test_jaccard_identical():
    assert jaccard_similarity({"a", "b", "c"}, {"a", "b", "c"}) == 1.0


def test_jaccard_disjoint():
    assert jaccard_similarity({"a", "b"}, {"c", "d"}) == 0.0


def test_jaccard_partial():
    sim = jaccard_similarity({"a", "b", "c"}, {"b", "c", "d"})
    assert 0.4 < sim < 0.6  # 2/4 = 0.5


def test_dedup_result_link():
    r = DedupResult(action="link", target_id="123", target_url="url", reason="match")
    assert r.action == "link"


def test_dedup_result_create():
    r = DedupResult(action="create")
    assert r.target_id is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/alext/claude-night-market && python -m pytest plugins/abstract/tests/scripts/test_insight_registry.py -v -k "normalize or jaccard or dedup_result"`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Add semantic dedup to insight_registry.py**

Add these to `insight_registry.py`:

```python
import re
from dataclasses import dataclass


@dataclass
class DedupResult:
    """Result of deduplication check."""

    action: str  # "create", "link", "update"
    target_id: str | None = None
    target_url: str | None = None
    reason: str = ""


# Thresholds for semantic similarity
LINK_THRESHOLD = 0.85
REFERENCE_THRESHOLD = 0.60

_NUMBER_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%?")


def normalize_terms(text: str) -> set[str]:
    """Extract and normalize key terms from text.

    Numbers are bucketed into ranges (e.g. 42% -> 40-50%).
    Short words and stopwords are removed.
    """
    stopwords = {
        "the", "a", "an", "is", "was", "are", "were",
        "to", "from", "in", "of", "for", "with", "and",
        "or", "but", "not", "this", "that",
    }
    terms: set[str] = set()

    # Normalize numbers to ranges
    for match in _NUMBER_RE.finditer(text):
        num = float(match.group(1))
        bucket_low = int(num // 10) * 10
        bucket_high = bucket_low + 10
        has_pct = "%" in match.group(0)
        suffix = "%" if has_pct else ""
        terms.add(f"{bucket_low}-{bucket_high}{suffix}")

    # Extract word tokens
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]+", text.lower())
    for w in words:
        if w not in stopwords and len(w) > 2:
            terms.add(w)

    return terms


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union) if union else 0.0
```

Then add a method to `InsightRegistry`:

```python
def check_github(
    self,
    finding: Finding,
    existing_discussions: list[dict],
) -> DedupResult:
    """Compare finding against existing GitHub discussions.

    Args:
        finding: The finding to check.
        existing_discussions: List of dicts with 'id',
            'url', 'title', 'body' from GitHub search.

    Returns:
        DedupResult with action and optional target.
    """
    finding_terms = normalize_terms(
        f"{finding.type} {finding.skill} {finding.summary}"
    )

    best_sim = 0.0
    best_discussion = None

    for disc in existing_discussions:
        disc_terms = normalize_terms(
            f"{disc.get('title', '')} {disc.get('body', '')[:500]}"
        )
        sim = jaccard_similarity(finding_terms, disc_terms)
        if sim > best_sim:
            best_sim = sim
            best_discussion = disc

    if best_sim > LINK_THRESHOLD and best_discussion:
        return DedupResult(
            action="link",
            target_id=best_discussion.get("id"),
            target_url=best_discussion.get("url"),
            reason=(
                f"Matches #{best_discussion.get('number', '?')} "
                f"({best_sim:.0%})"
            ),
        )
    elif best_sim > REFERENCE_THRESHOLD and best_discussion:
        return DedupResult(
            action="update",
            target_id=best_discussion.get("id"),
            target_url=best_discussion.get("url"),
            reason=(
                f"Related to #{best_discussion.get('number', '?')}"
            ),
        )

    return DedupResult(action="create")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/alext/claude-night-market && python -m pytest plugins/abstract/tests/scripts/test_insight_registry.py -v`
Expected: All tests PASS (original 6 + new 6 = 12).

- [ ] **Step 5: Commit**

```bash
git add plugins/abstract/scripts/insight_registry.py \
       plugins/abstract/tests/scripts/test_insight_registry.py
git commit -m "feat(abstract): add GitHub semantic dedup to InsightRegistry

Jaccard similarity on normalized terms compares findings
against existing discussions. >85% links as comment, 60-85%
creates with reference, <60% creates standalone."
```

---

## Task 5: Lens Auto-Discovery and DeltaLens

Create the lens infrastructure and the first (most
critical) lens that prevents repetitive posting.

**Files:**

- Create: `plugins/abstract/scripts/lenses/__init__.py`
- Create: `plugins/abstract/scripts/lenses/delta_lens.py`
- Test: `plugins/abstract/tests/scripts/lenses/__init__.py`
- Test: `plugins/abstract/tests/scripts/lenses/test_delta_lens.py`

- [ ] **Step 1: Create lenses package with auto-discovery**

```python
# plugins/abstract/scripts/lenses/__init__.py
"""Pluggable analyzer lenses for the Insight Engine.

Lenses are auto-discovered from .py files in this directory.
Each lens module must define:
- LENS_META: dict with name, insight_types, weight, description
- analyze(context: AnalysisContext) -> list[Finding]
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Callable

_LENSES_DIR = Path(__file__).parent

# Type alias for lens analyze function
LensAnalyze = Callable[..., list]


def discover_lenses(
    weight: str = "all",
    lenses_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Discover lens modules in the lenses directory.

    Args:
        weight: Filter by weight ("lightweight", "deep", "all").
        lenses_dir: Override directory (for testing).

    Returns:
        List of dicts with 'meta' and 'analyze' keys.
    """
    search_dir = lenses_dir or _LENSES_DIR
    lenses: list[dict[str, Any]] = []

    # Ensure search_dir is on sys.path for imports
    search_str = str(search_dir)
    if search_str not in sys.path:
        sys.path.insert(0, search_str)

    for py_file in sorted(search_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue

        module_name = py_file.stem
        try:
            mod = importlib.import_module(module_name)
        except ImportError:
            continue

        meta = getattr(mod, "LENS_META", None)
        analyze_fn = getattr(mod, "analyze", None)

        if meta is None or analyze_fn is None:
            continue

        if weight != "all" and meta.get("weight") != weight:
            continue

        lenses.append({"meta": meta, "analyze": analyze_fn})

    return lenses
```

- [ ] **Step 2: Write DeltaLens tests**

```python
# plugins/abstract/tests/scripts/lenses/__init__.py
# (empty - package marker)
```

```python
# plugins/abstract/tests/scripts/lenses/test_delta_lens.py

import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent.parent.parent / "scripts")
)
sys.path.insert(
    0,
    str(
        Path(__file__).parent.parent.parent.parent
        / "scripts"
        / "lenses"
    ),
)

from delta_lens import LENS_META, analyze
from insight_types import AnalysisContext


def _ctx(metrics=None, previous_snapshot=None):
    return AnalysisContext(
        metrics=metrics or {},
        previous_snapshot=previous_snapshot,
        performance_history=None,
        improvement_memory=None,
        trigger="stop",
    )


def test_lens_meta_valid():
    assert LENS_META["name"] == "delta"
    assert LENS_META["weight"] == "lightweight"
    assert "analyze" in dir(sys.modules["delta_lens"])


def test_no_findings_when_no_change():
    """Stable metrics produce no findings."""
    snapshot = {
        "abstract:skill-auditor": {
            "success_rate": 40.0,
            "avg_duration_ms": 100.0,
        }
    }
    metrics = {
        "abstract:skill-auditor": type(
            "M", (), {"success_rate": 40.0, "avg_duration_ms": 100.0}
        )(),
    }
    findings = analyze(_ctx(metrics=metrics, previous_snapshot=snapshot))
    assert len(findings) == 0


def test_finding_when_success_rate_drops():
    """Significant success rate drop produces a Trend finding."""
    snapshot = {
        "abstract:skill-auditor": {
            "success_rate": 90.0,
            "avg_duration_ms": 100.0,
        }
    }
    metrics = {
        "abstract:skill-auditor": type(
            "M",
            (),
            {"success_rate": 70.0, "avg_duration_ms": 100.0},
        )(),
    }
    findings = analyze(_ctx(metrics=metrics, previous_snapshot=snapshot))
    assert len(findings) >= 1
    assert findings[0].type == "Trend"
    assert "70" in findings[0].summary or "dropped" in findings[0].summary.lower()


def test_finding_when_new_skill_appears():
    """A skill not in the previous snapshot produces a finding."""
    snapshot = {}
    metrics = {
        "new:skill": type(
            "M",
            (),
            {"success_rate": 50.0, "avg_duration_ms": 200.0},
        )(),
    }
    findings = analyze(_ctx(metrics=metrics, previous_snapshot=snapshot))
    assert len(findings) >= 1


def test_no_findings_when_no_previous_snapshot():
    """First run (no snapshot) saves baseline, no findings."""
    metrics = {
        "abstract:skill-auditor": type(
            "M",
            (),
            {"success_rate": 40.0, "avg_duration_ms": 100.0},
        )(),
    }
    findings = analyze(_ctx(metrics=metrics, previous_snapshot=None))
    assert len(findings) == 0


def test_recovery_finding():
    """Skill recovering from failure produces positive finding."""
    snapshot = {
        "abstract:skill-auditor": {
            "success_rate": 40.0,
            "avg_duration_ms": 100.0,
        }
    }
    metrics = {
        "abstract:skill-auditor": type(
            "M",
            (),
            {"success_rate": 85.0, "avg_duration_ms": 100.0},
        )(),
    }
    findings = analyze(_ctx(metrics=metrics, previous_snapshot=snapshot))
    assert len(findings) >= 1
    assert findings[0].severity == "info"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /home/alext/claude-night-market && python -m pytest plugins/abstract/tests/scripts/lenses/test_delta_lens.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 4: Implement DeltaLens**

```python
# plugins/abstract/scripts/lenses/delta_lens.py
"""DeltaLens: only surface what changed since last post.

Compares current metrics snapshot to the previously posted
snapshot. Produces findings only for meaningful changes:
- Success rate shifts > 10%
- Duration shifts > 2000ms
- New skills appearing
- Skills recovering from failure
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Ensure parent scripts dir is importable
_scripts_dir = Path(__file__).resolve().parent.parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from insight_types import AnalysisContext, Finding

LENS_META = {
    "name": "delta",
    "insight_types": ["Trend"],
    "weight": "lightweight",
    "description": "Detects metric changes since last post",
}

SUCCESS_RATE_THRESHOLD = 10.0  # percent
DURATION_THRESHOLD_MS = 2000.0


def analyze(context: AnalysisContext) -> list[Finding]:
    """Compare current metrics to previous snapshot."""
    findings: list[Finding] = []
    prev = context.previous_snapshot

    if prev is None:
        # First run: no baseline to compare against
        return []

    for skill, metrics in context.metrics.items():
        prev_data = prev.get(skill)

        if prev_data is None:
            # New skill appeared
            findings.append(
                Finding(
                    type="Trend",
                    severity="info",
                    skill=skill,
                    summary=f"new skill detected ({metrics.success_rate:.0f}% success)",
                    evidence=(
                        f"First observation: {metrics.success_rate:.1f}% "
                        f"success, {metrics.avg_duration_ms:.0f}ms avg"
                    ),
                    recommendation="Monitor in next cycle",
                    source="delta_lens",
                )
            )
            continue

        # Check success rate change
        prev_rate = prev_data.get("success_rate", 0)
        curr_rate = getattr(metrics, "success_rate", 0)
        rate_delta = curr_rate - prev_rate

        if abs(rate_delta) >= SUCCESS_RATE_THRESHOLD:
            if rate_delta < 0:
                # Degradation
                findings.append(
                    Finding(
                        type="Trend",
                        severity="medium" if abs(rate_delta) < 20 else "high",
                        skill=skill,
                        summary=(
                            f"success rate dropped "
                            f"{prev_rate:.0f}% to {curr_rate:.0f}%"
                        ),
                        evidence=(
                            f"- Previous: {prev_rate:.1f}%\n"
                            f"- Current: {curr_rate:.1f}%\n"
                            f"- Change: {rate_delta:+.1f}%"
                        ),
                        recommendation="Investigate recent changes to this skill",
                        source="delta_lens",
                    )
                )
            else:
                # Recovery
                findings.append(
                    Finding(
                        type="Trend",
                        severity="info",
                        skill=skill,
                        summary=(
                            f"recovered {prev_rate:.0f}% to {curr_rate:.0f}%"
                        ),
                        evidence=(
                            f"- Previous: {prev_rate:.1f}%\n"
                            f"- Current: {curr_rate:.1f}%\n"
                            f"- Improvement: +{rate_delta:.1f}%"
                        ),
                        recommendation="Recovery confirmed, continue monitoring",
                        source="delta_lens",
                    )
                )

        # Check duration change
        prev_dur = prev_data.get("avg_duration_ms", 0)
        curr_dur = getattr(metrics, "avg_duration_ms", 0)
        dur_delta = curr_dur - prev_dur

        if abs(dur_delta) >= DURATION_THRESHOLD_MS:
            direction = "slower" if dur_delta > 0 else "faster"
            findings.append(
                Finding(
                    type="Trend",
                    severity="low",
                    skill=skill,
                    summary=(
                        f"{direction} by {abs(dur_delta):.0f}ms"
                    ),
                    evidence=(
                        f"- Previous: {prev_dur:.0f}ms\n"
                        f"- Current: {curr_dur:.0f}ms"
                    ),
                    recommendation=(
                        "Investigate performance regression"
                        if dur_delta > 0
                        else "Performance improvement noted"
                    ),
                    source="delta_lens",
                )
            )

    return findings
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/alext/claude-night-market && python -m pytest plugins/abstract/tests/scripts/lenses/test_delta_lens.py -v`
Expected: All 6 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add plugins/abstract/scripts/lenses/__init__.py \
       plugins/abstract/scripts/lenses/delta_lens.py \
       plugins/abstract/tests/scripts/lenses/__init__.py \
       plugins/abstract/tests/scripts/lenses/test_delta_lens.py
git commit -m "feat(abstract): add lens auto-discovery and DeltaLens

Lenses are auto-discovered from plugins/abstract/scripts/lenses/.
DeltaLens compares current metrics to previous snapshot and
only produces findings for meaningful changes (>10% success
rate shift, >2s duration shift, new skills, recoveries)."
```

---

## Task 6: TrendLens, PatternLens, and HealthLens

The remaining lightweight lenses that run in the Stop hook.

**Files:**

- Create: `plugins/abstract/scripts/lenses/trend_lens.py`
- Create: `plugins/abstract/scripts/lenses/pattern_lens.py`
- Create: `plugins/abstract/scripts/lenses/health_lens.py`
- Test: `plugins/abstract/tests/scripts/lenses/test_trend_lens.py`
- Test: `plugins/abstract/tests/scripts/lenses/test_pattern_lens.py`
- Test: `plugins/abstract/tests/scripts/lenses/test_health_lens.py`

- [ ] **Step 1: Write TrendLens tests**

```python
# plugins/abstract/tests/scripts/lenses/test_trend_lens.py

import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent.parent.parent / "scripts")
)
sys.path.insert(
    0,
    str(
        Path(__file__).parent.parent.parent.parent
        / "scripts"
        / "lenses"
    ),
)

from trend_lens import LENS_META, analyze
from insight_types import AnalysisContext


def _metrics_obj(**kwargs):
    defaults = {
        "success_rate": 80.0,
        "avg_duration_ms": 500.0,
        "failure_count": 2,
        "total_executions": 10,
        "recent_errors": [],
        "common_friction": [],
    }
    defaults.update(kwargs)
    return type("M", (), defaults)()


def _ctx(metrics=None):
    return AnalysisContext(
        metrics=metrics or {},
        previous_snapshot=None,
        performance_history=None,
        improvement_memory=None,
        trigger="stop",
    )


def test_lens_meta():
    assert LENS_META["weight"] == "lightweight"


def test_no_findings_for_healthy_skills():
    ctx = _ctx({"x:y": _metrics_obj(success_rate=95.0, failure_count=1)})
    findings = analyze(ctx)
    assert len(findings) == 0


def test_high_failure_rate_finding():
    ctx = _ctx({
        "x:y": _metrics_obj(
            success_rate=35.0,
            failure_count=13,
            total_executions=20,
            recent_errors=["TimeoutError"],
        ),
    })
    findings = analyze(ctx)
    assert len(findings) >= 1
    assert any(f.severity == "high" for f in findings)
```

- [ ] **Step 2: Write PatternLens tests**

```python
# plugins/abstract/tests/scripts/lenses/test_pattern_lens.py

import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent.parent.parent / "scripts")
)
sys.path.insert(
    0,
    str(
        Path(__file__).parent.parent.parent.parent
        / "scripts"
        / "lenses"
    ),
)

from pattern_lens import LENS_META, analyze
from insight_types import AnalysisContext


def _metrics_obj(**kwargs):
    defaults = {
        "success_rate": 80.0,
        "failure_count": 2,
        "total_executions": 10,
        "recent_errors": [],
        "common_friction": [],
    }
    defaults.update(kwargs)
    return type("M", (), defaults)()


def _ctx(metrics=None):
    return AnalysisContext(
        metrics=metrics or {},
        previous_snapshot=None,
        performance_history=None,
        improvement_memory=None,
        trigger="stop",
    )


def test_lens_meta():
    assert LENS_META["weight"] == "lightweight"


def test_no_pattern_with_unique_errors():
    ctx = _ctx({
        "a:x": _metrics_obj(recent_errors=["ErrorA"]),
        "b:y": _metrics_obj(recent_errors=["ErrorB"]),
    })
    findings = analyze(ctx)
    assert len(findings) == 0


def test_pattern_detected_with_shared_errors():
    ctx = _ctx({
        "a:x": _metrics_obj(recent_errors=["TimeoutError: GraphQL"]),
        "b:y": _metrics_obj(recent_errors=["TimeoutError: GraphQL"]),
        "c:z": _metrics_obj(recent_errors=["TimeoutError: GraphQL"]),
    })
    findings = analyze(ctx)
    assert len(findings) >= 1
    assert findings[0].type == "Pattern"
    assert "3" in findings[0].summary
```

- [ ] **Step 3: Write HealthLens tests**

```python
# plugins/abstract/tests/scripts/lenses/test_health_lens.py

import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent.parent.parent / "scripts")
)
sys.path.insert(
    0,
    str(
        Path(__file__).parent.parent.parent.parent
        / "scripts"
        / "lenses"
    ),
)

from health_lens import LENS_META, analyze
from insight_types import AnalysisContext


def _metrics_obj(**kwargs):
    defaults = {
        "success_rate": 80.0,
        "total_executions": 10,
        "failure_count": 2,
    }
    defaults.update(kwargs)
    return type("M", (), defaults)()


def _ctx(metrics=None, code_paths=None):
    return AnalysisContext(
        metrics=metrics or {},
        previous_snapshot=None,
        performance_history=None,
        improvement_memory=None,
        code_paths=code_paths or [],
        trigger="stop",
    )


def test_lens_meta():
    assert LENS_META["weight"] == "lightweight"


def test_no_findings_when_all_active():
    ctx = _ctx({"a:x": _metrics_obj(total_executions=10)})
    findings = analyze(ctx)
    # Only unused skills trigger findings
    assert all(f.type == "Health Check" for f in findings)


def test_unused_skills_detected():
    ctx = _ctx({
        "a:x": _metrics_obj(total_executions=0),
        "a:y": _metrics_obj(total_executions=0),
        "a:z": _metrics_obj(total_executions=5),
    })
    findings = analyze(ctx)
    unused = [f for f in findings if "unused" in f.summary.lower() or "0 execution" in f.summary.lower()]
    assert len(unused) >= 1
```

- [ ] **Step 4: Run all lens tests to verify they fail**

Run: `cd /home/alext/claude-night-market && python -m pytest plugins/abstract/tests/scripts/lenses/ -v`
Expected: DeltaLens passes, TrendLens/PatternLens/HealthLens FAIL.

- [ ] **Step 5: Implement TrendLens**

```python
# plugins/abstract/scripts/lenses/trend_lens.py
"""TrendLens: detect skills with concerning metrics.

Identifies skills with high failure rates, excessive failures,
and other threshold violations from current metrics.
"""

from __future__ import annotations

import sys
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent.parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from insight_types import AnalysisContext, Finding

LENS_META = {
    "name": "trend",
    "insight_types": ["Trend"],
    "weight": "lightweight",
    "description": "Detect skills with concerning metric thresholds",
}

FAILURE_RATE_THRESHOLD = 50.0  # success rate below this
EXCESSIVE_FAILURES = 10
MIN_EXECUTIONS = 5


def analyze(context: AnalysisContext) -> list[Finding]:
    """Identify skills with concerning metrics."""
    findings: list[Finding] = []

    for skill, metrics in context.metrics.items():
        execs = getattr(metrics, "total_executions", 0)
        if execs < MIN_EXECUTIONS:
            continue

        rate = getattr(metrics, "success_rate", 100.0)
        failures = getattr(metrics, "failure_count", 0)
        errors = getattr(metrics, "recent_errors", [])

        if rate < FAILURE_RATE_THRESHOLD:
            error_summary = ""
            if errors:
                error_summary = f"\n- Recent: {errors[0][:80]}"
            findings.append(
                Finding(
                    type="Trend",
                    severity="high",
                    skill=skill,
                    summary=f"{rate:.0f}% success rate ({failures} failures)",
                    evidence=(
                        f"- Success rate: {rate:.1f}%\n"
                        f"- Failures: {failures}/{execs}"
                        f"{error_summary}"
                    ),
                    recommendation="Review recent errors and fix root cause",
                    source="trend_lens",
                )
            )
        elif failures > EXCESSIVE_FAILURES:
            findings.append(
                Finding(
                    type="Trend",
                    severity="medium",
                    skill=skill,
                    summary=f"{failures} failures despite {rate:.0f}% success",
                    evidence=(
                        f"- Failures: {failures} in {execs} executions\n"
                        f"- Rate: {rate:.1f}% (above threshold but high volume)"
                    ),
                    recommendation="High failure volume despite acceptable rate",
                    source="trend_lens",
                )
            )

    return findings
```

- [ ] **Step 6: Implement PatternLens**

```python
# plugins/abstract/scripts/lenses/pattern_lens.py
"""PatternLens: detect shared failure modes across skills.

Groups errors and friction points to find common patterns.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent.parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from insight_types import AnalysisContext, Finding

LENS_META = {
    "name": "pattern",
    "insight_types": ["Pattern"],
    "weight": "lightweight",
    "description": "Detect shared failure patterns across skills",
}

MIN_SKILLS_FOR_PATTERN = 2


def _normalize_error(error: str) -> str:
    """Normalize error string for grouping."""
    # Remove file paths, line numbers, timestamps
    text = re.sub(r"/[^\s]+\.py:\d+", "<path>", error)
    text = re.sub(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", "<time>", text)
    # Keep the error type and first meaningful word
    text = text.strip()[:80]
    return text


def analyze(context: AnalysisContext) -> list[Finding]:
    """Find shared error patterns across skills."""
    findings: list[Finding] = []
    # Group skills by normalized error
    error_groups: dict[str, list[str]] = defaultdict(list)

    for skill, metrics in context.metrics.items():
        errors = getattr(metrics, "recent_errors", [])
        for error in errors:
            key = _normalize_error(error)
            if key:
                error_groups[key].append(skill)

    # Group skills by friction point
    friction_groups: dict[str, list[str]] = defaultdict(list)
    for skill, metrics in context.metrics.items():
        frictions = getattr(metrics, "common_friction", [])
        for friction in frictions:
            friction_groups[friction.lower().strip()].append(skill)

    # Report error patterns
    for error, skills in error_groups.items():
        unique_skills = sorted(set(skills))
        if len(unique_skills) >= MIN_SKILLS_FOR_PATTERN:
            findings.append(
                Finding(
                    type="Pattern",
                    severity="medium",
                    skill="",
                    summary=(
                        f"{len(unique_skills)} skills: "
                        f"{error[:60]}"
                    ),
                    evidence=(
                        f"Affected skills:\n"
                        + "\n".join(f"- {s}" for s in unique_skills)
                        + f"\n\nError: {error}"
                    ),
                    recommendation=(
                        "Shared error pattern suggests a common "
                        "root cause across these skills"
                    ),
                    source="pattern_lens",
                )
            )

    # Report friction patterns
    for friction, skills in friction_groups.items():
        unique_skills = sorted(set(skills))
        if len(unique_skills) >= MIN_SKILLS_FOR_PATTERN:
            findings.append(
                Finding(
                    type="Pattern",
                    severity="low",
                    skill="",
                    summary=(
                        f"{len(unique_skills)} skills: "
                        f"shared friction '{friction[:40]}'"
                    ),
                    evidence=(
                        f"Friction point: {friction}\n"
                        f"Affected skills:\n"
                        + "\n".join(f"- {s}" for s in unique_skills)
                    ),
                    recommendation="Address the shared friction point",
                    source="pattern_lens",
                )
            )

    return findings
```

- [ ] **Step 7: Implement HealthLens**

```python
# plugins/abstract/scripts/lenses/health_lens.py
"""HealthLens: identify unused skills and system health issues."""

from __future__ import annotations

import sys
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent.parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from insight_types import AnalysisContext, Finding

LENS_META = {
    "name": "health",
    "insight_types": ["Health Check"],
    "weight": "lightweight",
    "description": "Identify unused skills and system health issues",
}


def analyze(context: AnalysisContext) -> list[Finding]:
    """Check system health indicators."""
    findings: list[Finding] = []

    # Find skills with zero executions
    unused = [
        skill
        for skill, m in context.metrics.items()
        if getattr(m, "total_executions", 0) == 0
    ]

    if unused:
        findings.append(
            Finding(
                type="Health Check",
                severity="info",
                skill="",
                summary=(
                    f"{len(unused)} skills with 0 executions in analysis period"
                ),
                evidence=(
                    "Unused skills:\n"
                    + "\n".join(f"- {s}" for s in sorted(unused)[:20])
                    + (
                        f"\n... and {len(unused) - 20} more"
                        if len(unused) > 20
                        else ""
                    )
                ),
                recommendation=(
                    "Consider deprecating unused skills or "
                    "investigating why they are not being invoked"
                ),
                source="health_lens",
            )
        )

    return findings
```

- [ ] **Step 8: Run all lens tests**

Run: `cd /home/alext/claude-night-market && python -m pytest plugins/abstract/tests/scripts/lenses/ -v`
Expected: All tests PASS.

- [ ] **Step 9: Commit**

```bash
git add plugins/abstract/scripts/lenses/trend_lens.py \
       plugins/abstract/scripts/lenses/pattern_lens.py \
       plugins/abstract/scripts/lenses/health_lens.py \
       plugins/abstract/tests/scripts/lenses/test_trend_lens.py \
       plugins/abstract/tests/scripts/lenses/test_pattern_lens.py \
       plugins/abstract/tests/scripts/lenses/test_health_lens.py
git commit -m "feat(abstract): add TrendLens, PatternLens, and HealthLens

TrendLens detects skills with concerning failure rates.
PatternLens groups shared errors/friction across skills.
HealthLens identifies unused skills."
```

---

## Task 7: Insight Analyzer Orchestrator

Wires lenses together, builds the AnalysisContext, and
runs the analysis pipeline.

**Files:**

- Create: `plugins/abstract/scripts/insight_analyzer.py`
- Test: `plugins/abstract/tests/scripts/test_insight_analyzer.py`

- [ ] **Step 1: Write the failing test**

```python
# plugins/abstract/tests/scripts/test_insight_analyzer.py

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent.parent / "scripts")
)

from insight_analyzer import run_analysis
from insight_types import Finding


def _metrics_obj(**kwargs):
    defaults = {
        "success_rate": 80.0,
        "avg_duration_ms": 500.0,
        "failure_count": 2,
        "total_executions": 10,
        "recent_errors": [],
        "common_friction": [],
    }
    defaults.update(kwargs)
    return type("M", (), defaults)()


def test_run_analysis_returns_findings(tmp_path):
    """Analysis pipeline produces findings from metrics."""
    metrics = {
        "x:y": _metrics_obj(success_rate=30.0, failure_count=14, total_executions=20),
    }
    lenses_dir = (
        Path(__file__).parent.parent.parent / "scripts" / "lenses"
    )
    findings = run_analysis(
        metrics=metrics,
        weight="lightweight",
        lenses_dir=lenses_dir,
        state_path=tmp_path / "state.json",
    )
    assert isinstance(findings, list)
    assert all(isinstance(f, Finding) for f in findings)
    # At least trend_lens should fire for 30% success
    assert len(findings) >= 1


def test_run_analysis_empty_metrics(tmp_path):
    """Empty metrics produce no findings."""
    lenses_dir = (
        Path(__file__).parent.parent.parent / "scripts" / "lenses"
    )
    findings = run_analysis(
        metrics={},
        weight="lightweight",
        lenses_dir=lenses_dir,
        state_path=tmp_path / "state.json",
    )
    assert findings == []


def test_run_analysis_saves_snapshot(tmp_path):
    """Analysis saves a metrics snapshot for delta comparison."""
    metrics = {
        "x:y": _metrics_obj(success_rate=90.0),
    }
    lenses_dir = (
        Path(__file__).parent.parent.parent / "scripts" / "lenses"
    )
    run_analysis(
        metrics=metrics,
        weight="lightweight",
        lenses_dir=lenses_dir,
        state_path=tmp_path / "state.json",
    )
    from insight_registry import InsightRegistry
    reg = InsightRegistry(state_path=tmp_path / "state.json")
    snap = reg.load_snapshot()
    assert "x:y" in snap
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/alext/claude-night-market && python -m pytest plugins/abstract/tests/scripts/test_insight_analyzer.py -v`
Expected: FAIL

- [ ] **Step 3: Implement insight_analyzer.py**

```python
# plugins/abstract/scripts/insight_analyzer.py
"""Insight Engine analyzer orchestrator.

Discovers lenses, builds AnalysisContext, runs analysis,
and returns findings. This is the main entry point called
by hooks and agents.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from insight_registry import InsightRegistry
from insight_types import AnalysisContext, Finding
from lenses import discover_lenses

# Optional Hyperagents modules
_src = Path(__file__).resolve().parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))
try:
    from abstract.improvement_memory import ImprovementMemory

    _HAS_IMPROVEMENT_MEMORY = True
except ImportError:
    _HAS_IMPROVEMENT_MEMORY = False
try:
    from abstract.performance_tracker import PerformanceTracker

    _HAS_PERFORMANCE_TRACKER = True
except ImportError:
    _HAS_PERFORMANCE_TRACKER = False


def _build_context(
    metrics: dict[str, Any],
    registry: InsightRegistry,
    trigger: str = "stop",
    pr_diff: str | None = None,
    code_paths: list[Path] | None = None,
) -> AnalysisContext:
    """Build an AnalysisContext from available data."""
    previous_snapshot = registry.load_snapshot()

    perf_tracker = None
    if _HAS_PERFORMANCE_TRACKER:
        perf_file = Path.home() / ".claude" / "skills" / "performance_history.json"
        if perf_file.exists():
            try:
                perf_tracker = PerformanceTracker(perf_file)
            except (OSError, KeyError):
                pass

    imp_memory = None
    if _HAS_IMPROVEMENT_MEMORY:
        mem_file = Path.home() / ".claude" / "skills" / "improvement_memory.json"
        if mem_file.exists():
            try:
                imp_memory = ImprovementMemory(mem_file)
            except (OSError, KeyError):
                pass

    return AnalysisContext(
        metrics=metrics,
        previous_snapshot=previous_snapshot if previous_snapshot else None,
        performance_history=perf_tracker,
        improvement_memory=imp_memory,
        code_paths=code_paths or [],
        pr_diff=pr_diff,
        trigger=trigger,
    )


def _snapshot_from_metrics(metrics: dict[str, Any]) -> dict:
    """Extract a serializable snapshot from metrics objects."""
    snapshot: dict[str, dict[str, float]] = {}
    for skill, m in metrics.items():
        snapshot[skill] = {
            "success_rate": getattr(m, "success_rate", 0.0),
            "avg_duration_ms": getattr(m, "avg_duration_ms", 0.0),
        }
    return snapshot


def run_analysis(
    metrics: dict[str, Any],
    weight: str = "lightweight",
    trigger: str = "stop",
    pr_diff: str | None = None,
    code_paths: list[Path] | None = None,
    lenses_dir: Path | None = None,
    state_path: Path | None = None,
) -> list[Finding]:
    """Run the analysis pipeline.

    Args:
        metrics: Dict mapping skill name to metrics object.
        weight: Lens weight filter ("lightweight", "deep", "all").
        trigger: What triggered this analysis.
        pr_diff: Optional PR diff for PR-scoped analysis.
        code_paths: Optional code paths for LLM lenses.
        lenses_dir: Override lenses directory (for testing).
        state_path: Override state file path (for testing).

    Returns:
        List of findings from all lenses.
    """
    registry = InsightRegistry(state_path=state_path)
    context = _build_context(
        metrics, registry, trigger, pr_diff, code_paths
    )

    lenses = discover_lenses(weight=weight, lenses_dir=lenses_dir)
    all_findings: list[Finding] = []

    for lens in lenses:
        try:
            findings = lens["analyze"](context)
            all_findings.extend(findings)
        except Exception as e:
            sys.stderr.write(
                f"[insight_analyzer] Lens {lens['meta']['name']} "
                f"failed: {e}\n"
            )

    # Save current metrics as snapshot for next delta comparison
    registry.save_snapshot(_snapshot_from_metrics(metrics))

    return all_findings
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/alext/claude-night-market && python -m pytest plugins/abstract/tests/scripts/test_insight_analyzer.py -v`
Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/abstract/scripts/insight_analyzer.py \
       plugins/abstract/tests/scripts/test_insight_analyzer.py
git commit -m "feat(abstract): add insight analyzer orchestrator

Discovers lenses, builds AnalysisContext with Hyperagents
data, runs analysis pipeline, saves snapshots for delta
comparison."
```

---

## Task 8: Post Insights to Discussions

New posting script for the "Insights" Discussion category
with typed titles and the four-layer dedup flow.

**Files:**

- Create: `plugins/abstract/scripts/post_insights_to_discussions.py`
- Create: `.github/DISCUSSION_TEMPLATE/insights.yml`
- Test: `plugins/abstract/tests/scripts/test_post_insights.py`

- [ ] **Step 1: Create the Insights discussion template**

```yaml
# .github/DISCUSSION_TEMPLATE/insights.yml
title: "[Insight] "
labels:
  - insight
body:
  - type: dropdown
    id: insight-type
    attributes:
      label: Insight Type
      options:
        - Trend
        - Pattern
        - Bug Alert
        - Optimization
        - Improvement
        - PR Finding
        - Health Check
    validations:
      required: true
  - type: textarea
    id: finding
    attributes:
      label: Finding
      description: What was discovered
    validations:
      required: true
  - type: textarea
    id: evidence
    attributes:
      label: Evidence
      description: Data, metrics, or code references
    validations:
      required: true
  - type: textarea
    id: recommendation
    attributes:
      label: Recommended Action
      description: What should be done about this finding
```

- [ ] **Step 2: Write posting tests**

```python
# plugins/abstract/tests/scripts/test_post_insights.py

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(
    0, str(Path(__file__).parent.parent.parent / "scripts")
)

from insight_types import Finding
from post_insights_to_discussions import (
    format_insight_body,
    format_insight_title,
)


def _make_finding(**overrides):
    defaults = dict(
        type="Trend",
        severity="medium",
        skill="abstract:skill-auditor",
        summary="success rate dropped 92% to 71%",
        evidence="- Previous: 92%\n- Current: 71%",
        recommendation="Investigate error pattern",
        source="delta_lens",
    )
    defaults.update(overrides)
    return Finding(**defaults)


def test_format_title_trend():
    f = _make_finding(type="Trend", skill="x:y", summary="degrading")
    title = format_insight_title(f)
    assert title == "[Trend] x:y: degrading"


def test_format_title_pattern_no_skill():
    f = _make_finding(type="Pattern", skill="", summary="3 skills: timeout")
    title = format_insight_title(f)
    assert title == "[Pattern] 3 skills: timeout"


def test_format_title_truncated():
    f = _make_finding(summary="x" * 200)
    title = format_insight_title(f)
    assert len(title) <= 128


def test_format_body_contains_sections():
    f = _make_finding()
    body = format_insight_body(f)
    assert "### Finding" in body
    assert "### Evidence" in body
    assert "### Recommended Action" in body
    assert "**Severity:**" in body
    assert "delta_lens" in body


def test_format_body_with_related():
    f = _make_finding()
    body = format_insight_body(f, related_url="https://example.com/42")
    assert "Related" in body
    assert "https://example.com/42" in body
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /home/alext/claude-night-market && python -m pytest plugins/abstract/tests/scripts/test_post_insights.py -v`
Expected: FAIL

- [ ] **Step 4: Implement post_insights_to_discussions.py**

```python
# plugins/abstract/scripts/post_insights_to_discussions.py
"""Post insight findings to GitHub Discussions.

Posts to the "Insights" category with typed titles.
Integrates with InsightRegistry for four-layer dedup:
1. Content hash (local)
2. Metrics snapshot diff (via DeltaLens)
3. Staleness expiry (30 days)
4. GitHub semantic search
"""

from __future__ import annotations

import json
import subprocess  # nosec B404
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from insight_registry import InsightRegistry, DedupResult
from insight_types import INSIGHT_TYPES, Finding, finding_hash

# Reuse GraphQL helpers from existing posting script
from post_learnings_to_discussions import (
    detect_target_repo,
    resolve_category_id,
    run_gh_graphql,
    get_repo_node_id,
    PostedRecord,
    create_discussion,
)

MAX_TITLE_LENGTH = 128


def format_insight_title(finding: Finding) -> str:
    """Generate a discussion title from a finding."""
    title = finding.title()
    if len(title) > MAX_TITLE_LENGTH:
        title = title[: MAX_TITLE_LENGTH - 3] + "..."
    return title


def format_insight_body(
    finding: Finding,
    related_url: str | None = None,
) -> str:
    """Format a Discussion post body from a finding."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines: list[str] = []

    lines.append(f"**Severity:** {finding.severity}")
    if finding.skill:
        lines.append(f"**Skill:** {finding.skill}")
    lines.append(f"**Source:** {finding.source}")
    lines.append(f"**Generated:** {today}")
    lines.append("")
    lines.append("### Finding")
    lines.append(finding.summary)
    lines.append("")
    lines.append("### Evidence")
    lines.append(finding.evidence)
    lines.append("")
    lines.append("### Recommended Action")
    lines.append(finding.recommendation)

    if related_url:
        lines.append("")
        lines.append("### Related")
        lines.append(f"- See also: {related_url}")

    lines.append("")
    lines.append("---")
    lines.append("*Auto-generated by Insight Engine*")
    lines.append(
        "*React with \U0001f525 to prioritize. "
        "3+ reactions promoted to Issue.*"
    )

    return "\n".join(lines)


def _fetch_existing_insights(
    owner: str,
    name: str,
    category_slug: str = "insights",
) -> list[dict[str, Any]]:
    """Fetch recent discussions from the Insights category."""
    category_id = resolve_category_id(owner, name, category_slug)
    if not category_id:
        return []

    query = """
    query($owner: String!, $repo: String!, $categoryId: ID!) {
      repository(owner: $owner, name: $repo) {
        discussions(
          first: 20,
          categoryId: $categoryId,
          orderBy: {field: CREATED_AT, direction: DESC}
        ) {
          nodes {
            id number title body url createdAt
          }
        }
      }
    }
    """
    try:
        response = run_gh_graphql(
            query,
            variables={
                "owner": owner,
                "repo": name,
                "categoryId": category_id,
            },
        )
        return (
            response.get("data", {})
            .get("repository", {})
            .get("discussions", {})
            .get("nodes", [])
        )
    except (RuntimeError, KeyError):
        return []


def _add_comment_to_discussion(
    discussion_id: str,
    body: str,
) -> str | None:
    """Add a threaded comment to an existing discussion."""
    query = """
    mutation($discussionId: ID!, $body: String!) {
      addDiscussionComment(input: {
        discussionId: $discussionId,
        body: $body
      }) {
        comment { url }
      }
    }
    """
    try:
        response = run_gh_graphql(
            query,
            variables={"discussionId": discussion_id, "body": body},
        )
        return str(
            response["data"]["addDiscussionComment"]["comment"]["url"]
        )
    except (RuntimeError, KeyError):
        return None


def post_findings(
    findings: list[Finding],
    state_path: Path | None = None,
) -> list[str]:
    """Post findings to GitHub Discussions with full dedup.

    Returns:
        List of discussion URLs (posted or linked).
    """
    if not findings:
        return []

    repo = detect_target_repo()
    if repo is None:
        print("Could not detect target repository.", file=sys.stderr)
        return []
    owner, name = repo

    # Resolve "insights" category (falls back to "learnings")
    category_id = resolve_category_id(owner, name, "insights")
    fallback_slug = None
    if category_id is None:
        category_id = resolve_category_id(owner, name, "learnings")
        fallback_slug = "learnings"
    if category_id is None:
        print("No insights/learnings category found.", file=sys.stderr)
        return []

    registry = InsightRegistry(state_path=state_path)
    posted_record = PostedRecord.load()
    repo_id = get_repo_node_id(posted_record, owner, name)

    # Fetch existing discussions for semantic dedup
    slug = fallback_slug or "insights"
    existing = _fetch_existing_insights(owner, name, slug)

    urls: list[str] = []

    for finding in findings:
        # Layer 1-3: Local content hash check
        local_result = registry.check_local(finding)
        if local_result == "skip":
            continue

        # Layer 4: GitHub semantic dedup
        github_result = registry.check_github(finding, existing)

        title = format_insight_title(finding)

        if github_result.action == "link":
            # Add comment to existing discussion
            body = format_insight_body(finding)
            comment_url = _add_comment_to_discussion(
                github_result.target_id, body
            )
            if comment_url:
                registry.record_posted(finding, github_result.target_url)
                urls.append(comment_url)
                print(
                    f"Linked to existing: {github_result.reason}",
                    file=sys.stderr,
                )

        elif github_result.action == "update":
            # Create new with reference
            body = format_insight_body(
                finding, related_url=github_result.target_url
            )
            url = create_discussion(repo_id, category_id, title, body)
            registry.record_posted(finding, url)
            urls.append(url)
            print(f"Posted with reference: {url}", file=sys.stderr)

        else:
            # Create standalone
            body = format_insight_body(finding)
            url = create_discussion(repo_id, category_id, title, body)
            registry.record_posted(finding, url)
            urls.append(url)
            print(f"Posted new insight: {url}", file=sys.stderr)

    return urls
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/alext/claude-night-market && python -m pytest plugins/abstract/tests/scripts/test_post_insights.py -v`
Expected: All 5 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add plugins/abstract/scripts/post_insights_to_discussions.py \
       plugins/abstract/tests/scripts/test_post_insights.py \
       .github/DISCUSSION_TEMPLATE/insights.yml
git commit -m "feat(abstract): add insight posting with four-layer dedup

Posts findings to 'Insights' Discussion category with typed
titles. Four-layer dedup: content hash, snapshot diff,
staleness expiry, GitHub semantic search. Falls back to
'Learnings' category if 'Insights' not yet created."
```

---

## Task 9: Enhanced Stop Hook

Wire the insight analyzer into the existing Stop hook
so lightweight lenses run automatically at session end.

**Files:**

- Modify: `plugins/abstract/hooks/post_learnings_stop.py`
- Test: manual verification (hook requires Claude session)

- [ ] **Step 1: Read the existing Stop hook**

Review `plugins/abstract/hooks/post_learnings_stop.py`
(already read in context, 92 lines).

- [ ] **Step 2: Add insight analysis to the Stop hook**

Add the insight analysis chain after the existing learnings
posting. In `plugins/abstract/hooks/post_learnings_stop.py`,
add a new import and function call:

```python
# Add to imports section (after existing imports):
try:
    from aggregate_skill_logs import aggregate_logs
    from insight_analyzer import run_analysis
    from post_insights_to_discussions import post_findings

    _HAS_INSIGHT_ENGINE = True
except ImportError:
    _HAS_INSIGHT_ENGINE = False
```

Then add to `main()`, after the existing `_post_learnings()` call:

```python
    # Run lightweight insight lenses and post findings
    if _HAS_INSIGHT_ENGINE:
        try:
            result = aggregate_logs(days_back=30)
            findings = run_analysis(
                metrics=result.metrics_by_skill,
                weight="lightweight",
                trigger="stop",
            )
            if findings:
                urls = post_findings(findings)
                if urls:
                    print(
                        f"[post_learnings_stop] Posted {len(urls)} insights",
                        file=sys.stderr,
                    )
        except Exception:
            print(
                f"[post_learnings_stop] insight-engine: "
                f"{traceback.format_exc()}",
                file=sys.stderr,
            )
```

- [ ] **Step 3: Commit**

```bash
git add plugins/abstract/hooks/post_learnings_stop.py
git commit -m "feat(abstract): wire insight engine into Stop hook

Runs lightweight lenses at session end and posts findings
to Insights category. Graceful failure preserves existing
learnings posting behavior."
```

---

## Task 10: Enhanced Fetch Hook

Update `fetch-recent-discussions.sh` to query both
"Decisions" and "Insights" categories and inject both
into session context.

**Files:**

- Modify: `plugins/leyline/hooks/fetch-recent-discussions.sh`
- Test: `plugins/leyline/tests/unit/hooks/test_fetch_recent_discussions.py`

- [ ] **Step 1: Modify the fetch hook to also query Insights**

After the existing "decisions" category resolution block
(line 118-136), add a parallel resolution for "insights":

```bash
# Find the "insights" category ID (in addition to decisions)
insights_category_id=$(echo "$category_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('errors'):
        sys.exit(0)
    cats = data.get('data', {}).get('repository', {}).get('discussionCategories', {}).get('nodes', [])
    for c in cats:
        if c.get('slug', '').lower() == 'insights':
            print(c['id'])
            break
except Exception as exc:
    print(f'JSON parse error: {exc}', file=sys.stderr)
" || echo "")
```

- [ ] **Step 2: Add Insights query after the Decisions query**

After the existing discussions fetch (line 140-157),
add a second query if insights_category_id is set:

```bash
insights_summary=""
if [ -n "$insights_category_id" ]; then
    insights_response=$(gh api graphql -f query='
query($owner: String!, $repo: String!, $categoryId: ID!) {
  repository(owner: $owner, name: $repo) {
    discussions(first: 10, categoryId: $categoryId, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        number
        title
        createdAt
        body
      }
    }
  }
}' -f owner="$owner" -f repo="$repo" -f categoryId="$insights_category_id" 2>/dev/null || echo "")

    if [ -n "$insights_response" ]; then
        insights_summary=$(echo "$insights_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('errors'):
        sys.exit(0)
    nodes = data.get('data', {}).get('repository', {}).get('discussions', {}).get('nodes', [])
    if not nodes:
        sys.exit(0)
    lines = ['Recent Insights (from GitHub Discussions):']
    for d in nodes:
        num = d.get('number', '?')
        title = d.get('title', 'Untitled')
        date = d.get('createdAt', '')[:10]
        body = d.get('body', '')
        snippet = body.replace('\n', ' ').replace('\r', '')[:100].strip()
        if len(body) > 100:
            snippet += '...'
        lines.append(f'  #{num} {title} ({date}) -- {snippet}')
    print('\n'.join(lines))
except Exception as exc:
    print(f'Format error: {exc}', file=sys.stderr)
" || echo "")
    fi
fi
```

- [ ] **Step 3: Combine both summaries in the output**

Replace the final output section to combine both:

```bash
# Combine decisions + insights summaries
combined_summary=""
if [ -n "$summary" ]; then
    combined_summary="$summary"
fi
if [ -n "$insights_summary" ]; then
    if [ -n "$combined_summary" ]; then
        combined_summary="${combined_summary}
${insights_summary}"
    else
        combined_summary="$insights_summary"
    fi
fi

if [ -z "$combined_summary" ]; then
    _emit_empty
fi

escaped_summary=$(echo "$combined_summary" | python3 -c "
import sys, json
text = sys.stdin.read()
print(json.dumps(text)[1:-1])
" || echo "")

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "${escaped_summary}"
  }
}
EOF
```

- [ ] **Step 4: Update the fetch hook test**

Add test cases for the Insights category in
`plugins/leyline/tests/unit/hooks/test_fetch_recent_discussions.py`.
The existing test mocks GraphQL responses; add a mock
that returns an "insights" category alongside "decisions"
and verify both appear in the output.

- [ ] **Step 5: Commit**

```bash
git add plugins/leyline/hooks/fetch-recent-discussions.sh \
       plugins/leyline/tests/unit/hooks/test_fetch_recent_discussions.py
git commit -m "feat(leyline): fetch Insights alongside Decisions at session start

The SessionStart hook now queries both 'Decisions' and
'Insights' categories and injects both summaries into
session context. Insights are surfaced during PR reviews."
```

---

## Task 11: Insight Engine Agent

Create the LLM-augmented agent for deep analysis that
runs on a scheduled cadence.

**Files:**

- Create: `plugins/abstract/agents/insight-engine.md`

- [ ] **Step 1: Write the agent definition**

```markdown
# plugins/abstract/agents/insight-engine.md
---
name: insight-engine
description: >
  Deep analysis agent that reads codebase patterns,
  execution logs, and performance data to generate
  proactive insights about bugs, optimizations, and
  improvements. Posts findings to GitHub Discussions.
model: sonnet
tools:
  - Read
  - Bash
  - Glob
  - Grep
  - Write
---

# Insight Engine - Deep Analysis Agent

You are the Insight Engine deep analysis agent. Your job
is to analyze the codebase and generate proactive insights
that help improve the plugin marketplace.

## Your Inputs

You receive a `mode` parameter:
- `full`: Analyze the entire codebase
- `pr:<branch>`: Analyze changes in a specific PR branch
- `skill:<name>`: Deep-dive a specific skill

## Analysis Process

### Step 1: Load Context

Read these files for baseline understanding:
- `~/.claude/skills/LEARNINGS.md` (current metrics)
- `~/.claude/skills/improvement_memory.json` (what worked before)
- `~/.claude/skills/performance_history.json` (trends)

### Step 2: Run Built-in Lightweight Lenses

```bash
cd /home/alext/claude-night-market
python3 -c "
import sys
sys.path.insert(0, 'plugins/abstract/scripts')
from aggregate_skill_logs import aggregate_logs
from insight_analyzer import run_analysis
result = aggregate_logs(days_back=30)
findings = run_analysis(
    metrics=result.metrics_by_skill,
    weight='all',
    trigger='schedule',
)
for f in findings:
    print(f'[{f.type}] {f.skill}: {f.summary}')
"
```

### Step 3: Deep Code Analysis (BugLens)

For each skill flagged in LEARNINGS.md with high failure
rates, read the skill file and its hooks. Look for:

- **Concurrency issues**: Shared state without locking
- **Error handling gaps**: Bare except, swallowed errors
- **Edge cases**: Missing None checks, empty collections
- **Resource leaks**: Unclosed files, dangling processes

Report each finding as a `[Bug Alert]` type.

### Step 4: Optimization Analysis (OptimizationLens)

Read scripts with slow execution times. Look for:

- Sequential I/O that could be batched
- Repeated file reads that could be cached
- O(n^2) patterns in loops
- Unnecessary subprocess calls

Report each as `[Optimization]` type.

### Step 5: Improvement Synthesis (ImprovementLens)

Cross-reference friction points from LEARNINGS.md with
improvement_memory.json. For each friction point that
appears 3+ times:

- Propose a concrete fix
- Reference effective strategies from improvement_memory
- Report as `[Improvement]` type

### Step 6: Post Findings

```bash
cd /home/alext/claude-night-market
python3 -c "
import sys, json
sys.path.insert(0, 'plugins/abstract/scripts')
from insight_types import Finding
from post_insights_to_discussions import post_findings

# Read findings from stdin (JSON array)
findings_data = json.load(sys.stdin)
findings = [Finding(**f) for f in findings_data]
urls = post_findings(findings)
for url in urls:
    print(url)
"
```

Write your findings as a JSON array and pipe them through
the posting script. The script handles all dedup layers.

### Output

Report what you found and posted. Include:
- Number of findings by type
- URLs of posted discussions
- Summary of key insights
```

- [ ] **Step 2: Commit**

```bash
git add plugins/abstract/agents/insight-engine.md
git commit -m "feat(abstract): add insight-engine deep analysis agent

LLM-augmented agent for scheduled deep analysis. Runs
BugLens, OptimizationLens, and ImprovementLens on the
codebase and posts findings to Discussions."
```

---

## Task 12: PR-Review and Code-Refinement Integration

Add insight generation modules to existing skills.

**Files:**

- Create: `plugins/sanctum/skills/pr-review/modules/insight-generation.md`
- Create: `plugins/pensive/skills/code-refinement/modules/insight-generation.md`

- [ ] **Step 1: Create PR-review insight module**

```markdown
# plugins/sanctum/skills/pr-review/modules/insight-generation.md
---
name: insight-generation
description: Post PR-scoped insights to GitHub Discussions
---

## PR Insight Generation

After completing the PR review analysis, generate insights
from the review findings and post them to Discussions.

### When to Run

Run this module AFTER the main review is complete and
findings have been documented. Only generate insights for
findings with severity "high" or "medium".

### Process

1. Collect review findings from the current PR analysis
2. For each high/medium finding, create a Finding object:

```bash
cd /home/alext/claude-night-market
python3 -c "
import sys, json
sys.path.insert(0, 'plugins/abstract/scripts')
from insight_types import Finding
from post_insights_to_discussions import post_findings

findings = [
    Finding(
        type='PR Finding',
        severity='$SEVERITY',
        skill='',
        summary='PR #$PR_NUMBER: $FINDING_SUMMARY',
        evidence='$EVIDENCE',
        recommendation='$RECOMMENDATION',
        source='pr-review',
        related_files=$CHANGED_FILES,
    )
]
urls = post_findings(findings)
for url in urls:
    print(f'Posted: {url}')
"
```

3. The posting script handles all dedup automatically
4. Report posted URLs in the review summary
```

- [ ] **Step 2: Create code-refinement insight module**

```markdown
# plugins/pensive/skills/code-refinement/modules/insight-generation.md
---
name: insight-generation
description: Post codebase-wide insights from refinement analysis
---

## Code Refinement Insight Generation

After completing the code refinement analysis, post
findings as insights to GitHub Discussions for tracking.

### When to Run

Run this module AFTER the refinement analysis is complete.
Post findings of type Optimization, Bug Alert, or
Improvement.

### Process

1. Collect refinement findings from the analysis
2. Map refinement categories to insight types:
   - Duplication -> [Optimization]
   - Algorithm issues -> [Optimization]
   - Clean code violations -> [Improvement]
   - Error handling gaps -> [Bug Alert]
   - Architecture misfit -> [Improvement]

3. Post via the insight engine:

```bash
cd /home/alext/claude-night-market
python3 -c "
import sys, json
sys.path.insert(0, 'plugins/abstract/scripts')
from insight_types import Finding
from post_insights_to_discussions import post_findings

findings = [
    Finding(
        type='$INSIGHT_TYPE',
        severity='$SEVERITY',
        skill='$SKILL_OR_FILE',
        summary='$SUMMARY',
        evidence='$EVIDENCE',
        recommendation='$RECOMMENDATION',
        source='code-refinement',
    )
]
urls = post_findings(findings)
for url in urls:
    print(f'Posted: {url}')
"
```

4. The posting script handles all dedup automatically
```

- [ ] **Step 3: Commit**

```bash
git add plugins/sanctum/skills/pr-review/modules/insight-generation.md \
       plugins/pensive/skills/code-refinement/modules/insight-generation.md
git commit -m "feat(sanctum,pensive): add insight generation modules

PR-review posts [PR Finding] insights scoped to PR changes.
Code-refinement posts [Optimization], [Bug Alert], and
[Improvement] insights from codebase-wide analysis."
```

---

## Task 13: Add Content-Hash Dedup Fallback to Existing Learnings Poster

Prevent the existing `post_learnings_to_discussions.py`
from posting identical content day after day while the
new system ramps up.

**Files:**

- Modify: `plugins/abstract/scripts/post_learnings_to_discussions.py`
- Modify: `plugins/abstract/tests/scripts/test_post_learnings_to_discussions.py`

- [ ] **Step 1: Write a test for content-hash dedup**

Add to `test_post_learnings_to_discussions.py`:

```python
def test_content_hash_prevents_identical_repost():
    """Same content on different days should not repost."""
    summary1 = LearningSummary(
        skills_analyzed=1,
        total_executions=20,
        high_impact_issues=[
            {"skill": "x:y", "severity": "high", "metric": "40%", "type": "failure"},
        ],
    )
    summary2 = LearningSummary(
        skills_analyzed=1,
        total_executions=20,
        high_impact_issues=[
            {"skill": "x:y", "severity": "high", "metric": "40%", "type": "failure"},
        ],
    )
    body1 = format_discussion_body(summary1)
    body2 = format_discussion_body(summary2)

    import hashlib
    hash1 = hashlib.sha256(body1.encode()).hexdigest()[:12]
    hash2 = hashlib.sha256(body2.encode()).hexdigest()[:12]
    assert hash1 == hash2, "Identical content should have same hash"
```

- [ ] **Step 2: Add content hash to the posting flow**

In `post_learnings_to_discussions.py`, modify `_post_if_new`
to also check a content hash:

```python
def _post_if_new(
    summary: LearningSummary,
    owner: str,
    name: str,
    category_id: str,
) -> str | None:
    """Post a discussion if not already posted today AND content is new."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    title = f"[Learning] {today}"

    record = PostedRecord.load()
    if record.is_posted(title):
        print(f"Already posted for today ({title}).", file=sys.stderr)
        return record.posted[title]

    existing_url = check_existing_discussion(title, owner, name)
    if existing_url:
        print(f"Discussion already exists: {existing_url}.", file=sys.stderr)
        record.posted[title] = existing_url
        record.save()
        return existing_url

    # Content-hash dedup: skip if body is identical to recent post
    body = format_discussion_body(summary)
    import hashlib
    content_hash = hashlib.sha256(body.encode()).hexdigest()[:12]

    if record.posted.get("_last_content_hash") == content_hash:
        print(
            "Content identical to last post. Skipping.",
            file=sys.stderr,
        )
        return None

    repo_id = get_repo_node_id(record, owner, name)
    url = create_discussion(repo_id, category_id, title, body)

    record.posted[title] = url
    record.posted["_last_content_hash"] = content_hash
    record.save()

    print(f"Posted learning summary: {url}")
    return url
```

- [ ] **Step 3: Run tests**

Run: `cd /home/alext/claude-night-market && python -m pytest plugins/abstract/tests/scripts/test_post_learnings_to_discussions.py -v`
Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
git add plugins/abstract/scripts/post_learnings_to_discussions.py \
       plugins/abstract/tests/scripts/test_post_learnings_to_discussions.py
git commit -m "fix(abstract): add content-hash dedup to learnings poster

Prevents posting identical content on consecutive days.
If the body hash matches the last post, the discussion
is skipped. Stops the 'same learning every day' problem."
```

---

## Task 14: Run Full Test Suite and Verify

- [ ] **Step 1: Run all insight engine tests**

```bash
cd /home/alext/claude-night-market
python -m pytest plugins/abstract/tests/scripts/test_insight_types.py \
                 plugins/abstract/tests/scripts/test_insight_registry.py \
                 plugins/abstract/tests/scripts/test_insight_analyzer.py \
                 plugins/abstract/tests/scripts/test_post_insights.py \
                 plugins/abstract/tests/scripts/lenses/ \
                 -v --tb=short
```

Expected: All tests PASS.

- [ ] **Step 2: Run existing learnings tests (no regressions)**

```bash
cd /home/alext/claude-night-market
python -m pytest plugins/abstract/tests/scripts/test_post_learnings_to_discussions.py \
                 plugins/abstract/tests/scripts/test_auto_promote_learnings.py \
                 -v --tb=short
```

Expected: All tests PASS.

- [ ] **Step 3: Run plugin type check**

```bash
cd /home/alext/claude-night-market
python -m mypy plugins/abstract/scripts/insight_types.py \
              plugins/abstract/scripts/insight_registry.py \
              plugins/abstract/scripts/insight_analyzer.py \
              --ignore-missing-imports
```

Expected: No errors.

- [ ] **Step 4: Verify lens discovery works end-to-end**

```bash
cd /home/alext/claude-night-market
python3 -c "
import sys
sys.path.insert(0, 'plugins/abstract/scripts')
from lenses import discover_lenses
from pathlib import Path
lenses_dir = Path('plugins/abstract/scripts/lenses')
lightweight = discover_lenses(weight='lightweight', lenses_dir=lenses_dir)
print(f'Discovered {len(lightweight)} lightweight lenses:')
for l in lightweight:
    print(f'  - {l[\"meta\"][\"name\"]}: {l[\"meta\"][\"description\"]}')
"
```

Expected: Lists 4 lenses (delta, trend, pattern, health).
