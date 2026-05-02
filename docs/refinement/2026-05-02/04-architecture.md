# Architectural Fit Findings

Tier 3 architectural-fit scan of the claude-night-market plugin
ecosystem. Focus: cross-plugin coupling, layering, god modules,
leaky abstractions, paradigm misfits, skill <-> Python entanglement.

## Summary

- Cross-plugin coupling: 9
- God modules: 6
- Layering violations: 3
- Skill/Python misfits: 1
- Leaky abstractions / inappropriate intimacy: 2
- Global state misuse: 2
- Module explosion: 4
- Other (sys.path hacks, missing wrapper, paradigm mismatch): 4

Total: 31 findings.

The dominant smell is `sys.path.insert(...)` shims used to bypass
the plugin boundary so one plugin can import another. There are
45 such inserts across hooks/scripts. Several of these are wired
to `try: from <other_plugin>...; except: <stub>`, which is the
documented "Plugin Dependency Isolation" pattern (ADR-0001 in
egregore/notify.py), but the same pattern is being copy-pasted
without a shared helper, which creates drift risk.

The second dominant smell is god modules in `pensive/src/pensive/skills/*.py`:
six review skills sit at 700-968 lines, each with ~15-20 methods
in a single class. These look like single-class translations of
multi-module skill specs. They are tracked partially under prior
F06/F07/F10/F16 work, but the four 700+-line review files have
not been decomposed.

## Findings

### AR-01: pensive `architecture_review.py` is a 968-line single-class god module

- **Type**: god-module / oversized-module
- **Impact**: HIGH
- **Effort**: LARGE
- **Risk**: MEDIUM
- **Location(s)**: `plugins/pensive/src/pensive/skills/architecture_review.py:42-968`
- **Pattern**: One class `ArchitectureReviewSkill` with 17 methods
  spans pattern detection, SoC violations, ADR parsing, coupling
  scoring, cohesion scoring, architecture-specific reporting, and
  string-keyword heuristics. The file mixes unrelated detection
  domains (layered, microservices, event-driven, hexagonal,
  CQRS) inside one class with no submodules. The companion skill
  `plugins/pensive/skills/architecture-review/modules/` already
  has split documentation, so the Python implementation is the
  monolith.
- **Proposal**: Decompose along the module boundaries that already
  exist in `skills/architecture-review/modules/`: extract pattern
  detection, SoC checks, coupling/cohesion scoring, and ADR
  parsing into sibling modules under `pensive/skills/architecture_review/`
  (mirroring the existing `rust_review/` package layout).
- **Evidence**:
  ```
  [E1] $ wc -l plugins/pensive/src/pensive/skills/architecture_review.py
  968
  [E2] $ rg "^    def " plugins/pensive/src/pensive/skills/architecture_review.py | wc -l
  17
  [E3] $ rg "^class " plugins/pensive/src/pensive/skills/architecture_review.py
  42:class ArchitectureReviewSkill(BaseReviewSkill):
  ```

### AR-02: pensive `makefile_review.py` god module (921 lines, 19 methods)

- **Type**: god-module / oversized-module
- **Impact**: HIGH
- **Effort**: LARGE
- **Risk**: MEDIUM
- **Location(s)**: `plugins/pensive/src/pensive/skills/makefile_review.py`
- **Pattern**: Same shape as AR-01: one `MakefileReviewSkill`
  class crossing recipe parsing, dependency analysis, dogfooding
  detection, and reporting. No package split.
- **Proposal**: Mirror `rust_review/` structure: `makefile_review/__init__.py`
  + `parsing.py`, `analysis.py`, `dogfooding.py`, `reporting.py`.
- **Evidence**:
  ```
  [E1] $ wc -l plugins/pensive/src/pensive/skills/makefile_review.py
  921
  [E2] $ rg "^    def " plugins/pensive/src/pensive/skills/makefile_review.py | wc -l
  19
  ```

### AR-03: pensive `test_review.py` god module (902 lines, 19 methods)

- **Type**: god-module
- **Impact**: HIGH
- **Effort**: LARGE
- **Risk**: MEDIUM
- **Location(s)**: `plugins/pensive/src/pensive/skills/test_review.py`
- **Pattern**: Single `TestReviewSkill` class spans framework
  detection, coverage scoring, BDD/TDD compliance, mocking patterns,
  flake detection, and reporting.
- **Proposal**: Same decomposition pattern as AR-01/AR-02. Frame
  detection and coverage scoring are independent and orthogonal.
- **Evidence**:
  ```
  [E1] $ wc -l plugins/pensive/src/pensive/skills/test_review.py
  902
  [E2] $ rg "^    def " plugins/pensive/src/pensive/skills/test_review.py | wc -l
  19
  ```

### AR-04: pensive `api_review.py`, `performance_review.py`, `bug_review.py`, `math_review.py` god modules (700-760 lines)

