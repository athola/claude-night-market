---
date: 2026-05-02
scan-tier: 3
baseline-commits: e279b155..a0130839
scope: entire monorepo (plugins/, scripts/, tests/)
files-scanned: ~3634 source files, ~299K first-party LOC
findings: 18
---

# Code Quality Scan — 2026-05-02

Scope: entire claude-night-market monorepo.
Baseline: Phases 1-6 of the unbloat campaign closed (F01-F12).
Tier 3 (deep): all six dimensions + cross-plugin duplication.

---

## Summary

```
FINDINGS BY DIMENSION:
  Duplication:         5 (3 HIGH, 2 MEDIUM)
  Algorithm:           1 (1 MEDIUM)
  Clean Code:          5 (2 HIGH, 3 MEDIUM)
  Architecture:        3 (2 HIGH, 1 MEDIUM)
  Error Handling:      3 (2 HIGH, 1 MEDIUM)
  Type-system holes:   1 (1 MEDIUM)

QUALITY SCORE: 71/100
  (Baseline after F01-F12: estimated 62/100)
  Target: 80+ for production readiness
```

---

## Phase 1 — Zero-risk (mechanical, no behaviour change)

### F01 — DUPLICATE function: `run_gh_graphql` copied verbatim

**File A:** `plugins/abstract/scripts/post_learnings_to_discussions.py:307`
**File B:** `plugins/abstract/scripts/promote_discussion_to_issue.py:110`
**Action:** CONSOLIDATE into `plugins/abstract/src/abstract/gh_utils.py`
**Confidence:** HIGH | **Risk:** LOW | **Effort:** SMALL

Evidence: Two near-identical function bodies (30 LOC each). Version in
`post_learnings_to_discussions.py` has a dead `body` variable that is
constructed but never passed to subprocess — the `cmd.extend` lines
build the args directly. The version in `promote_discussion_to_issue.py`
is the correct implementation.

```python
# post_learnings_to_discussions.py:316 — dead variable, never used
body: dict[str, Any] = {"query": query}
if variables:
    body["variables"] = variables
# ... body is then ignored; cmd is built separately
```

Fix: delete the stale copy, extract `run_gh_graphql` to a shared
`gh_utils` module, import from both callers.

---

### F02 — MAGIC NUMBER: bare `3600` without constant (3 occurrences)

**Files:**
- `plugins/conjure/scripts/usage_logger.py:134`
- `plugins/gauntlet/hooks/precommit_gate.py:257`
- `plugins/conserve/tests/conftest.py:351`
**Action:** EXTRACT named constant `SECONDS_PER_HOUR = 3600`
**Confidence:** HIGH | **Risk:** LOW | **Effort:** SMALL

Evidence: Three separate inline `/3600` calculations with no constant,
while `plugins/memory-palace/src/memory_palace/garden_metrics.py:36`
already defines `SECONDS_PER_DAY = 86400` as a pattern to follow.
`plugins/leyline/scripts/usage_logger.py:47` also uses
`SESSION_TIMEOUT = 3600` as a named constant — the pattern exists.

```python
# gauntlet/hooks/precommit_gate.py:257
age_hours = (time.time() - mtime) / 3600  # magic; no constant

# conjure/scripts/usage_logger.py:134
cutoff_time = datetime.now(timezone.utc).timestamp() - (hours * 3600)
```

Fix: add `SECONDS_PER_HOUR = 3600` near each site or import from a
shared constants module.

---

### F03 — ERROR SWALLOWING: `TypeError` included in broad except in
`unified_review.py`

**File:** `plugins/pensive/src/pensive/skills/unified_review.py:147`
**Action:** REFACTOR — remove `TypeError` from the except tuple
**Confidence:** HIGH | **Risk:** LOW | **Effort:** SMALL

Evidence: `TypeError` is a programming error (wrong argument type), not
an I/O error. Catching it silently masks bugs in `context.get_file_content`.

