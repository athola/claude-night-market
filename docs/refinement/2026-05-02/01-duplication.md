# Duplication & Redundancy Findings

## Summary

- Total findings: 13
- HIGH impact: 4
- MEDIUM impact: 6
- LOW impact: 3

Scope: `plugins/*/src/`, `plugins/*/scripts/`, `plugins/*/hooks/`,
and root `scripts/`. Tests, vendored code, and cache directories
excluded.

A canonical shared package already exists at
`plugins/leyline/src/leyline/` (frontmatter, deferred_capture,
fs, mecw, quota_tracker, session_store, sqlite_graph_base,
tokens). Many findings below describe code that should consume
that package but currently re-implements the same logic.

## Findings

### D-01: Inline `escape_for_json` and `get_json_field` shell helpers duplicated despite a canonical shared module

- **Impact**: HIGH
- **Effort**: SMALL (<50 LOC net)
- **Risk**: LOW
- **Locations**:
  - `scripts/shared/json_utils.sh:1` — canonical implementation
    (file even lists its inlined copies in a header comment)
  - `plugins/imbue/hooks/session-start.sh:~16-80` — inlined copy
  - `plugins/imbue/hooks/user-prompt-submit.sh` — inlined copy
  - `plugins/conserve/hooks/session-start.sh:~16-80` — inlined copy
  - `plugins/conserve/hooks/setup.sh` — inlined copy
  - `plugins/memory-palace/hooks/setup.sh` — inlined copy
- **Pattern**: The same 60+ LOC `get_json_field` and
  `escape_for_json` block (jq -> grep -P -> sed/bash fallback)
  is hand-inlined into five separate hook scripts. The canonical
  source even documents this as a known wart with a maintenance
  list.
- **Proposal**: Convert each hook to source the shared file via
  the absolute plugin-cache path Claude Code resolves (e.g.
  `${CLAUDE_PLUGIN_ROOT}/scripts/shared/json_utils.sh`) or vendor
  one copy into each plugin's `hooks/shared/json_utils.sh` and
  source from there. Either eliminates the drift surface.
- **Evidence**: `[E1]`
  ```
  $ rg -l "escape_for_json\(\)" plugins scripts
  plugins/conserve/hooks/session-start.sh
  plugins/conserve/hooks/setup.sh
  plugins/imbue/hooks/session-start.sh
  plugins/imbue/hooks/user-prompt-submit.sh
  plugins/memory-palace/hooks/setup.sh
  scripts/shared/json_utils.sh
  ```
  Header of `scripts/shared/json_utils.sh:5-13` literally lists
  the inlined copies and asks future editors to keep them in sync.

### D-02: `parse_frontmatter` re-implemented four times when `leyline.frontmatter` exists

- **Impact**: HIGH
- **Effort**: SMALL (<50 LOC)
- **Risk**: LOW
- **Locations**:
  - `plugins/leyline/src/leyline/frontmatter.py:14` — canonical
    `parse_frontmatter(content)` with PyYAML + minimal fallback
  - `scripts/clawhub_export.py:30,38` — local `FRONTMATTER_RE`
    + `parse_frontmatter` with bespoke `_parse_yaml_block`
  - `scripts/a2a_cards.py:23` — same `FRONTMATTER_RE`,
    paired with a local `_parse_frontmatter`
  - `plugins/conserve/scripts/area_agent_registry.py:17`,
    `coordination_workspace.py:18` — same `FRONTMATTER_RE` plus
    private `_parse_frontmatter`
- **Pattern**: Each file declares the regex
  `^---\s*\n(.*?)\n---\s*\n` (DOTALL) and a parser that
  partitions on `:`. The leyline module already does this with a
  graceful PyYAML fallback.
- **Proposal**: Replace the four local copies with
  `from leyline.frontmatter import parse_frontmatter`. Where
  callers also need the body, add a single
  `parse_frontmatter_with_body(content)` to the leyline module
  and consume from there. Existing import users
  (`memory-palace/scripts/validate_knowledge_corpus.py`,
  `sanctum/src/sanctum/validators.py`) prove this works.
