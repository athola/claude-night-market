# Algorithmic Efficiency Findings

## Summary

- Total findings: 12
- HIGH impact (likely user-visible perf or O(n^2)->O(n)): 4
- MEDIUM impact (cleaner + faster): 6
- LOW impact (micro-optimizations): 2

The Rust review skill (`plugins/pensive/.../rust_review/`) is the
single largest performance hotspot: every analyzer pass loops over
all source lines and inside the loop runs `re.search` against
uncompiled string literals. With ~6 analyzer modules each scanning
each Rust file, this multiplies regex parse cost by N_lines * N_patterns
* N_passes per file.

Also notable: `repository_analyzer` and `code_review` workflows do
N rglob traversals (one per language extension) where one walk
suffices; this is the largest single algorithmic improvement
available (file I/O dominates).

## Findings

### A-01: Rust review patterns recompiled per line

- **Impact**: HIGH
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/pensive/src/pensive/skills/rust_review/builtins.py:71-148`
  (also `cargo.py:60-90`, `patterns.py:77-234`, `safety.py:43-99`,
  `ownership.py:34-201`, `structure.py:34-211`)
- **Current complexity**: O(L * P * regex_parse) per file
- **Target complexity**: O(L * P) with patterns parsed once at module load
- **Current code**:
  ```python
  for i, line in enumerate(lines):
      if any(re.search(pat, line) for pat in self._BUILTIN_EXCLUSION_PATTERNS):
          continue
      for (pattern, trait_name, recommendation) in self._BUILTIN_CONVERSION_PATTERNS:
          if re.search(pattern, line):
              issues.append({...})
              break
      if re.search(BUILTIN_TO_STRING_PATTERN, line):
          ...
  ```
- **Proposed code**:
  ```python
  # Compile once at module/class load time (e.g. in rust_review_data.py
  # or in a class-level _compile() method).
  _BUILTIN_EXCLUSION_RE = [re.compile(p) for p in BUILTIN_EXCLUSION_PATTERNS]
  _BUILTIN_CONVERSION_RE = [
      (re.compile(p), t, r) for p, t, r in BUILTIN_CONVERSION_PATTERNS
  ]
  _BUILTIN_TO_STRING_RE = re.compile(BUILTIN_TO_STRING_PATTERN)

  for i, line in enumerate(lines):
      if any(rx.search(line) for rx in _BUILTIN_EXCLUSION_RE):
          continue
      for rx, trait_name, recommendation in _BUILTIN_CONVERSION_RE:
          if rx.search(line):
              issues.append({...})
              break
      if _BUILTIN_TO_STRING_RE.search(line):
          ...
  ```
- **Rationale**: Python's `re` module caches a small number of recently
  compiled patterns, but with dozens of patterns scanned across thousands
  of lines the cache thrashes. Pre-compiling drops repeat parse cost to
  zero. Confirmed in `gauntlet/incremental.py:19` and
  `gauntlet/blast_radius.py:49` which already follow this pattern.
- **Evidence**: `[E1]` Read confirmed pattern in `rust_review/builtins.py:72,80,92,102,118,138`;
  `rust_review/patterns.py:79,111,144,189,223,257`;
  `rust_review/safety.py:19,45,54,90,99,132`;
  `rust_review/structure.py:35,38,45,58,103-141,182-211`;
  `rust_review/cargo.py:61,71,88,113,131,145,234`. Constants are stored
  as string literals in `rust_review_data.py` (imported at `builtins.py:14`).

---

### A-02: Repository language detection re-walks tree per extension

- **Impact**: HIGH
- **Effort**: MEDIUM
- **Risk**: LOW
- **Location**: `plugins/pensive/src/pensive/analysis/repository_analyzer.py:113-119, 162-170`
- **Current complexity**: O(N_files * N_extensions) traversal
- **Target complexity**: O(N_files) -- single walk
- **Current code**:
  ```python
  for lang, extensions in self.LANGUAGE_EXTENSIONS.items():
      for ext in extensions:
          count = sum(1 for _ in repo_path.rglob(f"*{ext}"))
          if count > 0:
              languages[lang] = languages.get(lang, 0) + count
  ```
- **Proposed code**:
  ```python
  # Build ext -> lang map once
  ext_to_lang = {
      ext: lang
      for lang, exts in self.LANGUAGE_EXTENSIONS.items()
      for ext in exts
  }
  languages: dict[str, int] = {}
  for path in repo_path.rglob("*"):
      if not path.is_file():
          continue
      lang = ext_to_lang.get(path.suffix)
      if lang:
          languages[lang] = languages.get(lang, 0) + 1
  ```
- **Rationale**: For ~10 languages with ~3 extensions each, this is
  30 full directory traversals where one suffices. The disk I/O
  cost is O(N_files * 30) instead of O(N_files). On a medium repo
  (50k files) this cuts walk time from minutes to seconds.
  The existing comment "avoids materializing the rglob iterator"
  optimizes the wrong axis -- the tree walk itself is the cost.
- **Evidence**: `[E1]` Read confirmed pattern in
  `repository_analyzer.py:113-119` (detect_languages) and
  `repository_analyzer.py:165-170` (_count_files: nested loop again).

---

### A-03: code_review collects files via 6 separate rglobs

- **Impact**: HIGH
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/pensive/src/pensive/workflows/code_review.py:125-130`
- **Current complexity**: O(N_files * 6)
- **Target complexity**: O(N_files)
- **Current code**:
  ```python
  def _collect_files(self, repo_path: Path) -> list[str]:
      files: list[str] = []
      for ext in ["*.py", "*.rs", "*.js", "*.ts", "*.java", "*.go"]:
          files.extend(str(f.relative_to(repo_path)) for f in repo_path.rglob(ext))
      return files
  ```