```python
# unified_review.py:147
except (FileNotFoundError, OSError, AttributeError, TypeError):
    pass
```

`AttributeError` on the same line has marginal justification (missing
`.get_file_content` method). `TypeError` has none. The same file at
line 345 repeats the pattern without `TypeError`, confirming the L147
version is inconsistent.

Fix: remove `TypeError` from both except tuples. If `AttributeError`
is also unjustified, remove it too and let the error propagate so it
surfaces in tests.

---

### F04 — SUBPROCESS WITHOUT TIMEOUT: `verify_plugin.py` and
`reinstall_all_plugins.py`

**Files:**
- `plugins/leyline/scripts/verify_plugin.py:75`
- `plugins/leyline/scripts/reinstall_all_plugins.py:36`
**Action:** REFACTOR — add `timeout=` parameter
**Confidence:** HIGH | **Risk:** LOW | **Effort:** SMALL

Evidence: Both call `subprocess.run` without a timeout. The other
scripts in the same directory (`update_all_plugins.py`) already pass
`timeout=30`. `egregore/scripts/scout.py` has the same gap at lines
328, 366, 409 but those already had `timeout=30` in the `gh api`
calls checked earlier — on recheck those are fine. The leyline scripts
are the real gap.

```python
# verify_plugin.py:75
result = subprocess.run(
    ["gh", "api", endpoint],
    capture_output=True,
    text=True,
    check=False,
)   # no timeout — hangs on network failure
```

Fix: add `timeout=60` (plugin verify may take longer than 30s for
slow registries).

---

## Phase 2 — Targeted (require understanding scope, low blast radius)

### F05 — DUPLICATE FRONTMATTER PARSERS: 7 bespoke inline parsers
ignoring `leyline.frontmatter.parse_frontmatter`

**Files with inline parsers (production, non-test):**
1. `plugins/imbue/scripts/imbue_validator.py`
2. `plugins/conserve/scripts/coordination_workspace.py:40`
3. `plugins/conserve/scripts/area_agent_registry.py:29`
4. `plugins/memory-palace/src/memory_palace/corpus/_frontmatter.py:12`
5. `plugins/abstract/scripts/rules_validator.py:48`
6. `plugins/abstract/scripts/validate_plugin.py`
7. `plugins/sanctum/src/sanctum/validators.py:21` (inline fallback)

**Action:** CONSOLIDATE — each should import from
`leyline.frontmatter.parse_frontmatter` (with try/except ImportError
fallback as sanctum already does, or add leyline as a declared dep).
**Confidence:** HIGH | **Risk:** MEDIUM | **Effort:** MEDIUM

Evidence: `plugins/leyline/src/leyline/frontmatter.py` is the canonical
parser (1 line header, full YAML + fallback). Its docstring says
"Canonical YAML frontmatter parser for the night-market ecosystem."
Seven production files reimplement it with varying capability gaps:
`coordination_workspace.py` drops list support; `area_agent_registry.py`
handles lists but not nested YAML; none handle `YAMLError` the same way.

Note: `abstract/src/abstract/frontmatter.py` (`FrontmatterProcessor`)
is a 461-LOC purpose-built module with richer semantics (validation,
required fields). That one is justified and should not be replaced.
The seven listed above are the simple "split on `---`, parse key:value"
variants.

---

### F06 — GOD FUNCTION: `web_research_handler.main` at 175 LOC

**File:** `plugins/memory-palace/hooks/web_research_handler.py:404`
**Action:** SIMPLIFY — extract `_handle_webfetch` and
`_handle_websearch` sub-functions
**Confidence:** HIGH | **Risk:** MEDIUM | **Effort:** MEDIUM

Evidence: `main` handles two wholly separate code paths (WebFetch and
WebSearch) in a single 175-LOC function with a `# noqa: PLR0912,
PLR0915` suppression. The function has a well-defined fork at line
~430 (`if tool_name == "WebFetch":` ... `elif tool_name ==
"WebSearch":`). Each branch is ~60-70 LOC and independently testable.