- **Type**: god-module
- **Impact**: MEDIUM
- **Effort**: LARGE
- **Risk**: MEDIUM
- **Location(s)**:
  - `plugins/pensive/src/pensive/skills/api_review.py` (760 lines, 14 methods)
  - `plugins/pensive/src/pensive/skills/performance_review.py` (744 lines)
  - `plugins/pensive/src/pensive/skills/bug_review.py` (744 lines)
  - `plugins/pensive/src/pensive/skills/math_review.py` (703 lines)
- **Pattern**: Identical shape to AR-01/02/03. The pensive review
  family has a one-class-per-monolith pattern that does not match
  the modular skill documentation. Note the recent F06/F07/F10/F16
  decomposition work has not touched these.
- **Proposal**: Apply the rust_review/ split pattern uniformly.
  Establish a single template (analysis/scoring/reporting/io) so
  all six review skills end up isomorphic.
- **Evidence**:
  ```
  [E1] $ wc -l plugins/pensive/src/pensive/skills/{api,performance,bug,math}_review.py
   760 api_review.py
   744 performance_review.py
   744 bug_review.py
   703 math_review.py
  ```

### AR-05: `memory_palace/project_palace.py` is 823 lines mixing room model + IO + serialization

- **Type**: god-module
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: MEDIUM
- **Location(s)**: `plugins/memory-palace/src/memory_palace/project_palace.py:1-823`
- **Pattern**: File has `RoomType`/`ReviewSubroom`/`SortBy` enums,
  module-level `REVIEW_CHAMBER_ROOMS`/`PROJECT_PALACE_ROOMS` data
  dicts, `ReviewEntry` model with `to_dict`/`from_dict`, and a
  `MemoryPalaceManager` extension for project palaces. The room
  schema, the entry value object, and the manager extension are
  three different concerns.
- **Proposal**: Split into `project_palace/rooms.py` (enums + dicts),
  `project_palace/entry.py` (ReviewEntry), and `project_palace/manager.py`
  (orchestration). The dict-based room schema in particular is
  data, not behavior, and belongs in a config module.
- **Evidence**:
  ```
  [E1] $ wc -l plugins/memory-palace/src/memory_palace/project_palace.py
  823
  [E2] $ rg "^class " plugins/memory-palace/src/memory_palace/project_palace.py
  38:class RoomType(str, Enum):
  48:class ReviewSubroom(str, Enum):
  57:class SortBy(str, Enum):
  114:class ReviewEntry:
  ```

### AR-06: `sanctum/validators.py` packs five validators in one 777-line file

- **Type**: god-module
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location(s)**: `plugins/sanctum/src/sanctum/validators.py:124-777`
- **Pattern**: Five validator classes (`AgentValidator`, `SkillValidator`,
  `CommandValidator`, `PluginValidator`, `SanctumValidator`) plus
  five paired result dataclasses share one module. Each validator
  is independently used and independently testable; nothing
  forces them into the same file.
- **Proposal**: One file per validator under `sanctum/validators/`,
  with `__init__.py` re-exporting the public surface. The file is
  small enough to do in a single pass.
- **Evidence**:
  ```
  [E1] $ rg "^class " plugins/sanctum/src/sanctum/validators.py | wc -l
  10
  [E2] $ wc -l plugins/sanctum/src/sanctum/validators.py
  777
  ```

### AR-07: `memory_palace_cli.py` is a 1050-line mega-CLI

- **Type**: oversized-module
- **Impact**: MEDIUM
- **Effort**: LARGE
- **Risk**: MEDIUM
- **Location(s)**: `plugins/memory-palace/scripts/memory_palace_cli.py:1-1050`
- **Pattern**: Single script with `main()` at line 983 dispatching
  every CLI command (tend garden, prune, archive, telemetry, etc.).
  The TendingOptions/TendingContext dataclasses suggest a
  "command object" pattern was started but not completed.
- **Proposal**: Move per-command handlers to `memory_palace/cli/`
  package with one module per subcommand. The `main()` becomes a
  thin argparse dispatcher.
- **Evidence**:
  ```
  [E1] $ wc -l plugins/memory-palace/scripts/memory_palace_cli.py
  1050
  [E2] $ rg "^def main\(" plugins/memory-palace/scripts/memory_palace_cli.py
  983:def main() -> None:
  ```

### AR-08: Cross-plugin import: `abstract.tokens` reaches into `leyline.tokens` via sys.path hack

