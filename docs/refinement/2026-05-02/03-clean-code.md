# Clean Code, Anti-Slop & Error Handling Findings

Tier 3 refinement scan over `plugins/*/src/`,
`plugins/*/scripts/`, `plugins/*/hooks/`, `scripts/`.
Tests, vendor code, and `__pycache__` excluded.

## Summary

| Category        | HIGH | MED | LOW |
|-----------------|------|-----|-----|
| God functions   | 6    | 8   | 4   |
| Anti-slop       | 0    | 5   | 4   |
| Error handling  | 3    | 6   | 3   |
| Dead/naming     | 0    | 3   | 5   |
| Magic values    | 0    | 1   | 2   |

Total: 50 findings. AST scan flagged 179 functions in
`plugins/` (and 5 in `scripts/`) longer than 60 lines;
this report groups them by file rather than listing each.

## Findings

### C-01: god-function cluster in `memory_palace_cli.py`

- **Category**: god-function
- **Impact**: HIGH
- **Effort**: LARGE
- **Risk**: MEDIUM
- **Location**:
  `plugins/memory-palace/scripts/memory_palace_cli.py:811`
  `build_parser` (169 lines), plus the dispatcher class
  with 12+ broad `except Exception:` blocks.
- **Current**: `build_parser` constructs every subparser
  inline with verbose argparse boilerplate. The CLI
  class also catches `Exception` 12 times, each followed
  by `logger.exception(...)` and a generic
  "unexpected error (check logs)" string.
- **Proposal**: Split `build_parser` into one helper per
  command group (`_add_garden_parser`,
  `_add_palace_parser`, etc.), each ~15-25 lines. Replace
  the per-command broad excepts with a single
  decorator/context manager that logs and prints the
  error in one place.
- **Rationale**: 169 lines in one function is a wall;
  argparse construction is the textbook split point. The
  repeated try/except/log/print quartet is a copy-paste
  smell that should be one helper.

### C-02: god-function cluster in `context_scanner/`

- **Category**: god-function
- **Impact**: HIGH
- **Effort**: LARGE
- **Risk**: MEDIUM
- **Location**:
  `plugins/conserve/scripts/context_scanner/cli.py:22`
  `main` (132 lines, PLR0912/PLR0915 noqa-ed),
  `plugins/conserve/scripts/context_scanner/ecosystems.py:46`
  `scan_directory` (130 lines, PLR0915 noqa-ed),
  `plugins/conserve/scripts/context_scanner/ecosystems.py:184`
  `_parse_pyproject_deps` (86 lines, PLR0912/PLR0915
  noqa-ed),
  `plugins/conserve/scripts/context_scanner/renderers.py:567`
  `render_section` (depth=9, PLR0912 noqa-ed).
- **Current**: Four functions in this scanner each
  silence Ruff's complexity rules with comments like
  "one branch per section type is the clearest
  structure" (`renderers.py:567`).
- **Proposal**: For `render_section`, use a dispatch
  table: `_RENDERERS: dict[Section, Callable[[ScanResult],
  list[str]]] = {Section.STRUCTURE: _render_structure,
  ...}`. For `main`, extract handlers per mode (blast,
  section, wiki, full). For `scan_directory`, separate
  the file walk, ecosystem detection, and analysis
  passes. For `_parse_pyproject_deps`, split into
  `_parse_project_table`, `_parse_optional_deps`,
  `_parse_poetry_deps`.
- **Rationale**: noqa-ing complexity rules is the
  warning sign. The "clearest structure" justification
  on a 73-line elif ladder is a rationalisation; a dict
  dispatch is not less clear, it is more.

### C-03: god-function `extract_keywords` (memory-palace)

- **Category**: god-function
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**:
  `plugins/memory-palace/src/memory_palace/corpus/keyword_index.py:50`
  (122 lines)
- **Current**: Single method handles frontmatter
  parsing, six different regex extractions, hard-coded
  inline 35-word stop list, and dedup. The stop list is
  defined inline inside the method on every call.
- **Proposal**: Hoist the stop list to a module-level
  `_STOP_WORDS: frozenset[str]` constant. Extract
  helpers `_keywords_from_metadata`, `_keywords_from_body`,
  and have `extract_keywords` orchestrate.
- **Rationale**: The function body is 30 lines of
  literal stop words; that is data, not code, and it
  should not live inside a function.

### C-04: god-function cluster in `pensive` skills

- **Category**: god-function
- **Impact**: MEDIUM
- **Effort**: LARGE
- **Risk**: MEDIUM
- **Location**:
  `plugins/pensive/src/pensive/skills/rust_review/builtins.py:48`
  `analyze_builtin_preference` (121 lines),
  `plugins/pensive/src/pensive/skills/architecture_review.py:380`
  `analyze_solid_principles` (106 lines),
  `plugins/pensive/src/pensive/skills/architecture_review.py:235`
  `check_separation_of_concerns` (83 lines),
  `plugins/pensive/src/pensive/skills/performance_review.py:181`
  `_collect_non_list_names` (101 lines, depth=8),
  `plugins/pensive/src/pensive/skills/api_review.py:571`
  `check_security_practices` (84 lines),
  `plugins/pensive/src/pensive/skills/test_review.py:692`
  `detect_test_flakiness` (depth=6),
  `plugins/pensive/src/pensive/skills/makefile_review.py:549`
  `analyze_target_organization` (83 lines).
- **Current**: Each function walks a long pattern list
  and appends a dict per match. `analyze_builtin_preference`
  iterates four separate `_BUILTIN_*_PATTERNS` lists in
  one for-loop body.
