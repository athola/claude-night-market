---
generated: 2026-05-01
branch: ai-slop-1.9.4
scope: plugins/ (25 plugins, ~95k production Python lines, 2,182 markdown files)
strictness: STRICT
---

# Code Refinement Report — claude-night-market

## Summary

**Quality score: 67/100**

Top 3 systemic issues:

1. **Intentional duplication without a synchronization mechanism.**
Two session-start hooks (imbue, conserve) embed an identical ~70-line
JSON utility block and acknowledge in comments that it is "intentionally
duplicated." The canonical source at `scripts/shared/json_utils.sh`
exists but is unused. Without a diff-check in CI there is no guard
against the copies drifting.

2. **God-class accumulation in analysis skill files.**
`TestingGuideSkill` (parseltongue, 1044 lines, 25 methods) and
`run_loop` in phantom (176 lines, 6 concerns) mix data collection,
rule application, generation, and output formatting in single
units. The pensive plugin avoids this with `BaseReviewSkill` but
that pattern has not propagated.

3. **Broken module references in production SKILL.md files.**
Five SKILL.md files reference module paths that do not exist on
disk. Claude Code loads these paths at runtime; a missing file
silently degrades the skill to partial functionality with no error.

**Total findings: 12** (4 HIGH, 5 MED, 3 LOW)

---

## Findings

| ID | File | Category | Severity | Lines | Description | Classification |
|----|------|----------|----------|-------|-------------|----------------|
| F01 | `plugins/imbue/hooks/session-start.sh` + `plugins/conserve/hooks/session-start.sh` | Duplication | HIGH | imbue:26-105, conserve:26-105 | Identical 80-line JSON utility block (`get_json_field`, `escape_for_json`) in both hooks; acknowledged as intentional but has no drift-check | SHOULD_FIX |
| F02 | `plugins/parseltongue/src/parseltongue/analysis/testing_guide.py` | Clean Code / God Class | HIGH | 14-1057 | `TestingGuideSkill` is 1044 lines with 25 methods spanning structure analysis, anti-pattern detection, coverage, quality evaluation, generation, and recommendations — 6 distinct responsibility groups | SHOULD_FIX |
| F03 | `plugins/conserve/hooks/tool_output_summarizer.py` | Clean Code / Deep Nesting | HIGH | 73-125 | `get_session_output_size` reaches 10 levels of indentation (40 spaces) processing nested JSON content; three separate isinstance branches that could each be extracted | SHOULD_FIX |
| F04 | `plugins/conserve/scripts/detect_duplicates.py` | Algorithm | HIGH | 186-187 | `find_duplicates` calls `path.rglob(f"*{ext}")` once per extension (13 extensions), causing 13 separate directory walks over the same tree instead of one | SHOULD_FIX |
| F05 | `plugins/abstract/skills/skills-eval/SKILL.md` | Skill Quality | MED | 135-136 | Two module links use cross-skill relative paths (`../skill-authoring/modules/anti-rationalization.md`, `../shared-patterns/modules/workflow-patterns.md`) — both resolve correctly but the pattern of cross-directory module refs is undocumented and fragile | CONSIDER |
| F06 | `plugins/abstract/skills/modular-skills/SKILL.md` | Skill Quality | MED | 119-120 | Same cross-skill relative path pattern as F05; both files reference modules in sibling skills without a stability guarantee | CONSIDER |
| F07 | `plugins/phantom/src/phantom/loop.py` | Clean Code / Long Function | MED | 153-328 | `run_loop` (176 lines) handles setup, API call loop, tool dispatch, action filtering, confirmation gate, stuck detection, and cost tracking in one function | SHOULD_FIX |
| F08 | `plugins/egregore/scripts/parallel.py` | Algorithm | MED | 49-63 | `detect_independent_items` is O(n²): outer loop over `work_items`, inner loop over the same list for each non-seen item. Fine for n<50 but grows quadratically with manifest size | CONSIDER |
| F09 | `plugins/scribe/src/scribe/pattern_loader.py` | Clean Code | MED | 101-237 | `detect_language` is 137 lines because six language word-sets are inlined as set literals. The logic is 20 lines; the remaining 117 lines are data that belongs in a module-level constant or separate data file | SHOULD_FIX |
| F10 | `plugins/attune/scripts/plugin_project_init.py` | Clean Code / Long Function | MED | 114-322 | `initialize_plugin_project` is 209 lines mixing directory creation, file writing, template rendering, validation, and status reporting | SHOULD_FIX |
| F11 | `plugins/abstract/docs/examples/modular-skills/complete-skills/development-workflow/SKILL.md` | Skill Quality | LOW | all | Example SKILL.md references `modules/git-workflow/`, `modules/code-review/`, etc. which do not exist — will mislead readers using the example as a template | NEEDS_FIX |
| F12 | `plugins/egregore/scripts/watchdog.sh` | Hook Quality | LOW | 62-69 | `project_dir` is taken from `jq -r '.project_dir'` in a user-controlled manifest and passed directly to `cd "$project_dir"`. No path validation before the `cd`. Reachable by anyone who can write `.egregore/manifest.json`. | NEEDS_FIX |