- **Type**: cross-plugin-coupling / sys.path-hack
- **Impact**: HIGH
- **Effort**: MEDIUM
- **Risk**: HIGH
- **Location(s)**: `plugins/abstract/src/abstract/tokens.py:21-29`
- **Pattern**: `abstract` mutates `sys.path` at module import time
  to point at leyline's source tree, then imports leyline. This
  runs on every abstract import and is invisible to packaging
  tools. If leyline moves or is renamed, abstract silently
  degrades to its inline fallback. There is no plugin-manifest
  declaration that abstract depends on leyline.
  ```python
  _LEYLINE_SRC = Path(__file__).resolve().parents[3] / "leyline" / "src"
  sys.path.insert(0, str(_LEYLINE_SRC))
  try:
      from leyline.tokens import estimate_tokens as _leyline_estimate_tokens
  ```
- **Proposal**: Either declare the dependency in `plugin.json` and
  install `leyline` as a real package, or invert the relationship
  by moving the shared estimator into a `leyline-public` namespace
  package that both plugins import normally. Centralize the
  sys.path shim into a single helper if the dependency must remain
  ad-hoc.
- **Evidence**:
  ```
  [E1] $ rg "_LEYLINE_SRC" plugins/abstract/src/abstract/tokens.py -n
  22:_LEYLINE_SRC = Path(__file__).resolve().parents[3] / "leyline" / "src"
  23:sys.path.insert(0, str(_LEYLINE_SRC))
  ```

### AR-09: Cross-plugin import: `pensive.skills.performance_review` imports from `gauntlet`

- **Type**: cross-plugin-coupling
- **Impact**: HIGH
- **Effort**: MEDIUM
- **Risk**: MEDIUM
- **Location(s)**: `plugins/pensive/src/pensive/skills/performance_review.py:26-31`
- **Pattern**: Conditional import of `gauntlet.treesitter_parser`
  and `gauntlet.graph.GraphStore` inside pensive's library code.
  If gauntlet is uninstalled, performance_review falls back. This
  silently changes behavior depending on what plugins are
  co-installed and is the canonical "plugins should be loosely
  coupled" violation called out in the codebase axioms.
- **Proposal**: Extract the tree-sitter parser and graph store
  contract into `leyline` (or a new `cartograph-core`-style shared
  plugin) and have both pensive and gauntlet depend on that shared
  base. Document the optional integration in `pensive`'s plugin
  manifest as a soft dependency.
- **Evidence**:
  ```
  [E1] $ rg "from gauntlet" plugins/pensive/src/pensive/skills/ -n
  performance_review.py:26: from gauntlet.treesitter_parser import parse_file as _gt_parse
  performance_review.py:31: from gauntlet.graph import GraphStore as _GraphStore
  ```

### AR-10: Cross-plugin import: `cartograph` hooks reach into `gauntlet` source tree

- **Type**: cross-plugin-coupling / layering
- **Impact**: HIGH
- **Effort**: MEDIUM
- **Risk**: HIGH
- **Location(s)**: `plugins/cartograph/hooks/graph_community_refresh.py:50-72`
- **Pattern**: The hook walks the filesystem looking for the
  gauntlet plugin's `src/` directory, inserts it into `sys.path`,
  then imports `gauntlet.communities` and `gauntlet.graph`. This
  is a hook reaching across plugin boundary into another plugin's
  Python implementation, doubly violating loose coupling and the
  "hooks should be small and fail-closed" axiom.
- **Proposal**: Move the community-detection algorithm into a
  shared module (`leyline.graph_communities` or similar). Hooks
  should never have to discover sibling plugins on disk.
- **Evidence**:
  ```
  [E1] $ rg "from gauntlet|import gauntlet" plugins/cartograph/hooks/ -n
  graph_community_refresh.py:68: import gauntlet.communities as _gc
  graph_community_refresh.py:69: import gauntlet.graph as _gg
  ```

### AR-11: Cross-plugin import: `egregore/scripts/notify.py` reaches into `herald` via importlib

- **Type**: cross-plugin-coupling / paradigm-mismatch
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: MEDIUM
- **Location(s)**: `plugins/egregore/scripts/notify.py:36-90`
- **Pattern**: Egregore loads herald's `notify.py` directly with
  `importlib.util.spec_from_file_location` and re-exports its
  symbols. Comments cite ADR-0001 (Plugin Dependency Isolation),
  so this is intentional. The pattern is fine but is implemented
  ad-hoc with bespoke try/except blocks rather than a shared
  helper. Other plugins (sanctum, conjure, memory-palace, tome)
  duplicate the same "import optional sibling" dance with subtle
  variations.
- **Proposal**: Extract a `leyline.optional_plugin` helper (e.g.,
  `try_import_sibling("herald.notify")`) so the ADR-0001 isolation
  pattern has one canonical implementation. Today there are at
  least six near-duplicate variants (see AR-15).
- **Evidence**:
  ```
  [E1] $ rg "spec_from_file_location" plugins/egregore/scripts/notify.py -n
  45: _spec = importlib.util.spec_from_file_location(
  ```

### AR-12: Cross-plugin import: `imbue/scripts/imbue_validator.py` reaches into `abstract`