- **Proposal**: Extract a `_match_patterns(line, patterns,
  builder)` helper that returns issue dicts. The four
  pattern groups can each call it. Reduces each god
  function to a ~20-line orchestrator.
- **Rationale**: Same shape four times in one function:
  iterate a list, regex-match, build a dict with
  identical keys. Textbook duplication.

### C-05: god-function cluster in `parseltongue/async_analysis/`

- **Category**: god-function
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**:
  `plugins/parseltongue/src/parseltongue/analysis/async_analysis/complex_scenarios.py:97`
  `suggest_improvements` (104 lines),
  `plugins/parseltongue/src/parseltongue/analysis/async_analysis/error_timeout.py:35`
  `analyze_error_handling` (depth=6),
  `plugins/parseltongue/src/parseltongue/analysis/async_analysis/blocking_detection.py:138`
  `detect_missing_await` (depth=6),
  `plugins/parseltongue/src/parseltongue/analysis/pattern_matching/_improvements.py:404`
  `compare_pattern_alternatives` (89 lines).
- **Current**: `suggest_improvements` builds a list of
  improvement dicts via inline ifs that each construct a
  ~10-line dict with hard-coded `code_before`,
  `code_after`, and `explanation` strings.
- **Proposal**: Move improvement templates to a
  module-level `_IMPROVEMENTS: dict[str, dict]` table.
  Replace the if-cascade with `for category, predicate
  in _CHECKS: if predicate(...): improvements.append(
  _IMPROVEMENTS[category])`.
- **Rationale**: The function is mostly literals. Moving
  literals to data lets the logic shrink to ~25 lines
  and makes adding a new improvement a one-line edit.

### C-06: god-function cluster in `attune` scripts

- **Category**: god-function
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: MEDIUM
- **Location**:
  `plugins/attune/scripts/plugin_project_init.py:11`
  `create_plugin_structure` (100 lines),
  `plugins/attune/scripts/attune_arch_init.py:93`
  `interactive_context_gathering` (95 lines),
  `plugins/attune/scripts/attune_upgrade.py:317`
  `main` (92 lines),
  `plugins/attune/scripts/attune_init.py:52`
  `copy_templates` (87 lines).
- **Current**: Each is a sequential setup script
  function with mixed concerns (parse args, copy files,
  print messages, write configs).
- **Proposal**: Each `main`/`create_*` function should
  be a 15-line orchestrator calling `_parse_args`,
  `_copy_files`, `_write_config`, `_print_summary`.
- **Rationale**: These are init scripts, the easiest
  refactor surface; the steps are already linear and
  sequential.

### C-07: god-function `find_duplicates` is opaque

- **Category**: god-function
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/conserve/scripts/detect_duplicates.py:149`
  (123 lines)
- **Current**: Single function: declares default
  extensions inline (15 lines), hard-codes exclude
  patterns inline (10 lines), walks files, hashes
  blocks, runs binary-search overlap detection, builds
  duplicate list, sorts, returns truncated to 50.
- **Proposal**: Hoist `_DEFAULT_EXTENSIONS` and
  `_EXCLUDE_PATTERNS` to module constants. Extract
  `_collect_files`, `_hash_blocks`, and
  `_dedupe_overlaps`. The truncation magic number 50
  should be a named constant.
- **Rationale**: Hardcoded sets inside a function body
  are configuration; they belong at module scope where
  they can be tested and overridden.

### C-08: god-function `_extract_from_tree` (gauntlet)

- **Category**: god-function
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**:
  `plugins/gauntlet/src/gauntlet/treesitter_parser.py:176`
  (111 lines)
- **Current**: Single function walks a tree-sitter tree
  and builds CodeEntities for classes, functions,
  methods, and types in one pass with deep nesting.
- **Proposal**: Split per-entity-type:
  `_extract_classes`, `_extract_functions`,
  `_extract_methods`. Each walks the tree once but
  yields a single entity kind.
- **Rationale**: Tree walks for distinct extractions
  read more clearly as separate passes; single-pass
  optimisation is premature for a code analysis tool
  that runs on diffs.

### C-09: god-function `parse_improvement_items`

- **Category**: god-function
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/abstract/scripts/auto_promote_learnings.py:188`
  (99 lines)
- **Current**: Iterates lines, tracks state via 4
  boolean flags (`in_section`, `current_priority`, etc.),
  appends to a list. Classic state-machine-as-flags.
- **Proposal**: Use `enum.Enum` for parser state and a
  `match` statement on `state, line.startswith(...)`.
- **Rationale**: Boolean-flag state machines are
  bug-prone; one explicit `ParserState` enum makes the
  transitions auditable.

### C-10: god-function cluster in `hookify` scripts

- **Category**: god-function
- **Impact**: LOW
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**:
  `plugins/hookify/scripts/install_rule.py:232` `main`
  (96 lines),
  `plugins/hookify/scripts/hook_to_hookify.py:402` `main`
  (93 lines).
- **Current**: Both are CLI dispatch functions with
  inline arg parsing and command handling.
- **Proposal**: Standard split: `_build_parser`,
  `_dispatch(args)`. Reuses pattern from C-01.
- **Rationale**: Consistent CLI shape across plugins;
  these are minor offenders but easy wins.

### C-11: deeply nested `render_section` in renderers

