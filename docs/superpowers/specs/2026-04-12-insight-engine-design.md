# Insight Engine Design

Transform the learnings system from a repetitive metrics reporter
into a proactive insight engine that generates diverse findings
and posts them to GitHub Discussions for iterative improvement.

## Problem Statement

The current learnings system posts identical content daily.
Evidence from GitHub Discussions #336 through #400: every post
reports `abstract:skill-auditor` at 40% success rate with
42-48 failures. Three root causes:

1. **Logging gap**: Only 1 of 200+ skills has execution logs.
   The `skill_execution_logger.py` PostToolUse hook either
   fails silently for most skills or other skills don't flow
   through the Skill tool path.
2. **No content dedup**: Date-based `[Learning] YYYY-MM-DD`
   prevents same-day duplicates but not cross-day repetition
   of identical observations.
3. **Single-lens analysis**: `aggregate_skill_logs.py` only
   reports failure rates, slow execution, and low ratings.
   No trend detection, no cross-skill patterns, no delta
   comparison, no proactive insight generation.

Additionally, `fetch-recent-discussions.sh` only queries
the "Decisions" category. Learnings and insights never
surface back into sessions or PR reviews.

## Architecture

```
TRIGGERS
  Stop Hook (lightweight)  |  Schedule (deep)  |  /pr-review  |  /code-refinement
       |                        |                     |               |
       v                        v                     v               v
  insight_analyzer.py      insight-engine agent   pr-review module  code-refinement module
  (script, fast)           (LLM, expensive)       (PR-scoped)       (codebase-wide)
       |                        |                     |               |
       +------------------------+---------------------+---------------+
                                |
                                v
                       InsightRegistry (Python)
                       - Accepts Finding objects from any source
                       - Content-hash dedup (local)
                       - GitHub semantic dedup (remote)
                       - Staleness expiry (30 days)
                                |
                                v
                  post_insights_to_discussions.py
                  - Posts to "Insights" category
                  - Typed titles: [Trend], [Bug Alert], etc.
                  - Links/references related discussions
                                |
                                v
                  fetch-recent-discussions.sh (enhanced)
                  - Queries "Decisions" AND "Insights"
                  - Surfaces findings in session context
```

## Insight Types

Seven insight types, each with a title prefix:

| Type | Prefix | Source | Example |
|------|--------|--------|---------|
| Trend | `[Trend]` | Script | "skill-improver degraded 92% to 71% over 2 weeks" |
| Pattern | `[Pattern]` | Script | "3 skills share GraphQL timeout errors" |
| Bug Alert | `[Bug Alert]` | Agent | "race condition in post_learnings_stop.py" |
| Optimization | `[Optimization]` | Agent | "sequential JSONL reads could batch by date" |
| Improvement | `[Improvement]` | Agent | "skill-authoring lacks module reference examples" |
| PR Finding | `[PR Finding]` | pr-review | "PR #47 introduces unbounded list growth" |
| Health Check | `[Health Check]` | Script | "12 skills have 0 executions in 30 days" |

## Analyzer Lenses

### Built-in Lightweight Lenses (hook-safe)

1. **TrendLens**: Compares current metrics to previous snapshot.
   Detects degradation/improvement over 7d, 14d, 30d windows.
   Reports skills crossing threshold boundaries and recoveries.
2. **PatternLens**: Groups errors and friction points across
   skills. Finds shared failure modes via term overlap.
3. **HealthLens**: Identifies unused skills (0 executions in
   30 days), orphaned hooks, configuration drift between
   plugin.json and disk contents.
4. **DeltaLens**: Compares current LEARNINGS.md to the
   last-posted snapshot. Only surfaces new observations.
   Produces nothing if metrics are stable.

### LLM-Augmented Lenses (agent-only)

5. **BugLens**: Reads flagged skill/script code and looks for
   concurrency issues, error handling gaps, edge cases.
6. **OptimizationLens**: Identifies performance bottlenecks,
   unnecessary I/O, algorithmic improvements.
7. **ImprovementLens**: Synthesizes friction points from
   improvement_memory into concrete proposals.

### Extensibility Protocol

Custom analyzers live in `plugins/abstract/scripts/lenses/`
and auto-discover via convention:

```python
# plugins/abstract/scripts/lenses/my_custom_lens.py

LENS_META = {
    "name": "my-custom-lens",
    "insight_types": ["Custom"],
    "weight": "lightweight",  # or "deep"
    "description": "Detects XYZ patterns",
}

def analyze(context: AnalysisContext) -> list[Finding]:
    """Return zero or more findings."""
    ...
```

The `insight_analyzer.py` discovers lenses at startup by
scanning for `.py` files with `LENS_META` and `analyze()`.
The Stop hook runs only `weight="lightweight"` lenses.
The agent runs all lenses. New `.py` files in `lenses/`
are picked up on next run with no registration needed.