- **Type**: cross-plugin-coupling / sys.path-hack
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: MEDIUM
- **Location(s)**: `plugins/imbue/scripts/imbue_validator.py:13-23`
- **Pattern**: imbue inserts abstract/src into sys.path then
  imports `abstract.report_formatter.format_validator_report`,
  with an inline lambda fallback. This puts imbue's correct
  output formatting at the mercy of a sibling plugin's filesystem
  layout.
- **Proposal**: Move `format_validator_report` to leyline (which
  already houses cross-cutting concerns) or copy it into imbue.
  Library code that's used by multiple plugins should not live
  in just one of them.
- **Evidence**:
  ```
  [E1] $ rg "abstract.report_formatter" plugins/imbue -n
  imbue_validator.py:16: from abstract.report_formatter import (
  ```

### AR-13: Cross-plugin import: `spec-kit`/`attune`/`sanctum` all reach into `abstract.tasks_manager_base`

- **Type**: cross-plugin-coupling / missing-shared-base
- **Impact**: HIGH
- **Effort**: MEDIUM
- **Risk**: MEDIUM
- **Location(s)**:
  - `plugins/spec-kit/scripts/tasks_manager.py:19`
  - `plugins/attune/scripts/tasks_manager.py:19`
  - `plugins/sanctum/scripts/tasks_manager.py:19`
- **Pattern**: Three different plugins each import
  `abstract.tasks_manager_base`. This is `abstract` acting as a
  de-facto shared library for half the ecosystem, but it is not
  declared as such in any `plugin.json`. There is no published
  contract for `tasks_manager_base.py` (which itself is 598
  lines).
- **Proposal**: Either (a) move the shared task manager to leyline
  (the documented home of cross-cutting infrastructure) or (b)
  formally declare `abstract` as a foundation plugin that other
  plugins depend on, with a stable public API surface marked in
  `__init__.py`. Also: rename the file - `tasks_manager_base.py`
  with three importers means it isn't really a "base", it's the
  implementation.
- **Evidence**:
  ```
  [E1] $ rg "from abstract.tasks_manager_base" plugins/ -n
  spec-kit/scripts/tasks_manager.py:19: from abstract.tasks_manager_base import (
  attune/scripts/tasks_manager.py:19: from abstract.tasks_manager_base import (
  sanctum/scripts/tasks_manager.py:19: from abstract.tasks_manager_base import (
  ```

### AR-14: Cross-plugin import: six plugins import `leyline.deferred_capture` via copy-pasted shim

- **Type**: cross-plugin-coupling / duplicated-pattern
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location(s)**: `plugins/{abstract,attune,egregore,imbue,pensive,sanctum}/scripts/deferred_capture.py`
- **Pattern**: Six plugins ship a near-identical
  `scripts/deferred_capture.py` that does
  `sys.path.insert(0, leyline_src); from leyline.deferred_capture import ...`.
  This is the documented `leyline:deferred-capture` contract, but
  every plugin re-implements the bootstrap.
- **Proposal**: Either ship a CLI wrapper directly from leyline
  (`plugins/leyline/scripts/deferred_capture.py`) and have each
  plugin's manifest reference that path, or generate the shim from
  a template owned by leyline. The current structure is identical
  in 6 places, which means a fix has to land 6 times.
- **Evidence**:
  ```
  [E1] $ ls plugins/*/scripts/deferred_capture.py
  plugins/abstract/scripts/deferred_capture.py
  plugins/attune/scripts/deferred_capture.py
  plugins/egregore/scripts/deferred_capture.py
  plugins/imbue/scripts/deferred_capture.py
  plugins/pensive/scripts/deferred_capture.py
  plugins/sanctum/scripts/deferred_capture.py
  ```

### AR-15: 45 sys.path.insert sites with no shared discovery helper

- **Type**: layering / paradigm-mismatch
- **Impact**: HIGH
- **Effort**: MEDIUM
- **Risk**: MEDIUM
- **Location(s)**: 45 files across `plugins/*/hooks/` and
  `plugins/*/scripts/` (sample below).
- **Pattern**: Both hooks and scripts mutate `sys.path` to either
  (a) make their own `src/` importable from a non-installed
  context, or (b) discover a sibling plugin. There is no shared
  bootstrap helper, so each file rolls its own discovery logic
  with subtle variations (`parents[2]`, `parents[3]`, walking
  upward, etc.). When the plugin layout changes, every shim must
  be edited.
- **Proposal**: Introduce a single `leyline.bootstrap.add_plugin_to_path("herald")`
  helper. Every hook and script should call this once, not
  re-implement path discovery. Even better: make plugins installable
  Python packages in their own venv so this whole pattern goes
  away.
