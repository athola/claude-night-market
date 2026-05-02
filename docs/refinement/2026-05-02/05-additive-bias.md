# Additive Bias Findings

Scope: `plugins/*/src/`, `plugins/*/scripts/`, `plugins/*/hooks/`,
`scripts/`, `tests/`. Generated 2026-05-02.

## Summary

- Workarounds: 4
- Test tampering: 6
- Unnecessary additions: 8
- Compatibility cruft: 7
- Comment slop / stub claims: 2

Total: 27 findings.

## Findings

### B-01: `extract_frontmatter` and three other deprecated wrappers in `abstract.utils`

- **Category**: compat-cruft
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/abstract/src/abstract/utils.py:152-202`,
  `205-259`, `306-325`
- **Current**:
  ```python
  def extract_frontmatter(content: str) -> tuple[str, str]:
      warnings.warn("extract_frontmatter is deprecated; use FrontmatterProcessor directly", DeprecationWarning, ...)
      return FrontmatterProcessor.extract_raw(content)
  ```
  Plus `parse_frontmatter_fields`, `validate_skill_frontmatter`,
  `parse_yaml_frontmatter`. All four emit `DeprecationWarning`
  and forward to `FrontmatterProcessor`.
- **Proposal**: Delete all four and migrate the few remaining
  callers to `FrontmatterProcessor` directly. They are documented
  as deprecated and tests already exercise the new path.
- **Rationale**: Wrappers that exist only to print "this is
  deprecated" before forwarding are pure cost: imports, tests,
  and warning filter noise without functional value.

### B-02: `PensivePlugin` and `PluginLoader` "deprecated alias" classes

- **Category**: compat-cruft
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/pensive/src/pensive/plugin/__init__.py:11-50`
- **Current**: Two full classes (`PensivePlugin`, `PluginLoader`)
  with init/cleanup/state methods, each tagged
  `"""Deprecated: use run_code_review() directly."""`.
- **Proposal**: Delete both classes and the `__all__` entries
  for them. Keep only `discover_plugins`, `run_code_review`.
- **Rationale**: 40 lines preserved "for backwards compat"
  with no live consumers cited. The body of `analyze` returns
  `{}` -- a stub kept for an interface no one uses.

### B-03: `always_confirm` and `confirm_clicks_only` aliases pointing to no-op stubs

- **Category**: compat-cruft
- **Impact**: HIGH
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/phantom/src/phantom/safety.py:35-36`,
  `61-62`
- **Current**:
  ```python
  always_confirm = always_approve  # backward-compatible alias
  confirm_clicks_only = approve_clicks_only  # backward-compatible alias
  ```
  And `always_approve` / `approve_clicks_only` themselves
  always return `True` regardless of input.
- **Proposal**: Delete the four functions and aliases. Force
  callers that want a confirmation gate to supply a real
  `ConfirmCallback`. If a no-op default is genuinely needed,
  keep only `no_confirm`.
- **Rationale**: Names like `always_confirm` and `approve_clicks_only`
  imply gating but the implementation is `return True`. This is
  worse than absent: it satisfies static checks and code review
  while delivering no safety. Compounding cost: aliases for the
  stubs.

### B-04: PyYAML "fallback" path in `leyline.frontmatter`

- **Category**: compat-cruft
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/leyline/src/leyline/frontmatter.py:7-11`,
  `40-54`
- **Current**: `try: import yaml as _yaml; except ImportError: pass`
  followed by a custom `_fallback_parse` for when PyYAML is
  unavailable. Project requires `pyyaml>=6.0.2`
  (`pyproject.toml:20`).
- **Proposal**: Delete the try/except, drop `_fallback_parse`,
  and `import yaml` at the top.
- **Rationale**: PyYAML is a hard dependency. The fallback is a
  guard against a state that cannot occur, plus a separate code
  path with no test against the real parser.

### B-05: Plugin-specific `tasks_manager.py` files duplicate the same scaffolding