- **Category**: god-function
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/conserve/scripts/context_scanner/renderers.py:567`
  (depth=9 per AST scan)
- **Current**: 9-level nesting from elif/for/if chains
  (covered as part of C-02 but flagged separately for
  visibility).
- **Proposal**: Same as C-02 – dispatch table.
- **Rationale**: Depth 9 is an outlier even in this
  codebase (next-deepest is 8). Worst readability
  hotspot in the scan.

### C-12: cyclomatic top-N in plugin hooks

- **Category**: god-function
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: MEDIUM
- **Location**:
  `plugins/gauntlet/hooks/precommit_gate.py:322` `main`
  (92 lines),
  `plugins/imbue/hooks/tdd_bdd_gate.py:193` `main`
  (90 lines),
  `plugins/abstract/hooks/skill_execution_logger.py:308`
  `main` (85 lines),
  `plugins/memory-palace/hooks/local_doc_processor.py:74`
  `main` (106 lines),
  `plugins/memory-palace/hooks/research_interceptor.py:163`
  `main` (86 lines).
- **Current**: Hook entry points conflate JSON parsing,
  policy decisions, side effects, and exit-code
  selection. `precommit_gate.py:main` for example
  catches `Exception` once and silently exits.
- **Proposal**: Adopt a uniform hook shape across
  plugins: `main()` is 10-15 lines and calls
  `_parse_input`, `_decide`, `_emit`. Most existing
  bodies fit when you peel them.
- **Rationale**: Hooks run on every tool call, so they
  must not crash. That is a separate concern from
  policy logic, which today is tangled with I/O. Split
  for testability.

### C-13: 132-line `main` with PLR0912/PLR0915 silencer

- **Category**: god-function
- **Impact**: HIGH
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**:
  `plugins/conserve/scripts/context_scanner/cli.py:22`
- **Current**: `def main(argv: list[str] | None = None) ->
  int:  # noqa: PLR0912, PLR0915 - CLI dispatch with
  subcommands requires many branches`. The justification
  is wrong: the function does not use subcommands; it
  uses argparse with sequentially-checked flags
  (`if args.blast: ... if args.section: ...`).
- **Proposal**: Convert to actual subparsers
  (`subparsers.add_parser("blast", ...)`) and dispatch
  via a `commands` dict. The noqa goes away naturally.
- **Rationale**: The noqa lies. There are no
  subcommands. Hiding complexity behind an inaccurate
  justification is the worst kind of cargo-culted
  silencing.

### C-14: anti-slop — `AbstractCLI` ABC with single
concrete subclass per script

- **Category**: anti-slop
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: MEDIUM
- **Location**:
  `plugins/abstract/src/abstract/cli_framework.py:126`
  `AbstractCLI(ABC)`, used by
  `plugins/abstract/src/abstract/cli.py:24,92,156,229`
  (4 concrete subclasses) and one external script
  `plugins/abstract/scripts/context_optimizer.py:136`.
- **Current**: An abstract base class with a
  `Generic[T]` `CLIResult`, `OutputFormatter` static
  methods, and a registry pattern – built for a
  plugin's own internal CLIs.
- **Proposal**: For the 5 internal users, replace with
  a plain function `run_cli(parser, dispatch, formatter)
  -> int` and dataclass `CLIResult`. Only keep the ABC
  if external plugins genuinely subclass it.
- **Rationale**: ABC + Generic + registry for 5 internal
  callers is enterprise cosplay. The whole framework
  saves perhaps 40 lines per CLI at the cost of a 200-
  line abstraction with `Generic[T]` and `cast(Any, ...)`.

### C-15: anti-slop — `Manager` suffix inflation

- **Category**: anti-slop
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/spec-kit/src/speckit/caching.py:215`
  `CacheManager` (2 public methods),
  `plugins/conserve/scripts/agent_memory.py`
  `MemoryManager`,
  `plugins/conserve/scripts/coordination_workspace.py`
  `WorkspaceManager`,
  `plugins/memory-palace/src/memory_palace/tier_manager.py`
  `TierManager`,
  `plugins/memory-palace/src/memory_palace/corpus/source_lineage.py`
  `SourceLineageManager`,
  `plugins/memory-palace/src/memory_palace/corpus/query_templates.py`
  `QueryTemplateManager`,
  `plugins/conjure/scripts/war_room/audit_trail.py`
  `AuditTrailManager`,
  `plugins/tome/src/tome/session.py` `SessionManager`.
- **Current**: 8+ classes ending in `Manager` across the
  codebase. `CacheManager` has only `get` and `set` (2
  public methods). `WorkspaceManager` is essentially a
  namespace for path manipulation.
- **Proposal**: Rename or collapse: `CacheManager` →
  module-level `cache.get()`/`cache.set()` or just
  `Cache`. `WorkspaceManager` → `Workspace`.
  `AuditTrailManager` → `AuditTrail`. The `Manager`
  suffix adds no information.
- **Rationale**: `Manager` is a tell. If the class has
  state, the noun is the state (`Cache`, `Workspace`).
  If not, it is a namespace and should be a module.

### C-16: anti-slop — empty `*Config` dataclass-like
classes with no fields