- **Evidence**:
  ```
  [E1] $ rg "sys\.path\.insert" plugins/*/hooks/ plugins/*/scripts/ -tpy | wc -l
  45
  [E2] sample variants:
  - plugins/abstract/scripts/discussion_enrichment.py: insert(0, _SCRIPTS_DIR)
  - plugins/cartograph/hooks/graph_community_refresh.py: walks up to find sibling
  - plugins/imbue/scripts/imbue_validator.py: parents[2]/abstract/src
  - plugins/abstract/src/abstract/tokens.py: parents[3]/leyline/src (in src/!)
  ```

### AR-16: `tome` reaches into leyline; `gauntlet.graph` reaches into `leyline.sqlite_graph_base`

- **Type**: cross-plugin-coupling
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location(s)**:
  - `plugins/tome/src/tome/session.py:12`
  - `plugins/gauntlet/src/gauntlet/graph.py:18`
  - `plugins/memory-palace/src/memory_palace/{session_history,knowledge_graph}.py`
  - `plugins/conjure/scripts/{quota_tracker,delegation_executor}.py`
  - `plugins/memory-palace/scripts/validate_knowledge_corpus.py`
- **Pattern**: Six modules import from `leyline.*` directly. This
  is consistent with leyline's documented role as foundation, but
  the pattern is conditional (`try: from leyline ...`) with inline
  fallbacks that drift apart over time.
- **Proposal**: Document leyline as a hard dependency of the
  plugins that need it. The conditional fallbacks suggest the
  authors are unsure whether leyline will be available; if so,
  the answer should be enforced at install time rather than
  inlined as a coping mechanism.
- **Evidence**:
  ```
  [E1] $ rg "^    from leyline\." plugins/ -n -tpy | wc -l
  10
  ```

### AR-17: Module explosion in `scribe/skills/slop-detector` (19 modules)

- **Type**: module-explosion
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location(s)**: `plugins/scribe/skills/slop-detector/modules/` (19 .md files)
- **Pattern**: 19 module files for a single skill. Many overlap
  by topic: `vocabulary-patterns.md`, `fiction-patterns.md`,
  `structural-patterns.md`, `i18n-patterns.md`, `language-support.md`
  - all about pattern matching at different scopes. The SKILL.md
  is also 451 lines. Total surface for this one skill is
  approximately 4200 estimated tokens (per the frontmatter), and
  every load pulls modules eagerly.
- **Proposal**: Consolidate into 4-5 modules grouped by audit
  layer (P0 critical, document-level, sentence-level, evidence,
  remediation). The `cleanup-workflow.md` and `remediation-strategies.md`
  pair is a clear merge candidate; so are the four pattern files.
- **Evidence**:
  ```
  [E1] $ ls plugins/scribe/skills/slop-detector/modules | wc -l
  19
  [E2] $ wc -l plugins/scribe/skills/slop-detector/SKILL.md
  451
  ```

### AR-18: Module explosion in `pensive/skills/rust-review` (16 modules)

- **Type**: module-explosion
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location(s)**: `plugins/pensive/skills/rust-review/modules/`
- **Pattern**: 16 modules for one skill, with thematic overlap
  between `iterator-and-allocation-slop.md`, `async-slop.md`,
  `test-slop.md`, `model-specific-tells.md` (all "slop" variants).
  The Python implementation under
  `pensive/src/pensive/skills/rust_review/` correctly splits into
  8 sibling modules of 91-286 lines, but the markdown skill modules
  are roughly 2x as fragmented as the code.
- **Proposal**: Either merge the slop-* variants into one module,
  or align the markdown module split 1:1 with the Python module
  split (which is the right granularity).
- **Evidence**:
  ```
  [E1] $ ls plugins/pensive/skills/rust-review/modules | wc -l
  16
  [E2] $ ls plugins/pensive/src/pensive/skills/rust_review/*.py | wc -l
  8
  ```

### AR-19: Module explosion in `attune/skills/mission-orchestrator` (12 modules)

- **Type**: module-explosion
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location(s)**: `plugins/attune/skills/mission-orchestrator/modules/`
  (12 .md files; SKILL.md is 330 lines; modules total 2191 lines)
- **Pattern**: The skill provides 7 capabilities (mission-lifecycle,
  state-detection, phase-routing, session-recovery, reflexion-buffer,
  trust-tier, adaptive-constraints) but ships 12 modules. Several
  modules (`context-injector.md`, `feedback-collector.md`,
  `iteration-governor.md`, `plan-versioner.md`) are not referenced
  in the SKILL.md frontmatter `modules:` list, suggesting they
  were added without integration.
- **Proposal**: Verify each module is loaded by some routing path,
  delete unreferenced ones, and merge the orchestration-related
  trio (context-injector, feedback-collector, iteration-governor)
  into a single `feedback-loop.md`.
- **Evidence**:
  ```
  [E1] $ ls plugins/attune/skills/mission-orchestrator/modules | wc -l
  12
  [E2] frontmatter lists 6 modules: mission-types, state-detection,
       phase-routing, mission-state, plan-review, plan-versioner
  ```