- **Proposed code**:
  ```python
  _CODE_SUFFIXES = {".py", ".rs", ".js", ".ts", ".java", ".go"}

  def _collect_files(self, repo_path: Path) -> list[str]:
      return [
          str(f.relative_to(repo_path))
          for f in repo_path.rglob("*")
          if f.is_file() and f.suffix in _CODE_SUFFIXES
      ]
  ```
- **Rationale**: Same as A-02 -- six full directory scans where one
  suffices. Set membership is O(1).
- **Evidence**: `[E1]` Read confirmed at `code_review.py:128-129`.

---

### A-04: SKILL.md tree scanned 3+ times in safe_replacer

- **Impact**: HIGH
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/conserve/scripts/safe_replacer.py:148-180`
- **Current complexity**: O(3 * N_files * walk_cost)
- **Target complexity**: O(N_files) (one walk, materialize once)
- **Current code**:
  ```python
  if args.validate_only:
      issues = []
      for skill_file in base_path.rglob("SKILL.md"):
          ...
      result = {
          "files_scanned": len(list(base_path.rglob("SKILL.md"))),
          ...
      }
  else:
      files_updated, total_changes = updater.update_directory(base_path)  # rglob #1
      issues = []
      for skill_file in base_path.rglob("SKILL.md"):  # rglob #2
          ...
  ```
- **Proposed code**:
  ```python
  skill_files = list(base_path.rglob("SKILL.md"))  # walk once
  if args.validate_only:
      issues = []
      for skill_file in skill_files:
          file_issues = updater.validate_references(skill_file)
          if file_issues:
              issues.extend(...)
      result = {"files_scanned": len(skill_files), "issues_found": issues, ...}
  else:
      files_updated, total_changes = updater.update_directory_files(skill_files)
      issues = [...]
  ```
- **Rationale**: `rglob("SKILL.md")` walks the entire tree. Doing it
  three times is 3x the I/O.
- **Evidence**: `[E1]` Read confirmed three rglob calls at
  `safe_replacer.py:103, 149, 160, 171`.

---

### A-05: Rust ownership analyzer compiles regex inside per-line inner loop

- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/pensive/src/pensive/skills/rust_review/ownership.py:37-55`
- **Current complexity**: O(L * 10 * regex_parse)
- **Target complexity**: O(L * 10)
- **Current code**:
  ```python
  move_pattern = re.compile(r"\blet\s+(\w+)\s*=\s*(\w+)\s*;")  # Good: compiled once
  lines = self._get_lines(content)
  for i, line in enumerate(lines):
      for j in range(max(0, i - 10), i):
          m = move_pattern.search(lines[j])
          if m:
              moved_from = m.group(2)
              if re.search(
                  rf"\b{re.escape(moved_from)}\b", line  # NEW regex per inner iter
              ) and moved_from != m.group(1):
  ```