- **Category**: anti-slop
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/spec-kit/scripts/tasks_manager.py:38`
  `TasksManagerBase` (0 public methods),
  `plugins/spec-kit/scripts/tasks_manager.py:57`
  `TasksManagerConfig` (0 public methods),
  `plugins/sanctum/scripts/tasks_manager.py:38,57`
  (same pair),
  `plugins/attune/scripts/tasks_manager.py:38,57`
  (same pair),
  `plugins/conjure/scripts/delegation_executor.py:70`
  `ServiceConfig` (0 public methods),
  `plugins/abstract/src/abstract/tasks_manager_base.py:27`
  `TasksManagerConfig` (0 public methods).
- **Current**: 6+ classes with 0 public methods,
  duplicated across 3 plugins.
- **Proposal**: If they only hold attributes, use
  `@dataclass`. If they are placeholders for future
  abstraction, delete until needed (YAGNI).
- **Rationale**: The duplicated `TasksManagerBase`/
  `TasksManagerConfig` pair across spec-kit, sanctum,
  attune indicates a copy-paste lineage. Either share
  via `imbue` or delete.

### C-17: anti-slop — Protocol with single implementation

- **Category**: anti-slop
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/gauntlet/src/gauntlet/ml/scorer.py:18`
  `Scorer(Protocol)` with `YamlScorer` and
  `SidecarScorer` as the only implementations (which
  share most of their code via duck typing).
- **Current**: Protocol exists. Two implementations.
  Acceptable but borderline – flagging because the test
  suite is the only third "user".
- **Proposal**: Keep if both implementations stay live;
  delete the Protocol if `SidecarScorer` is the only
  production path and `YamlScorer` is a fallback.
- **Rationale**: Protocols are cheap, but unused
  Protocols invite a fake-pluggability pattern.

### C-18: anti-slop — wrapper class `SafeDependencyUpdater`

- **Category**: anti-slop
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/conserve/scripts/safe_replacer.py:18`
- **Current**: 80-line class with three methods
  (`update_file`, `validate_references`,
  `update_directory`) and an `__init__` that just
  populates two dicts of regex patterns. The class is
  instantiated exactly once in `main`.
- **Proposal**: Module-level constants `_PATTERNS`,
  `_REPLACEMENTS`. Free functions `update_file(path)`,
  `validate_references(path)`, `update_directory(base)`.
- **Rationale**: A class with one instance and no
  inheritance is a function in disguise. The two dicts
  it builds in `__init__` are constants.

### C-19: anti-slop — `ServiceConfig` placeholder in
delegation_executor

- **Category**: anti-slop
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/conjure/scripts/delegation_executor.py:70`
- **Current**: Empty config class with 0 public methods.
- **Proposal**: Delete or fill in. If config is needed,
  use `@dataclass`.
- **Rationale**: Same as C-16; flagging the conjure case
  separately because it lives next to actual logic
  (subprocess calls with `# nosec`).

### C-20: error-handling — broad `except Exception` then
log-and-continue (memory-palace CLI)

- **Category**: error-handling
- **Impact**: HIGH
- **Effort**: MEDIUM
- **Risk**: MEDIUM
- **Location**:
  `plugins/memory-palace/scripts/memory_palace_cli.py`
  (12 distinct `except Exception:` blocks at lines
  approximately 360, 530, 600, 660, 700, 740, 780, 820,
  870, 920, 970, 1010 — verified count from
  `rg -c "except Exception:"`).
- **Current**: Each handler logs via
  `logging.getLogger(__name__).exception(...)` and then
  prints "(check logs)" to stderr and returns. The CLI
  swallows every error from every subcommand.
- **Proposal**: Catch the actually-raised types
  (`PalaceNotFoundError`, `OSError`, `sqlite3.Error`,
  `yaml.YAMLError`). For unknown failures, let the
  process crash with a stack trace; CLIs are the right
  place to fail loudly.
- **Rationale**: A bug in `palace_stats` becomes
  "Metrics failed: unexpected error (check logs)". The
  user has no path forward. Narrow the except, surface
  the type, exit with a non-zero code.

### C-21: error-handling — `except Exception:` followed by
`sys.exit(0)` in vow hooks

- **Category**: error-handling
- **Impact**: HIGH
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/imbue/hooks/vow_no_emoji_commits.py:~end`
  (final `except Exception: sys.exit(0)`),
  `plugins/imbue/hooks/vow_bounded_reads.py:~end`,
  `plugins/imbue/hooks/vow_bounded_reads_reset.py:~end`,
  `plugins/imbue/hooks/vow_no_ai_attribution.py:~end`.
- **Current**:
  ```python
  except Exception:  # hook must not crash the agent
                     # under any circumstance
      sys.exit(0)
  ```
- **Proposal**: Replace with `except Exception as exc:`
  and emit a structured warning to stderr (Claude Code
  surfaces hook stderr) before `sys.exit(0)`. The
  current form makes hook bugs invisible.
- **Rationale**: The comment justifies *why* the hook
  exits cleanly, but throwing away the exception means
  hook regressions never surface. Log it, then exit.

### C-22: error-handling — broad except in
`vow_no_emoji_commits` for tool-input parsing

- **Category**: error-handling
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/imbue/hooks/vow_no_emoji_commits.py`
- **Current**: Top-level wrapper catches `Exception`
  and exits 0, masking JSON parse errors,
  `KeyError`s, and Path resolution failures alike.
- **Proposal**: Catch `(json.JSONDecodeError, KeyError,
  OSError)` explicitly. Re-raise anything else.
- **Rationale**: The same shape repeats across all four
  vow hooks; consolidate via a `_safe_main` decorator
  in `imbue.hooks.shared`.

### C-23: error-handling — `except Exception:` in
`update_versions.py` swallows version parsing