### AR-20: Module explosion in `abstract/skills/skills-eval` (11 modules)

- **Type**: module-explosion
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location(s)**: `plugins/abstract/skills/skills-eval/modules/`
- **Pattern**: 11 modules. `integration.md` and `integration-testing.md`
  appear topically duplicated; `evaluation-criteria.md` and
  `evaluation-framework.md` and `evaluation-workflows.md` are
  three modules about the same thing.
- **Proposal**: Merge the three "evaluation-*" modules into one
  `evaluation.md` (criteria, framework, workflow as sections).
  Merge `integration.md` + `integration-testing.md`.
- **Evidence**:
  ```
  [E1] $ ls plugins/abstract/skills/skills-eval/modules
  advanced-tool-use-analysis.md, authoring-checklist.md,
  evaluation-criteria.md, evaluation-framework.md,
  evaluation-workflows.md, integration-testing.md,
  integration.md, performance-benchmarking.md,
  pressure-testing.md, trigger-isolation-analysis.md,
  troubleshooting.md
  ```

### AR-21: Singleton mutable state in `abstract.config.ConfigFactory._instances`

- **Type**: global-state / singleton
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: MEDIUM
- **Location(s)**: `plugins/abstract/src/abstract/config.py:430`
- **Pattern**:
  ```python
  class ConfigFactory:
      _instances: dict[str, AbstractConfig] = {}
  ```
  A class-attribute mutable dict acting as a process-global
  registry, with `get_config`, `set_config`, `reset_config` mutating
  it. This is the textbook "module-level mutable dict written
  from multiple places" smell. Tests must remember to reset_config()
  to avoid leaking state across runs.
- **Proposal**: Replace with a small DI container or contextmanager
  so callers explicitly pass a `Config` instance. If a singleton
  is required, expose it as a function `get_default_config()` with
  no setter; tests that need a different config should construct
  one and pass it explicitly.
- **Evidence**:
  ```
  [E1] $ rg "_instances" plugins/abstract/src/abstract/config.py -n
  430:    _instances: dict[str, AbstractConfig] = {}
  435,439,442,444,449,454,455: writes/reads
  ```

### AR-22: `pensive.workflows.code_review._skill_registry` is a per-instance registry written from outside

- **Type**: leaky-abstraction / global-state
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location(s)**: `plugins/pensive/src/pensive/workflows/code_review.py:22,192`
- **Pattern**: `self._skill_registry: dict[str, Any] = {}` and
  `return self._skill_registry[skill_name]`. The naming with the
  underscore prefix says "private", but the registry is populated
  by external `register_skill(...)` calls and reading it returns
  the raw stored value. The class is essentially a thin wrapper
  around a dict.
- **Proposal**: Either remove the wrapper (use a plain
  `dict[str, ReviewSkill]`) or expose a real interface
  (`get_skill(name) -> ReviewSkill | None`, `list_skills() -> list[str]`)
  and stop returning private data. The current shape provides no
  encapsulation.
- **Evidence**:
  ```
  [E1] plugins/pensive/src/pensive/workflows/code_review.py:22:
       self._skill_registry: dict[str, Any] = {}
  [E2] plugins/pensive/src/pensive/workflows/code_review.py:192:
       return self._skill_registry[skill_name]
  ```

### AR-23: `Configuration.merge` reaches into `other._config`

- **Type**: inappropriate-intimacy
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location(s)**: `plugins/pensive/src/pensive/config/configuration.py:124-130`
- **Pattern**:
  ```python
  merged = {**self._config}
  for key, value in other._config.items():
      ...
  ```
  The merge method reads the private `_config` attribute of a
  sibling instance. The two instances are the same class so this
  is technically fine in Python, but it cements the dict
  representation as part of the class's contract. If the storage
  ever changes (e.g., to a layered chainmap), every `other._config`
  site has to change too.
- **Proposal**: Add `def items()` (or `as_dict()`) to `Configuration`
  and call that in `merge`. Hide the storage shape.
- **Evidence**:
  ```
  [E1] plugins/pensive/src/pensive/config/configuration.py:125:
       for key, value in other._config.items():
  ```

### AR-24: Hooks importing through dynamic sibling discovery: `cartograph` -> `gauntlet`

- **Type**: layering
- **Impact**: HIGH
- **Effort**: MEDIUM
- **Risk**: HIGH
- **Location(s)**: `plugins/cartograph/hooks/graph_community_refresh.py`,
  `plugins/pensive/hooks/pr_blast_radius.py`
- **Pattern**: Two hook files perform filesystem-walk discovery
  to find the gauntlet plugin (`plugins_dir = Path(__file__).resolve().parents[2]`),
  insert its src into sys.path, and import gauntlet modules. Hooks
  run in the Claude Code lifecycle on a 5-second budget and are
  supposed to fail closed; this design forces them to make IO
  calls on every invocation just to find their dependencies.