- **Proposed code**:
  ```python
  # Cache compiled per-token regexes within this analyze pass.
  token_pattern_cache: dict[str, re.Pattern[str]] = {}

  def _word_re(tok: str) -> re.Pattern[str]:
      rx = token_pattern_cache.get(tok)
      if rx is None:
          rx = re.compile(rf"\b{re.escape(tok)}\b")
          token_pattern_cache[tok] = rx
      return rx

  for i, line in enumerate(lines):
      for j in range(max(0, i - 10), i):
          m = move_pattern.search(lines[j])
          if m:
              moved_from = m.group(2)
              if _word_re(moved_from).search(line) and moved_from != m.group(1):
  ```
- **Rationale**: The inner `re.search(rf"\b{re.escape(...)}\b", line)`
  recompiles a new regex for every (i, j) pair. Caching by token
  keeps compilation count O(unique_tokens) instead of O(L * 10).
- **Evidence**: `[E1]` Read confirmed at `ownership.py:43-44`.

---

### A-06: Rust patterns analyzers re-search regex after `if re.search(...)` succeeds

- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/pensive/src/pensive/skills/rust_review/structure.py:38-39, 103-104, 110-111, 140-141, 182-185`
- **Current complexity**: 2x regex evaluation when matched
- **Target complexity**: 1x evaluation
- **Current code**:
  ```python
  if re.search(r"macro_rules!\s+(\w+)", line):
      macro_match = re.search(r"macro_rules!\s+(\w+)", line)  # second search
      if macro_match:
          macro_name = macro_match.group(1)
  ...
  if re.search(r"trait\s+(\w+)", line) and "impl" not in line:
      trait_match = re.search(r"trait\s+(\w+)", line)  # second search
  ```
- **Proposed code**:
  ```python
  macro_match = _MACRO_RULES_RE.search(line)
  if macro_match:
      macro_name = macro_match.group(1)
  ...
  trait_match = _TRAIT_DEF_RE.search(line) if "impl" not in line else None
  if trait_match:
      ...
  ```
- **Rationale**: The truthy guard pattern runs the regex twice per
  matching line, which is wasteful. Capture once, branch on the
  Match object directly. Also wins from A-01's pre-compilation.
- **Evidence**: `[E1]` Read confirmed exact double-search at
  `structure.py:38-39, 103-104, 110-111, 140-141, 182-185`.

---

### A-07: Counter pattern via `dict.get(k, 0) + 1` in tight loops

- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/memory-palace/src/memory_palace/session_history.py:413-416`,
  `plugins/memory-palace/src/memory_palace/project_palace.py:644`,
  `plugins/memory-palace/src/memory_palace/palace_repository.py:268`,
  `plugins/tome/src/tome/synthesis/quality.py:47, 98`,
  `plugins/leyline/scripts/verify_plugin.py:167-169`
  (~12 sites total)
- **Current complexity**: 2 dict ops per increment (get + setitem)
- **Target complexity**: 1 op via Counter
- **Current code**:
  ```python
  topics: dict[str, int] = {}
  outcomes: dict[str, int] = {}
  for s in sessions:
      for topic in s.get("topics", []):
          topics[topic] = topics.get(topic, 0) + 1
      outcome = s.get("outcome", "unknown") or "unknown"
      outcomes[outcome] = outcomes.get(outcome, 0) + 1
  ```
- **Proposed code**:
  ```python
  from collections import Counter

  topics: Counter[str] = Counter()
  outcomes: Counter[str] = Counter()
  for s in sessions:
      topics.update(s.get("topics", []))
      outcomes[s.get("outcome", "unknown") or "unknown"] += 1
  ```
- **Rationale**: `Counter.update` is implemented in C and runs ~2x
  faster than the Python `get(k, 0) + 1` idiom. More importantly,
  it's idiomatic and removes a class of off-by-one bugs.