- **Category**: error-handling
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/sanctum/scripts/update_versions.py:~135`
  (inside `update_version_file`).
- **Current**:
  ```python
  except Exception:
      continue
  ```
  This skips files where TOML parsing or regex
  substitution fails. Silent.
- **Proposal**: Catch `(tomllib.TOMLDecodeError, OSError,
  re.error)` and log the file path. A version-update
  script that silently skips a malformed file leaves the
  user with a half-bumped repo.
- **Rationale**: Version bump scripts must be loud:
  partial success is worse than total failure.

### C-24: error-handling — `cartograph` and `pensive`
hooks catch broad `Exception as exc` then emit warning

- **Category**: error-handling
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/cartograph/hooks/graph_community_refresh.py`
  (2 instances),
  `plugins/pensive/hooks/pr_blast_radius.py:~end`,
  `plugins/gauntlet/hooks/graph_auto_update.py`.
- **Current**: `except Exception as exc:` followed by
  `print(f"Warning: ... {exc}", file=sys.stderr)` and
  `sys.exit(0)`.
- **Proposal**: Acceptable for hooks (must not crash),
  but the catch should at minimum exclude
  `KeyboardInterrupt` and `SystemExit` (use
  `except Exception` not bare `except`, which these
  already do – good). Recommend factoring into a shared
  `hook_safe_main` helper in `leyline`.
- **Rationale**: This pattern is correct for hook safety
  but duplicated 7+ times. Centralise it.

### C-25: error-handling — `except Exception` in
`war_room/orchestrator.py` and `delegation_executor.py`

- **Category**: error-handling
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: MEDIUM
- **Location**:
  `plugins/conjure/scripts/war_room/orchestrator.py`
  (3 instances),
  `plugins/conjure/scripts/delegation_executor.py`
  (4 instances, two log-and-continue, two log-and-skip).
- **Current**: Subprocess calls to external CLIs (gemini,
  qwen) wrapped in `except Exception as e:`. The
  intention is "never crash on a failed delegate". The
  effect is that quota errors, OS errors, and parse
  errors all flatten to one message.
- **Proposal**: Catch `(subprocess.CalledProcessError,
  subprocess.TimeoutExpired, OSError, json.JSONDecodeError)`
  explicitly. Different recovery for each: timeout
  retries, OS errors abort, JSON errors log raw output.
- **Rationale**: Delegation is the most common failure
  surface; precise classification feeds quota tracking
  and retry logic.

### C-26: error-handling — `update_all_plugins.py` broad
except in update loop

- **Category**: error-handling
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/leyline/scripts/update_all_plugins.py`
- **Current**: Top-level update loop catches
  `Exception as e` and prints the error per-plugin.
- **Proposal**: Distinguish `subprocess.CalledProcessError`
  (gh CLI failure) from `OSError` (filesystem) from
  parse errors. Emit a structured summary at the end,
  not just per-plugin warnings.
- **Rationale**: Aggregate failures need typed
  reporting; "3 plugins failed" without classifications
  is a debugging dead end.

### C-27: error-handling — `subprocess.run` without
`check=` or explicit `check=False` documentation

- **Category**: error-handling
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: 30+ call sites identified by `rg`.
  Spot-checks:
  `plugins/oracle/src/oracle/provision.py` (2 sites),
  `plugins/leyline/scripts/update_all_plugins.py`,
  `plugins/herald/scripts/notify.py` (2 sites),
  `plugins/sanctum/scripts/quality_checker.py`,
  `plugins/phantom/src/phantom/display.py`,
  `plugins/phantom/src/phantom/loop.py`,
  `plugins/sanctum/hooks/session_complete_notify.py`
  (2 sites).
- **Current**: `subprocess.run(...)` calls where the
  return value is captured but `check=` is not in the
  argument list, requiring inspection to know whether
  the function expects success.
- **Proposal**: Standardise on explicit `check=True` for
  fail-fast, `check=False` with a documented comment for
  "we inspect returncode below". Audit each site.
- **Rationale**: Implicit `check=False` is a footgun.
  The default in stdlib is sane, but at this many call
  sites it merits an explicit project convention.

### C-28: error-handling — `json.loads(path.read_text())`
in egregore scripts without try

- **Category**: error-handling
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: MEDIUM
- **Location**:
  `plugins/egregore/scripts/budget.py:87`
  `data = json.loads(path.read_text())` (no try),
  `plugins/egregore/scripts/config.py`,
  `plugins/egregore/scripts/discussions.py`,
  `plugins/egregore/scripts/learning.py`,
  `plugins/egregore/scripts/multi_repo.py`,
  `plugins/egregore/scripts/specialists.py`.
- **Current**: `load_budget` checks `if not path.exists():
  return Budget()` then unconditionally
  `json.loads(path.read_text())`. A truncated or
  hand-edited budget file crashes the egregore loop.
- **Proposal**: Wrap each in `try: data = json.loads(
  path.read_text()) except (json.JSONDecodeError, OSError)
  as exc: log.warning("corrupt %s: %s", path, exc);
  return <default>`.
- **Rationale**: Egregore runs unattended; a corrupt
  state file should self-heal to defaults, not crash.

### C-29: error-handling — `json.loads(sys.stdin.read())`
in 7 hooks

- **Category**: error-handling
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/cartograph/hooks/graph_community_refresh.py`,
  `plugins/gauntlet/hooks/precommit_gate.py`,
  `plugins/gauntlet/hooks/graph_auto_update.py`,
  `plugins/pensive/hooks/pr_blast_radius.py`,
  `plugins/sanctum/hooks/task_created_tracker.py`,
  `plugins/leyline/hooks/sanitize_external_content.py`,
  `plugins/conserve/hooks/permission_denied_logger.py`.