- **Category**: unnecessary
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: MEDIUM
- **Location**: `plugins/sanctum/scripts/tasks_manager.py:79-124`,
  `plugins/attune/scripts/tasks_manager.py` (138-141 lines),
  `plugins/spec-kit/scripts/tasks_manager.py` (139 lines)
- **Current**: Three near-identical 138-141 line files with a
  `# Plugin-specific constants (preserved for backward
  compatibility)` comment, differing only in a name string,
  env-var prefix, and a small keyword list.
- **Proposal**: Replace the three files with a single
  `TasksManagerConfig` JSON or YAML per plugin and instantiate
  the shared `tasks_manager_base` from a one-liner. Remove the
  "preserved for backward compatibility" constant blocks.
- **Rationale**: Same shape, different strings, copy-pasted three
  times. The "backward-compat" framing implies callers reference
  e.g. `sanctum.scripts.tasks_manager.PLUGIN_NAME`, but most
  consumers use the `TasksManagerConfig` instance.

### B-06: `self.tools_dir`, `self.skill_root`, `self.skills_root` aliases in skills_eval

- **Category**: unnecessary
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/abstract/src/abstract/skills_eval/performance.py:30`,
  `improvements.py:58,60`, `auditor.py`, `token_tracker.py`
- **Current**:
  ```python
  self.skills_dir = skills_dir
  self.tools_dir = skills_dir  # Alias for test compatibility
  self.skill_root = skills_dir  # Add alias for test compatibility
  self.skills_root = skills_dir  # Add alias for compatibility
  ```
- **Proposal**: Delete the alias attributes. Update the few
  tests that reference the aliases to use `skills_dir`.
- **Rationale**: Confirmed by grep: `self.tools_dir`, `self.skill_root`,
  and `self.skills_root` are written in `__init__` and never
  read inside the production source files. They exist solely to
  satisfy historical test signatures.

### B-07: `self.mock_context` set up in seven pensive test classes but never used

- **Category**: test-tamper
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/pensive/tests/skills/test_makefile_review.py:22-27`,
  and identical blocks in `test_api_review.py`, `test_bug_review.py`,
  `test_test_review.py`, `test_architecture_review.py`,
  `test_math_review.py`, `test_performance_review.py`
- **Current**:
  ```python
  def setup_method(self) -> None:
      self.skill = MakefileReviewSkill()
      self.mock_context = Mock()
      self.mock_context.repo_path = Path(tempfile.gettempdir()) / "test_repo"
      self.mock_context.working_dir = Path(tempfile.gettempdir()) / "test_repo"
  ```
- **Proposal**: Delete the `self.mock_context` lines (the only
  references to it are inside `setup_method` itself; tests use
  the `mock_skill_context` pytest fixture instead).
- **Rationale**: Setup creates state no test reads. Deleting it
  makes setup honest about what each test actually needs.

### B-08: Three perf "tests" in `test_review_workflow_integration.py` only assert `time.sleep` actually slept

- **Category**: test-tamper
- **Impact**: HIGH
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/imbue/tests/integration/test_review_workflow_integration.py:1036-1090`
- **Current**:
  ```python
  for _config in configs:
      for _skill in skills:
          time.sleep(0.001)
      workflow_times.append(...)
  ...
  assert total_duration < 1.0
  ```
  Marked `@pytest.mark.performance @pytest.mark.integration`,
  decorated with names like `test_individual_workflow_timing`
  and `test_skill_throughput`. They never call any production
  code.
- **Proposal**: Delete `test_individual_workflow_timing`,
  `test_skill_throughput`, and the surrounding "performance"
  block that just sleeps in nested loops. If real performance
  matters, write benchmarks against the actual workflow.
- **Rationale**: A test where the assertion is "time.sleep(0.001)
  took less than X seconds" is a test of the operating system
  scheduler, not of the code under test. It is mock-everything
  in its purest form: no SUT involvement.

### B-09: Three `xfail` markers labelled "not yet implemented"

- **Category**: test-tamper
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/abstract/tests/unit/test_validate_plugin.py:178,190,214`
- **Current**:
  ```python
  @pytest.mark.xfail(reason="Hook script existence check not yet implemented")
  ...
  @pytest.mark.xfail(reason="Event type validation not yet implemented")
  ```