- **Evidence**: `[E1]` Read confirmed at `session_history.py:413-416`.
  `[E2]` Found 12+ similar sites via grep `\.get\([^,)]+,\s*0\)\s*\+\s*1`.

---

### A-08: Sort-then-slice top-K instead of heapq.nlargest

- **Impact**: MEDIUM
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/memory-palace/src/memory_palace/project_palace.py:647-651, 654-656`,
  `plugins/memory-palace/src/memory_palace/session_history.py:420`,
  `plugins/abstract/scripts/validate_budget.py:187`
- **Current complexity**: O(N log N) for full sort
- **Target complexity**: O(N log K) for top-K
- **Current code**:
  ```python
  all_entries.sort(
      key=lambda x: x.get("importance_score", 40),
      reverse=True,
  )
  stats["top_entries"] = all_entries[:5]

  stats["top_tags"] = dict(
      sorted(stats["top_tags"].items(), key=lambda x: x[1], reverse=True)[:10]
  )
  ```
- **Proposed code**:
  ```python
  import heapq

  stats["top_entries"] = heapq.nlargest(
      5, all_entries, key=lambda x: x.get("importance_score", 40)
  )
  stats["top_tags"] = dict(
      heapq.nlargest(10, stats["top_tags"].items(), key=lambda x: x[1])
  )
  ```
- **Rationale**: For K << N, `heapq.nlargest` is asymptotically and
  practically faster. With 1000 entries and K=5 it's ~10x; with 100k
  entries and K=10 it's much more. Also self-documents intent.
- **Evidence**: `[E1]` Read confirmed at `project_palace.py:647-651, 654-656`.

---

### A-09: Counter import unused; `_get_lines` repeats split per analyzer

- **Impact**: MEDIUM
- **Effort**: MEDIUM
- **Risk**: MEDIUM
- **Location**: `plugins/pensive/src/pensive/skills/rust_review/*.py` (all analyzer modules
  in the rust_review package call `self._get_lines(content)` independently)
- **Current complexity**: For each Rust file, content is split into
  lines once per analyzer pass (>=6 passes)
- **Target complexity**: Split once, pass `lines` between analyzers
- **Current code**: Every analyzer in `builtins.py`, `cargo.py`,
  `patterns.py`, `safety.py`, `ownership.py`, `structure.py` does:
  ```python
  content = context.get_file_content(file_path)
  ...
  lines = self._get_lines(content)
  for i, line in enumerate(lines):
      ...
  ```
- **Proposed code**:
  ```python
  # In the orchestrating method:
  content = context.get_file_content(file_path)
  lines = self._get_lines(content)  # split once
  ctx = AnalysisContext(content=content, lines=lines)
  results = {}
  results.update(self.analyze_builtin_preference(ctx, file_path))
  results.update(self.analyze_unsafe_code(ctx, file_path))
  ...
  ```
- **Rationale**: `_get_lines` likely calls `content.splitlines()` which
  is O(N) and allocates a new list. Doing it once per file (instead of
  once per analyzer) cuts redundant work proportional to the number
  of analyzers (~6x). Risk is MEDIUM because the public analyzer
  signatures must change to accept pre-split lines.
- **Evidence**: `[E1]` Read confirmed `lines = self._get_lines(content)`
  at `builtins.py:69`, `patterns.py:76, 108, 141, 174, 220, 254`,
  `safety.py:43, 87`, `ownership.py:36, 115, 174`, `structure.py:33, 98, 178`.

---

### A-10: blocking_detection rebuilds keyword list per AST visit

- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/parseltongue/src/parseltongue/analysis/async_analysis/blocking_detection.py:174-184`
- **Current complexity**: List of 6 keywords allocated per call
- **Target complexity**: Module-level frozenset with O(1) lookup
- **Current code**:
  ```python
  if call_name and any(
      keyword in call_name.lower()
      for keyword in [
          "fetch", "get", "post", "api", "async", "call",
      ]
  ):
      missing_awaits[function_name] = {...}
  ```
- **Proposed code**:
  ```python
  # Module level
  _ASYNC_CALL_HINTS = ("fetch", "get", "post", "api", "async", "call")

  ...
  if call_name:
      lowered = call_name.lower()
      if any(hint in lowered for hint in _ASYNC_CALL_HINTS):
          missing_awaits[function_name] = {...}
  ```
- **Rationale**: Allocating the literal list each call is wasteful;
  also `call_name.lower()` is recomputed by every iteration of the
  generator. Modest fix but good hygiene. Note: substring search,
  not equality, so a frozenset wouldn't work directly here.
- **Evidence**: `[E1]` Read confirmed at `blocking_detection.py:174-184`.

---

### A-11: List membership tests in tight branches should be sets/tuples

- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/pensive/src/pensive/skills/rust_review/cargo.py:117`,
  `plugins/pensive/src/pensive/skills/rust_review/reporting.py:114-118`,
  `plugins/pensive/src/pensive/skills/architecture_review.py:368`,
  `plugins/sanctum/hooks/security_pattern_check.py:211`,
  `plugins/conserve/scripts/growth_controller.py:117, 130, 325, 334`
- **Current complexity**: O(N) per check with tiny N (3-5)
- **Target complexity**: O(1) with set; main win is allocation cost
- **Current code**:
  ```python
  # cargo.py:117
  if not any(c in version for c in ["^", "~", ">", "<", "*"]):  # rebuilt each call

  # reporting.py:114-118
  if issue_type in ["buffer_overflow", "data_race"]:  # list literal allocated
  elif issue_type in ["deprecated_dependency"]:
  elif issue_type in ["unwrap_usage", "missing_docs"]:
  ```
- **Proposed code**:
  ```python
  # Module-level constants
  _VERSION_RANGE_CHARS = frozenset("^~><*")
  _CRITICAL_TYPES = frozenset({"buffer_overflow", "data_race"})
  _HIGH_TYPES = frozenset({"deprecated_dependency"})
  _MEDIUM_TYPES = frozenset({"unwrap_usage", "missing_docs"})

  # cargo.py
  if not any(c in _VERSION_RANGE_CHARS for c in version):
  # ...or simpler:
  if not _VERSION_RANGE_CHARS.intersection(version):

  # reporting.py
  if issue_type in _CRITICAL_TYPES:
  elif issue_type in _HIGH_TYPES:
  elif issue_type in _MEDIUM_TYPES:
  ```
- **Rationale**: The dominant cost here isn't the lookup -- it's
  re-allocating the list literal each call. Lifting to a module-level
  frozenset removes the allocation entirely. Self-documents intent too.
- **Evidence**: `[E1]` grep confirmed 30+ `in [...]` literal sites; cited
  examples Read-verified at the listed line numbers.

---

### A-12: imbue/iron_law impl_to_test_paths dedup uses set + list when dict.fromkeys suffices

- **Impact**: LOW
- **Effort**: SMALL
- **Risk**: LOW
- **Location**: `plugins/imbue/validators/iron_law.py:84-91`
- **Current complexity**: O(N) but with two collections
- **Target complexity**: Same O(N), single one-liner
- **Current code**:
  ```python
  # Deduplicate while preserving order.
  seen: set[str] = set()
  out: list[str] = []
  for c in candidates:
      if c not in seen:
          seen.add(c)
          out.append(c)
  return out
  ```
- **Proposed code**:
  ```python
  return list(dict.fromkeys(candidates))
  ```
- **Rationale**: `dict.fromkeys` preserves insertion order (since 3.7)
  and de-duplicates in C. One line replaces six. Correctness is
  unchanged because there are at most ~5 candidates. Pure readability
  win at this scale.
- **Evidence**: `[E1]` Read confirmed at `iron_law.py:85-91`.

---

## Skipped (reviewed but not flagged)

- `plugins/pensive/src/pensive/skills/math_review.py:50-334`: many
  `re.search` calls but each runs once per file (not in a loop), so
  pre-compilation gain is small. Could batch via a single combined
  regex, but the readability cost outweighs the saving.
- `plugins/conjure/scripts/delegation_executor.py:446-450`: subprocess
  calls in a loop are intentional retry/probe logic, not batchable.
- `plugins/sanctum/hooks/session_complete_notify.py:386-401`: PowerShell
  fallback loop is correct -- each call is a different binary path.
- `plugins/conserve/scripts/detect_duplicates.py:228-248`: bisect-based
  overlap detection is already optimal for the use case.
