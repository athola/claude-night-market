# Inclusive Defaults Audit — 1.9.3

**Branch:** `inclusive-default-1.9.3`
**Date:** 2026-04-25
**Goal:** flip every reasonable opt-in flag to default ON,
expose `--no-X` (or equivalent) opt-out, and document the
TRUE-exception list where opt-in must stay.

The 1.9.x cycle established the pattern: ship `--no-insights`,
`--no-agent-teams`, `--no-auto-issues`, `--no-code-review`,
`--no-backup` as opt-outs, with the underlying behavior on
by default. This audit catalogues every remaining surface
and tags it FLIP / KEEP / DOC.

## Legend

- **FLIP** — change default to ON, add `--no-X` opt-out
- **KEEP** — TRUE exception, must stay opt-in (rationale required)
- **DOC** — already inclusive; only docs need to make
  default-ON status more discoverable
- **N/A** — no opt-in flag at this surface

## Already Inclusive (Baseline — 1.9.x)

These shipped with `--no-X` opt-outs and need no change:

- [x] `/sanctum:pr-review` — insights, agent-teams,
  auto-issues, line-comments, capture
- [x] `/sanctum:fix-pr` — insights, agent-teams
- [x] `/sanctum:do-issue` — review-between-tasks, agent-teams
- [x] `/sanctum:prepare-pr` — code-review
- [x] `/conserve:unbloat` — backup branch
- [x] `/attune:war-room` — discussion publishing (Y/n prompt)
- [x] `/abstract:aggregate-logs` — Learning post (config opt-out)
- [x] Imbue vow hooks — registered in `hooks.json`,
  shadow-mode default

## Per-Plugin Checklist

### abstract

Tooling for skill quality, plugin review, and discussion
publishing. Most surfaces already inclusive.

- [ ] **DOC** `post_review_insights.py` — confirm default ON,
  document `--no-insights` opt-out at the script level
  (already wired through `/pr-review`/`/fix-pr`)
- [ ] **DOC** `discussion_enrichment.py` — confirm default ON
  for Phase 6a Learning posts; surface opt-out path in
  `aggregate-logs.md`
- [ ] **FLIP?** `architecture-evolution.md` documents an
  "Experimental → Beta (opt-in) → Stable" lifecycle. Verify
  no specific abstract feature is stuck at "Beta (opt-in)"
  that should graduate.

### archetypes

Architecture paradigm router and sub-skills. Skills are
auto-loaded by the router; no opt-in flags surfaced.

- [ ] **N/A** — no flags

### attune

Project lifecycle. Most flags are positive feature toggles
(`--auto`, `--type`, `--phases`).

- [ ] **DOC** `/attune:mission --auto` — already a
  positive flag (skips checkpoints); current default of
  "ask between phases" is the correct inclusive choice
  (does not erode safety). No change.
- [ ] **DOC** `/attune:project-init --no-git` — already
  inclusive (git init ON by default).
- [ ] **KEEP** `attune:war-room` adversarial expert panel
  — invocation itself is opt-in via `/attune:war-room`,
  which is correct (heavy multi-LLM cost).
- [ ] **DOC** `attune:war-room` discussion publishing —
  already inclusive (Y/n prompt with Y default).

### cartograph

Mermaid diagram generator. No opt-in feature flags found;
each `/visualize <type>` is its own command.

- [ ] **N/A** — no flags

### conjure

Delegation to Gemini/Qwen CLIs.

- [ ] **KEEP** delegation framework itself — requires
  external CLI (`gemini`, `qwen`) installed and
  authenticated. No reasonable default; flipping is
  impossible, not just unwise.
- [ ] **DOC** mark `optional_dependencies` clearly so users
  know provider CLIs are not auto-installed.

### conserve

Context/token/CPU/GPU conservation tooling.

- [ ] **DOC** `Skill(conserve:clear-context)` auto-clear —
  already triggered automatically at 80% context. Confirm
  no opt-in env var is required for default behavior.
- [ ] **DOC** `/conserve:unbloat --no-backup` — already
  inclusive.
- [ ] **FLIP?** `Skill(conserve:context-map) --no-cache`,
  `--no-wiki` — these are existing opt-outs but verify
  cache/wiki are actually default ON.
- [ ] **FLIP?** `Skill(conserve:mcp-code-execution)` —
  `ENABLE_CLAUDEAI_MCP_SERVERS` default is set by
  Anthropic (default ON in 2.1.63+). Document opt-out
  rather than opt-in.

### egregore

Autonomous orchestrator. Three opt-in surfaces, each with
distinct rationale.

- [ ] **KEEP** `pipeline.auto_merge: false` —
  irreversible-ish action (revert PR is messy). Egregore
  is opt-in at `/egregore:summon`; auto-merge specifically
  gates the no-human-loop transition. **Recommend
  staying opt-in**.