- **Evidence**: `[E2]`
  ```
  $ rg -l "FRONTMATTER_RE = re.compile" plugins scripts
  scripts/a2a_cards.py
  scripts/clawhub_export.py
  plugins/conserve/scripts/area_agent_registry.py
  plugins/conserve/scripts/coordination_workspace.py
  ```

### D-03: `_extract_section` markdown helper copy-pasted across abstract/ scripts

- **Impact**: MEDIUM
- **Effort**: SMALL (<30 LOC)
- **Risk**: LOW
- **Locations**:
  - `plugins/abstract/scripts/discussion_enrichment.py:161`
  - `plugins/abstract/scripts/post_learnings_to_discussions.py:238`
  - `plugins/abstract/scripts/auto_promote_learnings.py:143`
  - `plugins/conserve/scripts/coordination_workspace.py:53`
    (variant — slightly different stop terminator)
- **Pattern**: All three abstract/ copies use the same
  6-line implementation:
  ```python
  pattern = re.escape(heading) + r"\n(.*?)(?=\n## |\n---|\Z)"
  match = re.search(pattern, content, re.DOTALL)
  return match.group(1).strip() if match else None
  ```
  The conserve variant differs only in the stop-anchor list.
- **Proposal**: Add `extract_section(content, heading)` to a
  shared helper module — natural home is
  `plugins/abstract/src/abstract/utils.py` (already exposes
  helpers used by the same scripts). Conserve can either import
  it or stay decoupled given its different anchor set.
- **Evidence**: `[E3]`
  ```
  $ rg "def _extract_section" plugins/abstract/scripts -n
  plugins/abstract/scripts/discussion_enrichment.py:161
  plugins/abstract/scripts/auto_promote_learnings.py:143
  plugins/abstract/scripts/post_learnings_to_discussions.py:238
  ```
  All three function bodies match line-for-line.

### D-04: `get_observability_dir`, `get_log_directory`, `get_config_dir` reinvented in hooks/scripts despite `abstract.utils` already exporting them

- **Impact**: MEDIUM
- **Effort**: SMALL (<60 LOC removed)
- **Risk**: LOW
- **Locations**:
  - `plugins/abstract/src/abstract/utils.py:74,93` — canonical
    `get_log_directory(create=…)` and `get_config_dir(create=…)`
  - `plugins/abstract/hooks/skill_execution_logger.py:34,114`
    — local `get_observability_dir` + `get_log_directory`
  - `plugins/abstract/hooks/pre_skill_execution.py:24` — local
    `get_observability_dir`
  - `plugins/abstract/scripts/aggregate_skill_logs.py:84` —
    local `get_log_directory`
  - `plugins/abstract/scripts/promote_discussion_to_issue.py:37`
    — local `get_config_dir`
  - `plugins/abstract/scripts/post_learnings_to_discussions.py:51`
    — local `get_config_dir`
- **Pattern**: Each local copy reads `CLAUDE_HOME`, falls back
  to `~/.claude`, and joins a fixed sub-path. The canonical
  versions in `abstract.utils` do the same with an opt-in
  `create=True` flag.
- **Proposal**: Replace the six local definitions with
  `from abstract.utils import get_log_directory, get_config_dir`
  and add `get_observability_dir` to `abstract.utils` (it is the
  same shape as `get_log_directory` with a different sub-path
  literal).
- **Evidence**: `[E4]` Six matches confirmed via:
  ```
  $ rg "def get_(log_directory|config_dir|observability_dir)" \
      plugins/abstract -n
  ```

### D-05: `resolve_session_file` duplicated verbatim in two conserve hooks

- **Impact**: MEDIUM
- **Effort**: SMALL (<40 LOC)
- **Risk**: LOW
- **Locations**:
  - `plugins/conserve/hooks/tool_output_summarizer.py:30`
  - `plugins/conserve/hooks/pre_compact_preserve.py:61`
- **Pattern**: ~40-line function — derives the project
  directory name from `cwd`, falls back to most-recently
  modified directory under `~/.claude/projects/`, and returns
  the JSONL session file. Bodies are identical.
