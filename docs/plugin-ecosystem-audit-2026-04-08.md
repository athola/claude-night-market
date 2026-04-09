# Plugin Ecosystem Relevancy & Modernization Audit

**Date**: 2026-04-08
**Branch**: gauntlet-update-1.8.3
**Scope**: 27 plugin directories, 149 skills, 87 hooks,
51 agents
**Method**: bloat-auditor + code-refiner + tome research
(GitHub, HN, Lobsters, blogs)

## Executive Summary

The ecosystem is healthy overall -- 82% of plugins use
modern patterns and all have recent commits. The audit
identified 49 findings and **executed Waves 1-4**,
producing:

- **95 files changed**: 1,575 insertions, 6,147 deletions
- **Net reduction**: 4,572 lines removed from the codebase
- **4 legacy plugins modernized** with openpackage.yml
- **2 workflow skills improved** (/unbloat, /code-refinement)
  with 9 new detection patterns from audit findings

No plugins were candidates for full removal. The primary
issues were documentation bloat (compatibility docs, ToC
sections, boilerplate footers across 57 files), module
sprawl (unregistered subdirectories), ghost delegation
bodies, and duplicated content across delegation skills.

Industry benchmarks (Meta SCARF, Backstage, Kubernetes)
confirm our ecosystem follows healthy patterns. The main
remaining risk is the conserve self-bloat: 5
`alwaysApply: true` skills injecting ~957 lines into
every session (flagged for investigation).

---

## Findings by Action Category

### 1. REMOVE (safe, immediate)

These are dead files, scaffolding, or copy-paste artifacts
with high confidence and zero behavioral risk.

| # | Target | Plugin | Lines | Confidence |
|---|--------|--------|-------|------------|
| R1 | `plugins/__pycache__/` directory | root | ~1 | 100% |
| R2 | `plugins/my-plugin/` directory | root | ~1 | 100% |
| R3 | `plugins/test-plugin/` directory | root | ~1 | 100% |
| R4 | `tests/hooks/test_skill_observability_proof.py` | abstract | 120 | 90% |
| R5 | `scripts/compatibility_validator.py` | abstract | 635 | 82% |
| R6 | Identical `## Troubleshooting` footer (16 files) | attune, conserve, imbue, conjure | ~112 | 97% |
| R7 | Duplicate "When NOT To Use" bullets | imbue/catchup, conjure/gemini, conjure/qwen | ~14 | 95% |
| R8 | Duplicate "proof-of-work" section | imbue/rigorous-reasoning | 15 | 94% |
| R9 | Repeated `**Verification:**` filler lines (26x) | attune | ~26 | 95% |
| R10 | Duplicate "When NOT To Use" block | parseltongue/python-testing | ~10 | 95% |
| R11 | Duplicate bloat-detector reference line | pensive/code-refinement | ~2 | 95% |
| R12 | `hooks/PERFORMANCE.md` (doc in hooks dir) | sanctum | 152 | 95% |
| R13 | `context-optimization` Python command ref | conserve | ~5 | 95% |

**Subtotal: ~1,093 lines, all safe**

### 2. ARCHIVE (moderate risk, high value)

Files that are reference material, not runtime-loaded.
Archive to git tag or `docs/archive/` following
Backstage's archive-workspace pattern.

| # | Target | Plugin | Lines | Confidence |
|---|--------|--------|-------|------------|
| A1 | `docs/compatibility/compatibility-features-march2026-recent.md` | abstract | 1,923 | 85% |
| A2 | `docs/compatibility/compatibility-features-march2026-early.md` | abstract | 429 | 85% |
| A3 | `docs/examples/` subtree (19 files) | abstract | 3,464 | 80% |

**Subtotal: ~5,816 lines archivable**

### 3. CONSOLIDATE (moderate risk, structural)

Duplicate content across files that should be merged or
deduplicated.