- **Proposal**: Either implement the hook-script-existence and
  event-type-validation checks in `validate_plugin.py` (small
  effort, file-existence check), or delete the tests. Do not
  leave xfail tests as a "TODO marker".
- **Rationale**: `xfail` without a tracked issue ages. These
  three have been "not yet implemented" without a date or link
  to drive resolution.

### B-10: Test asserts `True` to paper over a known-broken `audit_skill_modules`

- **Category**: test-tamper
- **Impact**: HIGH
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**:
  `plugins/sanctum/tests/test_update_plugin_registrations_modules.py:486-498`,
  `557-560`
- **Current**:
  ```python
  # The "missing" calculation is:
  # referenced_modules - modules_on_disk, but referenced_modules only
  # includes refs that ARE in modules_on_disk, so "missing" is always
  # empty in current implementation.
  if "my-skill" in issues:
      assert "existing.md" not in issues["my-skill"].get("orphaned", [])
  else:
      # No issues at all -- existing.md is properly referenced
      assert True
  ```
- **Proposal**: Fix `audit_skill_modules` so that "missing" is
  computed against all references (including those not on disk),
  then rewrite the test as a real assertion (`assert
  "nonexistent.md" in issues["my-skill"]["missing"]`).
- **Rationale**: The comment admits the production code's
  contract ("missing always empty") is wrong, and the test was
  rewritten to match the bug instead of the spec. This is the
  textbook "test mocks the bug" pattern.

### B-11: `time.sleep(10)` in test scaffolding code under `pensive`

- **Category**: comment-slop
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/pensive/tests/skills/test_test_review.py:303-306`
- **Current**: This is inside an embedded sample of "anti-pattern
  test code" used as input to the skill under test. The string
  contains `time.sleep(10)  # Why 10 seconds?` and `assert True`
  on the next line.
- **Proposal**: Verified -- this is a string literal exemplar,
  not real test code. Leave it. (Listed here so future scanners
  can skip it.)
- **Rationale**: False positive on the bulk-grep; recorded for
  signal-to-noise tracking.

### B-12: `_validate_session_id` private alias kept "so old tests still work"

- **Category**: compat-cruft
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/memory-palace/src/memory_palace/session_history.py:40-42`
- **Current**:
  ```python
  # Backward-compatible alias so existing code and tests using
  # the old private name continue to work without modification.
  _validate_session_id = validate_session_id
  ```
- **Proposal**: Update the one referencing test
  (`tests/unit/test_session_history.py:22,891-898`) to import
  `validate_session_id` directly. Delete the alias.
- **Rationale**: A leading-underscore alias publicly re-exported
  for tests inverts the visibility convention. Deleting one
  alias and updating one import is cheaper than maintaining the
  shim.

### B-13: `validate_plugin_json` aliases `validate_structure`

- **Category**: compat-cruft
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/sanctum/src/sanctum/validators.py:642-645`
- **Current**:
  ```python
  @staticmethod
  def validate_plugin_json(content: dict[str, Any]) -> PluginValidationResult:
      """Alias for validate_structure for backward compatibility."""
      return PluginValidationResult.validate_structure(content)
  ```
- **Proposal**: Delete the alias; update callers to use
  `validate_structure`.
- **Rationale**: Method-level alias for a public method,
  documented as legacy. Either remove it or formally choose a
  canonical name.

### B-14: `DEFAULT_LIMITS` constant duplicates `GEMINI_QUOTA_CONFIG`