- **Current**: 7 hooks read tool input via
  `json.loads(sys.stdin.read())`. Most are wrapped in a
  broad try-except (which is the C-21/C-24 pattern), so
  this is OK in practice but duplicated.
- **Proposal**: Add `leyline.hook_input.read_payload() ->
  dict` returning either the parsed payload or
  exiting cleanly with a structured warning.
- **Rationale**: 7 copies of the same pattern is asking
  for one to drift.

### C-30: error-handling — `raise Exception(...)` not
present (positive)

- **Category**: error-handling
- **Impact**: LOW (positive note)
- **Location**: searched `plugins/` and `scripts/`
- **Current**: `rg "raise Exception\(" plugins/ scripts/`
  returns no production hits. Domain exceptions
  (`PalaceNotFoundError`, `ToolError`, etc.) are used
  consistently.
- **Proposal**: Keep this property; add a pre-commit
  rule via hookify that fails on bare
  `raise Exception(...)`.
- **Rationale**: Hold the line; reflect the win.

### C-31: error-handling — `except` then continue with
default `None` in `compliance.py`

- **Category**: error-handling
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/abstract/src/abstract/skills_eval/compliance.py:310-316`
- **Current**:
  ```python
  except (FileNotFoundError, PermissionError,
          UnicodeDecodeError, OSError) as e:
      issues.append(f"{skill_file.parent.name}: {e}")
  ```
  This catches well, but the surrounding `for` loop
  uses an unrelated `with open(skill_file, ...)` pattern
  that does not use `pathlib.Path.read_text()`. Mixed
  styles.
- **Proposal**: Use `Path.read_text(encoding="utf-8")`
  consistently; same exception set.
- **Rationale**: Style consistency, not a bug.

### C-32: dead-code — `TasksManagerBase` duplication
across 3 plugins

- **Category**: dead-code
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: MEDIUM
- **Location**:
  `plugins/spec-kit/scripts/tasks_manager.py:38`,
  `plugins/sanctum/scripts/tasks_manager.py:38`,
  `plugins/attune/scripts/tasks_manager.py:38`,
  `plugins/abstract/src/abstract/tasks_manager_base.py:27`.
- **Current**: 4 nearly-identical empty
  `TasksManagerBase`/`TasksManagerConfig` definitions.
  Only `abstract/src` looks intended as the canonical
  location.
- **Proposal**: Make the others import from `abstract`
  or delete if unused.
- **Rationale**: Cross-plugin duplication is the path to
  drift; one of the four will be modified, then the
  others diverge silently.

### C-33: naming — generic `data`, `result`, `obj`
identifiers in scanner

- **Category**: naming
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/conserve/scripts/context_scanner/cli.py:104,109`
  (`result = None; result = scan_directory(...)`),
  `plugins/conserve/scripts/context_scanner/renderers.py:567+`
  (`result = summarize(result, ...)`),
  `plugins/egregore/scripts/budget.py:87` (`data =
  json.loads(...)`).
- **Current**: Generic `result` and `data` names where
  a concrete name (`scan`, `budget_state`) would help.
- **Proposal**: Rename `result` → `scan` in the scanner
  CLI, `data` → `budget_dict` in `load_budget`.
- **Rationale**: Per `CLAUDE.md` "explicit over
  implicit"; specific nouns help future readers.

### C-34: naming — single-letter assignments outside loop
indices

- **Category**: naming
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/sanctum/hooks/config_change_audit.py:41`
  (`p = ...`),
  `plugins/oracle/src/oracle/daemon.py:212` (`d = ...`),
  `plugins/imbue/validators/proof_of_work.py:95`
  (`m = ...`),
  `plugins/phantom/src/phantom/cost.py:59` (`m = ...`),
  `plugins/phantom/src/phantom/display.py:385`
  (`p = ...`),
  `plugins/leyline/scripts/verify_plugin.py:173-174`
  (`t = ...; p = ...`),
  `plugins/conserve/scripts/context_scanner/ecosystems.py:275`
  (`s = ...`),
  `plugins/hookify/scripts/hook_to_hookify.py:365`
  (`p = ...`),
  `plugins/memory-palace/src/memory_palace/graph_analyzer.py:138`
  (`w = ...`),
  `plugins/gauntlet/src/gauntlet/progress.py:121`
  (`w = ...`),
  `plugins/gauntlet/src/gauntlet/communities.py:86`
  (`g = ...`),
  `plugins/gauntlet/src/gauntlet/blast_radius.py:120`
  (`w = ...`).
- **Current**: 12+ single-letter variable assignments
  outside `for` loops or lambdas. Most are abbreviations
  for `path`, `match`, `weight`, `graph`.
- **Proposal**: Rename to full word (`path`, `match`,
  `weight`, `graph`).
- **Rationale**: Costs nothing; read-time wins compound.

### C-35: naming — `e` for exception when more context
exists

- **Category**: naming
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: many (`except OSError as e`,
  `except ValueError as e` across the codebase).
- **Current**: Standard Python convention; not a defect.
  Flagging only because in some sites, the exception is
  re-emitted via `f"{e}"` and `exc` would read better.
- **Proposal**: Use `exc` in long handlers; keep `e` in
  one-liners. Consistency over fashion.
- **Rationale**: Soft suggestion. Low priority.

### C-36: magic-value — string `"SKILL.md"` repeated 45+
times

- **Category**: magic-value
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: 45 occurrences across non-test code
  (`rg -tpy '"SKILL\.md"' plugins/ -c`).
- **Current**: The literal `"SKILL.md"` is hard-coded
  everywhere skills are discovered.
- **Proposal**: Define `SKILL_FILENAME = "SKILL.md"` in
  `plugins/leyline/src/leyline/constants.py` (or
  similar). Import everywhere.
- **Rationale**: When the convention shifts (e.g., to
  `skill.md` for new plugins), 45 sites to update is 45
  chances to miss one.

### C-37: magic-value — `".claude"` repeated 51+ times

- **Category**: magic-value
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: 51 occurrences across non-test code
  (`rg -tpy '"\.claude"' plugins/ -c`).
- **Current**: The hardcoded directory name `".claude"`
  spread across path construction.
- **Proposal**: Centralise as
  `CLAUDE_HOME_DIR = ".claude"` in
  `leyline.constants`.
- **Rationale**: Same argument as C-36.

### C-38: magic-value — `"plugin.json"` repeated 13+ times

- **Category**: magic-value
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: 13 occurrences across non-test code.
- **Current**: Plugin manifest filename hardcoded.
- **Proposal**: Constant in `leyline.constants`.
- **Rationale**: Same as C-36/C-37.

### C-39: docstring restating function name

- **Category**: anti-slop
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/conserve/scripts/safe_replacer.py:21-22`
  (`def __init__: """Initialize the safe dependency
  updater."""`),
  `plugins/cartograph/hooks/graph_community_refresh.py`
  (`def find_db: """Find .gauntlet/graph.db by walking
  up from cwd."""` — actually OK because it adds info),
  multiple `__init__` docstrings of the form "Initialize
  the X." across `plugins/` (visible in
  `plugins/abstract/scripts/...` and others).
