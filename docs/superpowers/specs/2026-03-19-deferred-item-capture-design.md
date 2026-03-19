# Deferred Item Capture -- Design Specification

## Problem Statement

The night-market plugin ecosystem generates insights, rejected
alternatives, and out-of-scope ideas across multiple workflows
(war-room deliberations, brainstorming sessions, scope-guard
deferrals, code reviews, autonomous agent discoveries).
Today these items are either lost entirely (war-room rejected
COAs buried in strategeion archives) or captured inconsistently
(scope-guard creates issues with one format, fix-pr uses another,
egregore publishes to Discussions).

There is no unified mechanism for a skill or hook to say
"this is deferred -- capture it" and have it reliably appear
as a GitHub issue with a consistent, queryable format.

## Goals

1. Any plugin skill can capture a deferred item with a single
   script call
2. Safety-net hooks catch items that skills miss
3. All deferred items produce GitHub issues with a unified
   format and label taxonomy
4. Duplicate detection prevents the same item from being
   filed twice
5. Each plugin bundles its own self-contained wrapper script
   (no cross-plugin file dependencies)

## Success Criteria

- [ ] `gh issue list --label deferred` returns all deferred
  items regardless of source plugin
- [ ] War-room rejected COAs appear as issues after deliberation
- [ ] Brainstorm non-selected approaches can be captured
  (with user confirmation)
- [ ] Scope-guard deferrals converge onto the shared format
- [ ] Stop hook catches uncaptured deferrals at session end
- [ ] PostToolUse hook catches deferrals from watched skills
  in real time
- [ ] No plugin references another plugin's files at runtime

## Constraints

- Python 3.9 compatible (system Python)
- No external dependencies beyond stdlib
- `gh` CLI required (graceful failure if missing)
- Hooks must complete in under 2 seconds
- Session ledger is ephemeral (cleaned up on next session)

## Selected Approach: Script-First (Approach A)

A standalone Python script per plugin that implements a shared
specification. Sanctum owns the reference implementation.
Two safety-net hooks (PostToolUse + Stop) provide fallback
capture. A leyline skill documents the contract.

### Rationale

- Follows the proven `rollback_reviewer.py` pattern
- Hooks and skills use the same codepath per plugin
- Convention over shared code: the specification is shared,
  not a library
- Each wrapper is ~30 lines of plugin-specific defaults
  around ~50 lines of shared logic

### Trade-offs Accepted

- Six copies of similar (not identical) scripts across plugins.
  Mitigated by: each is small (~30-80 lines), spec compliance
  test catches drift, a dedicated `make verify-deferred-capture`
  target runs the dry-run compliance test for all wrappers
- Safety-net hook pattern matching is conservative and may miss
  implicit deferrals.
  Mitigated by: explicit skill-level capture handles the
  high-value cases; hook is the fallback, not the primary

## Architecture

### Component Overview

```
Explicit Layer (skill-level)          Safety-Net Layer (hooks)
+---------------------------+    +-----------------------------+
| attune/scripts/            |    | sanctum/hooks/              |
|   deferred_capture.py      |    |   deferred_item_watcher.py  |
| imbue/scripts/             |    |   (PostToolUse, Skill)      |
|   deferred_capture.py      |    |                             |
| pensive/scripts/           |    |   deferred_item_sweep.py    |
|   deferred_capture.py      |    |   (Stop)                    |
| abstract/scripts/          |    +-----------------------------+
|   deferred_capture.py      |                |
| egregore/scripts/          |                v
|   deferred_capture.py      |    .claude/deferred-items-session.json
| sanctum/scripts/           |    (session-scoped ledger)
|   deferred_capture.py      |
|   (reference impl)         |
+---------------------------+
             |
             v
      leyline/skills/deferred-capture/SKILL.md
      (contract: CLI interface, template, labels)
```

### The Deferred Capture Script

**CLI Interface (from leyline contract):**

```
python3 scripts/deferred_capture.py \
  --title "Add cross-plugin insight aggregation" \
  --source war-room \
  --context "Raised during COA evaluation. Valid but requires
    infrastructure that doesn't exist yet." \
  --labels "deferred,war-room,enhancement" \
  --session-id "20260319-143022" \
  --artifact-path "$HOME/.claude/memory-palace/strategeion/..." \
  --captured-by explicit \
  --dry-run
```

**Required arguments:**

- `--title`: Concise description (becomes issue title
  after `[Deferred]` prefix)
- `--source`: Origin skill (war-room, brainstorm,
  scope-guard, feature-review, review, regression, egregore)
- `--context`: Why raised and why deferred

**Optional arguments:**