- **Proposal**: Move to a `plugins/conserve/hooks/shared/`
  module (the plugin already has a `hooks/` directory but no
  shared subpackage; add one mirroring `abstract/hooks/shared/`
  and `memory-palace/hooks/shared/`). Both callers import.
- **Evidence**: `[E5]`
  ```
  $ rg "def resolve_session_file" plugins -n
  plugins/conserve/hooks/tool_output_summarizer.py:30
  plugins/conserve/hooks/pre_compact_preserve.py:61
  ```
  First 22 lines of each are byte-identical (verified by
  reading both ranges).

### D-06: Imbue vow hooks repeat `_shadow_mode` and `_is_git_commit` verbatim

- **Impact**: MEDIUM
- **Effort**: SMALL (<30 LOC)
- **Risk**: LOW
- **Locations**:
  - `plugins/imbue/hooks/vow_no_emoji_commits.py:33,44`
  - `plugins/imbue/hooks/vow_no_ai_attribution.py:71,85`
  - `plugins/imbue/hooks/vow_bounded_reads.py:166`
    (`_shadow_mode` only)
- **Pattern**: All three vow hooks define the same 5-line
  `_shadow_mode()` reading `VOW_SHADOW_MODE`. Two of them also
  define identical 4-line `_is_git_commit()`. Same docstrings,
  same logic.
- **Proposal**: Extract to `plugins/imbue/hooks/shared/vow_utils.py`
  exporting `shadow_mode_active()` and `is_git_commit(cmd)`.
  All three hooks already share `VOW_SHADOW_MODE` semantics, so
  this is the consolidation point, not a new abstraction.
- **Evidence**: `[E6]` Function bodies confirmed identical via
  ```
  $ rg "_shadow_mode" plugins/imbue/hooks/vow_*.py -A 6
  ```
  Yields three identical 7-line blocks.

### D-07: `_jaccard_similarity` re-implemented in tome and memory-palace

- **Impact**: LOW
- **Effort**: SMALL (<20 LOC)
- **Risk**: LOW
- **Locations**:
  - `plugins/tome/src/tome/synthesis/merger.py:39`
  - `plugins/memory-palace/src/memory_palace/corpus/semantic_deduplicator.py:23`
- **Pattern**: Both compute Jaccard on whitespace-split word
  sets. The memory-palace variant lowercases first; tome does
  not. Five LOC of arithmetic identical otherwise.
- **Proposal**: Add `jaccard_similarity(a, b, *, lowercase=False)`
  to `plugins/leyline/src/leyline/` (a new `text_metrics.py` —
  this is the third plugin reaching for set-overlap math, so
  the rule of three is met counting the `slugify` finding
  below). Both call sites then import.
- **Evidence**: `[E7]`
  ```
  $ rg "def _jaccard_similarity" plugins -n
  plugins/tome/src/tome/synthesis/merger.py:39
  plugins/memory-palace/src/memory_palace/corpus/semantic_deduplicator.py:23
  ```

### D-08: `slugify` in three flavours across sanctum and memory-palace

- **Impact**: LOW
- **Effort**: SMALL (<30 LOC)
- **Risk**: LOW
- **Locations**:
  - `plugins/memory-palace/hooks/shared/text_utils.py:8` —
    canonical-looking implementation with `max_length`
    parameter and tail-safe truncation
  - `plugins/memory-palace/scripts/intake_cli.py:87` — already
    delegates to the canonical via `from .shared.text_utils
    import slugify as _slugify`
  - `plugins/sanctum/scripts/consolidation_planner.py:484` —
    independent 4-line copy without the tail-safe truncation
- **Pattern**: Both implementations lowercase, replace
  non-alphanumerics with `-`, and trim. memory-palace's keeps
  whole-word boundaries on truncation; sanctum's hard-cuts at
  50 chars.
- **Proposal**: Promote `text_utils.slugify` to
  `leyline.text` (or import directly from memory-palace if a
  cross-plugin import is acceptable per project rules).
  sanctum's hard-cut behaviour can be preserved with a
  parameter.