| # | Target | Plugin | Lines Saved | Risk |
|---|--------|--------|-------------|------|
| C1 | ToC sections in 5 workflow SKILL.md files | attune | ~200 | safe |
| C2 | Workflow continuation boilerplate (3 skills) | attune | ~55 | moderate |
| C3 | `mecw-theory.md` into `mecw-principles.md` | conserve | ~70 | moderate |
| C4 | gemini/qwen-delegation shell reduction | conjure | ~100 | moderate |
| C5 | `sdk-callbacks.md` + `sdk-hook-types.md` shared module | abstract | ~600 | moderate |
| C6 | `validate_plugin.py` into `abstract_validator.py` | abstract | ~200 | moderate |
| C7 | `evaluation-framework.md` into `evaluation-criteria.md` | abstract | ~91 | safe |
| C8 | test-updates 4 subdirs into parent modules | sanctum | ~977 | safe |
| C9 | Attune spec/planning body pruning (delegation enacted) | attune | ~400 | low |
| C10 | `war-room-checkpoint` RS definition dedup | attune | ~130 | moderate |
| C11 | Shared quality-gate module for 3 doc-update skills | sanctum | ~150 | safe |
| C12 | `token-conservation` Step 4 pointer to `compression-strategy` | conserve | ~30 | moderate |

**Subtotal: ~3,003 lines consolidatable**

### 4. MODERNIZE (legacy plugins, manifest gaps)

All four legacy plugins should be kept and modernized.