- **Proposal**: Move the integration logic out of the hook into a
  shared CLI under leyline and have the hook subprocess into it.
  Hook code itself should not have to discover sibling plugins.
- **Evidence**:
  ```
  [E1] plugins/cartograph/hooks/graph_community_refresh.py:50-65
  [E2] plugins/pensive/hooks/pr_blast_radius.py:50:
       sys.path.insert(0, str(gauntlet_src))
  ```

### AR-25: Layering inversion: `abstract/hooks/` imports from `abstract/scripts/`

- **Type**: layering
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: MEDIUM
- **Location(s)**:
  - `plugins/abstract/hooks/post_learnings_stop.py:37`
  - `plugins/abstract/hooks/aggregate_learnings_daily.py:44`
- **Pattern**: Both hooks insert the scripts directory on sys.path
  and import `auto_promote_learnings` (a script). The expected
  layering in this codebase is:
  `skills (docs)` <- `hooks (small/fail-closed)` <- `src/ (library)`,
  with `scripts/` at the same layer as hooks (CLI surface, not
  library). Importing scripts from hooks treats scripts as a
  library, which is what `src/` is for.
- **Proposal**: Move the reusable promotion logic from
  `scripts/auto_promote_learnings.py` into
  `src/abstract/learnings/promote.py` and have both the script
  and the hooks import it from there.
- **Evidence**:
  ```
  [E1] $ rg "from auto_promote_learnings" plugins/abstract/hooks/ -n
  hooks/post_learnings_stop.py:37: from auto_promote_learnings import (
  hooks/aggregate_learnings_daily.py:44: from auto_promote_learnings import run_auto_promote as _promote
  ```

### AR-26: Sibling-script discovery via sys.path: `abstract/scripts/discussion_enrichment.py` etc.

- **Type**: layering / sys.path-hack
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: MEDIUM
- **Location(s)**: `plugins/abstract/scripts/discussion_enrichment.py:26-30`,
  plus `insight_analyzer.py`, `insight_palace_bridge.py`,
  `post_insights_to_discussions.py`, `post_review_insights.py`,
  `lenses/*.py`, `insight_registry.py`,
  `tests/scripts/test_post_insights.py`.
- **Pattern**: Eight scripts plus tests share `insight_types.py`
  by inserting the scripts directory on sys.path and importing
  `from insight_types import Finding`. Standard Python packaging
  would either make `scripts/` a real package, or move shared
  models to `src/abstract/insight_types.py`.
- **Proposal**: Move `insight_types.py` to
  `src/abstract/insights/types.py` and import normally. Drop
  the sys.path mutation from every script.
- **Evidence**:
  ```
  [E1] $ rg "from insight_types|import insight_types" plugins/abstract/ -n
  (8 import sites in scripts/, plus 1 in agents/, plus tests)
  ```

### AR-27: `phantom.display` returns of private state through public API

- **Type**: leaky-abstraction
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location(s)**: `plugins/phantom/src/phantom/display.py:137-184`
- **Pattern**: Multiple "public" methods do nothing but
  `return self._do_screenshot({})`, `return self._click(action, button=1)`.
  The leading underscore signals private, but those private
  helpers are the actual implementations and the public methods
  are forwarders. Either the public/private convention is
  inverted, or the public methods should just be removed.
- **Proposal**: If the underscore methods are the canonical API
  (one private `_click` parameterized by button/repeat), drop the
  underscore and make the wrapper methods thin call-throughs. If
  they are truly private, the public methods need their own logic.
- **Evidence**:
  ```
  [E1] plugins/phantom/src/phantom/display.py:172,175,178,181,184
       return self._click(action, button=1)
       return self._click(action, button=3)
       return self._click(action, button=2)
       return self._click(action, button=1, repeat=2)
       return self._click(action, button=1, repeat=3)
  ```

### AR-28: `oracle/skills/setup/SKILL.md` instructs running Python from a non-installed venv layout

- **Type**: skill-misfit / dead-python-ref-borderline
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location(s)**: `plugins/oracle/skills/setup/SKILL.md:26-32`
- **Pattern**: The skill says
  `cd plugins/oracle && uv run python -c "from oracle.provision import ..."`.
  `oracle/src/oracle/provision.py` exists, but the working-directory
  step assumes a developer-style layout (`cd plugins/oracle`) which
  may not match where the plugin is installed in user environments
  (`~/.claude/plugins/...`). The skill thereby works only when run
  from the dev clone.
- **Proposal**: Replace the inline Python with a CLI shim
  (`oracle setup`) that runs from the installed location regardless
  of cwd. The skill should call the CLI, not embed a Python
  literal that depends on `cd`.