- **Evidence**: `[E8]`
  ```
  $ rg "^def slugify" plugins -n
  plugins/sanctum/scripts/consolidation_planner.py:484
  plugins/memory-palace/scripts/intake_cli.py:87
  plugins/memory-palace/hooks/shared/text_utils.py:8
  ```
  intake_cli already imports the shared one — proves the
  pattern works.

### D-09: `parse_skill_name` redefined in two abstract hooks despite shared module

- **Impact**: LOW
- **Effort**: SMALL (<20 LOC)
- **Risk**: LOW
- **Locations**:
  - `plugins/abstract/hooks/shared/skill_utils.py:10` —
    canonical with path-traversal sanitization
  - `plugins/abstract/hooks/skill_execution_logger.py:131` —
    already delegates correctly (`return _parse_skill_name(…)`)
  - `plugins/abstract/hooks/pre_skill_execution.py:32` —
    re-declares its own `parse_skill_name` instead of using
    the shared one (NOT verified to delegate; needs check
    during fix)
- **Pattern**: The shared module exists and one caller wraps
  it; the other declares an apparent fresh copy.
- **Proposal**: Inline-confirm `pre_skill_execution.py` is in
  fact a near-duplicate (or already a thin delegator); if
  duplicated, replace with `from shared.skill_utils import
  parse_skill_name`.
- **Evidence**: `[E9]`
  ```
  $ rg "^def parse_skill_name" plugins/abstract -n
  plugins/abstract/hooks/skill_execution_logger.py:131
  plugins/abstract/hooks/shared/skill_utils.py:10
  plugins/abstract/hooks/pre_skill_execution.py:32
  ```

### D-10: `run_gh_graphql` re-implemented in two abstract scripts

- **Impact**: MEDIUM
- **Effort**: SMALL (<40 LOC)
- **Risk**: LOW
- **Locations**:
  - `plugins/abstract/scripts/post_learnings_to_discussions.py:307`
  - `plugins/abstract/scripts/promote_discussion_to_issue.py:110`
- **Pattern**: Same 30-line wrapper around
  `subprocess.run(["gh", "api", "graphql", "-f",
  f"query={query}", ...])` with identical timeout, error
  shape, and JSON parsing. Bodies differ only in a `# nosec`
  comment.
- **Proposal**: Move to `abstract.utils` (or a new
  `abstract.gh` submodule). Both scripts already import from
  `abstract`. This also gives a single audit point for the
  `gh` shell-out that the security review will appreciate.
- **Evidence**: `[E10]`
  ```
  $ rg "def run_gh_graphql" plugins -n
  plugins/abstract/scripts/post_learnings_to_discussions.py:307
  plugins/abstract/scripts/promote_discussion_to_issue.py:110
  ```
  Diff shows only the `# nosec` annotation differs.

### D-11: `get_plugin_version` duplicated between `scripts/a2a_cards.py` and `scripts/clawhub_export.py`

- **Impact**: LOW
- **Effort**: SMALL (<20 LOC)
- **Risk**: LOW
- **Locations**:
  - `scripts/a2a_cards.py:201`
  - `scripts/clawhub_export.py:311`
- **Pattern**: Identical 9-line function reading
  `.claude-plugin/plugin.json` and returning `version` field
  with `"1.0.0"` default and `(json.JSONDecodeError, OSError)`
  swallowed.
- **Proposal**: Both are root scripts; create
  `scripts/_plugin_meta.py` exporting `get_plugin_version`
  (mirrors the existing `scripts/shared/` shell pattern).
  Two callers + low risk = exactly the rule-of-three threshold;
  hold off on broader abstraction until a third caller appears.
- **Evidence**: `[E11]`
  ```
  $ diff <(rg "def get_plugin_version" scripts/a2a_cards.py -A 8) \
         <(rg "def get_plugin_version" scripts/clawhub_export.py -A 8)
  # (only the trailing comment differs)
  ```

### D-12: `_warn` helper repeated across three abstract modules