```python
def main() -> None:  # noqa: PLR0912, PLR0915 - hook entry point with extensive request routing
    ...
    if tool_name == "WebFetch":
        # ~70 lines
    elif tool_name == "WebSearch":
        # ~60 lines
    # ~30 lines of shared epilogue
```

Fix: extract `_handle_webfetch(tool_input, tool_response, config,
feature_flags)` and `_handle_websearch(...)`, each returning
`tuple[list[str], str | None]`. `main` becomes ~30 LOC dispatcher.

---

### F07 — GOD FUNCTION: `render_markdown` at 163 LOC with suppressed
linter

**File:**
`plugins/conserve/scripts/context_scanner/renderers.py:247`
**Action:** SIMPLIFY — extract per-section render helpers
**Confidence:** MEDIUM | **Risk:** MEDIUM | **Effort:** MEDIUM

Evidence: `render_markdown` has a `# noqa: PLR0912, PLR0915`
suppression. It renders 10+ distinct sections (Structure,
Dependencies, Frameworks, Entry Points, Schemas, Config, Git, Recent
Changes, API endpoints, TODOs). Each section is 10-20 LOC and
independently testable.

```python
def render_markdown(  # noqa: PLR0912, PLR0915
    result: ScanResult, ...
) -> str:
    # 163 lines rendering many optional sections
```

Fix: extract `_render_structure_section`, `_render_deps_section`, etc.
The main function becomes a ~20-LOC orchestrator calling each helper
and joining results.

---

### F09 — INCONSISTENT EXCEPTION TYPES: "not found" failures use
`RuntimeError` instead of `FileNotFoundError`

**Files:**
- `plugins/sanctum/scripts/quality_checker.py:326`:
  `raise RuntimeError("Python not found")`
- `plugins/conjure/scripts/war_room/experts.py:105`:
  `raise RuntimeError("Claude CLI not found...")`

**Action:** REFACTOR — replace with `FileNotFoundError`
**Confidence:** HIGH | **Risk:** LOW | **Effort:** SMALL

Evidence: Both are binary-not-found scenarios. Python convention:
`FileNotFoundError` (a subclass of `OSError`) is the correct type for
missing executables/files. Using `RuntimeError` prevents callers from
catching specifically and forces them to match on message strings.
Contrast with `egregore/scripts/conventions.py:91`:
`raise FileNotFoundError(...)` (correct).

```python
# quality_checker.py:326
raise RuntimeError("Python not found")   # wrong type

# conventions.py:91
raise FileNotFoundError(f"Codex file not found: {path}")  # correct
```

Fix: `raise FileNotFoundError("Python executable not found in PATH")`
and similarly in `experts.py`.

---

## Phase 3 — Larger refactors (require test coverage verification)

### F10 — GOD FUNCTION: `attune_arch_init.main` at 160 LOC;
`attune_init.main` at 141 LOC

**Files:**
- `plugins/attune/scripts/attune_arch_init.py:385`
- `plugins/attune/scripts/attune_init.py:423`
**Action:** SIMPLIFY — extract phase helpers
**Confidence:** MEDIUM | **Risk:** MEDIUM | **Effort:** MEDIUM

Evidence: Both are linear scripts with distinct phases (parse args,
gather context, generate output, write files). The `attune_init.main`
function contains three large language-specific branches
(`_create_python_structure`, `_create_typescript_structure`,
`_create_rust_structure`) already extracted as sub-functions (good),
but the orchestration logic remains at 141 LOC.

---

### F11 — DEEP NESTING: 11-level dict literal construction in
`conjure/persistence.py`

**File:**
`plugins/conjure/scripts/war_room/persistence.py:234`
**Action:** REFACTOR — extract `_make_session_summary` helper
**Confidence:** MEDIUM | **Risk:** LOW | **Effort:** SMALL