- [ ] **KEEP** Tier 2 webhooks (Slack/Discord/ntfy.sh) —
  no reasonable default URL. Cannot flip.
- [ ] **KEEP** `/egregore:install-watchdog` — installs
  OS-level launchd plist or systemd unit. Persists outside
  Claude Code.
- [ ] **DOC** Tier 1 GitHub issue alerts — confirm all five
  alert categories (`crash`, `rate_limit`,
  `pipeline_failure`, `completion`, `watchdog_relaunch`)
  default ON in `config.json`.
- [ ] **FLIP** `pipeline.skip_brainstorm_for_issues: true`
  — already default true (skips brainstorm for issues
  that have a clear spec). Verify wording so users
  understand it's the inclusive default.

### gauntlet

Code knowledge base + challenge sessions.

- [ ] **DOC** `YamlScorer` (zero deps) is the default —
  already inclusive.
- [ ] **N/A** — no further opt-in flags

### herald

Marketplace metadata helpers. No opt-in flags surfaced in
the README.

- [ ] **N/A** — no flags

### hookify

Behavioral rules framework. Each rule is individually
installed via `/hookify:install <rule>`.

- [ ] **DOC** "rules enabled by default" set — confirm the
  README enumerates exactly which bundled rules ship ON
  (e.g., branch protection, secret blockers).
- [ ] **KEEP** individual destructive rules
  (`block-rm-rf`, `require-tests`) — each rule is its own
  hook; bundling all of them ON would surprise users with
  blocks for legitimate commands. **Recommend the
  current per-rule install model**.
- [ ] **FLIP?** Audit catalog: which rules are "obviously
  safe to default ON" (read-only audits, warnings) vs
  "blocking" (commits, file deletes). Consider a
  `safe-defaults` rule bundle that auto-installs.

### imbue

Workflow methodology + vow enforcement.

- [ ] **DOC** Vow hooks default to shadow mode (warn).
  **KEEP** blocking opt-in via `VOW_SHADOW_MODE=0` —
  shadow-default IS the inclusive choice. Flipping to
  block-default would interrupt legitimate workflows on
  first install.
- [ ] **DOC** `Skill(imbue:scope-guard)` advisory mode —
  already default; prescriptive mode is opt-in via
  frontmatter (correct).
- [ ] **DOC** `Skill(imbue:workflow-monitor) enabled: true`
  — already default ON.
- [ ] **FLIP?** `tdd_bdd_gate.py` PreToolUse hook —
  enforces test-first. Verify shadow-mode default and
  document `--no-tdd-gate` style override.

### leyline

Cross-cutting contracts and shared patterns.

- [ ] **KEEP** `Skill(leyline:utility)` prescriptive mode
  — opt-in via frontmatter is correct (advisory is the
  inclusive default).
- [ ] **DOC** `additive-bias-defense` — applies whenever
  loaded; document that it's load-by-reference, not a
  toggle.

### memory-palace

Spatial knowledge structures.

- [ ] **DOC** Agent `memory` frontmatter — opt-in per
  agent is the correct model (per-agent activation is
  finer-grained than global).
- [ ] **DOC** `Skill(memory-palace:knowledge-intake)`
  WebFetch on shared URLs — confirm fetching is gated by
  user invocation, not auto-fired on every URL mention.
- [ ] **FLIP?** Default vitality scoring on garden notes —
  verify `update_vitality_scores.py --dry-run` is opt-in
  for dry-run only, real updates happen by default.

### minister

GitHub issue management.

- [ ] **DOC** `--repo` defaults to current repository —
  inclusive default already.
- [ ] **DOC** Interactive template mode — already gated by
  user input; flipping to "always interactive" would slow
  scripted invocations.
- [ ] **N/A** — no further opt-in flags

### oracle

ONNX inference daemon.

- [ ] **KEEP** `/oracle:setup` provisioning — heavy install
  (Python 3.11+ venv, 50MB+ onnxruntime download,
  background HTTP daemon). Must stay opt-in.
- [ ] **DOC** Make the install footprint explicit in the
  README so users opting in know what they're getting.

### parseltongue

Python tooling agents (linter, optimizer, tester).

- [ ] **N/A** — agents are dispatched on demand; no
  opt-in flags

### pensive

Code review modes.

- [ ] **DOC** `Skill(pensive:tiered-audit)` — Tier 1
  default, Tier 2/3 escalation requires explicit user
  approval. **KEEP** this gate (Tier 3 = full codebase
  scan; should be explicit per
  `.claude/rules/plan-before-large-dispatch.md`).
- [ ] **DOC** `Skill(pensive:blast-radius)` — runs on
  changed files automatically when invoked; confirm no
  hidden opt-in.

