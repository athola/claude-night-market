# Tier 3 Code Refinement Report

**Date:** 2026-03-20
**Status:** ALL 54 FINDINGS IMPLEMENTED
**Scope:** Full codebase (18 plugins, 888 files, ~266K lines)
**Agents:** 6 audit + 7 implementation agents
**Branch:** research-1.7.0
**Changes:** 51 files modified, 7 new files, +964/-842 lines

## Executive Summary

The codebase is well-structured with excellent plugin isolation
(only 1 cross-plugin import) and consistent use of dataclasses
and type annotations.
The audit surfaced **54 findings** across all 6 refinement
dimensions.
The most impactful issues cluster into three themes:

1. **Redundant parsing** (parseltongue): 27 `ast.parse()` calls
   across 3 skill files with no shared parse result.
   A single `suggest_improvements()` call triggers 4 separate
   parses of the same source code.
2. **Actual bugs** (memory-palace, minister, pensive):
   indentation-level errors, type-ignore suppressing real
   crashes, and heuristics matching test fixtures instead of
   real code.
3. **Cross-plugin duplication** (hooks): `escape_for_json`
   copied into 5 shell files with diverging implementations,
   `parse_skill_name` reimplemented 3 times.

## Findings by Priority

Findings are ranked by: HIGH impact + SMALL effort + LOW risk
first.
Severity: HIGH / MEDIUM / LOW.
Effort: S (<1hr) / M (1-4hr) / L (>4hr).

### Phase 1: Quick Wins (HIGH impact, S effort)

These are correctness bugs or significant quality issues fixable
in under an hour each.

| # | Plugin | File:Line | Dimension | Description |
|---|--------|-----------|-----------|-------------|
| 1 | memory-palace | `corpus/knowledge_orchestrator.py:158` | Bug | `last_validated = datetime.now(...)` is outside `except` block (indentation error), unconditionally overwrites parsed value. Decay scores always compute as 1.0. |
| 2 | memory-palace | `scripts/memory_palace_cli.py:476-477` | Bug / Dead Code | `list_skills()` computes description string but never stores or prints it. Command is a no-op. |
| 3 | minister | `src/minister/project_tracker.py:192` | Bug | `type: ignore[arg-type]` papers over crash when `earliest` is None or empty string. `datetime.fromisoformat("")` raises `ValueError`. |
| 4 | pensive | `skills/architecture_review.py:558-578` | Error Handling | Triple-nested `except Exception: pass` silently fabricates score of 10.0 with no bottlenecks. |
| 5 | memory-palace | `src/memory_palace/palace_manager.py:651-658` | Bug | Timezone-stripping comparison via `.replace(tzinfo=None)` silently misclassifies entries with non-UTC offsets. |
| 6 | conserve | `scripts/fix_long_lines.py:112-115` | Dead Code | Two `sum()` expressions computed and results silently discarded. Misleading intent. |
| 7 | conserve | `scripts/dependency_manager.py:28-62` | Clean Code | `dict[str, set\|list]` return type forces `isinstance` guards everywhere. Should be a dataclass. |
| 8 | imbue | `scripts/imbue_validator.py:213-223` | Duplication | `scan_and_validate()` called 3 times (once per public method), each re-reading all SKILL.md files from disk. |
| 9 | conserve | `hooks/context_warning.py:199` | Correctness | Hardcodes `Path.home() / ".claude"` instead of using `CLAUDE_HOME` env var. Context estimation silently fails in non-default environments. |

### Phase 2: Algorithmic and Structural (HIGH/MEDIUM impact, M effort)

| # | Plugin | File:Line | Dimension | Description |
|---|--------|-----------|-----------|-------------|
| 10 | parseltongue | `skills/async_analysis.py` (12 sites) | Algorithm | 12 redundant `ast.parse()` calls on same input. `suggest_improvements()` triggers 4 parses via sub-calls. Same pattern in `pattern_matching.py` (10 calls) and `testing_guide.py` (5 calls). Total: 27 redundant parses. |
| 11 | parseltongue | `skills/async_analysis.py:1013-1029` | Bug | `_collect_module_shared_state()` uses `ast.walk(tree)` (all depths) instead of `tree.body` (top-level only). Treats function-local variables as module-level shared state, generating false race condition warnings. |
| 12 | conjure | `scripts/war_room/orchestrator.py:378-450` | Duplication | 73-line `convene_delphi()` is near-verbatim copy of `delphi.py:33-106`. Two sources of truth that will diverge. |
| 13 | pensive | `skills/rust_review.py:129-143` | Bug | Ownership analysis matches literal test fixture strings (`"let moved_data = data"`). Never fires on real Rust code. |
| 14 | pensive | `skills/rust_review.py:1339-1395` | Bug | `create_rust_security_report` reads keys that `analyze()` never sets. Report always shows zeros for every metric. |
| 15 | pensive | `skills/rust_review.py:162-168` | Bug | `mixed_borrows` flags any line with both `&mut` and `&`. Matches valid function signatures, producing mass false positives. |
| 16 | conserve | `scripts/detect_duplicates.py:222-248` | Algorithm | O(n^2) overlap scan: full list traversal for every candidate block. ~500K comparisons per 1K-line file. |
| 17 | spec-kit | `src/speckit/caching.py:131-145` | Bug | `invalidate(key)` does not accept `data` param, so entries stored with `data=` are never actually invalidated. |
| 18 | hooks (5 files) | `escape_for_json` across conserve, imbue, memory-palace | Duplication | ~70-line bash function copied into 5 hook files. `setup.sh` variants omit control-character escaping present in the canonical version. |