- **Category**: unnecessary
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/conjure/scripts/quota_tracker.py:131-145`
- **Current**:
  ```python
  GEMINI_QUOTA_CONFIG = QuotaConfig(
      requests_per_minute=60, requests_per_day=1000,
      tokens_per_minute=32000, tokens_per_day=1000000,
  )
  # Default limits dict for backward compatibility with tests
  DEFAULT_LIMITS = {
      "requests_per_minute": 60, "requests_per_day": 1000,
      "tokens_per_minute": 32000, "tokens_per_day": 1000000,
  }
  ```
- **Proposal**: Delete `DEFAULT_LIMITS` and its `limits`
  property (line 202-210). Update tests to instantiate
  `GeminiQuotaTracker` with no args (uses `GEMINI_QUOTA_CONFIG`)
  or via dataclass `asdict(GEMINI_QUOTA_CONFIG)` if a dict is
  required.
- **Rationale**: Two literals stating the same numbers. If they
  drift, the dict wins where it is used and silently masks
  bugs.

### B-15: `check_external_dependencies` returns hardcoded "ok" but claims "handles network timeouts gracefully"

- **Category**: comment-slop / unnecessary
- **Impact**: HIGH
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/pensive/src/pensive/skills/bug_review.py:704-719`
- **Current**:
  ```python
  def check_external_dependencies(self, _context: Any) -> dict[str, Any]:
      """Check external dependencies for issues."""
      # This method handles network timeouts gracefully
      # In a real implementation, this would check external services
      return {"status": "ok", "checked": [], "issues": []}
  ```