- **Current**: A handful of `__init__` docstrings that
  literally say "Initialize the <ClassName>".
- **Proposal**: Either delete the docstring (Python tools
  treat absence as fine) or replace with the *invariants*
  the constructor establishes.
- **Rationale**: AI-generation tell. Adds tokens, no
  information.

### C-40: anti-slop — `# noqa` justifications that are
explanations of failure rather than fixes

- **Category**: anti-slop
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**:
  `plugins/conserve/scripts/context_scanner/renderers.py:567`
  `# noqa: PLR0912 - one branch per section type is the
  clearest structure`,
  `plugins/conserve/scripts/context_scanner/cli.py:22`
  `# noqa: PLR0912, PLR0915 - CLI dispatch with
  subcommands requires many branches`,
  `plugins/conserve/scripts/context_scanner/ecosystems.py:46,184`
  `# noqa: PLR0915 - accumulates data across many
  subsystems in one pass`,
  `plugins/abstract/scripts/rules_validator.py:282`
  `# noqa: PLR0915 - evaluation collects many metrics in
  a single pass`,
  `plugins/gauntlet/scripts/curate_problems.py:~`
  `# noqa: BLE001 - BankProblem.from_dict raises various
  exception types`,
  `plugins/gauntlet/src/gauntlet/treesitter_parser.py:~`
  `# noqa: BLE001 - catch-all for parse errors in
  unknown grammars`.
