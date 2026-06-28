# Dogfooding and Feature Review (2026-06-28)

## Scope

Dogfood the interactive surfaces of the night-market plugin
ecosystem and review recently shipped features. Focus areas:

- The repo's own dogfooding harness (`make plugin-check`)
- The palace-index CLI shipped in mission
  `palace-index-methods-2026-05-27`
- The attune mission orchestrator exercised in this session

Directive overrides in effect: scope-guard relaxed, ultrathink
on. Safety Floor kept: dry-run defaults honored, no `--apply`,
no `--no-verify`, every claim tied to a command or path.

## Method

- tmux 3.4 drove the long-running harness and the palace CLI.
  Detached sessions, `send-keys`, log capture. tmux was the
  right tool: `make plugin-check` is long-lived and terminal
  bound, so a detached session let it run while the palace CLI
  ran in parallel.
- A tome research agent ran a multi-channel sweep (GitHub, HN,
  arXiv, Semantic Scholar) on dogfooding and feature-review
  practice for agent tooling.
- Coverage was reviewed from `coverage.xml` source data.

## Evidence index

[E1] `make plugin-check` reached `plugins/scry`, then hung
     (see F-G). Zero explicit `(plugin-check failed)` lines,
     but real defects were masked as skips (F-A, F-B, F-C).
[E2] `uv run python scripts/memory_palace_cli.py index report`
     shows 10 entries, 0 orphans, 100% inert pending. The
     mission-state evidence for the same file said 484/493
     inert and 90 orphans. See F-D.
[E3] `index promote` dry-run ends with: "DRY RUN - no changes
     written. Re-run with --apply to commit." Safety confirmed.
[E4] `plugins/conserve/Makefile:128` references
     `../conservation/...`; the directory is `plugins/conserve`.
     Masked by `2>/dev/null || echo "Token estimator test
     skipped"`. See F-A.
[E5] `plugins/parseltongue/Makefile:179` runs
     `ruff check parseltongue/`. That path does not exist
     (source is at `src/parseltongue/`). E902 masked by
     `|| echo "Linting clean or ruff not configured"`. See F-B.
[E6] `coverage.xml` reports line-rate 0.0% across 17 modules,
     all scripts and check tooling. Plugin source is absent.
     See F-E.
[E7] `make plugin-check` hung 8+ minutes at scry on
     `npm exec playwright --version` (process 1338165). See F-G.

## Findings

### F-A: stale `conservation` path drift (real defect)

`plugins/conserve/Makefile` lines 105, 108, 128 reference
`../conservation/...`. The directory is `plugins/conserve`.
The token-estimator demo fails with "File not found" and is
masked as "Token estimator test skipped".

Fix: change the three lines to `../conserve/...`, or use
`$(CURDIR)` for the local case.

### F-B: parseltongue demo-lint targets a missing path (real defect)

`plugins/parseltongue/Makefile:179` runs
`ruff check parseltongue/`. From `plugins/parseltongue/` that
path does not exist. Source lives at `src/parseltongue/`. ruff
returns E902 io-error, masked as "Linting clean or ruff not
configured".

Fix: target `src/parseltongue/` (or `.`), and stop masking
E902 as success.

### F-C: sanitized optimism in plugin Makefiles (systemic)

F-A and F-B share one pattern:

    cmd 2>/dev/null || echo "benign fallback"

A real failure (missing file, io-error) prints a harmless
message and the target exits 0. The harness then reports zero
failures. This is the "sanitized optimism" anti-pattern (tome
F5.1) at the harness layer, and it defeats the point of a
dogfooding check. The repo ships a `silent-failure-hunter`
agent for this class of bug in code. The same lens should
cover Makefile recipes.

Fix: separate "tool absent, skip with reason" from "tool ran
and failed, propagate the exit code". Drop the blanket
`2>/dev/null`.

### F-D: mission-state evidence drift (staleness)

The live index has 10 entries and 0 orphans (E2). Mission
`palace-index-methods-2026-05-27` recorded evidence of 484/493
inert entries and 90 orphans against the same file. The index
file is the one marked modified in git. The recorded evidence
is no longer reproducible.

