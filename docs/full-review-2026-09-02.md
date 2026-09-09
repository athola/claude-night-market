# Full review, Tier 3, whole codebase, 2026-09-02

Reader: practitioner. Knows Claude Code plugins and this repository's
plugin layout, not the state of each gate.

The finding that matters most is not a bug. It is that the gates
meant to catch bugs cannot fail: conserve's `make test` runs no
pytest, root `validate-all` and `plugin-check` swallow every
failure, `test-coverage` re-runs without coverage when the threshold
trips, scribe's `lint` warns and exits 0, and the house shell lint
gate crashes before it lints. Six test functions compute a result
and never assert on it. The codebase underneath is in good shape:
two bug reviewers over 458 source files found one high (a DNS
rebinding gap in herald's webhook guard), and the six Python 3.9
breaks one agent reported, four of them as critical, were refuted by
running the hooks under the system interpreter.

Branch `docs/audience-targeting` at `c86e753e`. `make test` is red
on this branch for reasons that predate the review: two
`test_cited_paths_resolve` failures in scribe's slop-detector
modules (example paths under `docs/deep-dive/`) and phantom's
missing README in `check-examples`. Every other suite passes.

## Coverage

| Dimension | Agent | Scope read | Verified | Refuted by me |
|-----------|-------|------------|----------|---------------|
| bugs-infra | pensive:code-reviewer | 136 files across leyline, abstract, conserve, sanctum, imbue, hookify; 15 close reads | 2 | 0 |
| bugs-domain | pensive:code-reviewer | 304 files across 17 plugins; deep on the conjure split and embedding_index.py | 3 | 0 |
| hooks | pensive:code-reviewer | 76 hook files, 13 hooks.json, import chains into src/ | 7 | 6 |
| tests | pensive:code-reviewer | 805 test files grep-swept, AST scan for assertion-free tests, 25 full reads | 6 | 0 |
| arch | pensive:architecture-reviewer | 23 ADRs (the scope said 28; 23 exist), 11 rules, import graph three ways | 7 | 0 |
| shell | general-purpose with shell-review | 40 of 40 scripts, 13 hooks.json commands, shellcheck on all 40 | 21 | 0 |
| make | general-purpose with makefile-review | 30 of 30 Makefiles, 16 dry runs, two make 3.81 probes | 33 | 0 |
| refine | pensive:code-refiner | 443 files, detect_duplicates.py, AST length scan; ran in a worktree | 4 | 0 |
| api | pensive:code-reviewer | 4 entry points, 23 plugin.json, 22 openpackage.yml, 176 June findings | 54 | 0 |

Every JSON file passed `citation_verifier.py` with exit 0, so every
`file:line` below carries a verbatim anchor that resolves. Verified
means the anchor resolves and the agent read around it. Confirmed
means I reproduced it myself; those are marked in the text.

## Domain findings

### Bugs, shared infrastructure

| Id | Severity | Location | Finding |
|----|----------|----------|---------|
| BUGS-INFRA-001 | medium | `plugins/leyline/src/leyline/quota_tracker.py:149` | QuotaTracker.record_request does an unlocked read-modify-write on the shared usage JSON file |
| BUGS-INFRA-002 | low | `plugins/abstract/scripts/insight_palace_bridge.py:216` | query_palace_insights swallows every exception (not just 'palace unavailable') and returns an empty list |

### Bugs, domain plugins

| Id | Severity | Location | Finding |
|----|----------|----------|---------|
| BUGS-DOMAIN-001 | high | `plugins/herald/scripts/notify.py:249` | Webhook SSRF check is TOCTOU: curl re-resolves DNS after validate_webhook_url() approved a different address |
| BUGS-DOMAIN-002 | medium | `plugins/conjure/scripts/delegation_prompt.py:174` | _prompt_argv falls through to an unescaped dash-leading prompt when a service declares prompt_flag but no p... |
| BUGS-DOMAIN-003 | low | `plugins/gauntlet/src/gauntlet/blast_radius.py:48` | load_weights() silently discards a malformed .gauntlet/config.json with no log, leaving an operator's typo ... |

### Hooks

| Id | Severity | Location | Finding |
|----|----------|----------|---------|
| HOOKS-001 | refuted | `plugins/memory-palace/src/memory_palace/paths.py:51` | PEP 604 union in return annotation breaks import under system Python 3.9 |
| HOOKS-002 | refuted | `plugins/memory-palace/hooks/web_research_handler.py:58` | Unguarded import of a module that fails to load on system Python 3.9 |
| HOOKS-003 | refuted | `plugins/abstract/src/abstract/utils.py:151` | PEP 604 union in parameter annotation breaks import under system Python 3.9 |
| HOOKS-007 | refuted | `plugins/memory-palace/hooks/research_interceptor.py:49` | Second unguarded import site for the 3.9-incompatible memory_palace.paths module |
| HOOKS-004 | refuted | `plugins/abstract/hooks/homeostatic_monitor.py:35` | except ImportError does not catch the TypeError raised by the underlying 3.9-incompatible module |
| HOOKS-005 | refuted | `plugins/gauntlet/src/gauntlet/graph.py:217` | PEP 604 union breaks gauntlet.graph import under system Python 3.9, silently swallowed |
| HOOKS-006 | medium | `plugins/memory-palace/hooks/hooks.json:86` | SessionEnd hook declares a 5s timeout but is not marked async |

Six of the seven hook findings are refuted. The agent read a
`Path | None` annotation as a 3.9 import failure without
checking for the future import. All three cited modules carry
`from __future__ import annotations` (paths.py:33, utils.py:13,
graph.py:7). Confirmed by execution on this host: every hook
and src file compiles under `/usr/bin/python3` 3.9.6, all five
hook-imported packages import cleanly (46 memory_palace, 23
abstract, 22 gauntlet, 3 oracle, 13 leyline modules), and every
memory-palace and abstract hook runs to exit 0 on an empty
SessionStart payload. The three memory_palace modules that
fail to import need faiss or networkx, and every hook reaches
them through a lazy import inside a function. HOOKS-006 stands:
a SessionEnd hook with a 5s timeout and no `async` flag hits
the 1.5s batch deadline.

### Test suites

| Id | Severity | Location | Finding |
|----|----------|----------|---------|
| TESTS-001 | high | `plugins/sanctum/tests/test_workflow_steps_modularization.py:212` | test_step_files_reference_adjacent_steps computes a boolean and discards it, never asserts |
| TESTS-002 | medium | `plugins/conserve/tests/unit/test_tool_output_summarizer.py:269` | test_fallback_to_most_recent_project_dir asserts nothing about the fallback result |
| TESTS-003 | medium | `plugins/conserve/tests/unit/test_pre_compact_preserve.py:451` | Duplicate of TESTS-002 in a sibling module: same unasserted fallback-branch test body |
| TESTS-004 | medium | `plugins/sanctum/tests/unit/hooks/test_deferred_item_sweep.py:236` | test_main_prints_summary_when_items_filed takes a capsys fixture but never reads captured output |
| TESTS-005 | low | `plugins/sanctum/tests/unit/hooks/test_deferred_item_sweep.py:253` | test_main_silent_when_no_items never checks stdout/stderr for silence |
| TESTS-006 | low | `plugins/sanctum/tests/test_quality_checker.py:1018` | test_run_check_or_validate_returns_report_str never inspects the returned report string despite its name |

### Architecture and ADR drift

| Id | Severity | Location | Finding |
|----|----------|----------|---------|
| ARCH-001 | high | `.claude/rules/bounded-discovery.md:55` | Two auto-injected rules disagree on rationalization tables; 5 files carry the retired side |
| ARCH-002 | high | `plugins/cartograph/hooks/graph_community_refresh.py:70` | cartograph imports gauntlet's src/ at runtime; gauntlet is not an ADR-0001 exception and cartograph declare... |
| ARCH-003 | medium | `docs/adr/0014-pensive-review-skill-consolidation.md:4` | ADR-0014 accepted 2026-05-06 to cut pensive review skills 9 to 7; the count is now 10 and both target skill... |
| ARCH-004 | medium | `docs/adr/0002-quota-tracker-refactoring.md:43` | ADR-0002 justifies conjure's hard leyline dependency on two claims the code contradicts |
| ARCH-005 | medium | `plugins/egregore/scripts/notify.py:55` | egregore consumes herald but declares only leyline; ADR-0001 names egregore as herald's sole consumer |
| ARCH-007 | medium | `plugins/leyline/README.md:55` | leyline README still advertises /verify-plugin against the ERC-8004 registry that ADR-0008 superseded in March |
| ARCH-006 | low | `Makefile:321` | leyline.deferred_capture is the top coupling hot spot at 6 consumer plugins; its contract is documented and... |

### Shell scripts

| Id | Severity | Location | Finding |
|----|----------|----------|---------|
| SHELL-001 | high | `scripts/shellcheck.sh:96` | House lint gate crashes on macOS /bin/sh with no arguments: `main "${@}"` under `set -eu` is an unbound-var... |
| SHELL-002 | high | `plugins/leyline/scripts/interactive_auth.sh:63` | is_ci() dereferences $CI/$GITHUB_ACTIONS/$GITLAB_CI/$AWS_EXECUTION_ENV unguarded; any `set -u` caller (incl... |
| SHELL-003 | medium | `plugins/leyline/scripts/interactive_auth.sh:23` | `declare -A` under `#!/usr/bin/env bash` fails on stock macOS (bash 3.2), so the module cannot be sourced w... |
| SHELL-004 | medium | `plugins/memory-palace/hooks/setup.sh:176` | Maintenance trigger dies on macOS: BSD `uniq` has no `-w`, pipefail fails the assignment, `set -e` exits th... |
| SHELL-005 | medium | `plugins/conserve/hooks/setup.sh:17` | `read -t 0.1` is rejected by bash 3.2, so TRIGGER_TYPE is always 'init' and the maintenance block is unreac... |
| SHELL-006 | medium | `plugins/imbue/hooks/user-prompt-submit.sh:57` | Predictable cache file in shared /tmp is both read into additionalContext and written through `>`; a plante... |
| SHELL-007 | medium | `scripts/clawhub-cron.sh:18` | Cron lock is a check-then-touch on a fixed /tmp path with no staleness or PID check; a SIGKILL or reboot-fr... |
| SHELL-008 | medium | `plugins/abstract/config/make/python.mk:71` | `test-coverage` swallows a coverage-threshold failure by re-running pytest without coverage, so `--cov-fail... |
| SHELL-009 | medium | `scripts/run-plugin-lint.sh:59` | The lint gate always rewrites source (`--fix`) regardless of caller intent, while check-all-quality.sh's `-... |
| SHELL-010 | medium | `plugins/egregore/scripts/watchdog.sh:72` | Bare `cd` to the manifest's project_dir after PIDFILE/LOG/MANIFEST were computed as relative paths; when pr... |
| SHELL-011 | low | `plugins/leyline/hooks/auto-star-repo.sh:84` | Under pipefail `gh api` exits 1 on HTTP 404, so `status` becomes "404\n000" and the gh path can never yield... |
| SHELL-012 | low | `plugins/leyline/hooks/fetch-recent-discussions.sh:180` | The `HEADING=` prefix binds to `echo`, not to `python3`, so both sections are labelled with the default 'Di... |
| SHELL-013 | low | `plugins/leyline/hooks/fetch-recent-discussions.sh:119` | Whitespace-separated read shifts the Insights category ID into `category_id` when no Decisions category exi... |
| SHELL-014 | low | `plugins/leyline/scripts/interactive_auth.sh:299` | Personal access token and GITHUB_TOKEN are passed through `echo` in the script body, so any caller running ... |
| SHELL-015 | low | `scripts/logging.sh:1` | The canonical logging library has no shebang and no `# shellcheck shell=sh` directive, so bare `shellcheck`... |
| SHELL-016 | low | `Makefile:207` | `skrills-build` and `skrills-verify` call `sha256sum`, which stock macOS does not ship, so both targets fai... |
| SHELL-017 | low | `plugins/conserve/hooks/setup.sh:105` | A path is interpolated unescaped inside double quotes into a file that Claude Code later sources; a path co... |
| SHELL-018 | low | `scripts/run-plugin-tests.sh:12` | Systemic: 39 of 40 tracked scripts do not follow the house preamble (logging.sh, main-last, braced vars, no... |
| SHELL-019 | low | `plugins/leyline/scripts/interactive_auth.sh:361` | SC2145 (error level): `${!ARRAY[@]}` inside a string concatenates only the first key with the text and emit... |
| SHELL-020 | low | `plugins/conserve/hooks/hooks.json:8` | Every hook command across 13 hooks.json files expands `${CLAUDE_PLUGIN_ROOT}` unquoted; a plugin cache path... |
| SHELL-021 | low | `plugins/leyline/scripts/interactive_auth.sh:101` | jq program is built by string interpolation of `$key` and `$value`; a value containing `"` or `\(` becomes ... |

### Makefiles

| Id | Severity | Location | Finding |
|----|----------|----------|---------|
| MAKE-001 | high | `plugins/abstract/config/make/common.mk:6` | Shared includes rely on .SHELLFLAGS/.ONESHELL, which GNU make 3.81 (stock macOS Xcode CLT make) silently ig... |
| MAKE-002 | high | `plugins/conserve/Makefile:57` | conserve `make test` runs no pytest: 38 test files are skipped by root `make test`, `make conserve-test`, t... |
| MAKE-003 | medium | `plugins/abstract/config/make/python.mk:71` | test-coverage falls back to a no-coverage pytest run on failure, so a `--cov-fail-under` breach passes as l... |
| MAKE-004 | medium | `plugins/conserve/tests/Makefile:38` | conserve/tests/Makefile is unrunnable from its own directory: every target points at tests/tests, tests/per... |
| MAKE-005 | medium | `plugins/conserve/tests/Makefile:172` | quality-gate parses the SQLite .coverage database as JSON; the substitution errors out, the empty value mak... |
| MAKE-006 | medium | `plugins/spec-kit/tests/Makefile:25` | spec-kit/tests/Makefile installs from a requirements.txt that does not exist, runs bare `pytest` outside uv... |
| MAKE-007 | medium | `plugins/spec-kit/Makefile:264` | Orphan recipe blocks (lines 264-272 and 363-368) have no target line, so make attaches them to the precedin... |
| MAKE-008 | medium | `plugins/sanctum/Makefile:391` | test-update-plugins cites two test files that no longer exist and has no fallback, so the target always fai... |
| MAKE-009 | medium | `plugins/pensive/Makefile:85` | pensive docs, docs-serve, duplication-check, complexity-check and coverage-badge call mkdocs, radon, xenon ... |
| MAKE-010 | medium | `plugins/abstract/Makefile:224` | validate-migration and generate-wrappers guard on three scripts that were removed (compatibility_validator.... |
| MAKE-011 | medium | `plugins/abstract/Makefile:144` | abstract docs/docs-check build a Sphinx tree from docs/source, which does not exist; the same recipes are d... |
| MAKE-012 | medium | `plugins/memory-palace/Makefile:35` | $(PWD) is the caller's environment, not the Makefile directory: under `make -C` (root delegation, root `mak... |
| MAKE-013 | medium | `Makefile:158` | Root plugin-check cannot fail (every failure becomes an echo, stderr is discarded) and depends on GNU coreu... |
| MAKE-014 | medium | `Makefile:149` | validate-all swallows every validator failure, so the root structure gate always exits 0 |
| MAKE-015 | medium | `plugins/scribe/Makefile:45` | scribe lint cannot fail: a slop hit prints WARNING and exits 0, and a grep error is reported as 'No tier-1 ... |
| MAKE-024 | medium | `Makefile:93` | Root `lint` (and `all`) rewrites sources with `ruff format` and `ruff check --fix`, so it cannot detect for... |
| MAKE-016 | low | `plugins/spec-kit/Makefile:51` | validate-plugin masks the validator's exit code and runs it with bare python3 instead of the plugin's uv en... |
| MAKE-017 | low | `Makefile:32` | Root .PHONY omits six recipe-only targets, and the delegation template's `.PHONY: $(1)-%` is a no-op becaus... |
| MAKE-018 | low | `plugins/abstract/config/make/python.mk:32` | python.mk defines nine targets (format lint type-check typecheck security test-unit unit-tests test-coverag... |
| MAKE-019 | low | `plugins/memory-palace/Makefile:8` | Stale .PHONY entries name targets that do not exist: memory-palace demo-pensive/test-pensive (copied from p... |
| MAKE-020 | low | `plugins/abstract/config/make/common.mk:26` | common.mk runs four parse-time $(shell) probes (uv, python3, pre-commit, a python `import sphinx`) on every... |
| MAKE-021 | low | `plugins/abstract/Makefile:40` | .NOTPARALLEL prerequisites are honored only by recent GNU make; on 3.81 (verified) the prerequisites are ig... |
| MAKE-022 | low | `plugins/egregore/Makefile:117` | Catch-all uses `$$@` (shell positional params, empty under bash -c) instead of make's `$@`, so the unknown-... |
| MAKE-023 | low | `plugins/abstract/Makefile:183` | Recursive invocations use bare `make` instead of `$(MAKE)`, so -n/-k/jobserver flags and a non-default make... |
| MAKE-025 | low | `plugins/conjure/Makefile:31` | The same help/awk recipe, `Makefile.local:;` + `-include`, `%::` catch-all, status, debug-variables, clean,... |
| MAKE-026 | low | `plugins/conserve/Makefile:26` | Four plugins feed `Makefile` instead of `$(MAKEFILE_LIST)` to the help awk, so `make help` omits the format... |
| MAKE-027 | low | `plugins/imbue/Makefile:22` | `safety check` is the legacy CLI verb; the pinned safety>=3.7 deprecates it in favor of `safety scan`, and ... |
| MAKE-028 | low | `plugins/pensive/Makefile:177` | `safety check` is the legacy CLI verb, deprecated upstream in favor of `safety scan`; it also needs network... |
| MAKE-029 | low | `plugins/conserve/Makefile:305` | Pinned test paths that no longer exist make the primary branch of several per-command test targets fail eve... |
| MAKE-030 | low | `plugins/leyline/Makefile:175` | demo-reinstall-all-plugins looks for `<plugin>/plugin.json`; the manifest is at `<plugin>/.claude-plugin... |
| MAKE-031 | low | `Makefile:16` | cartograph has tests/, pyproject.toml and a manifest but no Makefile, so it gets no root `cartograph-*` del... |
| MAKE-032 | low | `plugins/imbue/Makefile:160` | imbue and minister benchmark targets discard stderr and report any pytest failure as 'pytest-benchmark not ... |
| MAKE-033 | low | `plugins/abstract/Makefile:116` | audit-skill, improve-skill, check-compliance, audit-all and eval-report end in `// echo "... completed"`, s... |

MAKE-002 is confirmed and it touches this branch's own
evidence: the unbloat session earlier today reported "conserve
passed" on the strength of `make conserve-test`, which runs
lint, mypy and bandit and no pytest. Run directly, conserve's
suite is 787 passed, so nothing was hidden, but the gate would
not have said so.

### Code quality

| Id | Severity | Location | Finding |
|----|----------|----------|---------|
| REFINE-001 | medium | `plugins/memory-palace/src/memory_palace/session_history.py:195` | SessionStore CRUD body copy-pasted as an ImportError fallback in memory-palace and tome instead of reused f... |
| REFINE-002 | medium | `plugins/conjure/scripts/delegation_executor.py:168` | Delegator is a 691-line class (910 before today's split) mixing config loading, credential verification, la... |
| REFINE-003 | low | `plugins/memory-palace/scripts/memory_palace_cli.py:1` | 1,396 lines but argparse boilerplate, longest function main at 80 lines; leaving it alone is the right call |
| REFINE-004 | low | `plugins/egregore/scripts/night_run.py:103` | Single-implementor Protocol, but FakeRunner test doubles exist so it is a legitimate seam |

The code-refiner agent ran in an auto-removed worktree, so its
JSON was reconstructed from its report and re-verified. Its
Delegator measurement (910 lines) was of the pre-split file;
the current class is 691 lines starting at line 168.

### API surface

| Id | Severity | Location | Finding |
|----|----------|----------|---------|
| API-001 | high | `plugins/abstract/scripts/compliance_checker.py:25` | compliance_checker.py CLI accepts only positional directory + --rules-file/--format/--output, but four skil... |

### June 2026 findings, re-verified

The June 22 review left 176 findings in `.review/findings.json`.
Anchor check: 62 still resolve, 114 do not (the June 22 to 24
refactor series moved or fixed them; not re-judged line by line).
Of the 62, the agent found 9 closed by a later commit and listed
53 as standing. Two mechanical checks narrow that: every SKILL.md in
the repository now has an Exit Criteria section (`rg` over all 209
finds none missing), which closes the 13 "missing Exit
Criteria" entries whose anchor is the frontmatter `name:` line, and
memory-palace's `.gitignore` now lists `.venv/` and `.uv-cache/`,
which closes MP-001. That leaves 39 standing, of
which two were re-read here: PEN-003, `CodeReviewWorkflow.run()`
still returns empty findings unconditionally, and SML-002, the
5-line `parse_code` is still duplicated across two parseltongue
modules.

| June id | Severity then | Location now | Claim |
|---------|---------------|--------------|-------|
| LEY-004 | low | `plugins/leyline/skills/quota-management/SKILL.md:2` | quota-management and usage-logging both list 'cost-tracking' in their provides/usage_patterns. Witho |
| MP-009 | medium | `plugins/memory-palace/src/memory_palace/corpus/knowledge_orchestrator.py:379` | get_source_lineage is a pure delegation stub: it receives entry_id and immediately returns self.line |
| MP-010 | medium | `plugins/memory-palace/src/memory_palace/corpus/knowledge_orchestrator.py:431` | batch_assess is a four-line method whose entire body is a list comprehension over assess_entry. It a |
| MP-014 | low | `plugins/memory-palace/src/memory_palace/palace_renderer.py:267` | journey_replay (lines 267-326) is 60 lines long and builds a Mermaid sequenceDiagram by hand. It con |
| PEN-001 | low | `plugins/pensive/src/pensive/skills/rust_review_data.py:15` | rust_review_data.py is 832 lines mixing TypedDict schema, ~50 raw pattern strings, ~50 compiled RE o |
| PEN-002 | low | `plugins/pensive/src/pensive/skills/rust_review_data.py:616` | Lines 616-738 mechanically mirror every pattern string with a compiled RE object. The 1:1 mapping (F |
| PEN-003 | high | `plugins/pensive/src/pensive/workflows/code_review.py:26` | CodeReviewWorkflow.run() is a stub that returns {"findings": [], "summary": ""} unconditionally. It  |
| PEN-004 | high | `plugins/pensive/src/pensive/skills/unified_review.py:14` | dispatch_agent() is a module-level stub that returns f"{skill_name} execution result" — a hardcoded  |
| PEN-006 | medium | `plugins/pensive/src/pensive/workflows/code_review.py:138` | _determine_skills() in CodeReviewWorkflow (lines 138-154) and select_review_skills() in UnifiedRevie |
| PEN-007 | medium | `plugins/pensive/src/pensive/workflows/code_review.py:67` | execute_full_review() catches bare Exception on every skill execution (lines 67-71) and execute_skil |
| PEN-012 | low | `plugins/pensive/src/pensive/skills/unified_review.py:63` | detect_languages() (lines 61-84) iterates over all files O(F) for each language O(L), making the inn |
| SAN-002 | medium | `plugins/sanctum/scripts/update_plugin_registrations.py:112` | _scan_plugin_for_module_refs is never called from production code; only tests invoke it directly. Th |
| SAN-004 | low | `plugins/sanctum/scripts/meta_evaluation.py:86` | check_file_exists is a one-liner that returns (skill_path / 'SKILL.md').exists() via a redundant if/ |
| SML-002 | high | `plugins/parseltongue/src/parseltongue/analysis/async_analysis/_base.py:10` | Identical 5-line parse_code function copied verbatim in plugins/parseltongue/src/parseltongue/analys |
| SML-008 | low | `plugins/herald/.claude-plugin/plugin.json:5` | Herald registers zero skills despite the description 'Provides GitHub issue alerts and webhook suppo |
| SML-009 | info | `plugins/archetypes/.claude-plugin/plugin.json:18` | Archetypes has 14 registered skills but zero Python source: the only Python file is a 120-line test. |
| SML-010 | info | `plugins/cartograph/.claude-plugin/plugin.json:8` | Cartograph has 7 registered skills and 1 hook but no Python src directory. All skill logic is in mar |
| TOME-002 | low | `plugins/tome/src/tome/channels/triz.py:22` | triz.py inlines ~180 lines of static domain data as Python dicts (INVENTIVE_PRINCIPLES, FIELD_ADJACE |
| XPL-001 | high | `plugins/sanctum/src/sanctum/validators/_frontmatter.py:17` | Sanctum directly imports from leyline.frontmatter with an inline fallback duplicate. This is the cor |
| XPL-002 | high | `plugins/gauntlet/src/gauntlet/graph.py:18` | Gauntlet imports SqliteGraphBase from leyline with an inline fallback at line 24. leyline is the can |
| XPL-003 | high | `plugins/tome/src/tome/session.py:12` | Tome imports SessionStore and validate_session_id from leyline with an inline fallback. The fallback |
| XPL-004 | high | `plugins/memory-palace/src/memory_palace/session_history.py:20` | Memory-palace imports SessionStore and validate_session_id from leyline with a near-identical fallba |
| XPL-005 | medium | `plugins/pensive/src/pensive/skills/performance_review/__init__.py:23` | Pensive's performance_review skill optionally imports gauntlet's treesitter parser. This is a docume |
| XPL-006 | medium | `plugins/pensive/src/pensive/skills/performance_review/__init__.py:28` | Same file as XPL-005. Pensive optionally imports gauntlet's GraphStore for Tier 3 blast-radius analy |
| XPL-007a | medium | `plugins/tome/src/tome/synthesis/merger.py:39` | Identical Jaccard similarity function duplicated in tome/synthesis/merger.py and memory-palace/corpu |
| XPL-007b | medium | `plugins/memory-palace/src/memory_palace/corpus/semantic_deduplicator.py:23` | Duplicate of XPL-007a. Minor behavioral difference: this version lowercases inputs before splitting  |
| XPL-008a | medium | `plugins/tome/src/tome/session.py:19` | Fallback implementation of validate_session_id duplicates leyline.session_store.validate_session_id. |
| XPL-008b | medium | `plugins/memory-palace/src/memory_palace/session_history.py:31` | Duplicate of XPL-008a, also a fallback for when leyline is absent. Same regex, same 128-char limit.  |
| XPL-010b | medium | `plugins/leyline/src/leyline/tokens.py:199` | Canonical implementation. Different API from abstract's deprecated version (takes file list + prompt |
| XPL-011a | medium | `plugins/pensive/src/pensive/skills/bug_review/_reporting.py:8` | ReportingMixin is a naming convention used across 7 pensive skill subdirectories, all within plugins |
| XPL-011b | medium | `plugins/pensive/src/pensive/skills/rust_review/reporting.py:86` | See XPL-011a. Rust-specific reporting mixin within pensive. |
| XPL-011c | medium | `plugins/pensive/src/pensive/skills/architecture_review/reporting.py:8` | See XPL-011a. Architecture-review-specific reporting mixin within pensive. |
| XPL-011d | medium | `plugins/pensive/src/pensive/skills/api_review/_reporting.py:11` | See XPL-011a. API-review-specific reporting mixin within pensive. |
| XPL-011e | medium | `plugins/pensive/src/pensive/skills/math_review/_reporting.py:8` | See XPL-011a. Math-review-specific reporting mixin within pensive. |
| XPL-011g | medium | `plugins/pensive/src/pensive/skills/test_review/_reporting.py:16` | See XPL-011a. Test-review-specific reporting mixin within pensive. |
| XPL-012a | low | `plugins/pensive/src/pensive/skills/architecture_review/quality.py:11` | QualityMixin shared name across 3 pensive skill subdirectories. Like ReportingMixin (XPL-011), each  |
| XPL-012b | low | `plugins/pensive/src/pensive/skills/api_review/_quality.py:11` | See XPL-012a. |
| XPL-012c | low | `plugins/pensive/src/pensive/skills/makefile_review/_quality.py:26` | See XPL-012a. |
| XPL-013 | medium | `plugins/abstract/src/abstract/frontmatter.py:39` | abstract.FrontmatterProcessor and leyline.frontmatter.parse_frontmatter are independent implementati |

## Integrated issues

**Gates that cannot fail.** Fifteen findings across three dimensions,
fourteen distinct defects since MAKE-003 and SHELL-008 coincide,
describe the same shape: a quality target whose failure is
converted to output. MAKE-002 (conserve `test` runs no pytest),
MAKE-013 and MAKE-014 (root `plugin-check` and `validate-all` echo
every failure and exit 0), MAKE-003 and SHELL-008 (the same
`test-coverage` fallback, found independently), MAKE-015 (scribe
`lint` warns and exits 0), MAKE-033 (five abstract audit targets end
in `|| echo`), MAKE-016 (spec-kit `validate-plugin`), SHELL-001 (the
house shellcheck gate aborts on macOS `/bin/sh` before linting),
and TESTS-001 through TESTS-006 (assertions computed and dropped).
The commit `fix(gates): make quality gates able to fail` fixed one
instance of this class in June. This is the rest of it.

**macOS is the documented toolchain and several gates assume GNU.**
The build-and-env skill accepts Xcode CLT make, which is 3.81, and
3.81 ignores `.SHELLFLAGS` and `.ONESHELL` (MAKE-001, probed: a
failing pipeline passes). Stock bash 3.2 rejects `declare -A`
(SHELL-003) and `read -t 0.1` (SHELL-005, so conserve's setup hook
never sees its maintenance branch). BSD `uniq` has no `-w`
(SHELL-004, memory-palace's Setup hook dies before JSON output),
BSD grep has no `-P`, and macOS ships `shasum` not `sha256sum`
(SHELL-016). Each was reproduced on this host.

**Doctrine still contradicts doctrine.** Today's unbloat removed
the ToC contradiction. ARCH-001 is the next one: `bounded-discovery`
carries a rationalization table that `bounded-autonomy` retires,
both auto-inject into every session, and four skill files carry the
losing side. MAKE-024 and SHELL-009 are the same shape in tooling:
root `lint` rewrites sources with `--fix`, so it cannot detect what
it fixes.

**Manifests lag the code.** ARCH-002 (cartograph imports gauntlet's
src at runtime, outside ADR-0001's exceptions), ARCH-005 (egregore
consumes herald and declares only leyline), ARCH-004 (ADR-0002's
two justifications are contradicted by the code), ARCH-003
(ADR-0014 accepted a 9 to 7 consolidation; the count is 10),
ARCH-007 (leyline README documents a superseded registry). None is
a runtime break. All of them mean the documents a new reader trusts
are wrong.

**Agent reliability is itself a finding.** One reviewer reported
four criticals that a single command refuted. One ran in a worktree
that was auto-removed with its output and measured a file at a
pre-split commit. One triaged 53 June findings as standing when a
one-line `rg` closes 13 of them. The verifier catches a wrong
anchor and cannot catch a wrong conclusion. Anything above medium
in this report was reproduced or re-read before it was ranked.

## Action items

Ordered by what a fix buys. Owner is the plugin.

| # | Item | Findings | Owner | Size |
|---|------|----------|-------|------|
| 1 | Make conserve `test` run pytest; make root `validate-all`, `plugin-check`, scribe `lint`, abstract audit targets, spec-kit `validate-plugin` exit nonzero on failure; drop the no-coverage rerun in `python.mk` | MAKE-002, 013, 014, 015, 016, 033, 003, SHELL-008 | conserve, root, scribe, abstract, spec-kit | small each, one PR |
| 2 | Assert on the computed value in the six tests | TESTS-001 to 006 | sanctum, conserve | trivial |
| 3 | Resolve once, connect to the resolved IP in herald's webhook sender | BUGS-DOMAIN-001 | herald | small |
| 4 | Fix `main "${@}"` in the house lint gate and the rule that mandates it; guard `$CI` and friends in `interactive_auth.sh` | SHELL-001, 002, 014, 019, 021 | root, leyline | small |
| 5 | Version-guard `common.mk` for make 3.82 or later, replace `declare -A`, `read -t 0.1`, `uniq -w`, `grep -P`, `sha256sum` | MAKE-001, 021, SHELL-003, 004, 005, 016 | abstract, leyline, conserve, memory-palace, root | medium |
| 6 | Pick one side of the rationalization-table rule and remove the other from five files | ARCH-001 | rules, abstract, conserve | small, policy |
| 7 | Declare gauntlet and herald in the manifests that consume them, or move the shared API; correct ADR-0002 and ADR-0014 status | ARCH-002, 004, 005, 003, 007 | cartograph, egregore, conjure, pensive, leyline | small each |
| 8 | Lock the quota tracker's read-modify-write; narrow the palace bridge's except | BUGS-INFRA-001, 002 | leyline, abstract | small |
| 9 | Escape or refuse a dash prompt for a flag-only provider; log malformed gauntlet config | BUGS-DOMAIN-002, 003 | conjure, gauntlet | trivial |
| 10 | Mark memory-palace's SessionEnd hook async; move imbue's scope cache out of shared /tmp; atomic lock in clawhub-cron | HOOKS-006, SHELL-006, 007 | memory-palace, imbue, root | trivial |
| 11 | Align `compliance_checker.py` flags with the four skill docs that call it | API-001 | abstract | small |
| 12 | Delete the dead Makefile targets and orphan test Makefiles; fix `$(PWD)` to `$(CURDIR)`, `$$@` to `$@`, `make` to `$(MAKE)`, `.PHONY` drift | MAKE-004 to 012, 017 to 023, 025 to 032 | abstract, conserve, spec-kit, sanctum, pensive, memory-palace, egregore, gauntlet, herald | medium, mechanical |
| 13 | Reuse leyline's SessionStore in memory-palace and tome; next Delegator seam | REFINE-001, 002 | memory-palace, tome, conjure | medium |
| 14 | Re-judge the 39 June findings this report lists as standing, close or file each | June table | per plugin | medium |

Items 1 and 2 first. Until they land, a green `make test` on this
repository proves less than it claims, and every other item's fix
would be verified by a gate that cannot say no.

## Refuted findings

| Id | Claim | Evidence against |
|----|-------|------------------|
| HOOKS-001, 003, 005 | A PEP 604 union annotation breaks import on 3.9 | Each file has `from __future__ import annotations`; `PYTHONPATH=<src> /usr/bin/python3 -c "import <module>"` succeeds for all three |
| HOOKS-002, 007 | Unguarded import of a broken module | The module is not broken; `web_research_handler.py` and `research_interceptor.py` run to exit 0 under 3.9.6 |
| HOOKS-004 | `except ImportError` misses a TypeError from `improvement_memory` | `abstract.improvement_memory` imports cleanly under 3.9.6; the guard is reachable and unneeded |

## Method

Nine agents, one per dimension, each with the same output contract:
a JSON findings file with verbatim anchors, `citation_verifier.py`
exit 0 or every reject labeled, a 40-line report. Read-only: no
edits, no git writes. Files under `.review/full-2026-09-02/`
(machine-local) hold
the full findings with recommendations and evidence; they are
gitignored, so this report is the durable record.

Confirmations run by hand on this host (macOS, `/usr/bin/python3`
3.9.6, bash 3.2.57, GNU make 3.81):

```
git ls-files 'plugins/*/hooks/*.py' 'plugins/*/src/**/*.py' | xargs /usr/bin/python3 -m py_compile
PYTHONPATH=plugins/memory-palace/src /usr/bin/python3 -c "import memory_palace.paths"
echo '{"hook_event_name":"SessionStart"}' | /usr/bin/python3 plugins/memory-palace/hooks/web_research_handler.py
make -n -C plugins/conserve test          # no pytest line
cd plugins/conserve && uv run python -m pytest -q   # 787 passed
for f in plugins/*/skills/*/SKILL.md; do rg -q '^## Exit Criteria' "$f" || echo "$f"; done   # empty
```
