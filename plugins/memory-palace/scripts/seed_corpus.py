#!/usr/bin/env python3
"""Seed the Memory Palace knowledge corpus with curated entries and index metadata.

This script generates markdown knowledge entries plus keyword/query indexes so the
cache interceptor has a sufficiently rich base (≥50 entries). It is idempotent:
running it again updates existing seed files in place without touching manual entries.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import textwrap
from pathlib import Path
from typing import Any

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = PLUGIN_ROOT / "docs" / "knowledge-corpus"
INDEX_DIR = PLUGIN_ROOT / "data" / "indexes"
DEFAULT_CACHE_CATALOG = CORPUS_DIR / "cache_intercept_catalog.yaml"


@dataclasses.dataclass
class Variation:
    slug: str
    title: str
    language: str
    focus: str
    keywords: list[str]
    summary: str
    playbook_steps: list[str]


@dataclasses.dataclass
class Topic:
    slug: str
    title: str
    palace: str
    district: str
    tags: list[str]
    base_keywords: list[str]
    variations: list[Variation]


TODAY = dt.datetime.now(dt.timezone.utc).date()


def _topics() -> list[Topic]:
    """Define the base topic catalogue used for seeding."""

    def variation(
        slug: str,
        title: str,
        language: str,
        focus: str,
        keywords: list[str],
        summary: str,
        steps: list[str],
    ) -> Variation:
        return Variation(slug, title, language, focus, keywords, summary, steps)

    return [
        Topic(
            slug="structured-concurrency",
            title="Structured Concurrency",
            palace="Async Systems",
            district="Execution Safety",
            tags=["async", "structured-concurrency", "reliability"],
            base_keywords=["structured", "concurrency", "scoped", "async", "lifecycle"],
            variations=[
                variation(
                    "task-groups",
                    "Task Group Patterns",
                    "Python",
                    "TaskGroup orchestration for API workers",
                    ["taskgroup", "context", "python", "api"],
                    "Use Python's TaskGroup to keep concurrent child tasks scoped to the lifetime of a request handler.",
                    [
                        "Create a TaskGroup per inbound request context.",
                        "Spawn child tasks for background I/O and await group completion.",
                        "Propagate cancellations when the handler scope exits.",
                    ],
                ),
                variation(
                    "cancellation-graphs",
                    "Cancellation Graphs",
                    "Go",
                    "propagating cancellations across goroutine trees",
                    ["context", "goroutine", "cancellation", "go"],
                    "Attach child contexts for each spawned goroutine so cancellation flows downward deterministically.",
                    [
                        "Derive child contexts with timeout budgets per subsystem.",
                        "Log cancellation reasons at the parent before bubbling up errors.",
                        "Use errgroup.Group to aggregate failures and join goroutines safely.",
                    ],
                ),
                variation(
                    "service-boundaries",
                    "Service Boundaries",
                    "Kotlin",
                    "structuring coroutines across microservice boundaries",
                    ["kotlin", "coroutines", "supervisorjob"],
                    "Leverage SupervisorJob to isolate failures inside service-specific coroutine scopes.",
                    [
                        "Define a SupervisorJob per inbound transport session.",
                        "Launch child coroutines for downstream calls and instrumentation.",
                        "Convert uncaught exceptions into structured telemetry.",
                    ],
                ),
                variation(
                    "load-shedding",
                    "Load Shedding",
                    "Rust",
                    "structured concurrency for overload protection",
                    ["rust", "tokio", "budget", "load-shed"],
                    "Integrate budget-aware cancellation tokens so excess work is dropped before saturating executors.",
                    [
                        "Attach a Budget token to each TaskSet.",
                        "Abort subordinate tasks when budgets expire.",
                        "Emit metrics for shed workloads to drive scaling decisions.",
                    ],
                ),
                variation(
                    "observability",
                    "Observability Hooks",
                    "Python",
                    "instrumenting structured tasks with trace spans",
                    ["otel", "spans", "instrumentation"],
                    "Wrap TaskGroup creation with OpenTelemetry spans to trace child task lifecycles.",
                    [
                        "Use contextvars to carry trace ids into TaskGroup scopes.",
                        "Record start/stop events for each spawned task.",
                        "Tag spans with cancellation causes for root-cause analysis.",
                    ],
                ),
            ],
        ),
        Topic(
            slug="async-error-handling",
            title="Async Error Handling",
            palace="Async Systems",
            district="Failure Domains",
            tags=["async", "error-handling", "safety"],
            base_keywords=["async", "error", "retry", "timeout", "fallback"],
            variations=[
                variation(
                    "boundary-contracts",
                    "Boundary Contracts",
                    "Python",
                    "ensuring awaitable boundaries enforce retries + timeouts",
                    ["interface", "timeout", "retry"],
                    "Define awaitable service contracts that centralize retry, timeout, and circuit-breaker policies.",
                    [
                        "Wrap outbound awaitables with `asyncio.timeout` contexts.",
                        "Track retry budget per logical request.",
                        "Propagate structured failure summaries upstream.",
                    ],
                ),
                variation(
                    "idempotent-retries",
                    "Idempotent Retries",
                    "Go",
                    "ensuring retried operations stay idempotent",
                    ["idempotent", "retries", "go"],
                    "Mark operations as idempotent via request ids and persist dedupe tokens to survive restarts.",
                    [
                        "Generate deterministic request ids at ingress.",
                        "Persist request ledger entries before invoking downstream systems.",
                        "Drop duplicate retries by consulting the ledger.",
                    ],
                ),
                variation(
                    "fallback-strategies",
                    "Fallback Strategies",
                    "Node.js",
                    "graceful degradation for async pipelines",
                    ["fallback", "node", "graceful", "degradation"],
                    "Provide typed fallback implementations so UI flows return helpful responses during outages.",
                    [
                        "Define fallback resolvers per feature flag.",
                        "Route to cached responses when primary providers fail.",
                        "Emit Canary alerts when fallback usage spikes.",
                    ],
                ),
                variation(
                    "error-budget-alerts",
                    "Error Budget Alerts",
                    "Python",
                    "surfacing async failures via budgets",
                    ["error-budget", "alerts", "slo"],
                    "Track error budgets for async workers and raise structured alerts when burn rates exceed policy.",
                    [
                        "Derive budgets from service level objectives.",
                        "Instrument awaitable failures with severity tags.",
                        "Trigger PagerDuty when burn rate threshold is crossed.",
                    ],
                ),
                variation(
                    "dead-letter-streams",
                    "Dead Letter Streams",
                    "Python",
                    "capturing irrecoverable async messages",
                    ["dead-letter", "queue", "stream"],
                    "Publish irrecoverable tasks into a dead-letter stream with enough metadata for replay.",
                    [
                        "Attach failure snapshots (payload + error) to DLS events.",
                        "Add replay CLI for curated re-processing.",
                        "Expire DLS entries per compliance requirements.",
                    ],
                ),
            ],
        ),
        Topic(
            slug="cache-eviction-strategies",
            title="Cache Eviction Strategies",
            palace="Knowledge Brain",
            district="Caching Layer",
            tags=["cache", "eviction", "memory-palace"],
            base_keywords=["cache", "eviction", "ttl", "knowledge", "vitality"],
            variations=[
                variation(
                    "vitality-decay",
                    "Vitality Decay",
                    "Python",
                    "evicting entries when vitality drops below 10",
                    ["vitality", "decay", "lifecycle"],
                    "Apply a daily decay to vitality scores and flag entries under 10 for review / eviction.",
                    [
                        "Subtract configured decay per day of inactivity.",
                        "Promote entries when referenced frequently.",
                        "Auto-move low scores into staging for review.",
                    ],
                ),
                variation(
                    "konmari-sessions",
                    "KonMari Sessions",
                    "Notebook",
                    "structured tidy sessions with gratitude",
                    ["konmari", "tidy", "gratitude"],
                    "Schedule weekly KonMari reviews to archive stale entries with gratitude rituals.",
                    [
                        "Generate stale list from `vitality-scores.yaml`.",
                        "Prompt human curator with spark-joy question set.",
                        "Record outcome in `docs/curation-log.md`.",
                    ],
                ),
                variation(
                    "context-budgeting",
                    "Context Budgeting",
                    "Python",
                    "evicting large entries to maintain context budgets",
                    ["context-budget", "token-limit"],
                    "Estimate token footprint per entry and trim oversized notes when caches exceed budgets.",
                    [
                        "Store approximate token counts per entry.",
                        "Prefer summarization over deletion when knowledge is rare.",
                        "Emit telemetry when budgets are at risk.",
                    ],
                ),
                variation(
                    "marginal-value-score",
                    "Marginal Value Score",
                    "Python",
                    "evicting duplicates using marginal value filter results",
                    ["marginal", "duplicate", "filter"],
                    "Use marginal value scores to reject redundant entries before they pollute the palace.",
                    [
                        "Reject EXACT/HIGH overlap entries automatically.",
                        "Merge partial overlaps via knowledge-orchestrator prompts.",
                        "Tag replacements with `supersedes:<entry>` metadata.",
                    ],
                ),
                variation(
                    "intake-quarantine",
                    "Intake Quarantine",
                    "Python",
                    "keeping new knowledge in probation before promotion",
                    ["probation", "quarantine", "intake"],
                    "Place fresh knowledge into probation with heightened monitoring before it becomes evergreen.",
                    [
                        "Set maturity=probation for new entries.",
                        "Require ≥3 references before promoting to growing.",
                        "Auto-archive probation items untouched after 14 days.",
                    ],
                ),
            ],
        ),
        Topic(
            slug="knowledge-indexing",
            title="Knowledge Indexing",
            palace="Knowledge Brain",
            district="Index Fabric",
            tags=["indexing", "search", "metadata"],
            base_keywords=["index", "keyword", "query-template", "search"],
            variations=[
                variation(
                    "keyword-curation",
                    "Keyword Curation",
                    "Python",
                    "standardizing keyword vocabularies",
                    ["keyword", "vocabulary", "taxonomy"],
                    "Maintain a single source of truth for index vocabularies to prevent drift.",
                    [
                        "Lint keywords via `scripts/validate_indexes.py`.",
                        "Normalize casing + hyphenation.",
                        "Emit warnings for orphaned entries.",
                    ],
                ),
                variation(
                    "query-templates",
                    "Query Templates",
                    "Python",
                    "mapping question phrasings to palace entries",
                    ["query", "template", "ranking"],
                    "Capture canonical query phrasings per entry to boost match strength.",
                    [
                        "Mirror natural-language questions from support tickets.",
                        "Store normalized query variants for deduplication.",
                        "Add tests ensuring templates resolve to entries.",
                    ],
                ),
                variation(
                    "semantic-tags",
                    "Semantic Tags",
                    "Python",
                    "adding semantic tags for multi-modal lookup",
                    ["semantic", "tagging", "ontology"],
                    "Enrich entries with semantic tags bridging projects, languages, and patterns.",
                    [
                        "Use shared ontology file to define tag families.",
                        "Update both keyword + query templates when tags change.",
                        "Add telemetry to track tag usage frequency.",
                    ],
                ),
                variation(
                    "index-refresh",
                    "Index Refresh",
                    "Python",
                    "rebuilding indexes on each intake batch",
                    ["rebuild", "automation", "index"],
                    "Automate rebuilds of keyword + query indexes after each intake batch.",
                    [
                        "Hook `knowledge-orchestrator` to call `build_indexes.py`.",
                        "Validate indexes before swapping via checksum.",
                        "Alert on build failures with actionable logs.",
                    ],
                ),
                variation(
                    "index-telemetry",
                    "Index Telemetry",
                    "Python",
                    "tracking search hits per entry",
                    ["telemetry", "hits", "ranking"],
                    "Record how often entries are returned to tune ranking heuristics.",
                    [
                        "Increment counters per entry in telemetry CSV.",
                        "Surface top-hit dashboards for curators.",
                        "Demote noisy entries by tuning keywords.",
                    ],
                ),
            ],
        ),
        Topic(
            slug="autonomy-scoring",
            title="Autonomy Scoring",
            palace="Governance",
            district="Trust Engine",
            tags=["autonomy", "scoring", "governance"],
            base_keywords=["autonomy", "score", "trust", "regret-rate"],
            variations=[
                variation(
                    "level-promotions",
                    "Level Promotions",
                    "Python",
                    "criteria for promoting autonomy levels",
                    ["promotion", "criteria", "level"],
                    "Define multi-window accuracy thresholds before promoting autonomy levels.",
                    [
                        "Track rolling accuracy windows (7d, 30d).",
                        "Require consecutive windows above threshold before promotion.",
                        "Log promotions in `autonomy-state.yaml` with rationale.",
                    ],
                ),
                variation(
                    "domain-overrides",
                    "Domain Overrides",
                    "Python",
                    "locking sensitive domains at Level 0",
                    ["domain-lock", "override", "sensitive"],
                    "Allow overrides that lock autonomy levels for security/privacy domains.",
                    [
                        "Store overrides in `domain_controls` map.",
                        "Expose CLI to toggle locks with reason codes.",
                        "Audit overrides weekly for stale decisions.",
                    ],
                ),
                variation(
                    "regret-rate-tracking",
                    "Regret Rate Tracking",
                    "Python",
                    "monitoring regret rate spikes",
                    ["regret-rate", "alerts"],
                    "Compute regret rate and emit alerts if it spikes >5% WoW.",
                    [
                        "Log regret events in telemetry CSV.",
                        "Compare week-over-week rates in scoring job.",
                        "Auto-demote levels when thresholds breached.",
                    ],
                ),
                variation(
                    "human-in-loop",
                    "Human-in-the-Loop",
                    "Python",
                    "ensuring sample audits even at Level 3",
                    ["audit", "sample", "level3"],
                    "Force sample audits even for trusted autonomy levels to detect drift.",
                    [
                        "Sample N decisions per week for manual review.",
                        "Record disagreements and feed scoring job.",
                        "Demote when disagreement ratio exceeds tolerance.",
                    ],
                ),
                variation(
                    "cli-workflows",
                    "CLI Workflows",
                    "Python",
                    "command palette for trust adjustments",
                    ["cli", "workflow", "trust"],
                    "Add CLI workflows for granting trust, demoting, and reviewing metrics.",
                    [
                        "Expose `autonomy trust <domain>` commands.",
                        "Display recent metrics after each adjustment.",
                        "Log CLI action metadata into telemetry for audits.",
                    ],
                ),
            ],
        ),
        Topic(
            slug="garden-tending",
            title="Garden Tending",
            palace="Knowledge Garden",
            district="Lifecycle",
            tags=["garden", "tending", "lifecycle"],
            base_keywords=["garden", "tend", "stale", "probation", "evergreen"],
            variations=[
                variation(
                    "stale-sweeps",
                    "Stale Sweeps",
                    "Python",
                    "automated stale queue generation",
                    ["stale", "queue", "automation"],
                    "Generate stale queues weekly so curators focus on highest-impact reviews.",
                    [
                        "Sort entries by vitality ascending.",
                        "Batch reviews by palace to maintain flow.",
                        "Log outcomes for each sweep in curation log.",
                    ],
                ),
                variation(
                    "konmari-prompts",
                    "KonMari Prompts",
                    "Python",
                    "embedding spark-joy prompts into CLI",
                    ["konmari", "prompts", "cli"],
                    "Guide curators through spark-joy prompts before deleting knowledge.",
                    [
                        "Prompt for aspiration alignment + enthusiasm.",
                        "Require gratitude statement before archive.",
                        "Record final decision + rationale per entry.",
                    ],
                ),
                variation(
                    "garden-reports",
                    "Garden Reports",
                    "Python",
                    "weekly lifecycle health reports",
                    ["report", "garden", "health"],
                    "Generate weekly reports summarizing probation/growing/evergreen ratios.",
                    [
                        "Compute per-stage counts from vitality file.",
                        "Highlight overdue probation entries.",
                        "Email/report to maintainers.",
                    ],
                ),
                variation(
                    "tending-cli",
                    "Tending CLI",
                    "Python",
                    "interactive CLI for lifecycle decisions",
                    ["cli", "tending", "workflow"],
                    "Provide interactive CLI to cycle through stale entries and capture actions.",
                    [
                        "Load queue from `vitality-scores.yaml`.",
                        "Offer actions: promote, refresh, archive, merge.",
                        "Persist updates + telemetry from CLI session.",
                    ],
                ),
                variation(
                    "evergreen-guards",
                    "Evergreen Guards",
                    "Python",
                    "regressions preventing evergreen deletions",
                    ["evergreen", "regression", "tests"],
                    "Add regression tests that fail when evergreen entries disappear without archive notes.",
                    [
                        "Map evergreen ids to docs referencing them.",
                        "Fail CI when references break.",
                        "Require archive note or replacement entry id.",
                    ],
                ),
            ],
        ),
        Topic(
            slug="telemetry-pipeline",
            title="Telemetry Pipeline",
            palace="Observability",
            district="Event Stream",
            tags=["telemetry", "metrics", "logging"],
            base_keywords=["telemetry", "metrics", "csv", "event", "dashboard"],
            variations=[
                variation(
                    "cache-hit-dashboard",
                    "Cache Hit Dashboard",
                    "Notebook",
                    "visualizing cache hit rates",
                    ["cache-hit", "dashboard", "visualization"],
                    "Plot cache hit rate vs. query volume to validate ROI of the knowledge corpus.",
                    [
                        "Parse telemetry CSV for decision outcomes.",
                        "Aggregate by day and query mode.",
                        "Publish chart to dashboards directory.",
                    ],
                ),
                variation(
                    "latency-profiling",
                    "Latency Profiling",
                    "Python",
                    "profiling hook latency",
                    ["latency", "profiling", "hook"],
                    "Measure cache interception latency to ensure hooks stay under 20ms.",
                    [
                        "Record latency_ms for each query.",
                        "Compute P50/P95 per mode daily.",
                        "Alert when P95 exceeds threshold.",
                    ],
                ),
                variation(
                    "intake-flags",
                    "Intake Flags",
                    "Python",
                    "tracking intake flag volume",
                    ["intake", "flag", "volume"],
                    "Track how many queries trigger intake to meter curator workload.",
                    [
                        "Summarize should_flag_for_intake counts daily.",
                        "Correlate spikes with taxonomy gaps.",
                        "Suggest candidate knowledge to research teams.",
                    ],
                ),
                variation(
                    "autonomy-alerts",
                    "Autonomy Alerts",
                    "Python",
                    "alerting on autonomy events",
                    ["autonomy", "alert", "telemetry"],
                    "Emit alerts when autonomy level changes or regret spikes occur.",
                    [
                        "Log promotions/demotions with context.",
                        "Send Slack alerts summarizing rationale.",
                        "Attach curation log excerpt for reviewers.",
                    ],
                ),
                variation(
                    "token-savings",
                    "Token Savings",
                    "Python",
                    "measuring context savings per cache interception",
                    ["token", "savings", "context"],
                    "Estimate tokens saved when the cache answers queries without web searches.",
                    [
                        "Store estimated token delta per decision.",
                        "Roll up weekly savings to share with leadership.",
                        "Use savings metrics to prioritize future knowledge work.",
                    ],
                ),
            ],
        ),
        Topic(
            slug="feature-flag-governance",
            title="Feature Flag Governance",
            palace="Governance",
            district="Rollout",
            tags=["feature-flag", "rollout", "safety"],
            base_keywords=["feature-flag", "rollout", "staging", "kill-switch"],
            variations=[
                variation(
                    "flag-matrix",
                    "Flag Matrix",
                    "Markdown",
                    "documenting flag dependencies",
                    ["flag", "matrix", "dependency"],
                    "Maintain a feature flag matrix showing dependencies and safe rollback orders.",
                    [
                        "List all flags with owners and kill-switch steps.",
                        "Encode dependencies so rollouts happen in order.",
                        "Store matrix next to rollout playbook.",
                    ],
                ),
                variation(
                    "staged-rollout",
                    "Staged Rollout",
                    "Python",
                    "rolling cache intercept flag through stages",
                    ["staged", "rollout", "flag"],
                    "Define staged rollout steps for cache intercept flag from dev → staging → prod.",
                    [
                        "Automate toggles via CLI/Env var combos.",
                        "Capture dry-run transcripts with telemetry snapshots.",
                        "Provide rollback instructions for each stage.",
                    ],
                ),
                variation(
                    "flag-telemetry",
                    "Flag Telemetry",
                    "Python",
                    "linking telemetry to flag states",
                    ["flag", "telemetry", "state"],
                    "Annotate telemetry with active flag states to aid correlation.",
                    [
                        "Record flag config with each telemetry event.",
                        "Enable dashboards to filter by flag state.",
                        "Store snapshots in `telemetry/flag_states/`.",
                    ],
                ),
                variation(
                    "oncall-runbooks",
                    "On-call Runbooks",
                    "Markdown",
                    "on-call guides for flipping flags",
                    ["oncall", "runbook", "flag"],
                    "Document on-call runbooks for feature flag adjustments during incidents.",
                    [
                        "List commands to disable cache/autonomy/lifecycle flags.",
                        "Specify verification steps post-change.",
                        "Link to telemetry dashboards for validation.",
                    ],
                ),
                variation(
                    "audit-trails",
                    "Audit Trails",
                    "Python",
                    "logging flag changes for audits",
                    ["audit", "trail", "flag-change"],
                    "Log every flag adjustment with actor, timestamp, and reason.",
                    [
                        "Write entries to `telemetry/flag_changes.csv`.",
                        "Include CLI invocations + manual edits.",
                        "Review weekly for unauthorized toggles.",
                    ],
                ),
            ],
        ),
        Topic(
            slug="semantic-embedding",
            title="Semantic Embedding",
            palace="Knowledge Brain",
            district="Search Upgrades",
            tags=["embedding", "semantic", "search"],
            base_keywords=["embedding", "semantic", "vector", "search"],
            variations=[
                variation(
                    "local-embeddings",
                    "Local Embeddings",
                    "Python",
                    "building local sentence-transformer index",
                    ["sentence-transformers", "local", "index"],
                    "Generate local embeddings with sentence-transformers to improve semantic recall.",
                    [
                        "Use MiniLM-based model for fast inference.",
                        "Persist vectors under `data/embeddings/`.",
                        "Provide CLI to rebuild or toggle provider.",
                    ],
                ),
                variation(
                    "fusion-ranking",
                    "Fusion Ranking",
                    "Python",
                    "combining keyword + embedding scores",
                    ["fusion", "ranking", "hybrid"],
                    "Fuse keyword and embedding scores using weighted sums to improve precision.",
                    [
                        "Normalize scores before blending.",
                        "Expose config for weighting knobs.",
                        "Add regression tests for fallback behavior.",
                    ],
                ),
                variation(
                    "evaluation-suite",
                    "Evaluation Suite",
                    "Notebook",
                    "benchmarking semantic search",
                    ["evaluation", "benchmark", "semantic"],
                    "Benchmark semantic search improvements using curated QA pairs.",
                    [
                        "Store evaluation corpus in fixtures.",
                        "Compute recall/precision vs. keyword-only baseline.",
                        "Share results in embedding upgrade doc.",
                    ],
                ),
                variation(
                    "provider-toggles",
                    "Provider Toggles",
                    "YAML",
                    "toggling embedding providers",
                    ["provider", "toggle", "config"],
                    "Expose config flag to switch between none/local/api embedding providers.",
                    [
                        "Update config schema with `embedding_provider`.",
                        "Teach unified search to branch accordingly.",
                        "Add CLI showing current provider + health.",
                    ],
                ),
                variation(
                    "vector-maintenance",
                    "Vector Maintenance",
                    "Python",
                    "keeping vector indexes fresh",
                    ["vector", "maintenance", "cron"],
                    "Add cron to rebuild or update vectors when entries change.",
                    [
                        "Track last embedding timestamp per entry.",
                        "Incrementally update vectors for changed docs.",
                        "Purge orphaned vectors when entries deleted.",
                    ],
                ),
            ],
        ),
        Topic(
            slug="marginal-value-filter",
            title="Marginal Value Filter",
            palace="Governance",
            district="Curation",
            tags=["marginal-value", "curation", "filter"],
            base_keywords=["marginal", "redundancy", "delta", "integration"],
            variations=[
                variation(
                    "redundancy-checks",
                    "Redundancy Checks",
                    "Python",
                    "classifying overlap levels",
                    ["redundancy", "exact-match", "partial"],
                    "Classify overlap levels (exact/high/partial/novel) before storing knowledge.",
                    [
                        "Compare hashed fingerprints for quick duplicate detection.",
                        "Treat >80% overlap as reject and log duplicates.",
                        "Forward partial overlaps to delta analysis.",
                    ],
                ),
                variation(
                    "delta-analysis",
                    "Delta Analysis",
                    "Python",
                    "summarizing what's new",
                    ["delta", "novel-insight", "analysis"],
                    "Explain what is genuinely new so curators can accept or merge with confidence.",
                    [
                        "Highlight novel headings/keywords.",
                        "Score value 0..1 to guide decisions.",
                        "Surface suggested integration path.",
                    ],
                ),
                variation(
                    "integration-decisions",
                    "Integration Decisions",
                    "Python",
                    "automating store/merge/replace/skip",
                    ["integration", "decision", "automation"],
                    "Recommend integration actions (store/merge/replace/skip) with confidence bands.",
                    [
                        "Auto-store high-scoring novel insights.",
                        "Route merge candidates with targeted entry ids.",
                        "Require human review when confidence <0.6.",
                    ],
                ),
                variation(
                    "explanations",
                    "Explanations",
                    "Python",
                    "producing curator-friendly explanations",
                    ["explanation", "curator", "payload"],
                    "Generate curator-friendly explanations for each suggestion.",
                    [
                        "Summarize novelty, overlaps, and duplicates.",
                        "Link to supporting entries by id.",
                        "Persist explanation in intake payload.",
                    ],
                ),
                variation(
                    "cli-workbench",
                    "CLI Workbench",
                    "Python",
                    "interactive marginal value review",
                    ["cli", "workbench", "curation"],
                    "Provide CLI workbench to review marginal value assessments interactively.",
                    [
                        "Render color-coded overlap summaries.",
                        "Collect curator decision + notes.",
                        "Write outcomes to curation log automatically.",
                    ],
                ),
            ],
        ),
    ]


def generate_entries() -> list[dict[str, Any]]:
    """Build entry payloads describing markdown + index metadata."""
    entries: list[dict[str, Any]] = []

    for topic in _topics():
        for variation in topic.variations:
            entry_id = f"{topic.slug}-{variation.slug}"
            title = f"{topic.title} — {variation.title}"
            tags = sorted(set(topic.tags + [topic.slug, variation.slug.replace("-", "_")]))
            keywords = sorted({*(topic.base_keywords), *variation.keywords})
            queries = [
                f"How to apply {topic.title.lower()} to {variation.focus}?",
                f"{topic.title} best practices for {variation.language.lower()} teams",
                f"{variation.title} guidance for {variation.focus}",
            ]
            relative_md_path = f"{topic.slug}/{variation.slug}.md"
            entries.append(
                {
                    "entry_id": entry_id,
                    "title": title,
                    "file": f"knowledge-corpus/{relative_md_path}",
                    "palace": topic.palace,
                    "district": topic.district,
                    "tags": tags,
                    "keywords": keywords,
                    "queries": queries,
                    "language": variation.language,
                    "focus": variation.focus,
                    "summary": variation.summary,
                    "steps": variation.playbook_steps,
                },
            )

    return entries


def seed_cache_catalog(
    *,
    index_dir: Path,
    fixture_path: Path,
    keyword_index: Path | None = None,
) -> dict[str, Any]:
    """Merge curated cache intercept entries into the keyword index."""
    keyword_index = keyword_index or (index_dir / "keyword-index.yaml")
    keyword_index.parent.mkdir(parents=True, exist_ok=True)
    curated = yaml.safe_load(fixture_path.read_text(encoding="utf-8")) or {}
    curated_entries: list[dict[str, Any]] = curated.get("entries", []) or []

    existing = (
        yaml.safe_load(keyword_index.read_text(encoding="utf-8"))
        if keyword_index.exists()
        else {"entries": {}, "keywords": {}, "metadata": {}}
    )
    entries_map: dict[str, Any] = existing.setdefault("entries", {})
    keyword_map: dict[str, list[str]] = existing.setdefault("keywords", {})

    for entry in curated_entries:
        slug = entry["slug"]
        entries_map[slug] = {
            "file": entry.get("file", f"knowledge-corpus/{slug}.md"),
            "keywords": sorted(set(entry.get("keywords", []))),
            "title": entry.get("title", slug.replace("-", " ").title()),
            "tags": entry.get("tags", ["cache-intercept"]),
            "summary": entry.get("summary", ""),
            "source": entry.get("source", "memory-palace/cache-intercept"),
        }
        for keyword in entry.get("keywords", []):
            bucket = keyword_map.setdefault(keyword, [])
            if slug not in bucket:
                bucket.append(slug)

    for bucket in keyword_map.values():
        bucket.sort()

    metadata = existing.setdefault("metadata", {})
    cache_meta = metadata.setdefault("cache_intercept", {})
    cache_meta["curated_count"] = len(curated_entries)
    cache_meta["last_seeded"] = dt.datetime.now(dt.timezone.utc).isoformat()

    keyword_index.write_text(yaml.safe_dump(existing, sort_keys=False), encoding="utf-8")
    return existing


def write_markdown(entry: dict[str, Any]) -> None:
    """Create/overwrite the markdown file for an entry."""
    path = PLUGIN_ROOT / "docs" / entry["file"]
    path.parent.mkdir(parents=True, exist_ok=True)
    front_matter = {
        "title": entry["title"],
        "source": f"memory-palace://seed/{entry['entry_id']}",
        "author": "Memory Palace Seed Bot",
        "date_captured": str(TODAY),
        "palace": entry["palace"],
        "district": entry["district"],
        "maturity": "growing",
        "tags": entry["tags"],
        "queries": entry["queries"],
    }
    body = textwrap.dedent(
        f"""
        # {entry["title"]}

        ## Why it matters

        {entry["summary"]}

        ## Focus Area

        - **Language / Runtime**: {entry["language"]}
        - **Primary Focus**: {entry["focus"]}

        ## Implementation Playbook

        """
    ).strip()
    steps = "\n".join(
        f"1. {step}" if idx == 0 else f"{idx + 1}. {step}"
        for idx, step in enumerate(entry["steps"])
    )
    content = (
        f"---\n{yaml.safe_dump(front_matter, sort_keys=False).strip()}\n---\n\n{body}\n{steps}\n"
    )
    path.write_text(content, encoding="utf-8")


def update_keyword_index(entries: list[dict[str, Any]]) -> None:
    index_path = INDEX_DIR / "keyword-index.yaml"
    with index_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    entries_map: dict[str, Any] = data.get("entries", {})
    keyword_map: dict[str, list[str]] = data.get("keywords", {})

    for entry in entries:
        entry_id = entry["entry_id"]
        entries_map[entry_id] = {
            "file": entry["file"],
            "keywords": entry["keywords"],
            "title": entry["title"],
            "tags": entry["tags"],
        }
        for kw in entry["keywords"]:
            bucket = keyword_map.setdefault(kw, [])
            if entry_id not in bucket:
                bucket.append(entry_id)

    for bucket in keyword_map.values():
        bucket.sort()

    data["entries"] = entries_map
    data["keywords"] = dict(sorted(keyword_map.items()))
    data.setdefault("metadata", {})
    data["metadata"]["total_entries"] = len(entries_map)
    data["metadata"]["total_keywords"] = len(keyword_map)
    data["metadata"]["last_updated"] = dt.datetime.now(dt.timezone.utc).isoformat()

    with index_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def update_query_templates(entries: list[dict[str, Any]]) -> None:
    templates_path = INDEX_DIR / "query-templates.yaml"
    with templates_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    entry_map: dict[str, Any] = data.get("entries", {})
    query_map: dict[str, list[str]] = data.get("queries", {})

    for entry in entries:
        entry_id = entry["entry_id"]
        entry_map[entry_id] = {
            "file": entry["file"],
            "queries": entry["queries"],
            "title": entry["title"],
        }
        for query in entry["queries"]:
            key = query.lower()
            bucket = query_map.setdefault(key, [])
            if entry_id not in bucket:
                bucket.append(entry_id)

    for bucket in query_map.values():
        bucket.sort()

    data["entries"] = entry_map
    data["queries"] = dict(sorted(query_map.items()))
    data.setdefault("metadata", {})
    data["metadata"]["total_entries"] = len(entry_map)
    data["metadata"]["total_queries"] = len(query_map)
    data["metadata"]["last_updated"] = dt.datetime.now(dt.timezone.utc).isoformat()

    with templates_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def main() -> None:
    cache_catalog = DEFAULT_CACHE_CATALOG
    if cache_catalog.exists():
        seed_cache_catalog(index_dir=INDEX_DIR, fixture_path=cache_catalog)
    else:
        print(f"[seed] cache intercept catalog missing at {cache_catalog}, skipping curated merge.")

    entries = generate_entries()
    for entry in entries:
        write_markdown(entry)
    update_keyword_index(entries)
    update_query_templates(entries)
    print(f"Seeded {len(entries)} entries into corpus + indexes.")


if __name__ == "__main__":
    main()