- **Proposal**: Either delete the method (callers can be removed)
  or replace the docstring/comment with `"""Stub: returns
  empty result. External-dependency checking not implemented."""`
  Most importantly remove the lie ("handles network timeouts
  gracefully") since there is no network call.
- **Rationale**: The comment promises behaviour that is not
  present. A future reader trusting the docstring will rely on a
  no-op as if it were a real check.

### B-16: 8 `try / except: pass` blocks swallowing structured failures in `auto_promote_learnings`, `post_learnings_to_discussions`, `delegation_executor`

- **Category**: workaround
- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**:
  `plugins/abstract/scripts/auto_promote_learnings.py` (2 blocks),
  `plugins/abstract/scripts/post_learnings_to_discussions.py` (5 blocks),
  `plugins/conjure/scripts/delegation_executor.py` (2 blocks),
  `plugins/conjure/scripts/usage_logger.py` (3 blocks)
- **Current**: Multiple
  ```python
  except (json.JSONDecodeError, OSError):
      pass
  ```
  and `except FileNotFoundError: pass`. Errors silently dropped;
  no `logger.debug`, no warning.
- **Proposal**: Replace bare `pass` with `logger.debug("...: %s",
  err)` so silent failures leave a trail. Where the exception is
  truly expected (e.g. cache miss), document why; otherwise
  surface and handle.
- **Rationale**: `except: pass` in production code is the most
  common form of "fix the symptom" -- the next time the JSON is
  malformed, the script silently produces wrong output and a
  debugging session burns hours.

### B-17: `skill_root`/`skills_dir`/`tools_dir` "alias" pattern reproduced in three skills_eval modules

- **Category**: unnecessary
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: see B-06 for line numbers.
  Repeats the same anti-pattern in three sibling files.
- **Proposal**: Replace with one canonical attribute name across
  all skills_eval modules; rename old test references.
- **Rationale**: Repeated occurrence of the same alias pattern
  signals a systemic preference for adding state over editing
  callers. This is the single highest-leverage cleanup signal in
  the package.

### B-18: `WarRoomOrchestrator` re-export shim at `war_room/__init__.py`

- **Category**: compat-cruft
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/conjure/scripts/war_room/__init__.py:1-62`
- **Current**: Module docstring explicitly says "Re-exports
  WarRoomOrchestrator and key types for backward compatibility."
  Imports 8 names from the implementation modules.
- **Proposal**: If the package layout (war_room.experts,
  war_room.orchestrator) is the intended public API, drop the
  re-exports and update callers. If `from war_room import X` is
  the public contract, drop the "backward compatibility" framing
  -- it is the API.
- **Rationale**: A package init that calls itself a
  "compatibility re-export" is admitting it has no clear contract.
  Either own the public surface or remove it.

### B-19: `Backward compat` reconstruction logic in `egregore.scripts.learning`

- **Category**: compat-cruft
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: MEDIUM
- **Location**: `plugins/egregore/scripts/learning.py:54-60`
- **Current**:
  ```python
  # Backward compat: reconstruct success_count from success_rate
  if "success_count" not in filtered and "success_rate" in data:
      freq = filtered.get("frequency", 1)
      filtered["success_count"] = round(data["success_rate"] * freq)
  ```
- **Proposal**: Run a one-time data migration to backfill
  `success_count`, then delete this branch. Lossy reconstruction
  on every load wastes cycles and risks silent rounding drift.
- **Rationale**: Reconstructing data from a derived field on
  every load is the opposite of "fix the root": the missing
  column should be backfilled once.

### B-20: Three `# noqa: BLE001` blanket-except suppressions in production hooks

- **Category**: workaround
- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: MEDIUM
- **Location**:
  `plugins/imbue/hooks/vow_bounded_reads.py`,
  `plugins/imbue/hooks/vow_bounded_reads_reset.py`,
  `plugins/memory-palace/hooks/web_research_handler.py`,
  `plugins/memory-palace/hooks/local_doc_processor.py`,
  `plugins/memory-palace/hooks/session_lifecycle.py`,
  `plugins/gauntlet/scripts/curate_problems.py`,
  `plugins/gauntlet/src/gauntlet/treesitter_parser.py`
- **Current**:
  ```python
  except Exception as exc:  # noqa: BLE001 - hook must not crash agent
  ```
- **Proposal**: Convert each `except Exception` into the
  narrowest specific exceptions actually raised by the inner
  block. For hooks, keep a final outer `except Exception` only
  at the top-level entry point with explicit logging.
- **Rationale**: Five files agree the inner block "must not
  crash the agent", but inside each block there are 1-3
  distinguishable failure modes (`OSError`, `JSONDecodeError`,
  custom plugin errors). Catching `Exception` here will swallow
  bugs in the new code added next sprint.

### B-21: `Re-export package symbols` shim at `makefile_dogfooder.py:25-32`

- **Category**: compat-cruft
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/abstract/scripts/makefile_dogfooder.py:25-32`
- **Current**:
  ```python
  # Re-export package symbols for backward compatibility with existing imports
  # (e.g. tests that do: from makefile_dogfooder import MakefileDogfooder)
  from dogfooder import (
      MakefileDogfooder, ProcessingConfig, ...
  )
  ```
- **Proposal**: Update the cited tests to
  `from dogfooder import MakefileDogfooder`. Delete the
  re-import block.
- **Rationale**: A 7-line re-export to support an import path
  the comment itself says only tests use. Easier to fix the
  tests once.

### B-22: `_walk_limited` cache `try/except OSError: pass` ignores stat failures

- **Category**: workaround
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/conserve/scripts/context_scanner/cache.py:54-65`
- **Current**: Two `try/except OSError: pass` blocks while
  iterating files for cache fingerprint. Files that cannot be
  stat'd are silently excluded from the fingerprint, so a
  cached scan can become stale without invalidation.
- **Proposal**: On `OSError`, return a fingerprint that
  encodes "stat failures occurred" (e.g. include error count
  in the hash). Then a stat failure invalidates the cache
  rather than masking it.
- **Rationale**: Silently-skipped files are a correctness hole:
  cache returns stale results. Counting failures into the
  fingerprint is a one-line fix that turns a correctness bug
  into a cache-miss.

### B-23: `tests/test_async_patterns.py` retry blocks are sample input, not test code

- **Category**: comment-slop / false-positive
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/parseltongue/tests/test_async_patterns.py:291-301`,
  `390-401`
- **Current**: `for attempt in range(max_retries):` inside a
  triple-quoted Python literal that is fed to the analyzer.
- **Proposal**: Mark with `# language=python` or similar so
  scanners don't flag. No code change required.
- **Rationale**: False positive recorded for tooling tuning.

### B-24: `pytest.skip("ffmpeg not installed")` chain in `scry/test_workflow_integration.py`

- **Category**: test-tamper
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/scry/tests/test_workflow_integration.py:69, 84, 97, 117, ...`
  (15+ occurrences)
- **Current**: Each test starts with `if not has_X: pytest.skip("X not installed")`.
- **Proposal**: Use a single `@pytest.mark.requires_vhs` /
  `@pytest.mark.requires_ffmpeg` autouse skipper at the class
  level; drop the per-test `if not X: pytest.skip` boilerplate.
  The markers are already declared in conftest.
- **Rationale**: 15 copies of the same skip check is itself
  additive. A class-level marker collapses them to one line.

### B-25: `# This method does X` style comments above self-explanatory code

- **Category**: comment-slop
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: scattered; flagged samples:
  - `plugins/abstract/src/abstract/skills_eval/performance.py:17`:
    `# Thresholds for performance scoring` above
    `SLOW_THRESHOLD = 0.05`
  - `plugins/sanctum/scripts/test_generator.py:201-205`: the
    generator emits `# TODO: Act - Call the method` and
    `# TODO: Assert - Verify the outcome` for every test.
- **Proposal**: Templates can drop the inline TODOs (the
  generated test will be filled in by the user; the
  Arrange-Act-Assert structure is conveyed by the empty lines).
- **Rationale**: Generator produces docstring-rich test
  scaffolds with inline `# TODO` comments at every step. Each
  generated test has 4-5 such markers.

### B-26: Hardcoded `time.sleep(0.05)` in tests to "ensure different mtimes"

- **Category**: workaround
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/conserve/tests/unit/test_context_warning.py:194`,
  `plugins/sanctum/tests/unit/test_update_plugins_modules.py:339`
- **Current**:
  ```python
  older.write_text("{}\n")
  time.sleep(0.05)
  newer.write_text("{}\n")
  ```
- **Proposal**: After writing each file, set the mtime
  explicitly with `os.utime(path, (now, now - delta))`. Avoid
  sleeping in tests.
- **Rationale**: Tests that depend on wall-clock for ordering
  are flaky on busy CI. Setting mtime explicitly is one extra
  line and removes the sleep.

### B-27: `time.sleep(0.1)` to wait for token expiry in `test_precommit.py`

- **Category**: workaround
- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**:
  `plugins/gauntlet/tests/unit/test_precommit.py:78-80`
- **Current**:
  ```python
  write_pass_token(tmp_gauntlet_dir, "abc123", ttl_seconds=0)
  time.sleep(0.1)
  assert check_pass_token(tmp_gauntlet_dir, "abc123") is False
  ```
- **Proposal**: Pass a frozen "now" via a mock or write the
  token with a `created_at` that is already in the past
  (`ttl_seconds=0` and back-dated mtime). Avoid sleeping.
- **Rationale**: `time.sleep(0.1)` is also flaky on slow CI
  and adds 100ms per test run; with parametrization this
  compounds. A clock injection point is the proper fix.

## Closing Notes

The dominant pattern in this codebase is **alias proliferation
for backward compatibility**: `tools_dir = skills_dir`,
`always_confirm = always_approve`, `_validate_session_id =
validate_session_id`, three `tasks_manager.py` files. Each is
small in isolation, but together they form a pattern of
preferring "add a new name" over "change the call site". A
dedicated cleanup pass focused on this pattern would shed
several hundred lines.

The second-most-frequent pattern is **`try/except: pass` at
file boundaries** -- 25+ instances across hooks, scripts,
and src. These are workarounds for "what if the file is
missing/corrupt" that hide real bugs. Each should be either
narrowed to specific exception types or paired with
`logger.debug`.

The most concerning single finding is **B-10**: a test that
documents a known-broken implementation in its comment, then
asserts `True` to keep CI green. That is the canonical case
of "test mocks the bug rather than the dependency".