Fix: refresh mission-state evidence when the index changes, or
tag each evidence block with the index checksum it was taken
against.

### F-E: coverage.xml scope is misleading (tooling)

`coverage.xml` reports 0% on 17 modules. All 17 are scripts
and check tooling. Plugin source (for example
`index_analytics.py`, `index_promoter.py`) is absent. A reader
could conclude the palace work is uncovered, when it is simply
out of scope for this file.

Fix: label the artifact's scope, generate per-plugin coverage
in CI, or drop the misleading root file.

### F-F: Playwright path has no target here (environment)

No web app ships in this repo, and no Chrome or Chromium binary
exists in this WSL2 host (the Chrome MCP auto-start failed).
The browser-automation track is dead here. tmux carried the
interactive testing load instead. The directive "playwright
for browser/console apps" assumes a browser surface exists. In
this codebase it does not.

### F-G: scry plugin-check hangs on the playwright probe (critical)

`plugins/scry` plugin-check dependency step runs
`npx playwright --version`. In this offline or slow-network
host, `npm exec` blocks trying to resolve the package, with no
timeout. The whole `make plugin-check` run hung at scry for
8+ minutes and never reached spec-kit or tome. stdout and
stderr are redirected, so the hang is silent (E7).

This is the most damaging finding: a dogfooding harness that
hangs on its own dependency probe is not safe to run in CI or
unattended.

Fix: replace `npx playwright --version` with a bounded check
(`timeout 10 command -v playwright`, or test the npm package
without network). Add an overall timeout to `make plugin-check`
so one hanging plugin cannot stall the run.

## Positive confirmations

- Palace `index` CLI advertises dry-run defaults in `--help`
  and honors them (E3). `report` and `promote` outputs agree:
  `[0.790]` in the report equals `score=0.79` in promote. The
  safety posture is self-evidencing from the help text.
- attune directive-override parsing worked. "ignore scope
  guard" and "ultrathink" were recognized and the orchestrator
  stopped asking for phase checkpoints. The prior mission-state
  shows the same machinery recorded `directive_overrides` on
  2026-05-27.
- attune state-detection found all artifacts and the
  mission-state file. Progressive-loading token costs are
  documented per mission type. Good observability.

## Meta gap: mission types omit review work

attune mission types are full, standard, tactical, quickfix.
All assume building from artifacts. A dogfooding or
feature-review effort fits none. The orchestrator handled it
through directive overrides, but a `review` mission type (no
build artifacts required, evidence-driven output) would be a
cleaner fit and is a candidate feature.

## Research-backed recommendations (tome)

Ranked by fit to this ecosystem:

1. Activation reliability. The ecosystem ships 100+ skills.
   tome F2.1: Claude does near-keyword matching at the
   activation layer. A forced-eval hook lifted activation from
   50-55% to 100% (Scott Spence, $5.59 over about 250 runs).
   The repo's `skill-graph-audit` and `skills-eval` skills are
   the natural home for a forced-eval gate.

2. Discovery-budget truncation. tome F4.1: the skill Discovery
   budget is about 16,000 characters, and skills past it are
   silently dropped (one report showed 42 of 63 displayed).
   With this many skills, silent truncation is a live risk.
   Add a layer-count guard. The research rule "audit when any
   layer exceeds 10 skills" applies directly.

3. Hook latency. tome F4.4: a Node hook costs 50-60ms
   cold-start and they compound. The memory-palace Stop hook
   has an 8.5s budget. Audit hook cold-starts and shim heavy
   ones to background.

4. Sanitised optimism. tome F5.1: builder and verifier must be
   separate sessions. F-C above is the local instance. Point
   `silent-failure-hunter` at Makefiles as well as code.

5. tmux for evidence. tome cites drmaciver (2015) and the
   fcoury tmux-tui-testing skill. This session validated tmux
   as the correct tool for long-running, terminal-bound
   dogfooding here.

## Recommended next actions

