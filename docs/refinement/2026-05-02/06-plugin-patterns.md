# Plugin-Specific Pattern Findings

Scope: 23 plugins under `plugins/`, 186 SKILL.md files,
8 shell hooks, plus their modules and src trees.

## Summary

- Delegation stubs (large bodies referencing other skills): 5
- Module explosions (>=10 modules in one skill): 4
- Oversized modules (>500 lines): 12
- Oversized SKILL.md (>500 lines): 4
- Modules-dir-but-bloated-SKILL (>=200 body lines with sibling
  modules dir): 15 (top 5 listed)
- Dead Python references: 1 confirmed (placeholder text)
- Skill metadata problems: 0
- Plugin manifest problems: 0
- Hook issues: 6 oversized (>200 lines, should delegate to
  Python). All 8 hooks have `set -euo pipefail` (initial
  detection was a false positive: directive sits below the
  header comment block).

## Findings

### P-01: `mcp-code-execution` SKILL has unfilled template placeholder

- **Type**: dead-python-ref
- **Impact**: HIGH
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/conserve/skills/mcp-code-execution/SKILL.md:47-50`
- **Issue**: Quick Start section instructs the user to run
  `python -m module_name` and `python -m module_name --help`.
  The literal string `module_name` is a scaffolding placeholder
  that was never replaced. There is no module of that name and
  the conserve plugin has no `src/` tree at all.
- **Proposal**: Either delete the Basic Usage block (the skill
  is invoked via `Skill(...)`, not a CLI), or replace with the
  actual entry point. Verify with `ls plugins/conserve/src` —
  no such directory exists.
- **Evidence**: `[E1]`
  ```
  $ rg "python -m module_name" plugins/conserve/skills/mcp-code-execution/SKILL.md
  47:python -m module_name
  50:python -m module_name --help
  $ ls plugins/conserve/src
  ls: cannot access 'plugins/conserve/src': No such file or directory
  ```

### P-02: `slop-detector` SKILL is 451 lines despite 19 modules

- **Type**: oversized-module
- **Impact**: HIGH
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**: `plugins/scribe/skills/slop-detector/SKILL.md`
- **Issue**: SKILL.md is 451 lines and references 19 sibling
  modules in frontmatter, yet still inlines the full Tier 1/2/3
  vocabulary tables, em-dash counter, sycophantic phrase list,
  and density formula. The content the modules are supposed to
  hold lives in the SKILL.md too, defeating progressive loading.
- **Proposal**: Cut SKILL.md to a thin hub (<150 lines) that
  loads `vocabulary-patterns`, `structural-patterns`, and
  `identity-and-voice-leaks` on demand. Move the Tier 1/2/3
  tables into `vocabulary-patterns.md` (they already belong
  there per the module name).
- **Evidence**: `[E2]`
  ```
  $ wc -l plugins/scribe/skills/slop-detector/SKILL.md
  451 plugins/scribe/skills/slop-detector/SKILL.md
  $ rg -c "modules:" plugins/scribe/skills/slop-detector/SKILL.md
  1
  $ ls plugins/scribe/skills/slop-detector/modules | wc -l
  19
  ```

### P-03: `hook-authoring` SKILL is 706 lines (largest in repo)

- **Type**: oversized-module
- **Impact**: HIGH
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**: `plugins/abstract/skills/hook-authoring/SKILL.md`
- **Issue**: 706-line SKILL.md with 48 sub-headings, plus a
  sibling `modules/` directory containing 5 already-extracted
  modules (`hook-types.md`, `performance-guidelines.md`,
  `scope-selection.md`, `sdk-callbacks.md`, `testing-hooks.md`).
  The SKILL still inlines hook event types, performance
  guidance, and scope-selection content while saying
  "See modules/X.md for detailed guidance".
- **Proposal**: Move duplicated content into the existing
  modules. SKILL should be <200 lines: hub + load directives.
- **Evidence**: `[E3]`
  ```
  $ wc -l plugins/abstract/skills/hook-authoring/SKILL.md
  706 plugins/abstract/skills/hook-authoring/SKILL.md
  $ rg "^## |^### " plugins/abstract/skills/hook-authoring/SKILL.md | wc -l
  48
  $ ls plugins/abstract/skills/hook-authoring/modules
  hook-types.md  performance-guidelines.md  scope-selection.md
  sdk-callbacks.md  testing-hooks.md
  ```

### P-04: `knowledge-intake` SKILL is 704 lines

- **Type**: oversized-module
- **Impact**: HIGH
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**: `plugins/memory-palace/skills/knowledge-intake/SKILL.md`
- **Issue**: 704-line SKILL.md with 5 modules already extracted.
  Body content (677 lines after frontmatter) covers evaluation,
  curation, pruning, and storage patterns inline despite the
  matching modules existing.
- **Proposal**: Cut to a hub + load directives. Migrate inline
  evaluation tables to `evaluation-rubric.md`, pruning steps to
  `pruning-workflows.md`.
- **Evidence**: `[E4]`
  ```
  $ wc -l plugins/memory-palace/skills/knowledge-intake/SKILL.md
  704 plugins/memory-palace/skills/knowledge-intake/SKILL.md
  $ ls plugins/memory-palace/skills/knowledge-intake/modules
  discussion-promotion.md  evaluation-rubric.md  konmari-tidying.md
  pruning-workflows.md  storage-patterns.md
  ```

### P-05: `tutorial-updates` SKILL is 628 lines

- **Type**: oversized-module
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**: `plugins/sanctum/skills/tutorial-updates/SKILL.md`
- **Issue**: 628 lines with only 3 sibling modules. SKILL body
  (~599 lines) carries content that should live alongside
  `manifest-parsing.md`, `markdown-generation.md`,
  `tape-validation.md`.
- **Proposal**: Add modules for VHS workflow, Playwright workflow,
  and dual-tone narrative; move inline content there.
- **Evidence**: `[E5]`
  ```
  $ wc -l plugins/sanctum/skills/tutorial-updates/SKILL.md
  628 plugins/sanctum/skills/tutorial-updates/SKILL.md
  $ ls plugins/sanctum/skills/tutorial-updates/modules | wc -l
  3
  ```

### P-06: `pr-review` SKILL is 582 lines

- **Type**: oversized-module
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**: `plugins/sanctum/skills/pr-review/SKILL.md`
- **Issue**: 582-line SKILL.md with 7 sibling modules. Body
  (~536 lines) covers PR hygiene, comment guidelines, and
  insight generation inline despite matching modules.
- **Proposal**: Migrate inline guidance into existing modules
  (`comment-guidelines.md`, `pr-hygiene.md`,
  `insight-generation.md`). Target SKILL <200 lines.
- **Evidence**: `[E6]`
  ```
  $ wc -l plugins/sanctum/skills/pr-review/SKILL.md
  582 plugins/sanctum/skills/pr-review/SKILL.md
  $ ls plugins/sanctum/skills/pr-review/modules
  comment-guidelines.md  educational-insights.md  github-comments.md
  insight-generation.md  knowledge-capture.md  pr-hygiene.md
  version-validation.md
  ```

### P-07: `sdk-callbacks` module is 621 lines

- **Type**: oversized-module
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**: `plugins/abstract/skills/hook-authoring/modules/sdk-callbacks.md`
- **Issue**: Single module file at 621 lines is itself a SKILL-
  sized blob. The whole point of progressive loading is broken
  if a leaf module is the same size as a hub SKILL.
- **Proposal**: Split into `sdk-callback-types.md`,
  `sdk-callback-examples.md`, `sdk-callback-edge-cases.md`.
- **Evidence**: `[E7]`
  ```
  $ wc -l plugins/abstract/skills/hook-authoring/modules/sdk-callbacks.md
  621 plugins/abstract/skills/hook-authoring/modules/sdk-callbacks.md
  ```

### P-08: `performance-guidelines` module is 610 lines

- **Type**: oversized-module
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**: `plugins/abstract/skills/hook-authoring/modules/performance-guidelines.md`
- **Issue**: Same pattern as P-07. A 610-line "module" is a
  document, not a leaf reference.
- **Proposal**: Split by performance domain (latency, memory,
  startup, IPC).
- **Evidence**: covered by `[E7]` from sibling listing.

### P-09: `scope-selection` module is 603 lines

- **Type**: oversized-module
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**: `plugins/abstract/skills/hook-authoring/modules/scope-selection.md`
- **Issue**: Third oversized module under `hook-authoring`.
  Pattern: this entire skill's modules are bloated.
- **Proposal**: Treat the hook-authoring skill as a single
  refactor: each oversized module gets split.
- **Evidence**: `[E8]`
  ```
  $ find plugins/abstract/skills/hook-authoring/modules -name "*.md" \
      -exec wc -l {} \; | sort -rn
  621 .../sdk-callbacks.md
  610 .../performance-guidelines.md
  603 .../scope-selection.md
  503 .../hook-types.md
  ```

### P-10: `progressive-disclosure` module is 593 lines

- **Type**: oversized-module
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**: `plugins/abstract/skills/skill-authoring/modules/progressive-disclosure.md`
- **Issue**: A module documenting progressive disclosure that is
  itself 593 lines is self-contradicting.
- **Proposal**: Split into `progressive-disclosure-rules.md` and
  `progressive-disclosure-examples.md`.
- **Evidence**: `[E9]`
  ```
  $ wc -l plugins/abstract/skills/skill-authoring/modules/progressive-disclosure.md
  593 .../progressive-disclosure.md
  ```

### P-11: `subagent-coordination` module is 585 lines

- **Type**: oversized-module
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**: `plugins/conserve/skills/context-optimization/modules/subagent-coordination.md`
- **Proposal**: Split by coordination concern (dispatch,
  isolation, output merging, error recovery).
- **Evidence**: `[E10]`
  ```
  $ find plugins/conserve/skills/context-optimization/modules -name "*.md" \
      -exec wc -l {} \; | sort -rn | head -3
  585 .../subagent-coordination.md
  ```

### P-12: `evaluation-criteria` and `evaluation-framework` overlap

- **Type**: module-explosion
- **Impact**: HIGH
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/abstract/skills/skills-eval/modules/{evaluation-criteria,evaluation-framework}.md`
- **Issue**: Both modules define a scoring rubric for skills.
  `evaluation-criteria.md` (454 lines) uses MCDA / AHP weighting:
  compliance 30%, effectiveness 30%, maintainability 20%,
  performance 20%. `evaluation-framework.md` (91 lines) defines
  a parallel rubric: priority levels (Critical/High/Medium/Low),
  score bands (0-25, 26-50, ...), and component categories
  (Structure Compliance 25 pts, Content Quality 25 pts, ...).
  A reader picking one over the other gets a different rubric.