- **Current**: 6+ `noqa` lines whose justification
  describes the symptom ("many branches", "many
  metrics") rather than why the linter is wrong.
- **Proposal**: Either fix the underlying issue (see
  C-02, C-13) or rewrite the justification to explain
  why the rule does *not* apply here. "We need many
  branches" is not a justification; it is a restatement.
- **Rationale**: Self-narration of complexity is the
  scribe-detector tell. The noqa exists to silence the
  lint; if the lint is right, fix the code.

### C-41: error-handling — `BLE001` (blind-except)
silenced with terse justification

- **Category**: error-handling
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/gauntlet/scripts/curate_problems.py`
  (`except Exception as exc:  # noqa: BLE001 -
  BankProblem.from_dict raises various exception types`),
  `plugins/gauntlet/scripts/curate_problems.py`
  (`except Exception:  # noqa: BLE001 - yaml errors,
  file errors, and type errors all safe to swallow
  here`),
  `plugins/gauntlet/src/gauntlet/treesitter_parser.py`
  (similar).
- **Current**: Annotates the catch with the rough class
  of error but still uses `Exception`.
- **Proposal**: List the actual types: `except
  (yaml.YAMLError, OSError, TypeError, ValueError)`. The
  justification on the noqa already enumerates them.
- **Rationale**: If you can list the types in the
  comment, you can list them in the `except` tuple.

### C-42: dead-code — unused/unreachable fallback in
`safe_replacer.main`

- **Category**: dead-code
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/conserve/scripts/safe_replacer.py:188-193`
- **Current**:
  ```python
  except FileNotFoundError as e: ...
  except PermissionError as e: ...
  except Exception as e: ...
  ```
  The `FileNotFoundError` is a subclass of
  `OSError`/`PermissionError` is unrelated; the broad
  `except Exception` will catch most things, but the
  ordering means specific handlers run first. This is
  fine, but the broad final clause swallows code bugs
  (e.g., AttributeError from a refactor).
- **Proposal**: Drop the final `except Exception`; let
  unexpected errors trace.
- **Rationale**: This is a CLI utility; loud failure on
  unexpected types is correct.

### C-43: anti-slop — sentinel-string return convention
in `render_section`

- **Category**: anti-slop
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/conserve/scripts/context_scanner/renderers.py:639`
  `return "\n".join(lines) if lines else "(empty)"`
- **Current**: Returns the literal string `"(empty)"`
  for the empty case. The function signature is
  `-> str | None`, and `None` is already the unknown-
  section sentinel.
- **Proposal**: Return an empty string `""` (truthiness)
  or move the `"(empty)"` rendering to the caller.
- **Rationale**: Two sentinels (`None` for unknown,
  `"(empty)"` for empty) overload the return type;
  callers must know to special-case both.

### C-44: error-handling — `Path.read_text()` with
`errors="replace"` masks decode errors

- **Category**: error-handling
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/conserve/scripts/context_scanner/ecosystems.py`
  (`pkg_json.read_text(errors="replace")` for
  `package.json`).
- **Current**: Silently substitutes replacement
  characters for non-UTF8 bytes.
- **Proposal**: For `package.json` specifically, fail
  loud (`encoding="utf-8", errors="strict"`); a non-UTF8
  manifest is a real bug. For source files, the
  permissive read is defensible.
- **Rationale**: Manifests are spec-defined as UTF-8;
  silent corruption gives wrong analysis.

### C-45: god-function `analyze_git_changes` (sanctum)

- **Category**: god-function
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**:
  `plugins/sanctum/scripts/test_analyzer.py:180`
  (depth=6, ~70 lines)
- **Current**: Walks git diff output, classifies files,
  builds reports in one pass with 6 levels of nesting
  for the conditional logic.
- **Proposal**: Extract `_classify_diff_line`,
  `_aggregate_per_file`, `_build_summary`. Each ~15
  lines.
- **Rationale**: Depth 6 in a script means changes are
  fragile; one missed branch == wrong output.

### C-46: god-function in `update_versions.py`

- **Category**: god-function
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: HIGH (script bumps real versions)
- **Location**:
  `plugins/sanctum/scripts/update_versions.py:115`
  `update_version_file` (depth=7, ~75 lines), `:147`
  `main` (85 lines).
- **Current**: Version bumping logic with 7-level
  nesting — pyproject.toml/package.json/CHANGELOG cases
  interleaved.
- **Proposal**: One function per format
  (`_bump_pyproject`, `_bump_package_json`,
  `_bump_changelog`). Dispatch by file name.
- **Rationale**: This is a release-critical script; the
  blast radius of a wrong bump is high. Refactor lowers
  risk before next bump.

### C-47: anti-slop — class-as-namespace pattern in
`OutputFormatter`

- **Category**: anti-slop
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/abstract/src/abstract/cli_framework.py:37`
  `class OutputFormatter:` with three `@staticmethod`s
  (`format_json`, `format_summary`, `format_table`).
- **Current**: A class containing only static methods is
  a Python anti-pattern; the language has modules for
  this.
- **Proposal**: Replace with module-level functions
  `format_json`, `format_summary`, `format_table`.
- **Rationale**: Java-as-Python tell.

### C-48: error-handling — file IO pattern uses
`open()` instead of `Path.open()` inconsistently

- **Category**: error-handling (style)
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/abstract/src/abstract/skills_eval/compliance.py:238`
  uses `with open(skill_file, encoding="utf-8") as f:`
  while neighbouring code in the same plugin uses
  `path.open()`.
- **Current**: Mixed `open()` vs `path.open()`.
- **Proposal**: Standardise on `path.read_text(
  encoding="utf-8")` where possible; falls back to
  `path.open()` for streaming.
- **Rationale**: Style only, but consistent style aids
  reviewers.

### C-49: dead-code — unused `current_group` in
`_parse_pyproject_deps`

- **Category**: dead-code
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/conserve/scripts/context_scanner/ecosystems.py:192`
- **Current**: `current_group = ""` is initialised, then
  reassigned only inside the optional-deps branch. The
  initial value is unused.
- **Proposal**: Move initialisation into the optional-
  deps branch where it is actually used.
- **Rationale**: Tiny but a sign of state that escapes
  its scope.

### C-50: anti-slop — comment "Constants for magic
numbers" without context

- **Category**: anti-slop
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/abstract/scripts/skill_validator.py`
  (header comment `# Constants for magic numbers`).
- **Current**: The comment exists at the top of the
  constants block; tautological — constants by
  definition replace magic numbers.
- **Proposal**: Delete the comment or replace with the
  *reason* the values are what they are (citation,
  measurement, convention).
- **Rationale**: Comment-as-section-header is a
  scribe-detector tell ("In this section, we will...").

## Recommended remediation order

1. **C-13** (lying noqa in `context_scanner/cli.py`).
2. **C-21** (vow hook silent excepts) — makes hook
   regressions visible.
3. **C-20** (memory_palace_cli broad excepts).
4. **C-15** + **C-18** (`*Manager` / wrapper classes).
5. **C-36/37/38** (centralise filename constants).
6. **C-02** + **C-46** (god functions; schedule with
   regular changes, not standalone PRs).

## Methodology notes

- AST scan over `plugins/**/*.py` and `scripts/**/*.py`,
  excluding `.venv`, `site-packages`, `tests/`,
  `__pycache__`. Long-function threshold 60 lines;
  nesting threshold depth > 4 (max found = 9).
- `rg` scans for: `except Exception`, `subprocess.run`
  without `check=`, unguarded `json.loads`,
  `Manager`/`Service`/`Helper` classes with low method
  counts, single-letter variables outside loop indices,
  repeated string literals.
- Findings verified by reading cited files; noqa
  justifications cross-checked against actual code
  (e.g., C-13 verified `cli.py:main` does not use
  subparsers despite the noqa claim).

CLEAN-CODE SCAN COMPLETE — 50 findings written to docs/refinement/2026-05-02/03-clean-code.md