Evidence: `list_sessions` contains a triply nested loop
(project_dirs > session_dirs > sessions) with a try/except inside,
and builds an inline dict literal 11 levels deep. The construction
of the summary dict should be a named helper.

```python
# persistence.py:226-248 (simplified)
for project_dir in ...:
    for session_dir in ...:
        if session_file.exists():
            try:
                with open(session_file) as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
            sessions.append({
                "session_id": data["session_id"],
                "problem": data["problem_statement"][:100],
                ...11 levels deep...
            })
```

Fix: extract `_load_session_summary(session_file) -> dict | None`.

---

### F13 — TYPE-SYSTEM HOLE: `classify_redundancy` passes enum class
as `Any` parameter

**File:**
`plugins/memory-palace/hooks/shared/decision_engine.py:14`
**Action:** REFACTOR — use `Protocol` or import the actual enum
**Confidence:** MEDIUM | **Risk:** LOW | **Effort:** SMALL

Evidence: `classify_redundancy(score: float, RedundancyLevel: Any)`
takes the `RedundancyLevel` enum class as a runtime argument typed
`Any`. This defeats type checking for the entire function. The enum
lives in the same plugin; there is no circular import barrier.

```python
def classify_redundancy(score: float, RedundancyLevel: Any) -> Any:
    """Map a match score to a RedundancyLevel enum value."""
```

Fix: import `RedundancyLevel` directly and remove the parameter, or
define a `Protocol` with the required class attributes if the enum
must remain injected.

---

### F14 — ERROR SWALLOWING: `architecture_review.py` swallows
`NotImplementedError` in fallback file-content fetch

**File:**
`plugins/pensive/src/pensive/skills/architecture_review.py:577,587`
**Action:** REFACTOR — separate `NotImplementedError` handling
**Confidence:** MEDIUM | **Risk:** LOW | **Effort:** SMALL

Evidence: Two `except (OSError, NotImplementedError): pass` blocks
inside `_get_file_content_fallback`. `OSError` is an acceptable
catch for missing files. `NotImplementedError` is a programming
contract violation (interface not implemented) and should not be
silently swallowed — it should propagate or log at WARNING level.

```python
# architecture_review.py:577
try:
    content = context.get_file_content("") or ""
    ...
except (OSError, NotImplementedError):
    pass  # NotImplementedError silently dropped
```

---

### F15 — DUPLICATE LOGIC: `sanctum/validators.py` re-implements
frontmatter split in three separate class methods

**File:**
`plugins/sanctum/src/sanctum/validators.py:21,242,447`
**Action:** CONSOLIDATE — extract `_split_frontmatter(content)`
private helper used by all three validators
**Confidence:** HIGH | **Risk:** LOW | **Effort:** SMALL

Evidence: Three classes (`FrontmatterValidator`, `SkillValidator`,
`CommandValidator`) each open with the same ~15-LOC
`if not content.strip().startswith("---"):` block. The logic is
identical: check for `---`, find closing `---`, extract raw YAML,
call `yaml.safe_load`. Consolidated as a private module-level
helper, the three `parse_frontmatter` methods become ~5 LOC each.

---

### F16 — GOD FUNCTION: `visit_Call` AST visitor at 142 LOC in
`performance_review.py`

**File:**
`plugins/pensive/src/pensive/skills/performance_review.py:474`
**Action:** SIMPLIFY — extract per-pattern detector methods
**Confidence:** MEDIUM | **Risk:** MEDIUM | **Effort:** MEDIUM

Evidence: `visit_Call` handles 8+ distinct detection patterns (T3:
re.compile in loop; T6: list comp to reducer; S2: list() wrapping
generator; S4: += in loop; etc.). Each check is 15-20 LOC with its
own `self.findings.append(...)`. This is a classic "match-all"
visitor that grows unboundedly with new patterns.

Fix: extract `_check_recompile_in_loop`, `_check_listcomp_reducer`,
etc. as private methods called by `visit_Call`. Each is independently
testable and the dispatcher becomes self-documenting.

---