- **Impact**: LOW
- **Effort**: SMALL (<15 LOC)
- **Risk**: LOW
- **Locations**:
  - `plugins/abstract/src/abstract/improvement_queue.py:19`
  - `plugins/abstract/src/abstract/improvement_memory.py:35`
  - `plugins/abstract/src/abstract/performance_tracker.py:21`
- **Pattern**: Each module defines a 3-line `_warn(msg)` that
  writes to `stderr` with a module-name prefix. Same shape,
  three different prefix literals.
- **Proposal**: Add a single
  `abstract.utils.warn(module: str, message: str)` (or use
  `logging.getLogger(__name__).warning`). Three call sites
  satisfy rule-of-three; standard library `logging` is the
  boring-and-obvious choice and also makes prefixing
  automatic.
- **Evidence**: `[E12]`
  ```
  $ rg "^def _warn" plugins/abstract/src -A 4
  ```
  Three identical 4-line blocks differing only in the prefix
  string.

### D-13: `output_result` / `output_error` JSON+plain-text dual emitters duplicated across sanctum and conserve scripts

- **Impact**: MEDIUM
- **Effort**: MEDIUM (50-100 LOC)
- **Risk**: MEDIUM (CLI contract surface)
- **Locations**:
  - `plugins/sanctum/scripts/test_generator.py:401`
    (`output_result`) and `:418` (`output_error`)
  - `plugins/sanctum/scripts/quality_checker.py:604,622`
  - `plugins/conserve/scripts/safe_replacer.py:196,217`
- **Pattern**: Each script reimplements the same dual-mode
  output: when `--output-json` is set, emit
  `{"success": True, "data": …}` (or `{"success": False,
  "error": …}`); otherwise print a human-readable summary.
  The bodies have minor differences (file-vs-stdout, indent
  level, default keyword) but the contract is identical.
- **Proposal**: Extract to a new `leyline.cli_output`
  helper exposing `emit_result(args, payload)` and
  `emit_error(args, message)`. The contract is small enough
  that one shared module is cheaper than three independent
  evolutions, and three call sites meet rule-of-three. Treat
  as MEDIUM risk because tooling that consumes the CLI JSON
  may rely on exact output shape — bake current shape into
  shared tests before consolidating.
- **Evidence**: `[E13]`
  ```
  $ rg "^def output_(result|error)" plugins -n
  plugins/sanctum/scripts/test_generator.py:401
  plugins/sanctum/scripts/test_generator.py:418
  plugins/sanctum/scripts/quality_checker.py:604
  plugins/sanctum/scripts/quality_checker.py:622
  plugins/conserve/scripts/safe_replacer.py:196
  plugins/conserve/scripts/safe_replacer.py:217
  ```

## Notes on what was deliberately not flagged

- **`plugins/*/scripts/deferred_capture.py` (5 files, ~47 LOC
  each)**: these already import from `leyline.deferred_capture`
  and only declare per-plugin `_enrich` + `PluginConfig`. The
  remaining boilerplate (~25 lines of imports +
  `if __name__ == "__main__"`) is the agreed contract surface
  for the leyline `deferred-capture` skill. Consolidating
  further would replace boilerplate with a registry-style
  abstraction that costs more than it saves at five plugins.
- **`def analyze(context: AnalysisContext)` across four
  abstract `lenses/` modules**: this is an intentional Strategy
  pattern with a stable shape; not duplication.
- **`def parse_code(code: str)` in two parseltongue modules**:
  the function is 5 LOC and the two call sites have different
  surrounding constants modules (`async_analysis/_constants.py`
  vs `testing_guide/_constants.py`); below the 10-LOC
  threshold, keep as-is.
- **30+ hook files calling `json.load(sys.stdin)` inside a
  `try/except json.JSONDecodeError`**: this is the Claude Code
  hook entrypoint contract. Wrapping in a shared helper would
  obscure the SDK-mandated shape; not refactor-worthy.
- **`get_ledger_path` in three sanctum hook modules**: the two
  non-canonical callers already delegate (`return
  _get_ledger_path()`); this is correct delegation, not
  duplication.

DUPLICATION SCAN COMPLETE — 13 findings written to docs/refinement/2026-05-02/01-duplication.md