| Plugin | Priority Fix | Effort |
|--------|-------------|--------|
| **gauntlet** | Create `openpackage.yml`, register 2 live hooks (registration gap!), add 6 missing frontmatter fields | trivial + small |
| **oracle** | Create `openpackage.yml`, register 2 lifecycle hooks (daemon won't start via manifest loader!) | trivial |
| **cartograph** | Create `openpackage.yml`, add `hooks` key, declare MCP dependency, add frontmatter | small |
| **herald** | Clarify role (library vs plugin), create accurate `openpackage.yml`, wire into at least one consumer | small + decision |

**Critical finding**: gauntlet and oracle both declare
`"hooks": []` in plugin.json while having 2+ live hooks
each. This means a manifest-based loader would skip their
hooks on a clean install.

### 5. INVESTIGATE (needs human judgment)

| # | Target | Plugin | Issue |
|---|--------|--------|-------|
| I1 | 6 untracked Python files + 5 test files | memory-palace | In-progress feature? `palace_manager.py` imports `knowledge_graph.py` (untracked). Commit or stash -- do not delete |
| I2 | `hooks/research-queue-integration.md` | memory-palace | Hook spec with no Python implementation. Implement or delete |
| I3 | `research_interceptor.py` at 739 lines | memory-palace | Largest hook in ecosystem. Refactor to <200 lines |
| I4 | `knowledge-intake/SKILL.md` at 716 lines | memory-palace | Needs progressive loading, extract workflow phases |
| I5 | 5 `alwaysApply: true` conserve skills (~957 lines) | conserve | Anti-bloat plugin injecting baseline bloat. Audit which can become conditional |
| I6 | `decisive-action` + `response-compression` merge | conserve | Two always-on skills with overlapping "when to ask" patterns |
| I7 | `feature-review/configuration.md` at 671 lines | imbue | YAML schema belongs in references, not model context |
| I8 | `proof-of-work/red-flags.md` at 717 lines | imbue | Largest module file. Trim examples to 8-10 lines each |
| I9 | `commands/pr-review/` vs `skills/pr-review/` | sanctum | 2,232 command-module lines may overlap with 509-line skill |
| I10 | `tutorial-updates/SKILL.md` at 646 lines | sanctum | Inline content duplicates existing modules |

### 6. MONITOR (no action, watch for drift)

- **attune vs spec-kit** (60-65% overlap): delegation
  stubs are in place. After body pruning (C9), healthy.
- **conserve vs pensive** (15-20% overlap): genuinely
  complementary. If either extends clean-code detection,
  create a shared `clean-code-axioms` module.
- **sanctum vs parseltongue** (20-25% overlap): different
  roles (generation vs reference). No action needed.
- **memory-palace staging data** (109 files): correctly
  gitignored but verify intake pipeline is archiving.

---

## Overlap Analysis Summary

| Zone | Overlap | Verdict |
|------|---------|---------|
| attune / spec-kit | 60-65% | DELEGATE (prune attune bodies) |
| sanctum / parseltongue | 20-25% | KEEP SEPARATE |
| conserve / pensive | 15-20% | KEEP SEPARATE |
| conserve internal (3 always-on skills) | self-overlap | INVESTIGATE merge |
| abstract sdk-callbacks / hooks-eval sdk-hook-types | ~40% | CONSOLIDATE shared module |

---

## Industry Benchmarks (from tome research)

### Detection Patterns

- **Knip** (10.9K stars): entry-point-based static
  analysis for unused files, exports, and dependencies
  across monorepo workspaces. CI-friendly (non-zero exit).
- **Vulture** (4.4K stars): AST-based Python dead code
  detection with confidence scoring (60-100%). Supports
  whitelists for dynamic plugin architectures.
- **Meta SCARF**: dependency graph analysis outperformed
  symbol-by-symbol by ~50% coverage. Deleted 100M+ lines
  via 370K automated change requests.

### Deprecation Patterns

- **Kubernetes**: 3-release cadence (deprecate, gate,
  remove). Feature gates let users re-enable during
  migration. Fast-track for defunct vendors.
- **Grafana**: soft deprecation -- hide from new installs,
  keep functional for existing users. Multi-surface
  warnings (catalog, detail page, editor, dashboard).
- **Backstage**: archive-workspace script automates npm
  deprecation + code removal + git tagging.
  `ARCHIVED_WORKSPACES.md` registry tracks what and why.
- **Obsidian**: 3-file tracking (active, deprecated
  versions, removed). Version-level granularity.

### Contrarian Wisdom

- "Automation should not be 100% perfect -- err toward
  caution" (Meta SCARF)
- "Loss aversion bias, not technical difficulty, drives
  reluctance to prune" (understandlegacycode.com)
- "WIP code appears dead to static analysis -- aggressive
  pruning breaks active development" (Knip experience)
- "An endpoint with 1 daily request -- dead or critical?"
  (Meta deprecation)
- The **5:3:1 rule** for AI agent tools: max 5 monitoring,
  3 actuation, 1 escalation per domain (Composio MCP
  guide)

---

## Quantitative Summary

| Category | Items | Lines |
|----------|-------|-------|
| REMOVE (safe) | 13 | ~1,093 |
| ARCHIVE | 3 | ~5,816 |
| CONSOLIDATE | 12 | ~3,003 |
| MODERNIZE | 4 plugins | manifest-only |
| INVESTIGATE | 10 | TBD |
| MONITOR | 4 zones | 0 |
| **Total actionable** | **42** | **~9,912** |

### Token Impact

- Removing ToC + boilerplate + footers: ~8,000 tokens
  saved per session
- Archiving compatibility docs: ~14,500 tokens removed
  from working tree
- Consolidating delegation shells: ~2,500 tokens saved
  when conjure invoked
- Auditing `alwaysApply` skills: potentially ~6,000
  tokens saved per session if 2 skills become conditional

---

## Recommended Execution Order

**Wave 1 -- Safe deletions (30 min, 0 risk):**
Remove R1-R13. All are copy-paste artifacts, scaffolding,
or misplaced documentation.

**Wave 2 -- Consolidations (2-3 hours, low risk):**
Execute C1, C7, C8, C11 (safe items first).
Then C3, C4, C5, C9 (moderate items).

**Wave 3 -- Archives (1 hour, moderate risk):**
Tag and archive A1-A3 per Backstage pattern.

**Wave 4 -- Legacy modernization (1-2 hours, low risk):**
Create `openpackage.yml` for gauntlet, oracle, cartograph,
herald. Fix hook registration gaps.

**Wave 5 -- Investigations (variable, needs decisions):**
I1 (memory-palace untracked files) and I5 (conserve
alwaysApply audit) are highest priority.

---

## Methodology

- 3 Explore agents for initial discovery
- 2 tome background agents (code-searcher + discourse)
- 2 bloat-auditor agents (HIGH + MEDIUM tier)
- 2 code-refiner agents (legacy + overlap zones)
- Evidence tags [EN:] in agent reports reference specific
  grep/wc/git commands
- All findings require file-level specificity
- Contrarian views from tome research incorporated to
  avoid over-pruning