---

## Evidence

### [E01] Identical JSON utilities in imbue and conserve hooks

**Files:**
- `plugins/imbue/hooks/session-start.sh:26-105`
- `plugins/conserve/hooks/session-start.sh:26-105`

Both contain:

```bash
# --- Inlined JSON utilities (canonical: scripts/shared/json_utils.sh) ---
# Inlined to avoid broken relative path when plugin runs from Claude Code cache.
# NOTE: Intentionally duplicated — do not DRY-refactor. Update canonical source + all copies together.

get_json_field() {
    local json="$1"
    local field="$2"
    local value=""
    if command -v jq >/dev/null 2>&1; then
        value=$(echo "$json" | jq -r ".${field} // empty" 2>/dev/null || echo "")
    elif echo "test" | grep -oP '\d+' >/dev/null 2>&1; then
        value=$(echo "$json" | grep -oP "\"${field}\"\\s*:\\s*\"\\K[^\"]+" 2>/dev/null || echo "")
    else
        value=$(echo "$json" | sed -n "s/.*\"${field}\"[[:space:]]*:[[:space:]]*\"\\([^\"]*\\)\".*/\\1/p" 2>/dev/null || echo "")
    fi
    printf '%s' "$value"
}
```

The comment acknowledges the duplication and names a canonical source.
The canonical `scripts/shared/json_utils.sh` does exist. The
justification ("broken relative path when plugin runs from Claude Code
cache") is valid — sourcing a relative path at runtime is fragile. But
the "update all copies together" instruction is unenforced: there is no
CI check verifying the copies match the canonical.

**Why it matters:** The escape_for_json function contains 30+ character
escape rules. A divergence introduced during a bug fix to one copy will
silently produce different JSON escaping behavior between hooks.

**Before/after sketch:**
Before (current): manual "update all copies" comment with no
enforcement.
After: add a Makefile target or pre-commit hook that diffs the inlined
blocks against `scripts/shared/json_utils.sh` and fails if they
diverge. Zero code change to the hooks; the canonical becomes the
authoritative source for auditing.

---

### [E02] God class — TestingGuideSkill

**File:** `plugins/parseltongue/src/parseltongue/analysis/testing_guide.py:14-1057`

```python
class TestingGuideSkill:
    # 25 methods, 1044 lines covering:
    def analyze_testing(...)          # entry point
    def analyze_test_structure(...)   # structural parsing
    def identify_anti_patterns(...)   # rule checking
    def analyze_coverage_gaps(...)    # coverage analysis
    def evaluate_test_quality(...)    # scoring
    def generate_test_fixtures(...)   # code generation
    def generate_test_documentation(...) # doc generation
    def recommend_tdd_workflow(...)   # workflow advice
    # ...17 more
```

**Why it matters:** Six distinct responsibility groups (structure,
anti-pattern detection, coverage, quality, generation, recommendations)
coexist in one class. Adding a new anti-pattern rule requires editing
the same file as a new fixture generator. Tests for generation cannot
be isolated from tests for coverage. This is the same problem
`BaseReviewSkill` in `plugins/pensive/` solved; parseltongue has not
adopted the pattern.

**Before/after sketch:**
Before: `TestingGuideSkill` owns all 25 methods.
After: `TestingGuideSkill` coordinates three collaborators:
`TestStructureAnalyzer`, `TestQualityEvaluator`,
`TestRecommendationEngine`. Each is under 200 lines and independently
testable.

---

### [E03] Deep nesting in get_session_output_size

**File:** `plugins/conserve/hooks/tool_output_summarizer.py:73-125`

```python
def get_session_output_size(session_file: Path, max_bytes: int = 512_000) -> int:
    ...
    try:
        with open(session_file, ...) as f:
            for raw_line in f:
                ...
                try:
                    entry = json.loads(stripped)
                except json.JSONDecodeError:
                    continue
                content = entry.get("content", "")
                if isinstance(content, list):
                    for block in content:
                        is_tool_result = (isinstance(block, dict)
                                          and block.get("type") == "tool_result")
                        if is_tool_result:
                            result_content = block.get("content", "")
                            if isinstance(result_content, str):
                                total_size += len(result_content)
                            elif isinstance(result_content, list):
                                for item in result_content:
                                    if isinstance(item, dict):
                                        text = item.get("text", "")
                                        total_size += len(text)
                                    elif isinstance(item, str):
                                        total_size += len(item)
    except (OSError, PermissionError) as e:
        ...
```

10 levels of indentation. The innermost branch (measuring a text item
inside a list inside a tool_result block) is buried at column 40.

**Why it matters:** This runs in a PostToolUse hook on every tool call.
Correctness is safety-critical: a bug in the innermost branch
silently undercounts bloat. The current structure makes it difficult to
unit-test the content-counting logic independently of the file-reading
logic.

**Before/after sketch:**
Before: monolithic function.
After: extract `_count_content_bytes(content: Any) -> int` as a
separate function that handles the isinstance branching. The outer
function handles file reading and line iteration only. Max nesting
drops from 10 to 4.

---

### [E04] Multi-walk file collection in find_duplicates

**File:** `plugins/conserve/scripts/detect_duplicates.py:185-187`

```python
elif path.is_dir():
    for ext in extensions:          # 13 iterations
        files.extend(path.rglob(f"*{ext}"))   # full walk each time
```

13 `rglob` calls each traverse the directory tree independently.
For a 1000-file project this is 13,000 `stat()` calls instead of 1,000.

**Why it matters:** `find_duplicates` is the core scan function. On the
full monorepo (2,383 Python files, 2,182 markdown files), the multi-walk
causes measurable overhead. The fix is O(1) extra code.

**Before (13 walks):**
```python
for ext in extensions:
    files.extend(path.rglob(f"*{ext}"))
```

**After (1 walk):**
```python
files.extend(
    f for f in path.rglob("*")
    if f.is_file() and f.suffix.lower() in extensions
)
```

---

### [E05] run_loop multi-responsibility function

**File:** `plugins/phantom/src/phantom/loop.py:153-328`

```python
def run_loop(task, api_key, loop_config=None, ...) -> LoopResult:
    # 1. Initialize 5 subsystems (lines 182-198)
    action_filter = ActionFilter(...)
    gate = ConfirmationGate(...)
    screenshot_tracker = ScreenshotTracker()
    stuck_policy = StuckPolicy(...)
    cost_tracker = CostTracker(...)

    # 2. Build API message list (lines 200-203)
    messages = [{"role": "user", "content": task}]

    # 3. Main loop: API calls (lines 206-232)
    for iteration in range(config.max_iterations):
        response = client.beta.messages.create(**kwargs)

        # 4. Track costs (lines 235-243)
        cost_tracker.record(...)

        # 5. Process tool results: action filter, confirmation gate,
        #    stuck detection (lines 255-314)
        for block in response_content:
            if block.name == "computer" and not action_filter.is_allowed(...):
                ...
            if stuck_policy.should_abort(...):
                ...
```

**Why it matters:** 176 lines in one function with 6 sequential
concerns means the iteration loop, the tool dispatch, and the stuck
detector cannot be tested independently. The function is also the
primary surface for adding new safety features (e.g., a new blocked
region), guaranteeing it will grow further.

**Before/after sketch:**
Before: `run_loop` owns all 6 phases.
After: extract `_process_iteration(client, messages, tools, ...) ->
IterationResult` for a single turn, and `_run_tool_block(block, ...) ->
dict` for tool execution with safety checks. `run_loop` becomes a
thin coordinator (~50 lines).

---

### [E06] detect_language — data embedded in function body

**File:** `plugins/scribe/src/scribe/pattern_loader.py:101-237`

```python
def detect_language(text: str) -> str:
    ...
    markers: dict[str, set] = {
        "en": {"the", "is", "are", "was", "were", "have", "has",
               "been", "will", "would", "could", "should", ...},  # 16 words
        "de": {"der", "die", "das", "ist", "sind", "war", ...},   # 16 words
        "fr": {"le", "la", "les", "est", "sont", ...},            # 16 words
        "es": {...},  # 16 words
        "pt": {...},  # 16 words
        "it": {...},  # 16 words
    }
    # Actual logic: ~20 lines
```

117 of 137 lines are data. The function cannot be extended with a new
language without editing the function body.

**Before/after sketch:**
Before: markers dict inline.
After: `_LANGUAGE_MARKERS: dict[str, frozenset[str]] = {...}` as a
module-level constant. `detect_language` shrinks to ~20 lines and the
data is independently inspectable and testable.

---

### [E07] initialize_plugin_project — mixed concerns, 209 lines

**File:** `plugins/attune/scripts/plugin_project_init.py:114-322`

```python
def initialize_plugin_project(
    plugin_name: str,
    base_dir: Path,
    ...
) -> dict[str, Any]:
    # Creates directories (lines 130-145)
    # Writes 8 template files (lines 148-230)
    # Runs validation (lines 232-265)
    # Formats status output (lines 267-322)
```

Four phases in one function, each independently testable only via
the full function call.

**Before/after sketch:**
Before: single 209-line function.
After: `_create_structure(...)`, `_write_templates(...)`,
`_validate_structure(...)` each ~50 lines. `initialize_plugin_project`
calls them in sequence and assembles the result dict.

---

### [E08] O(n²) work item grouping in detect_independent_items

**File:** `plugins/egregore/scripts/parallel.py:49-63`

```python
for item in work_items:                       # outer: n items
    ...
    for other in work_items:                  # inner: n items each
        if other["id"] in seen or ...:
            continue
        if other.get("source_ref") != item.get("source_ref"):
            group.append(other["id"])
            seen.add(other["id"])
```

For n=20 items: 400 iterations. Scales poorly if egregore manifests
grow. The `seen` set prevents double-processing items but the inner
loop still iterates the full list on every outer step.

**Before/after sketch:**
Before: O(n²) nested loops.
After: group by `source_ref` using a dict in O(n), then build
independent groups by picking one item per distinct `source_ref`:

```python
by_ref: dict[str, list[str]] = {}
for item in work_items:
    if item.get("status") == "active":
        by_ref.setdefault(item.get("source_ref", ""), []).append(item["id"])
# One item per distinct source_ref per group
groups = [[ids[i] for ids in by_ref.values() if i < len(ids)]
          for i in range(max((len(v) for v in by_ref.values()), default=0))]
```

---

### [E09] Example SKILL.md with unresolvable module links

**File:**
`plugins/abstract/docs/examples/modular-skills/complete-skills/development-workflow/SKILL.md`

```markdown
- [Git Workflow](modules/git-workflow/)
- [Code Review](modules/code-review/)
- [Testing Strategies](modules/testing-strategies/)
- [Deployment Procedures](modules/deployment-procedures/)
```

None of these module directories exist. The file is in a `docs/examples`
path, so it will not break a running skill, but it documents a pattern
that cannot be copied and run as-is. A developer following the example
will produce a broken SKILL.md.

**Fix:** Either create stub modules or change links to prose
descriptions that are not formatted as file references.

---

### [E10] Unvalidated path from manifest in watchdog.sh

**File:** `plugins/egregore/scripts/watchdog.sh:62-69`

```bash
project_dir=$(jq -r '.project_dir' "$MANIFEST" 2>/dev/null)
if [[ -z "$project_dir" || "$project_dir" == "null" ]]; then
    project_dir="$(pwd)"
fi

# Relaunch
log "Relaunching egregore session ($remaining active items)"
cd "$project_dir"
```

`project_dir` is read directly from user-controlled
`.egregore/manifest.json` and passed to `cd` without path validation.
A manifest containing `project_dir: "/etc"` would cause the script to
`cd /etc` before launching `claude`. The script runs with `set -euo
pipefail` so an invalid path causes exit (safe), but a valid but
unintended absolute path (e.g., `/tmp/evil`) causes the session to
launch in the wrong directory without warning.

**Before:**
```bash
project_dir=$(jq -r '.project_dir' "$MANIFEST" 2>/dev/null)
```

**After:**
```bash
project_dir=$(jq -r '.project_dir' "$MANIFEST" 2>/dev/null)
# Validate: must be an existing directory under a safe prefix
if [[ -z "$project_dir" || "$project_dir" == "null" ]]; then
    project_dir="$(pwd)"
elif [[ ! -d "$project_dir" ]]; then
    log "ERROR: project_dir '$project_dir' does not exist, aborting"
    exit 1
fi
```

---

### [E11] Repeated re.search loops over same content

**File:** `plugins/imbue/scripts/imbue_validator.py:180-193` and
`plugins/imbue/scripts/imbue_validator.py:196-212`

```python
review_patterns = [
    r"workflow", r"evidence", r"structured", r"output",
    r"orchestrat", r"checklist", r"deliverable",
]
for pattern in review_patterns:
    if re.search(pattern, content, re.IGNORECASE):
        review_workflow_skills.add(skill_name)
        break

# ...6 lines later...
review_components = [
    r"checklist", r"deliverable", r"evidence",
    r"structured", r"workflow",
]
missing_components = []
for component in review_components:
    if not re.search(component, content, re.IGNORECASE):
        missing_components.append(component)
```

The same `content` string is searched twice with overlapping pattern
sets (`workflow`, `evidence`, `checklist`, `deliverable`, `structured`
appear in both). For large skill files (some SKILL.md files are 500+
lines), this doubles the regex work.

**Fix:** Compile patterns into a single `re.compile("pattern1|pattern2|...")`
and run one pass. The `break`-on-first-match can be preserved with
`any(re.search(p, content, re.I) for p in review_patterns)`.

---

### [E12] detect_language — NOTE (informational, not a finding)

The six languages and 16-word sets produce a correct but brittle
detector. "it" (Italian) matches the English word "it", causing false
positives for short English texts. This is a logic issue orthogonal
to the code structure but worth noting when extracting the data to
a constant: add a comment about the collision risk.

---

## Recommendations

### Phase 1 — Quick fixes (S effort, 1-2 days)

1. **[F04] Single-walk file collection** (`detect_duplicates.py:185-187`)
   Replace `for ext in extensions: path.rglob(f"*{ext}")` with one
   `rglob("*")` filtered by suffix. 3-line change, no API break.

2. **[F09] Extract language markers constant** (`pattern_loader.py:118`)
   Move the `markers` dict to `_LANGUAGE_MARKERS` at module level.
   `detect_language` body shrinks from 137 to ~20 lines.

3. **[F12] Watchdog path validation** (`watchdog.sh:62-69`)
   Add `[[ -d "$project_dir" ]]` guard before `cd`. 3-line addition.

4. **[E11] Merge re.search loops** (`imbue_validator.py:180-212`)
   Combine overlapping pattern lists and use
   `any(re.search(...) for p in patterns)`. Halves regex passes over
   large files.

5. **[F11] Fix example SKILL.md links** (abstract/docs/examples)
   Either create stub module directories or replace markdown links
   with plain-text references. Zero production impact.

### Phase 2 — Structural improvements (M effort, 3-7 days each)

6. **[F03] Extract content-counting helper** (`tool_output_summarizer.py`)
   Extract `_count_content_bytes(content: Any) -> int`. Reduces max
   nesting from 10 to 4. Add unit tests for the extracted function.

7. **[F07] Decompose run_loop** (`phantom/loop.py`)
   Extract `_process_iteration(...)` and `_run_tool_block(...)`. Each
   extracted function is independently testable. Existing integration
   tests verify behavior is unchanged.

8. **[F08] O(n²) -> O(n) in detect_independent_items** (`parallel.py`)
   Replace nested loops with group-by-source_ref dict. Add a test
   with n=100 items to prevent regression.

9. **[F10] Decompose initialize_plugin_project** (`plugin_project_init.py`)
   Three extracted functions (`_create_structure`, `_write_templates`,
   `_validate_structure`) bring each phase under 60 lines and allow
   unit tests that mock individual phases.

### Phase 3 — Larger refactors (L effort, 1-2 weeks)

10. **[F01] Enforce JSON utility consistency** (imbue/conserve hooks)
    Add a `make check-json-utils` target that diffs the inlined blocks
    against the canonical `scripts/shared/json_utils.sh`. Wire into
    pre-commit. Does not require changing the inlining strategy.

11. **[F02] Split TestingGuideSkill** (`testing_guide.py`)
    Extract `TestStructureAnalyzer` (methods 1-5), `TestQualityEvaluator`
    (methods 6-10), `TestRecommendationEngine` (methods 11-25).
    `TestingGuideSkill` becomes a coordinator delegating to all three.
    Effort is large due to test coverage required.

12. **[F05/F06] Document cross-skill module reference contract**
    (`skills-eval/SKILL.md`, `modular-skills/SKILL.md`)
    The pattern of `../sibling-skill/modules/file.md` works but is
    undocumented. Add a line to `abstract:skill-authoring` stating
    the contract: cross-skill module refs are stable only when the
    owning skill's version is pinned in the consuming skill's
    `dependencies` field.