### F17 — RESOURCE LEAK: unclosed file handle in `daemon_lifecycle.py`

**File:**
`plugins/oracle/hooks/daemon_lifecycle.py:89`
**Action:** REFACTOR — use context manager or explicit close
**Confidence:** MEDIUM | **Risk:** LOW | **Effort:** SMALL

Evidence: `log_fh = open(str(data_dir / "daemon.log"), "a")` is
assigned and passed to `Popen(..., stdout=log_fh, stderr=log_fh)`.
The comment says "fd passed to Popen, must outlive this scope" and
has a `# noqa: SIM115`. But `log_fh` is never explicitly closed
when the process exits or if `Popen` raises. The file handle will
leak until GC collects it.

```python
# daemon_lifecycle.py:89
log_fh = open(str(data_dir / "daemon.log"), "a")  # noqa: SIM115
proc = subprocess.Popen(
    cmd,
    stdout=log_fh,
    stderr=log_fh,
    ...
)
```

Fix: use `contextlib.ExitStack` to own both `log_fh` and the
subprocess, or register `log_fh.close()` on process exit using
`proc.wait()` in a finally block.

---

## Quick-win ranking (top 10)

| # | ID  | Impact | Effort | Risk | Summary |
|---|-----|--------|--------|------|---------|
| 1 | F01 | HIGH   | SMALL  | LOW  | Merge duplicate `run_gh_graphql` + kill dead `body` var |
| 2 | F09 | HIGH   | SMALL  | LOW  | `RuntimeError` -> `FileNotFoundError` (2 sites) |
| 3 | F03 | HIGH   | SMALL  | LOW  | Remove `TypeError` from broad except in `unified_review` |
| 4 | F04 | HIGH   | SMALL  | LOW  | Add `timeout=` to 2 leyline subprocess calls |
| 5 | F02 | HIGH   | SMALL  | LOW  | Name 3x bare `3600` magic numbers |
| 6 | F15 | HIGH   | SMALL  | LOW  | Extract `_split_frontmatter` in sanctum validators |
| 7 | F17 | MEDIUM | SMALL  | LOW  | Wrap `daemon_lifecycle.py` file handle |
| 8 | F11 | MEDIUM | SMALL  | LOW  | Extract `_load_session_summary` helper |
| 9 | F14 | MEDIUM | SMALL  | LOW  | Separate `NotImplementedError` from `OSError` in arch_review |
|10 | F13 | MEDIUM | SMALL  | LOW  | Type `classify_redundancy` with real enum (INVESTIGATE first) |

---

## Items for orchestrator to skip (INVESTIGATE)

- **F13** (INVESTIGATE): `decision_engine` enum injection — check for
  circular import constraint before removing the `Any` parameter.

---

## Evidence references

- [E1] `diff post_learnings:307-346 promote_discussion:110-165` —
  duplicate functions confirmed; dead `body` var at `:316-318`.
- [E2] `rg "/ 3600" plugins/ --glob "*.py"` — 3 bare occurrences vs
  1 named constant in leyline.
- [E3] `grep -n "except.*TypeError.*pass" unified_review.py:147` —
  confirmed.
- [E4] `grep -n "timeout" verify_plugin.py reinstall_all_plugins.py`
  — no timeout found; `update_all_plugins.py` has `timeout=30`.
- [E5] find-based scan of `startswith("---")` patterns in production
  `.py` excluding leyline — 7 bespoke parsers confirmed.
- [E6] `wc -l web_research_handler.py` = 583; `main` = L404-578 =
  175 LOC.
- [E7] `rg "raise RuntimeError.*not found"` — 2 confirmed;
  `raise FileNotFoundError` used correctly in other plugins.
- [E8] `rg "def parse_frontmatter" sanctum/validators.py` — 3
  occurrences in 3 different classes.
- [E9] `oracle/hooks/daemon_lifecycle.py:89` — `open()` without
  context manager confirmed by `# noqa: SIM115` comment.