- **Proposal**: Pick one rubric (the MCDA-based one in
  `evaluation-criteria.md` is more rigorous), delete the other,
  redirect callers.
- **Evidence**: `[E11]`
  ```
  $ rg -c "Structure Compliance" \
      plugins/abstract/skills/skills-eval/modules/evaluation-{criteria,framework}.md
  evaluation-criteria.md:1
  evaluation-framework.md:1
  ```

### P-13: `skills-eval` has 11 modules with naming overlap

- **Type**: module-explosion
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**: `plugins/abstract/skills/skills-eval/modules/`
- **Issue**: 11 modules, multiple covering similar surfaces:
  `evaluation-criteria.md` + `evaluation-framework.md` +
  `evaluation-workflows.md` (three "evaluation-*"); `integration.md`
  + `integration-testing.md` (two "integration-*"). The naming
  alone signals coverage thrash.
- **Proposal**: After resolving P-12, audit the remaining 9 for
  similar collisions. Consolidate to <8 modules.
- **Evidence**: `[E12]`
  ```
  $ ls plugins/abstract/skills/skills-eval/modules/
  advanced-tool-use-analysis.md  authoring-checklist.md
  evaluation-criteria.md  evaluation-framework.md
  evaluation-workflows.md  integration-testing.md
  integration.md  performance-benchmarking.md
  pressure-testing.md  trigger-isolation-analysis.md
  troubleshooting.md
  ```