### phantom

Computer Use API for desktop control.

- [ ] **KEEP** `phantom:control-desktop` — uses Computer
  Use API to take screenshots and synthesize keyboard/
  mouse input. Cross-process side effects. Must remain
  explicit invocation only.

### sanctum

Git/PR workflow primitives. Most surfaces already inclusive
(see baseline above).

- [ ] **DOC** `/sanctum:acp` (auto-commit-push) — verify
  push step is gated and document it. Pushing is harder
  to reverse than committing.
- [ ] **DOC** `/sanctum:prepare-pr` — already inclusive
  (`--no-code-review`, `--skip-updates` opt-outs).
- [ ] **FLIP?** `/sanctum:update-docs --skip-slop` —
  slop-scan is non-blocking by default per command doc;
  verify default is "scan and warn" not "skip silently".
- [ ] **DOC** `/sanctum:pr-review --skip-version-check`,
  `--skip-doc-review` — these are opt-outs of default-ON
  checks; already inclusive.
- [ ] **FLIP** `/sanctum:resolve-threads` — verify
  resolution is the default behavior when called; if
  there's a `--dry-run` it should already be opt-in.

### scribe

Voice profiling and prose generation.

- [ ] **DOC** `Skill(scribe:slop-detector)` — already
  invoked by `.claude/rules/slop-scan-for-docs.md`
  automatically after markdown writes. Inclusive default.
- [ ] **DOC** Voice profiles are per-user; correct model.
- [ ] **N/A** — no further opt-in flags

### scry

Recording (VHS/Playwright) and GIF generation.

- [ ] **N/A** — explicit invocation per recording

### spec-kit

Spec-driven development.

- [ ] **DOC** `/speckit-tasks` — TDD task generation is
  opt-in per the doc ("Tests are OPTIONAL: only generate
  test tasks if explicitly requested"). **Consider
  FLIP** so TDD tasks generate by default with `--no-tdd`
  opt-out, given the project's iron-law stance.
- [ ] **KEEP** `/speckit-constitution` — auto-applying
  every constitution from a marketplace template would
  override user intent. Explicit invocation is correct.
- [ ] **DOC** Auto-chain forward (brainstorm → specify →
  plan) — already default; users use `--standalone` to
  opt out of the chain. Inclusive default.

### tome

Multi-source research.

- [ ] **DOC** `/tome:research` runs all channels (code,
  discourse, papers) by default — inclusive already.
- [ ] **N/A** — no further opt-in flags

## TRUE Exceptions Summary

The following must stay opt-in. Each has a concrete reason
stronger than "user might be surprised":

| Surface | Why opt-in must stay |
|---|---|
| `/oracle:setup` | Heavy install (Python venv, 50MB+ onnxruntime, background daemon) |
| Egregore `auto_merge` | Irreversible-ish merge without human review |
| Egregore Tier 2 webhooks | No reasonable default URL exists |
| `/egregore:install-watchdog` | Installs OS-level launchd/systemd unit |
| Conjure delegation (Gemini/Qwen) | Requires external CLI auth, no default |
| Phantom desktop control | Cross-process side effects via Computer Use API |
| Hookify destructive rules | Each rule can interrupt legitimate commands |
| Spec-kit constitution | Auto-applying overrides user project rules |
| Pensive tiered-audit Tier 3 | Full-codebase scan, explicit per existing rule |
| Imbue vow blocking mode | Shadow-default IS inclusive; blocking interrupts work |
| Leyline utility prescriptive mode | Advisory default is inclusive; prescriptive needs frontmatter consent |

## Proposed Follow-Up PRs

Based on the audit, the actionable flips group into three
PRs of decreasing certainty:

1. **PR-A: doc clarifications only**
   Sweep all "DOC" entries above and ensure each plugin
   README + relevant skill/command doc clearly states the
   default-ON behavior and the opt-out flag. No code
   changes; pure markdown edits. Low risk.

2. **PR-B: targeted flips with TDD**
   - Spec-kit: TDD tasks default ON, `--no-tdd` opt-out
   - Sanctum update-docs: slop-scan default ON
   - Hookify: introduce `safe-defaults` rule bundle
   Each flip needs a failing test first per iron law.

3. **PR-C: TRUE-exception documentation**
   Add a `docs/inclusive-defaults.md` explaining the
   TRUE-exception list as project policy, so future
   features have a written rubric for when opt-in is
   appropriate.

## How to use this checklist

- Each `[ ]` item becomes a sub-task in a follow-up issue
  or PR
- Cross off `[x]` once the change ships and CHANGELOG
  records it
- The "FLIP?" entries are the ones that need your
  judgment call before implementation
- The "KEEP" entries are the TRUE exceptions; they go
  into `docs/inclusive-defaults.md` as the project policy