## Data Structures

### Finding

```python
@dataclass
class Finding:
    type: str           # "Trend", "Bug Alert", etc.
    severity: str       # "high", "medium", "low", "info"
    skill: str          # affected skill or "" for cross-cutting
    summary: str        # one-line, used in title and hash
    evidence: str       # markdown body with data/metrics
    recommendation: str # what to do about it
    source: str         # which lens/trigger produced this
    related_files: list[str] = field(default_factory=list)
```

### AnalysisContext

```python
@dataclass
class AnalysisContext:
    metrics: dict[str, SkillLogSummary]
    previous_snapshot: dict | None
    performance_history: PerformanceTracker | None
    improvement_memory: ImprovementMemory | None
    code_paths: list[Path]  # for LLM lenses
    pr_diff: str | None     # for PR-scoped analysis
    trigger: str            # "stop", "schedule", "pr-review", "code-refinement"
```

## Deduplication (Four Layers)

### Layer 1: Content Hashing

Each finding gets a deterministic hash from key fields:

```python
def finding_hash(finding: Finding) -> str:
    key = f"{finding.type}:{finding.skill}:{finding.summary}"
    return hashlib.sha256(key.encode()).hexdigest()[:12]
```

Tracked in `~/.claude/skills/discussions/insights_posted.json`.
A finding with a matching hash is never reposted.

### Layer 2: Metrics Snapshot Diffing

The DeltaLens stores a snapshot of last-posted metrics
in `insights_posted.json` under `last_snapshot`. On next
run it compares and only produces findings for:

- New skills appearing (not in previous snapshot)
- Skills crossing threshold boundaries
- Skills recovering (positive finding)
- Metric changes exceeding significance (>10% success
  rate shift, >2s duration shift)

Stable metrics produce nothing.

### Layer 3: Staleness Expiry

Finding hashes expire after 30 days. If a problem persists
beyond 30 days, the system re-posts with updated data.
Prevents permanent suppression of persistent problems
while avoiding daily repetition.

### Layer 4: GitHub Semantic Dedup

Before posting, query existing Insights discussions and
compare using lightweight term-based similarity:

| Similarity | Action |
|-----------|--------|
| >85% | Link: add threaded comment to existing discussion |
| 60-85% | Create with "Related to #N" reference |
| <60% | Create standalone discussion |

Similarity uses Jaccard overlap on normalized key terms
(skill name, metric type, error strings, number ranges).
No LLM call needed for this step.

## Discussion Format

### New Category

`.github/DISCUSSION_TEMPLATE/insights.yml` defines the
"Insights" category as Open Discussion format with
structured fields: insight type, finding, evidence,
recommended action.

### Posted Discussion Body

```markdown
## [Trend] skill-improver success rate degrading

**Severity:** medium
**Skill:** abstract:skill-improver
**Source:** metrics-delta (Stop hook)
**Generated:** 2026-04-12

### Finding
Success rate dropped from 92.3% to 71.1% over 14 days.

### Evidence
- 2026-03-29: 92.3% (26/28 success)
- 2026-04-12: 71.1% (27/38 success)
- Common error: "KeyError: 'skill_ref'"

### Recommended Action
Investigate error pattern in skill-improver agent.

### Related
- Linked to #34 (previous observation)

---
*Auto-generated by Insight Engine (Phase 6a+)*
*React with fire emoji to prioritize. 3+ reactions promoted to Issue.*
```

### Title Patterns

| Type | Format |
|------|--------|
| Trend | `[Trend] {skill}: {direction} {metric}` |
| Pattern | `[Pattern] {N} skills: {shared issue}` |
| Bug Alert | `[Bug Alert] {file}: {issue}` |
| Optimization | `[Optimization] {skill}: {opportunity}` |
| Improvement | `[Improvement] {skill}: {proposal}` |
| PR Finding | `[PR Finding] PR #{n}: {issue}` |
| Health Check | `[Health Check] {summary}` |

## Fetch Hook Enhancement

`fetch-recent-discussions.sh` updated to query both
"Decisions" and "Insights" categories:

```
Recent Decisions (from GitHub Discussions):
  #271 [War Room] Wire Publishing... (2026-03-05) -- ...

Recent Insights (from GitHub Discussions):
  #302 [Bug Alert] post_learnings_stop.py: shared state (2026-04-11) -- ...
  #298 [Trend] skill-improver: degrading success rate (2026-04-10) -- ...
```

Every session, including PR reviews, sees the latest
insights in context automatically.

## Observation Sources

Beyond execution logs, the insight engine draws from:

| Source | Data | Access |
|--------|------|--------|
| Execution logs | Skill success/failure/duration | `~/.claude/skills/logs/` |
| Git history | Change frequency to skills/hooks | `git log plugins/` |
| Performance history | Cross-generation trends | `performance_history.json` |
| Improvement memory | Effective/failed strategies | `improvement_memory.json` |
| Plugin structure | Registered vs actual components | `plugin.json` files |
| Test results | Failing tests by plugin | pytest output |
| Codebase patterns | Quality, duplication, complexity | LLM analysis |
| PR diffs | What's changing in this PR | `git diff` |

## Integration Points

### Stop Hook (lightweight)

Enhanced `post_learnings_stop.py` runs lightweight lenses
after the existing learnings posting. Posts to "Insights"
category. Must complete within the 10s timeout budget.

### Scheduled Agent (deep)

New `insight-engine` agent runs on a configurable cadence
(default: daily). Executes all lenses including
LLM-augmented ones. Can take minutes. Posts deep findings.
Cadence is set in `~/.claude/skills/discussions/config.json`
via `insight_schedule: "daily"` (or `"weekly"`).

### /pr-review Module

New `insight-generation.md` module in
`plugins/sanctum/skills/pr-review/modules/`.
Runs after review analysis. Feeds PR-scoped findings
into InsightRegistry. Posts `[PR Finding]` discussions.

### /code-refinement Module

New `insight-generation.md` module in
`plugins/pensive/skills/code-refinement/modules/`.
Runs after refinement analysis. Feeds codebase-wide
findings. Posts `[Optimization]`, `[Bug Alert]`,
`[Improvement]` discussions.

## File Map

### New Files

| File | Purpose |
|------|---------|
| `plugins/abstract/scripts/insight_analyzer.py` | Core: loads lenses, runs analysis, returns findings |
| `plugins/abstract/scripts/insight_registry.py` | Dedup: content hashing, GitHub semantic search, post decisions |
| `plugins/abstract/scripts/post_insights_to_discussions.py` | Posts findings to "Insights" category |
| `plugins/abstract/scripts/lenses/__init__.py` | Lens auto-discovery |
| `plugins/abstract/scripts/lenses/trend_lens.py` | Metrics delta over time windows |
| `plugins/abstract/scripts/lenses/pattern_lens.py` | Cross-skill error/friction grouping |
| `plugins/abstract/scripts/lenses/health_lens.py` | Unused skills, orphaned hooks, drift |
| `plugins/abstract/scripts/lenses/delta_lens.py` | What changed since last post |
| `plugins/abstract/agents/insight-engine.md` | LLM-augmented deep analysis agent |
| `.github/DISCUSSION_TEMPLATE/insights.yml` | "Insights" category template |
| `plugins/sanctum/skills/pr-review/modules/insight-generation.md` | PR-scoped insight posting |
| `plugins/pensive/skills/code-refinement/modules/insight-generation.md` | Codebase-wide insight posting |

### Modified Files

| File | Change |
|------|--------|
| `plugins/abstract/hooks/post_learnings_stop.py` | Run lightweight lenses, post to Insights |
| `plugins/leyline/hooks/fetch-recent-discussions.sh` | Query "Insights" alongside "Decisions" |
| `plugins/abstract/hooks/skill_execution_logger.py` | Diagnose and fix logging gap |
| `plugins/abstract/scripts/post_learnings_to_discussions.py` | Add content-hash dedup fallback |

### Test Files

| File | Coverage |
|------|----------|
| `plugins/abstract/tests/scripts/test_insight_analyzer.py` | Analyzer + lens discovery |
| `plugins/abstract/tests/scripts/test_insight_registry.py` | Dedup logic (4 layers) |
| `plugins/abstract/tests/scripts/test_post_insights.py` | Posting flow |
| `plugins/abstract/tests/scripts/lenses/test_trend_lens.py` | Trend detection |
| `plugins/abstract/tests/scripts/lenses/test_delta_lens.py` | Delta comparison |

## Implementation Phases

| Phase | Scope | Rationale |
|-------|-------|-----------|
| 0 | Fix skill_execution_logger, diagnose logging gap | Without data, everything else is useless |
| 1 | Finding dataclass, InsightRegistry, content-hash dedup | Core infrastructure |
| 2 | Built-in lightweight lenses (Trend, Pattern, Health, Delta) | Diverse findings from existing data |
| 3 | post_insights_to_discussions.py + Insights category template | Gets findings into GitHub |
| 4 | Enhanced Stop hook + fetch hook | Automated posting and retrieval |
| 5 | insight-engine agent (LLM lenses) | Deep analysis capability |
| 6 | PR-review and code-refinement integration modules | Trigger from existing workflows |
| 7 | Lens auto-discovery and extensibility | Open for custom analyzers |
