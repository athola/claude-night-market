# ADR-0019: Retire docs/superpowers/ and Record Its Shipped Design Decisions

**Date**: 2026-07-28
**Status**: Accepted
**Deciders**: Claude Night Market maintainers
**Supersedes**: the ten design and plan files formerly under
`docs/superpowers/`
**Related**: ADR-0018 already carries the tome research engine decision

## Context

The `superpowers` brainstorm-design-plan pipeline writes its working
artifacts to `docs/superpowers/`. Eight design specs and two
implementation plans accumulated there between 2026-03-23 and
2026-07-17, roughly 19,700 words.

Only one of those ten files was ever tracked in git. The other nine were
untracked local scratch, so every checkout held a different set. That
split is the problem: the directory read as a doc of record while
behaving like a build artifact.

Seven of the eight designs shipped. Their skills, rules, and tests are
the source of truth now, and the specs restate them at lower fidelity.
The specs do hold one thing the shipped artifacts do not: the
alternatives that were weighed and rejected. Grepping
`.claude/rules/prefer-invariants-over-fallbacks.md` and
`.claude/rules/ceremony-requires-need.md` for rejected alternatives
returns nothing. The rules record the answer, not the search.

## Decision

Add `docs/superpowers/` to `.gitignore` and stop tracking it. Salvage
two classes of content first:

1. Rejected alternatives and deferred scope from the seven shipped
   designs, recorded below.
2. The one design that never shipped, `slop-clean-before-post`, recorded
   below in full. `docs/backlog/` is itself gitignored, so the ranking
   entry there is a local working note and this ADR is the record.

Everything else in those files (table schemas, task checklists, file
inventories, line-count estimates) is scaffolding that the shipped code
documents better than the spec did. It goes.

## Decisions recorded

### scribe:session-replay, 2026-03-23

Parse Claude Code session JSONL, generate a VHS tape file, delegate GIF
rendering to the existing `scry` plugin.

The tape file is the stable interface. That choice is what keeps the
renderer swappable and the parser format-agnostic, so a Codex parser or
an SVG renderer can be added later without a redesign.

| Deferred from v1 | Reason |
|------------------|--------|
| Codex session format | One parser first; the tape seam absorbs the second |
| SVG, MP4, WebM output | Swap the scry renderer when a consumer asks |
| Web-based preview | No consumer |
| Color schemes beyond VHS built-ins | No consumer |
| Audio tracks, interactive session picker | No consumer |

### leyline:utility, 2026-03-24

A utility function scoring candidate actions by gain against step cost,
uncertainty, and redundancy, living in `leyline` as a shared primitive.
Consumers integrate in advisory mode by default and prescriptive mode by
opt-in, so no existing caller changes behavior on adoption.

Lambda defaults are not arbitrary. They come from Liu, Zhao, and Xu,
"Utility-Guided Agent Orchestration for Efficient LLM Tool Use"
(arXiv:2603.19896, March 2026):

| Lambda | Default | Why that value |
|--------|---------|----------------|
| lambda_1, cost | 1.0 | Baseline weight |
| lambda_2, uncertainty | 0.5 | Weak quality correlation, r = 0.0131 |
| lambda_3, redundancy | 0.8 | Paper measured 10% token savings, no quality loss |

The phased adoption path was deliberate: gate agent count in `do-issue`
and `attune:execute` first, then the `egregore` queue, then `conjure`
model-tier selection, and only then open advisory use to any skill.

### memory-palace v2, 2026-04-07

Hybrid storage. Palace JSON files stay as the human-readable blueprint
holding layout, metaphor, and sensory metadata. A SQLite database holds
entities, residencies, triples, synapses, and traversal data. Scripts
open the file, query, and close. No daemon.

| Rejected | Reason |
|----------|--------|
| ChromaDB or a vector database | Existing optional FAISS already covers the need |
| AAAK abbreviation dialect | Benchmarks showed it regresses retrieval quality |
| MCP server for palace operations | Future work, no current consumer |
| Web UI for visualization | Mermaid already renders in GitHub and VS Code |

Backward compatibility was a hard constraint: existing palace JSON must
keep loading, and migration populates the graph from that existing data
rather than requiring a rewrite.

### attune interactive plan review, 2026-04-13

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Interaction model | Markdown plus terminal review | Works over SSH and phone, no browser |
| Iteration cap | 3 rounds | Bounds token churn, then escalates to war-room or abort |
| Version storage | `.attune/plan-history/` | Browsable markdown, pairs with mission state |
| Feedback structure | Section verdicts, optional typed annotations | Fast from a phone, rich when needed |
| Review granularity | Architecture first, then phases | Most consequential decisions reviewed first |
| War room | Mandatory gate after user approval | Every plan is pressure-tested before execution |
| Bias defense | Strengthen `imbue:justify`, add a leyline contract | Systemic rather than opt-in |

The design studied `plannotator` and declined most of it: no browser
annotation UI, no zero-knowledge encryption or plan sharing, no
Copilot/Gemini/Codex multi-agent support. Those solve distribution
problems this repo does not have.

### prefer-invariants-over-fallbacks, 2026-07-01

Shipped as a behavioral rule in `.claude/rules/`, not a skill. The
design verified the candidate homes before deciding rather than assuming
the gap: `imbue:scope-guard` covers feature scope and over-abstraction
but not defensive-code patterns, `imbue:proof-of-work` enforces
verification rather than invariant design, and
`pensive:safety-critical-patterns` deliberately requires the defensive
checks this rule discourages, which made a stated carve-out mandatory.