### Phase 3: Clean Code and Duplication (MEDIUM/LOW impact)

| # | Plugin | File:Line | Dimension | Description |
|---|--------|-----------|-----------|-------------|
| 19 | memory-palace | `project_palace.py:349,648,685` + `palace_manager.py` (2 sites) | Duplication | 5 independent glob-open-parse loops iterating palace JSON files. Should be a shared `_iter_palace_files()` generator. |
| 20 | memory-palace | `palace_manager.py:460-565` | Clean Code | `sync_from_queue` has 12 branches (suppressed with `noqa: PLR0912`), mixes 3 concerns: parsing, routing, queue write-back. |
| 21 | memory-palace | `project_palace.py:140-142` | Anti-Slop | `ReviewEntry.__init__` hashes with `datetime.now()` for non-deterministic ID, then `from_dict` overwrites it. Hash in `__init__` is both unreliable and redundant. |
| 22 | memory-palace | `scripts/memory_palace_cli.py:616-631` | Bug | `prune_apply` constructs `_manager()` twice in sequence. Each reads from disk; concurrent write between calls produces inconsistent state. |
| 23 | pensive | `skills/architecture_review.py:183-213` | Algorithm | `analyze_cohesion` rescans full file content per keyword group. `.lower()` called repeatedly instead of once. |
| 24 | pensive | `skills/architecture_review.py:317-353` | Anti-Slop | `check_dependency_inversion` scans for 6 hardcoded class names (`MySQLDatabase`, etc.). Toy-example data with zero generality. |
| 25 | pensive | `skills/architecture_review.py:603` | Anti-Slop | Flags `"for item in " in content` as sequential-processing bottleneck. Matches every Python file ever written. |
| 26 | pensive | `skills/rust_review.py:402-437` | Bug | `analyze_async_patterns` tracks `in_async_fn` with single boolean, reset on any `}`. Nested blocks prematurely clear the flag. |
| 27 | pensive | `skills/rust_review.py:44-45` | Clean Code | Mutable class-level attributes with `noqa: RUF012` suppression. Should be instance attributes in `__init__`. |
| 28 | pensive | `severity_mapper.py:112-121` | Anti-Slop | Deprecated `SeverityMapper` class still imported. Should be removed and callers updated. |
| 29 | sanctum | `validators.py:387-406,535-546` | Duplication | `extract_skill_references` duplicated between `SkillValidator` and `CommandValidator` with silent behavioral difference. |
| 30 | parseltongue | `skills/pattern_matching.py:493-570` | Duplication | Observer detection duplicated verbatim with identical 7-element method set between `_check_observer_pattern()` and `recognize_gof_patterns()`. |
| 31 | parseltongue | `skills/testing_guide.py:820` | Bug | `"for " in code` triggers "data-driven testing" credit for any file with a for-loop. |
| 32 | parseltongue | `skills/async_analysis.py:1228-1288` | Algorithm | Sequential `await` calls in `validate_best_practices()` that could use `asyncio.gather()`. Ironic for an async analysis tool. |
| 33 | parseltongue | `skills/pattern_matching.py:1045-1087` | Anti-Slop | `recognize_patterns()` is hollow: just lists classes and functions, not actual pattern recognition. Misleading API surface. |
| 34 | tome | `hooks/session_start.py` + `pre_compact.py` | Duplication | Near-identical 25-line hook bodies differing only in output message. No shared helper. |
| 35 | tome | `output/report.py:179` + `synthesis/ranker.py:68` + `output/export.py:43` | Duplication | Three independent implementations of group-by-channel when `group_by_theme` already exists. |
| 36 | tome | `session.py:58-68` | Algorithm | `load_latest` deserializes every session JSON file to find the most recent. Hook already uses O(1) `st_mtime` approach. |
| 37 | hookify | `core/rule_engine.py:172-209` | Clean Code | 38-line if-elif chain replaceable by a 5-element priority list. |
| 38 | hookify | `core/config_loader.py:155-168` + 2 more | Duplication | "Scan category dirs, glob `*.md`" pattern appears 3 times. Needs `_iter_bundled_rule_files()` helper. |
| 39 | hookify | `utils/helpers.py` + 3 more files | Duplication | Valid-events set `{"bash","file","stop","prompt","all"}` duplicated in 4 places. Should be a module-level constant. |
| 40 | hooks (3 files) | `parse_skill_name` across abstract, sanctum | Duplication | 3 independent implementations with different return contracts. |
| 41 | sanctum hooks | `deferred_item_sweep.py:19` + `watcher.py:55` | Duplication | `get_ledger_path()` byte-identical in two files in the same directory. |
| 42 | leyline | `quota_tracker.py:94,132,144,155,211` | Algorithm | `_cleanup_old_data()` called at every public entry point including read-only methods. Wasted work on probe paths. |
| 43 | attune | `scripts/attune_upgrade.py:8-10` | Architectural Fit | Bare-name imports with `type: ignore[import]` only work when CWD is `scripts/`. Invisible to test runner. |
| 44 | conserve | `scripts/detect_duplicates.py:271-293` | Clean Code | `find_similar_functions` hardcoded to `*.py`, ignores `extensions` parameter. |
| 45 | conserve | `growth_analyzer.py:70` + `growth_controller.py:63` | Clean Code | Naive `datetime.now().isoformat()` vs codebase standard `datetime.now(timezone.utc)`. |
| 46 | conserve | `scripts/safe_replacer.py:188` | Error Handling | Bare `except Exception` in `main()` formats all errors generically. |
| 47 | leyline | `hooks/noqa_guard.py:56-58` | Architectural Fit | Reads from env vars while all other hooks read from stdin. |
| 48 | abstract | `src/abstract/base.py:101-115` | Duplication | `AbstractScript.find_markdown_files` method is identical to module-level `find_markdown_files` function. |
| 49 | sanctum hooks | `session_complete_notify.py:292-317` | Duplication | `notify_windows` and `notify_wsl` share identical 60-line PowerShell toast XML template. |
| 50 | sanctum hooks | `post_implementation_policy.py:109-110` | Clean Code | `pass` after `print(...)` in except block is dead code. |
| 51 | hooks (5 files) | `escape_for_json` setup.sh variants | Error Handling | Truncated copies omit control-character escaping (`\x00`-`\x1f`). |
| 52 | hooks (2 files) | `session-start.sh` read timeout | Correctness | imbue uses `-t 1` (1s), conserve uses `-t 0.1` (100ms). Conserve may drop payload on slow machines. |
| 53 | spec-kit | `caching.py:18-168` | Anti-Slop | Three cache layers (memory, LRU, file) with no coherent invalidation. LRU is always a strict subset of memory dict. `cachetools` dependency for 10 lines of functionality. |
| 54 | memory-palace | `scripts/memory_palace_cli.py` (12 sites) | Error Handling | Broad `except Exception as e` on 12 call sites converts structured exceptions into generic strings. |