- `--labels`: Additional labels beyond `deferred` + source
- `--session-id`: Session identifier for traceability.
  Canonical source: `$CLAUDE_SESSION_ID` env var if set,
  otherwise a UTC timestamp generated at script startup
  (`YYYYMMDD-HHMMSS`). All callers use the same resolution
  order so ledger deduplication is consistent.
- `--artifact-path`: Link to source artifact. Must use
  `$HOME` or absolute paths, not `~` (Python does not
  auto-expand tilde in subprocess contexts)
- `--captured-by`: `explicit` (default) or `safety-net`
- `--dry-run`: Print without creating

**Behavior:**

1. Duplicate detection: `gh issue list
   --search "<title> in:title" --state open
   --json number,title`. Compare by exact title match
   after stripping the `[Deferred]` prefix and normalizing
   to lowercase. Skip if a match is found
2. Label management: ensure `deferred` label exists
   (auto-create with color `#7B61FF` if missing)
3. Issue creation: `gh issue create` with unified template
4. JSON output to stdout:
   `{"status": "created", "issue_url": "...", "number": 42}`
   or `{"status": "duplicate", "existing_url": "...",
   "number": 17}`
   or `{"status": "error", "message": "..."}`

### Unified Issue Template

**Title:** `[Deferred] <title>`

**Labels:** `deferred` + source label (e.g., `war-room`,
`scope-guard`)

**Body:**

```markdown
## Deferred Item

**Source:** <source-skill> (session <id>)
**Captured:** <date>
**Branch:** <current-branch>
**Captured by:** <explicit|safety-net>

### Context

<Why this was raised and why it was deferred.
Verbatim context from the originating workflow.>

### Original Artifact

<Link to strategeion file, PR, spec, or Discussion
where this originated. Optional but encouraged.>

### Next Steps

- [ ] Evaluate feasibility in a future cycle
- [ ] Link to related work if applicable
```

### Label Taxonomy

| Label | Color | Purpose |
|-------|-------|---------|
| `deferred` | `#7B61FF` | Universal query handle |
| `war-room` | `#B60205` | Source: war-room deliberation |
| `brainstorm` | `#1D76DB` | Source: brainstorming session |
| `scope-guard` | `#FBCA04` | Source: scope-guard deferral |
| `review` | `#0E8A16` | Source: code/PR review |
| `regression` | `#D73A4A` | Source: skill regression |
| `egregore` | `#5319E7` | Source: autonomous agent |

### Plugin Wrappers

Each plugin bundles a self-contained script (~30 lines)
that pre-fills plugin-specific defaults and enriches context:

| Plugin | Default source | Context enrichment |
|--------|---------------|-------------------|
| sanctum | (reference impl) | Full implementation (~80 lines) |
| attune | war-room or brainstorm | Strategeion session path |
| imbue | scope-guard or feature-review | Worthiness score |
| pensive | review | Review dimension |
| abstract | regression | Stability gap metrics |
| egregore | egregore | Pipeline step context |

Each wrapper implements the leyline contract independently.
No cross-plugin imports. A dedicated `make verify-deferred-capture`
target runs the dry-run compliance test for all wrappers during
the release process.

### Safety-Net Hooks

#### PostToolUse Hook: `deferred_item_watcher.py`

**Owner:** sanctum
**Matcher:** `Skill`
**Watch list:** war-room, brainstorm, scope-guard,
feature-review, unified-review, rollback-reviewer

**Logic:**

1. Read hook input JSON from stdin (standard Claude Code
   hook protocol, same as `skill_execution_logger.py`).
   Parse the `tool_input` field to identify the invoked
   skill name and the `tool_output` field for content
2. If skill not in watch list, exit (fast path)
3. Scan tool_output for deferral signals: `[Deferred]`
   markers, `rejected`, `out of scope`, `deferred`,
   `not yet applicable`, `future cycle`
4. Check session ledger
   (`.claude/deferred-items-session.json`) for duplicates
5. If uncaptured, call `scripts/deferred_capture.py`
   with `--captured-by safety-net`
6. Append to ledger with `{"title": "...", "filed": true}`

**Constraint:** Completes in under 2 seconds. Conservative
matching (better to miss than create spurious issues).

#### Stop Hook: `deferred_item_sweep.py`

**Owner:** sanctum

**Logic:**

1. Read session ledger
   (`.claude/deferred-items-session.json`)
2. Filter for entries where `filed` is `false` (items
   logged by the PostToolUse hook that failed to file,
   e.g., due to `gh` timeout or network error)
3. Create issues for unfiled entries via
   `scripts/deferred_capture.py`
4. Print summary to stderr:
   `"Deferred items: N filed, M skipped (duplicate)"`
5. Delete the session ledger file