| Rejected | Reason |
|----------|--------|
| A full `imbue` skill with modules | Over-engineering for a behavioral guardrail, on an already RED-ZONE branch |
| A PreToolUse hook blocking broad `except` | Too blunt. Boundary code legitimately uses broad handlers, so a static block produces false positives |

The rule teaches the keep-versus-remove distinction because that is the
altitude a static check cannot reach.

One gap was deferred rather than dropped: binding `egregore` and
`ralph-wiggum` outer-loop completion to a non-fakeable signal plus a
human checkpoint. Modifying harness behavior needs explicit sign-off and
is not purely additive. It has since been picked up by
`.claude/skills/night-market-completion-integrity-campaign/`.

### DDD paradigm and ceremony-requires-need, 2026-07-13

Four files across two existing plugins plus one rule. No new plugin, no
changes to the other twelve paradigm skills, no AST detectors (the
ceremony audit is a reading lens), and no refactor of existing repo code
to conform. The rule binds future work only.

Building it surfaced a latent gap in the paradigm test harness worth
recording: `plugins/archetypes/tests/test_paradigm_components.py` drives
its parametrize from a hand-maintained `EXPECTED_COMPONENTS` dict, so a
fourteenth paradigm could land on disk and go silently untested. That
design closed it. Registration in `.claude-plugin/plugin.json` is a
fifth required artifact: a skill absent from that array does not load.

### slop-clean-before-post, 2026-06-17, not shipped

The one design in the directory with no shipped artifact. No `launder`
module exists under `plugins/`. It is recorded here in full because
deleting the spec would otherwise drop it entirely.

**Problem.** The slop rules cover markdown written to disk and a
model-invoked skill. Content drafted and posted at runtime to GitHub
Discussions, Issues, and PR comments never becomes a tracked file, so
nothing intercepts it.

**Goal.** Every craft-and-post pipeline launders drafted content through
a deterministic slop remediation pass before posting. The text that goes
out is the cleaned text.

**Locked decisions.**

1. Posture is fix-then-post. The pipeline detects slop, remediates,
   re-verifies, and posts the cleaned text. A posting run always
   completes and always posts cleaned content.
2. Remediation depth is the deterministic full table. Encode the
   slop-detector remediation table as runnable transforms. Defer only
   explicitly low-confidence patterns (semicolon splice, chiasmus,
   subject-swap) to a report.

**Approach.** A centralized launder library with a subprocess seam. One
module owns the transforms, every poster calls it ahead of posting, and
a rule extends the contract to agent-prose paths that never touch code.

| Rejected | Reason |
|----------|--------|
| Hook interceptor on Bash `gh` calls | Payload parsing is brittle across `--body`, `--body-file`, heredocs, and in-process API calls, and it misses direct API posts. Possible follow-up once the launder seam is proven |
| A rule with per-skill self-check, no code | Convention cannot guarantee deterministic transforms, so it does not honor locked decision 2 |

**Non-goals.** No hook-level interception of `gh` in this iteration, no
LLM-assisted rewriting (deterministic only), no re-linting of files
already on disk, since the docs rule owns that.

**Open questions.** New rule file or fold into `slop-scan-for-docs.md`?
The design defaulted to a new file, since the trigger differs, posting
versus file write. And the `--ci` threshold for posted content: 3.0 to
match the slop-detector default, or tighter for public posts? The design
defaulted to 3.0, to revisit after the pilot.

**Rollout.** Pilot on the three abstract posters, then `sanctum`
PR-comment commands, then `scribe:session-to-post`,
`scribe:voice-generate`, and `minister:create-issue`. Build on a branch
cut from `master` rather than an existing scope-guard RED branch, so the
feature starts from a green base.

## Lessons that generalize

Two findings from the DDD build outlive their design and apply to any
test work in this repo. Both now live where a test author will meet
them, in `plugins/sanctum/skills/validate-pr/SKILL.md` under the
revert-test procedure: a revert harness must assert pytest exit code `1`
specifically, and a content test must normalize whitespace before
matching while anchoring on a clause unique to the passage it guards.
That skill is the operational home. This ADR only records that the
lessons came from the DDD paradigm build and PR #612.

## Consequences

### Positive

- `docs/superpowers/` stops presenting scratch output as documentation.
- Rejected alternatives survive in a doc of record, so a future proposal
  to add the hook, the vector database, or the browser UI meets an
  answer rather than a blank page.
- The undelivered `slop-clean-before-post` design is recorded in a
  tracked file rather than living only in one machine's working tree.

### Negative

- Full design specs are gone. Anything not salvaged here is recoverable
  for the tome spec only, which was the single tracked file, via git
  history. The nine untracked files are recoverable only from a local
  working tree that still has them.
- This ADR compresses six designs into one document, so per-design
  detail is thinner than a dedicated ADR would be. That was the accepted
  trade: six ADRs would have restated the shipped rules at length.

## Status of implementation

- [x] `docs/superpowers/` added to `.gitignore`
- [x] Tracked tome spec removed from the index (ADR-0018 supersedes it)
- [x] Rejected alternatives and deferred scope recorded above
- [x] The unshipped `slop-clean-before-post` design recorded above, with
      a `[DESIGN-001]` ranking note in the local `docs/backlog/queue.md`
- [x] Dangling-reference check in
      `.claude/skills/night-market-research-methodology/SKILL.md`
      extended to cover `docs/backlog/`

## Source

The eight design specs and two implementation plans formerly under
`docs/superpowers/specs/` and `docs/superpowers/plans/`, dated
2026-03-23 through 2026-07-17.