## Cross-Plugin Duplication Summary

| Pattern | Plugins | Files | Priority |
|---------|---------|-------|----------|
| `escape_for_json` (~70 lines) | conserve, imbue, memory-palace | 5 shell hooks | HIGH (diverged copies) |
| `ast.parse(code)` without caching | parseltongue (3 skills) | 3 files, 27 call sites | HIGH (performance) |
| Palace JSON glob-parse loop | memory-palace | 5 methods across 2 files | MEDIUM |
| `parse_skill_name` | abstract, sanctum | 3 hook files | MEDIUM |
| Group-by-channel | tome | 3 files | LOW |
| Observer detection | parseltongue | 2 methods in 1 file | LOW |
| `extract_skill_references` | sanctum | 2 validator classes | LOW |
| `get_ledger_path()` | sanctum | 2 hooks in same dir | LOW |
| Valid-events set | hookify | 4 locations | LOW |
| Bundled-rules dir scan | hookify | 3 methods | LOW |

## TODO/FIXME Triage

Of 844 reported TODO/FIXME comments across 209 files:

- **1 actionable**: `abstract/src/abstract/experience_library.py:5`
  (issue #296, context injection not yet implemented)
- **~843 non-actionable**: `.venv` packages, template scaffolding,
  documentation examples, and grep-command references

The reported metric should exclude `.venv` directories.

## Implementation Phases

### Phase 1: Bug Fixes (findings 1-9)
9 items, all S effort.
Fixes correctness issues and dead code.
Estimated: 1 focused session.

### Phase 2: Algorithmic Improvements (findings 10-18)
9 items, mostly M effort.
Addresses redundant parsing, O(n^2) algorithms,
and cross-plugin divergence.
Estimated: 2-3 focused sessions.

### Phase 3: Clean Code and Deduplication (findings 19-54)
36 items, mixed S/M effort.
Consolidates duplicated patterns and improves
code clarity.
Estimated: 4-5 focused sessions, can be done
incrementally.

## Methodology

Each of 6 agents analyzed its plugin group across all
6 refinement dimensions:

1. **Duplication**: Copy-paste patterns, similar utilities
2. **Algorithm Efficiency**: Unnecessary iterations, repeated
   computation
3. **Clean Code**: Long methods, deep nesting, magic values
4. **Architectural Fit**: Coupling violations, god objects
5. **Anti-Slop**: Premature abstraction, hollow patterns
6. **Error Handling**: Bare excepts, swallowed errors

All findings include file:line evidence with actual code
snippets verified against the source.