**Ledger schema:**

```json
[
  {
    "title": "...",
    "source": "war-room",
    "filed": true,
    "issue_number": 42,
    "timestamp": "2026-03-19T14:30:22Z"
  }
]
```

### Skill Integration Points

| Skill | Deferral point | Trigger |
|-------|---------------|---------|
| attune:war-room | Phase 5 (Voting + Narrowing) | Rejected COAs with votes. Context: COA summary + rejection rationale from Phase 5 output |
| attune:brainstorm | Phase 5 (Decision + Rationale) | Non-selected approaches from "Rejected Approaches" section (user confirms) |
| imbue:scope-guard | Existing deferral (Worthiness < 1.0) | Replaces bespoke gh issue create |
| imbue:feature-review | Phase 6 (GitHub Integration) | Suggestions scored > 2.5 |
| pensive:unified-review | Phase 4 (Action Plan) | Out-of-scope findings |
| abstract:rollback-reviewer | Regression detection | Converges from bespoke method |
| egregore | Pipeline completion | tangential_idea or discovery (automatic, no confirmation -- respects egregore's "never wait for human input" rule) |

### Leyline Contract

`plugins/leyline/skills/deferred-capture/SKILL.md` defines:

1. CLI interface spec (arguments, types, defaults)
2. Issue template spec (markdown body format)
3. Label taxonomy (names, colors, purposes)
4. Duplicate detection spec (exact title match,
   case-normalized, `in:title` search filter)
5. Output spec (JSON to stdout)
6. Compliance test (dry-run validation snippet)

## File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `sanctum/scripts/deferred_capture.py` | ~80 | Reference implementation |
| `attune/scripts/deferred_capture.py` | ~30 | Attune wrapper |
| `imbue/scripts/deferred_capture.py` | ~30 | Imbue wrapper |
| `pensive/scripts/deferred_capture.py` | ~30 | Pensive wrapper |
| `abstract/scripts/deferred_capture.py` | ~30 | Abstract wrapper |
| `egregore/scripts/deferred_capture.py` | ~30 | Egregore wrapper |
| `leyline/skills/deferred-capture/SKILL.md` | ~60 | Contract |
| `sanctum/hooks/deferred_item_watcher.py` | ~60 | PostToolUse hook |
| `sanctum/hooks/deferred_item_sweep.py` | ~50 | Stop hook |
| War-room module addition | ~30 | Capture instructions |
| Brainstorm module addition | ~20 | Capture instructions |
| Scope-guard module update | ~-10 | Converge to shared script |
| Feature-review module update | ~10 | Converge to shared script |
| Unified-review module update | ~10 | Capture instructions |
| Rollback-reviewer method update | ~-20 | Converge to shared script |
| Egregore pipeline update | ~15 | Capture alongside Discussion |

**Estimated total:** ~400 new lines, ~30 lines removed
from bespoke implementations.

## Migration Notes

### Scope-guard label migration

Scope-guard currently uses the label `scope-guard-deferred`.
The new taxonomy replaces this with `deferred` + `scope-guard`
(two labels). During rollout:

1. Run a one-time migration:
   `gh issue list --label scope-guard-deferred --json number |
   jq -r '.[].number' | xargs -I{} gh issue edit {}
   --add-label deferred --add-label scope-guard`
2. Remove `scope-guard-deferred` from scope-guard's
   `github-integration.md`
3. Optionally delete the old label:
   `gh label delete scope-guard-deferred --yes`

Pre-existing issues created before this migration will not
match `gh issue list --label deferred` until the migration
runs. This is acceptable for a one-time transition.

### Cross-plugin observability

The PostToolUse safety-net hook (owned by sanctum) watches
attune skill outputs (war-room, brainstorm). This is an
intentional cross-plugin observability dependency: sanctum
monitors other plugins' outputs but never imports their
files. If attune's skills have bugs or skip explicit capture,
sanctum's hook provides the fallback. This is the same
pattern used by `skill_execution_logger.py` (abstract)
which already monitors all Skill invocations.

## Out of Scope

- Central deferred-items registry or dashboard (future: could
  use GitHub Projects v2)
- Cross-source deduplication (each source creates independently;
  within-source dedup handled by the script)
- Scoring normalization across plugins (worthiness vs RICE
  vs gap analysis remain source-specific)
- Automatic prioritization of deferred items
- GitHub Discussions integration (egregore already handles
  this; deferred capture focuses on Issues)

## Next Steps

1. Create implementation plan with phased delivery
2. Implement reference script (sanctum) with tests
3. Build safety-net hooks
4. Integrate with skills (one plugin at a time)
5. Add `make verify-deferred-capture` target for compliance