- **Evidence**:
  ```
  [E1] $ ls plugins/oracle/src/oracle/
  __init__.py client.py daemon.py provision.py
  [E2] plugins/oracle/skills/setup/SKILL.md:25-32:
       cd plugins/oracle && uv run python -c "
           from oracle.provision import provision_venv, get_venv_path
           ...
       "
  ```

### AR-29: Paradigm mismatch: deeply imperative `RoomType`/`PROJECT_PALACE_ROOMS` literal vs. enums-and-dataclasses elsewhere

- **Type**: paradigm-mismatch
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location(s)**: `plugins/memory-palace/src/memory_palace/project_palace.py:38-111`
- **Pattern**: The file declares typed enums (`RoomType`, `ReviewSubroom`,
  `SortBy`) using `enum.Enum` (declarative, type-safe) but then
  models the same data as nested module-level `dict[str, dict[str, str]]`
  literals (`REVIEW_CHAMBER_ROOMS`, `PROJECT_PALACE_ROOMS`) that
  duplicate the enum members as string keys. The two views drift:
  changing the enum doesn't change the dict, and the dict has no
  type checking.
- **Proposal**: Promote the room metadata to dataclasses and key
  them by the enum: `dict[RoomType, RoomMetadata]`. One source of
  truth for the room set.
- **Evidence**:
  ```
  [E1] enum members: RoomType.ENTRANCE='entrance', LIBRARY='library',
       WORKSHOP='workshop', REVIEW_CHAMBER='review-chamber', GARDEN='garden'
  [E2] dict keys: 'entrance', 'library', 'workshop',
       'review-chamber', 'garden' (manually duplicated)
  ```

### AR-30: Missing wrapper layer: 7+ raw `gh` invocations across plugins with no shared helper

- **Type**: missing-layer
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: MEDIUM
- **Location(s)**:
  - `plugins/leyline/scripts/verify_plugin.py:76`
  - `plugins/herald/scripts/notify.py:169`
  - `plugins/abstract/scripts/promote_discussion_to_issue.py:124`
  - `plugins/abstract/scripts/post_learnings_to_discussions.py:321,366`
  - `plugins/abstract/scripts/auto_promote_learnings.py:315,385`
- **Pattern**: Seven sites build raw `["gh", "api", ...]` argv
  lists and call `subprocess.run`, despite a documented `leyline:git-platform`
  skill describing a "git platform detection and cross-platform
  command mapping for GitHub, GitLab, and Bitbucket." There is
  no Python wrapper enforcing that contract; every script
  reinvents argv construction, error handling, and JSON parsing.
- **Proposal**: Implement the `git-platform` skill's contract as
  `leyline.git_platform` Python module (`gh_api(endpoint, query=...)`,
  `gh_graphql(query, vars)`, etc.) and migrate the 7 sites. Future
  GitLab/Bitbucket support gains a single switching point.
- **Evidence**:
  ```
  [E1] $ rg '"gh",' plugins/*/scripts/ -n -tpy
  (7 sites listed above)
  [E2] $ find plugins -name "git_platform*"
  (no Python module exists; only the skill markdown)
  ```

### AR-31: Hooks > 500 lines violate "small and fail-closed" axiom

- **Type**: oversized-module / layering
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: MEDIUM
- **Location(s)**:
  - `plugins/memory-palace/hooks/web_research_handler.py` (617 lines, 13 functions)
  - `plugins/sanctum/hooks/session_complete_notify.py` (571 lines, 17 functions)
  - `plugins/conserve/hooks/context_warning.py` (481 lines)
  - `plugins/gauntlet/hooks/precommit_gate.py` (429 lines)
  - `plugins/abstract/hooks/skill_execution_logger.py` (397 lines)
- **Pattern**: The codebase axiom says "hooks should be small and
  fail-closed". Five hooks exceed 400 lines. `web_research_handler.py`
  is 617 lines and orchestrates URL parsing, dedup, safety, queue
  storage, graph entity registration, and storage prompting in one
  file - the docstring explicitly notes it merges two prior hooks.
- **Proposal**: Push business logic out of hooks into `src/`
  modules and reduce the hook to dispatch + safety guards. The
  rule of thumb is: a hook should fit on one screen plus a tail
  for argument parsing.
- **Evidence**:
  ```
  [E1] $ find plugins -name "*.py" -path "*/hooks/*" -exec wc -l {} \; | sort -rn | head -5
  617 plugins/memory-palace/hooks/web_research_handler.py
  571 plugins/sanctum/hooks/session_complete_notify.py
  481 plugins/conserve/hooks/context_warning.py
  429 plugins/gauntlet/hooks/precommit_gate.py
  397 plugins/abstract/hooks/skill_execution_logger.py
  ```

ARCHITECTURE SCAN COMPLETE - 31 findings written to docs/refinement/2026-05-02/04-architecture.md