1. Fix F-G first. Add a timeout to the scry playwright probe
   and an overall timeout to `make plugin-check`. Until then
   the harness is unsafe unattended.
2. Fix F-A and F-B (one-line Makefile edits each).
3. Fix F-C by removing blanket `2>/dev/null || echo` masks, or
   by splitting skip from failure. Most important after F-G: it
   is what makes `make plugin-check` trustworthy.
4. Refresh or checksum-tag mission-state evidence (F-D).
5. Scope-label or remove the misleading `coverage.xml` (F-E).
6. Open a discussion for a `review` mission type in attune.
7. Prototype a forced-eval activation gate (recommendation 1).

## Fixes applied and verified (2026-06-28)

F-A, F-B, and F-G were fixed right after the review. Each was
proven by re-running the affected target, not by inspection.

- F-A FIXED [E8]: `plugins/conserve/Makefile:105,108,128` now
  reference `../conserve/`. The token-estimator command runs
  and reports "Total tokens: 1,456" for the file that was
  previously "not found". No `../conservation/` refs remain in
  `plugins/`.
- F-B FIXED [E9]: `plugins/parseltongue/Makefile:179` now
  targets `src/parseltongue/`. `make -C plugins/parseltongue
  demo-lint` runs with no E902 io-error.
- F-G FIXED [E10,E11]: `plugins/scry/Makefile` dep-check uses
  `npx --no-install playwright --version`, which fast-fails
  instead of fetching. `make -C plugins/scry check-deps` now
  exits 0 in well under 30s (it hung 8+ minutes before). The
  root `make plugin-check` loop now bounds each plugin with
  `timeout 180`, so any future hang surfaces as
  "(plugin-check failed or timed out)" instead of stalling the
  whole run.

Deferred to a focused follow-up (see Recommended next actions):
F-C systemic mask cleanup, F-D mission-state evidence refresh,
F-E coverage scope label, the attune `review` mission type, and
the forced-eval activation gate.

## Deferred items resolved (2026-06-28)

- F-C PARTIALLY FIXED: removed failure-masking from the
  verification runs that needed it most. `plugins/scribe/Makefile`
  `test` and `test-coverage` no longer swallow pytest output and
  no longer print "No tests found" on failure. Verified [E12]:
  `make -C plugins/scribe test` runs 700 tests (passing, exit 0)
  with output visible, and `test-coverage` shows the full table.
  The scribe suite is not "markdown-only" as its typecheck
  comment claims; it is 637 statements at 93-95% coverage. The
  remaining 30-plus `|| echo` instances across plugins are
  legitimate (presence probes, empty-result handlers, intentional
  "skill-only command, no unit tests" messages) and were left in
  place on purpose. A blind sweep would have broken them.
- F-D FIXED: added an `evidence_provenance` field to
  `.attune/mission-state.json` marking E1 as a 2026-05-27
  point-in-time claim and noting the live index has since changed
  to 10 entries. Historical evidence is preserved, not overwritten.
  JSON re-validated after the edit.
- F-E NON-ISSUE at repo level: `coverage.xml` is untracked and
  already in `.gitignore` (line 50). It is a local build artifact,
  never shipped, so its misleading 0% never reaches consumers. No
  repo change needed. A local `rm coverage.xml` clears it; it
  regenerates on the next coverage run.

## Sources

- Scott Spence, "How to make Claude Code skills activate
  reliably": https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably
- Scott Spence, "Measuring Claude Code skill activation with
  sandboxed evals": https://scottspence.com/posts/measuring-claude-code-skill-activation-with-sandboxed-evals
- shimo4228, "15 days of skill sprawl in Claude Code":
  https://dev.to/shimo4228/15-days-of-skill-sprawl-in-claude-code-lessons-from-3-audits-27em
- HN discussion (sanitized optimism, hook latency):
  https://news.ycombinator.com/item?id=47602986
- HN discussion (Anthropic "antfooding"):
  https://news.ycombinator.com/item?id=44678535
- D. R. MacIver, "Using tmux to test your console applications"
  (2015): https://drmaciver.com/2015/05/using-tmux-to-test-your-console-applications/