### P-14: `slop-detector` modules dir has 19 files

- **Type**: module-explosion
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**: `plugins/scribe/skills/slop-detector/modules/`
- **Issue**: 19 modules — highest in the repo. Some are very
  scoped (`i18n-patterns.md`, `progress-indicators.md`); these
  read as a fan-out of every section heading rather than a
  load-on-demand structure. Hub-and-spoke loses utility when
  spokes proliferate.
- **Proposal**: Group adjacent modules. Candidates:
  `vocabulary-patterns.md` + `structural-patterns.md` ->
  `pattern-detection.md`; `progress-indicators.md` +
  `metrics.md` -> `reporting.md`. Target <12 modules.
- **Evidence**: `[E13]`
  ```
  $ ls plugins/scribe/skills/slop-detector/modules | wc -l
  19
  ```

### P-15: `rust-review` has 16 modules

- **Type**: module-explosion
- **Impact**: LOW
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**: `plugins/pensive/skills/rust-review/modules/`
- **Issue**: 16 modules. Unlike P-14, manual inspection shows
  each module is well-scoped to a distinct Rust anti-pattern
  (async-slop, iterator-and-allocation-slop, test-slop, etc.).
  Flagged for awareness but lower priority.
- **Proposal**: No action unless content audit finds duplication.
  Document that 16 fine-grained modules is the intended design.
- **Evidence**: `[E14]`
  ```
  $ ls plugins/pensive/skills/rust-review/modules | wc -l
  16
  ```

### P-16: `mission-orchestrator` has 12 modules

- **Type**: module-explosion
- **Impact**: LOW
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**: `plugins/attune/skills/mission-orchestrator/modules/`
- **Issue**: 12 modules. Sample inspection shows each has a
  distinct concern (mission-state, phase-routing, plan-versioner,
  trust-tier, etc.) -- looks intentional. SKILL.md is 330 lines.
- **Proposal**: No action. Listed for completeness against the
  >=10 modules threshold.
- **Evidence**: `[E15]`
  ```
  $ ls plugins/attune/skills/mission-orchestrator/modules | wc -l
  12
  ```

### P-17: 6 hooks exceed 200 lines (delegate to Python)

- **Type**: hook
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: MEDIUM
- **Location**: multiple (see evidence)
- **Issue**: Six bash hooks exceed the 200-line guidance. Bash
  past this size becomes hard to test and audit. Note: all 8
  hooks DO use `set -euo pipefail` (initial detector flagged
  them because the directive sits below the header comment;
  it's a comment-block false positive, not a real defect).
- **Proposal**: Move logic into Python helpers under each
  plugin's `scripts/` and reduce the bash file to dispatch.
  Largest offender is `imbue/hooks/session-start.sh` (291).
- **Evidence**: `[E16]`
  ```
  $ for f in $(find plugins -path '*/hooks/*' -name '*.sh'); do
      loc=$(wc -l < "$f"); [ "$loc" -gt 200 ] && echo "$loc $f"
    done | sort -rn
  291 plugins/imbue/hooks/session-start.sh
  283 plugins/conserve/hooks/session-start.sh
  260 plugins/memory-palace/hooks/setup.sh
  246 plugins/leyline/hooks/fetch-recent-discussions.sh
  237 plugins/imbue/hooks/user-prompt-submit.sh
  234 plugins/conserve/hooks/setup.sh
  ```

### P-18: `clear-context` SKILL is 363 lines with only 2 modules

- **Type**: delegation-stub
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/conserve/skills/clear-context/SKILL.md`
- **Issue**: SKILL.md is 363 lines (~347 body lines) and only
  has 2 sibling modules. The body inlines the auto-clear pattern,
  thresholds, hook integration, and self-monitoring patterns --
  a textbook over-stuffed hub.
- **Proposal**: Extract `auto-clear-pattern.md`,
  `threshold-tuning.md`, `hook-integration.md`. Cut SKILL.md
  to <120 lines (hub + load directives).
- **Evidence**: `[E17]`
  ```
  $ wc -l plugins/conserve/skills/clear-context/SKILL.md
  363 plugins/conserve/skills/clear-context/SKILL.md
  $ ls plugins/conserve/skills/clear-context/modules
  agent_memory.py  area_agent_registry.py  context_scanner
  coordination_workspace.py  detect_duplicates.py
  growth_analyzer.py  growth_controller.py  safe_replacer.py
  token_estimator.md
  ```
  (The "modules" dir contains scripts and a single .md, not the
  expected progressive-loading modules.)

### P-19: `egregore:summon` SKILL is 331 lines

- **Type**: delegation-stub
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/egregore/skills/summon/SKILL.md`
- **Issue**: 331-line SKILL with 5 sibling modules
  (`budget.md`, `decisions.md`, `intake.md`, `model-routing.md`,
  `pipeline.md`) and 8 cross-skill references in body. The
  delegations are real, but the SKILL still documents pipeline
  stages, budget tracking, and intake protocol inline.
- **Proposal**: Cut SKILL to <150 lines. Move stage descriptions
  into `pipeline.md`, budget tracking to `budget.md`.
- **Evidence**: `[E18]`
  ```
  $ wc -l plugins/egregore/skills/summon/SKILL.md
  331 plugins/egregore/skills/summon/SKILL.md
  $ rg -c "modules/" plugins/egregore/skills/summon/SKILL.md
  8
  ```

### P-20: `attune:mission-orchestrator` SKILL is 330 lines

- **Type**: delegation-stub
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/attune/skills/mission-orchestrator/SKILL.md`
- **Issue**: 330-line SKILL with 12 modules already extracted.
  Detection caught it as a delegation stub because body matches
  "delegate" and "see Skill(...)" patterns; in practice this is
  borderline (the modules carry most weight). Listed for
  awareness rather than urgent fix.
- **Proposal**: Once mission types stabilize, trim narrative
  scaffolding from SKILL body. Target <200 lines.
- **Evidence**: covered by `[E15]`.

### P-21: `sanctum:doc-consolidation` SKILL is 295 lines

- **Type**: delegation-stub
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/sanctum/skills/doc-consolidation/SKILL.md`
- **Issue**: 295-line SKILL with 4 modules already extracted.
  References `modules/X.md` 8 times but body still narrates
  the workflow inline. Same pattern as P-19.
- **Proposal**: Trim body now that modules carry detail. Target
  <150 lines.
- **Evidence**: `[E19]`
  ```
  $ wc -l plugins/sanctum/skills/doc-consolidation/SKILL.md
  295 plugins/sanctum/skills/doc-consolidation/SKILL.md
  $ rg -c "modules/" plugins/sanctum/skills/doc-consolidation/SKILL.md
  8
  ```

### P-22: 15 SKILL files have modules dirs but >=200 body lines

- **Type**: oversized-module
- **Impact**: HIGH (aggregate)
- **Effort**: LARGE
- **Risk**: LOW
- **Location**: see top-15 list in evidence
- **Issue**: Pattern is systemic, not localized to one plugin.
  The plugins extracted modules but did not actually move the
  content. Top offenders (body lines / module count / file):
  - 677 / 5 / `memory-palace/skills/knowledge-intake/SKILL.md`
  - 675 / 5 / `abstract/skills/hook-authoring/SKILL.md`
  - 599 / 3 / `sanctum/skills/tutorial-updates/SKILL.md`
  - 536 / 7 / `sanctum/skills/pr-review/SKILL.md`
  - 440 / 6 / `attune/skills/war-room/SKILL.md`
  - 431 / 2 / `attune/skills/project-brainstorming/SKILL.md`
  - 409 / 19 / `scribe/skills/slop-detector/SKILL.md`
  - 361 / 7 / `sanctum/skills/test-updates/SKILL.md`
  - 349 / 5 / `imbue/skills/feature-review/SKILL.md`
  - 347 / 2 / `conserve/skills/clear-context/SKILL.md`
  - 336 / 5 / `sanctum/skills/doc-updates/SKILL.md`
  - 299 / 5 / `egregore/skills/summon/SKILL.md`
  - 285 / 3 / `memory-palace/skills/review-chamber/SKILL.md`
  - 273 / 4 / `sanctum/skills/doc-consolidation/SKILL.md`
  - 270 / 12 / `attune/skills/mission-orchestrator/SKILL.md`
- **Proposal**: Establish a "SKILL body <= 250 lines when modules
  exist" policy and enforce in CI. Sequence the cleanup by
  impact: P-03, P-04, P-05, P-06 first.
- **Evidence**: `[E20]` (Python script in scan log; counts body
  lines after frontmatter and matches against module dir).

## Notes on what was NOT a finding

- **Skill metadata**: All 186 SKILL.md files have valid
  frontmatter, name matches directory, and description <=1024
  chars. Clean.
- **Plugin manifests**: All 23 `.claude-plugin/plugin.json`
  files reference only existing skills/agents/commands/hooks.
  Clean.
- **`set -euo pipefail` in hooks**: All 8 hooks have it. The
  initial bash detector (which checks the first 5 lines)
  produced a false positive because hooks place the directive
  below their banner comment block (around lines 12-27).
- **Other Python `python -m / -c` references**: All verified
  resolve. Examples checked: `oracle.provision` (exists),
  `phantom.cli --check` (exists, has handler at line 98 of
  cli.py), `gauntlet.models.BankProblem` (exists at
  `plugins/gauntlet/src/gauntlet/models.py`).
