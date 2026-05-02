# AI Hygiene Audit Report

**Scan date:** 2026-05-01
**Branch:** `ai-slop-1.9.4`
**Scope:** 1,547 markdown files, 2,384 Python files (first-party)
**Excluded:** `.venv/`, `node_modules/`, `__pycache__/`, `.git/`,
`htmlcov/`, `.pytest_cache/`, `clawhub/`, `.claude/worktrees/`,
`.uv-tools/`, `CHANGELOG.md`, `plugins/scribe/skills/slop-detector/`
**Strictness:** STRICT

---

## Summary

**AI Hygiene Score: 61/100 — MODERATE CONCERN**

The meta-irony of branch `ai-slop-1.9.4` is earned. The repo ships
slop-detection tooling that correctly identifies the same patterns
found in its own authored prose. The codebase is not critically
broken, but it carries measurable AI-generation debt concentrated
in five systemic patterns.

**Top 5 systemic patterns:**

1. Em-dash overuse in skill/command prose (up to 26/1000 words;
   rule target: <2/1000). Affects writing-guide files most severely
   — the guides for how to write well violate the rule they teach.
2. Tier-1 slop phrases in 254 markdown files (16.4% penetration).
   "actionable" leads at 122 hits; "structured" at 314. Most hits
   in command descriptions, SKILL.md descriptions, and skill
   discoverability templates — contexts where a single word
   becomes a repeated template fill.
3. Self-narration in tutorial content. Two files open with "By the
   end of this tutorial" — the canonical pattern the slop-scan
   rules prohibit.
4. 1,185 restating docstrings across Python source and tests.
   The majority restate the function name with no added semantic
   content ("Add a new task to the tracker." on `add_task()`).
5. 14.9% code duplication in `plugins/` (50,970 / 342,486 lines),
   driven by copy-pasted boilerplate comment separators, `from
   __future__ import annotations` blocks, and test fixture scaffolds.

**Files with worst density:**

| File | Primary issue | Metric |
|------|--------------|--------|
| `plugins/scribe/skills/session-to-post/modules/narrative-structure.md` | Em-dash density | 26.2/1000 words |
| `plugins/sanctum/commands/update-ci.md` | Em-dash density | 20.4/1000 words |
| `plugins/scribe/skills/session-to-post/SKILL.md` | Em-dash density | 18.8/1000 words |
| `plugins/imbue/commands/structured-review.md` | Tier-1 phrases | 18 hits / 489 words |
| `plugins/imbue/skills/structured-output/SKILL.md` | Tier-1 phrases | 17 hits / 580 words |

---

## P0 Critical

Every entry is reproducible with the command shown.

### P0-1: Self-narration opener in public tutorial

**File:** `book/src/getting-started/first-plugin.md:8`

**Pattern:** "By the end of this tutorial, you'll:"

**Rule violated:** `.claude/rules/slop-scan-for-docs.md` Layer 2,
item 4: "Scan for self-narration of structure: 'By the end of this
guide...'"

**Reproduction:**

```bash
rg -n "By the end of this" book/src/getting-started/first-plugin.md
```

**Fix:** Replace with the list directly under a heading, or open
with what the reader will have built. "After this tutorial you have
a working sanctum PR review pipeline" is a concrete claim; "By the
end you'll:" is throat-clearing.

---

### P0-2: Self-narration opener in tutorial skill module

**File:**
`plugins/sanctum/skills/tutorial-updates/modules/markdown-generation.md:178`

**Pattern:** "By the end of this tutorial, you'll understand:"

**Rule violated:** Same as P0-1.

**Reproduction:**

```bash
rg -n "By the end of" \
  plugins/sanctum/skills/tutorial-updates/modules/markdown-generation.md
```

**Note:** This file is a skill that generates tutorials. The
self-narration appears inside an example template it produces,
which means the generated output will carry the prohibited pattern
into every tutorial it creates. Higher blast radius than a single
doc.

**Fix:** Replace the example template with a thesis-first opener.
Slop in a template multiplies across all generated artifacts.

---

### P0-3: Bare stub entries in public docs/guides/README.md

**File:** `docs/guides/README.md:175-176`

```markdown
| Error Handling | _(TODO)_ |
| LSP Setup      | _(TODO)_ |
```

**Rule violated:** `.claude/rules/slop-scan-for-docs.md` Layer 0,
item 3: "Bare stubs in production paths: every TODO, FIXME, XXX,
HACK must either link to a tracked issue or be deleted."

Neither entry links to a tracker issue.

**Reproduction:**

```bash
rg -n "TODO" docs/guides/README.md
```

**Fix:** Delete the rows or replace `_(TODO)_` with
`_(TODO: #NNN)_` referencing an open issue.

---

## Findings

| ID | Path:Line | Pattern | Severity | Excerpt | Fix |
|----|-----------|---------|----------|---------|-----|
| F-01 | `book/src/getting-started/first-plugin.md:8` | Self-narration opener | HIGH | "By the end of this tutorial, you'll:" | Remove; start at the list or a thesis sentence |
| F-02 | `plugins/sanctum/skills/tutorial-updates/modules/markdown-generation.md:178` | Self-narration in template | HIGH | "By the end of this tutorial, you'll understand:" | Replace template opener; slop multiplies via codegen |
| F-03 | `docs/guides/README.md:175-176` | Bare TODOs without tracker link | HIGH | `_(TODO)_` in two table cells | Delete rows or add `#NNN` issue ref |
| F-04 | `plugins/scribe/skills/session-to-post/modules/narrative-structure.md` | Em-dash density | HIGH | 15 em-dashes / 573 words = 26.2/1000 (target <2) | Replace most with colons, commas, or periods |
| F-05 | `plugins/sanctum/commands/update-ci.md` | Em-dash density | HIGH | 18 em-dashes / 882 words = 20.4/1000 | Replace numbered-list `**label** —` separators with colons |
| F-06 | `plugins/scribe/skills/session-to-post/SKILL.md` | Em-dash density | HIGH | 23 em-dashes / 1223 words = 18.8/1000 | Reduce to ≤3 prose em-dashes; list items can use colons |
| F-07 | `plugins/leyline/skills/supply-chain-advisory/modules/incident-response.md` | Em-dash density | MEDIUM | 6 em-dashes / 306 words = 19.6/1000 | Replace `**Type** —` bullets with colons |
| F-08 | `plugins/imbue/commands/structured-review.md:9` | Tier-1 slop phrase — "actionable" | MEDIUM | "evidence capture, and deliverable structuring" + 18 total hits | `actionable` → `specific`; review all 18 hits for necessity |
| F-09 | `plugins/imbue/skills/structured-output/SKILL.md:41` | Tier-1 slop phrase — "actionable" | MEDIUM | "format findings in a consistent and actionable way" | "actionable" → "specific and ready to act on" or delete adjective |
| F-10 | `book/src/plugins/pensive.md:77` | Tier-1 slop phrase in skill prompt | MEDIUM | `# 5. Provide actionable recommendations` | Change heading to "Provide specific recommendations with evidence" |
| F-11 | `plugins/egregore/tests/test_user_prompt_hook.py:19` | Stale pytest.skip | MEDIUM | `pytest.skip("user_prompt_hook.py not yet created")` but hook exists at `plugins/egregore/hooks/user_prompt_hook.py` | Remove the skip guard; the file exists and the test should run |
| F-12 | `plugins/imbue/skills/rigorous-reasoning/SKILL.md` | File thrashing — 12 commits in 30 days | MEDIUM | Commit history shows repeated small edits; last 12 touch this file | Stabilize content; review whether churn reflects unclear ownership or scope |
| F-13 | `plugins/spec-kit/src/speckit/caching.py:66,118` | Restating docstrings | LOW | `def get()` → `"""Get cached data."""`; `def invalidate()` → `"""Invalidate cache entries."""` | Add what the function returns/does beyond the name, or delete |
| F-14 | `plugins/minister/src/minister/project_tracker.py:96` | Restating docstring | LOW | `def add_task()` → `"""Add a new task to the tracker."""` | Say what it returns, validates, or raises instead |
| F-15 | `plugins/scribe/tests/test_metrics.py:101` | Tab-completion boilerplate — 978 occurrences of 5-line comment separator | LOW | `# --------------------------------------------------------------------` repeated identically | Replace with a single module-level comment pattern; not a separate offense per block |

---

## Evidence

### Em-dash density scan

```
Command: find . -name "*.md" [exclusions] -exec bash -c '
  emdash=$(grep -o "—" "$f" | wc -l)
  words=$(wc -w < "$f")
  if [ "$words" -gt 200 ] && [ "$emdash" -gt 0 ]; then
    density=$(echo "scale=1; $emdash * 1000 / $words" | bc)
    echo "$density $emdash $words $f"
  fi
' _ {} \; | sort -rn | head -20
```

Top offenders (density / em-dashes / words / file):

```
26.2  15   573   plugins/scribe/skills/session-to-post/modules/narrative-structure.md
20.4  18   882   plugins/sanctum/commands/update-ci.md
19.6   6   306   plugins/leyline/skills/supply-chain-advisory/modules/incident-response.md
18.8  23  1223   plugins/scribe/skills/session-to-post/SKILL.md
18.9   5   264   plugins/scribe/commands/session-to-post.md
```

Rule target from `.claude/rules/slop-scan-for-docs.md`:
0-2 per 1000 words. These files exceed the target by 9-13x.
Most occurrences follow the pattern `**label** — description`
in numbered and bulleted lists. Using a colon instead
(`**label**: description`) satisfies readability without the
em-dash markup.

---

### Tier-1 slop phrase counts in markdown

```
Command: for phrase in "structured" "comprehensive" "actionable"
         "seamless" "robust" "myriad" "empower" "navigate"; do
  count=$(rg -i "\b${phrase}\b" --type md [exclusions] -c \
    | awk -F: '{sum+=$2} END {print sum}')
  echo "$phrase: $count"
done
```

Results:

```
structured:    314  (majority are command/skill names — see note)
actionable:    122  (genuine prose slop in 40+ files)
comprehensive:  107  (mix of prose and before/after examples)
navigate:        51  (majority are /navigate command references)
robust:          21
seamless:        17
empower:          1
myriad:           0
```

Note: `structured` and `navigate` are partially false positives
because `/structured-review` and `/navigate` are command names.
After filtering command names and `before/after` teaching
examples (scribe README, doc-generator remediation-workflow),
the genuine prose slop count for "actionable" alone is ~40 files.

Files with >3 unambiguous slop-phrase hits (not command names,
not before/after examples, not code blocks):

```
plugins/imbue/commands/structured-review.md     18 hits / 489 words
plugins/imbue/skills/structured-output/SKILL.md 17 hits / 580 words
plugins/memory-palace/skills/knowledge-intake/SKILL.md  11 hits / 2989 words
plugins/imbue/agents/review-analyst.md           9 hits / 353 words
plugins/memory-palace/commands/navigate.md       9 hits / 260 words
```

---

### Self-narration scan

```
Command: rg -in "let'?s dive into|in this section.{0,10}we will|
         we'?ll cover|by the end of this (guide|tutorial|section)"
         --type md [exclusions]
```

Results (3 hits):

```
book/src/getting-started/first-plugin.md:8
  "By the end of this tutorial, you'll:"
plugins/sanctum/skills/tutorial-updates/modules/markdown-generation.md:178
  "By the end of this tutorial, you'll understand:"
plugins/scribe/skills/tech-tutorial/modules/progressive-complexity.md:101
  "By the end of this tutorial, you will have a Node.js server"
  (inside a code block — borderline, but it is inside a triple-backtick
  block showing a sample tutorial structure, not authored prose)
```

---

### Stale skip guard

```
Command: rg -n "pytest.skip" plugins/egregore/tests/test_user_prompt_hook.py
Result:  19: pytest.skip("user_prompt_hook.py not yet created")

Verification: find plugins/egregore/hooks -name "user_prompt_hook.py"
Result: plugins/egregore/hooks/user_prompt_hook.py  (exists)
```

The skip guard was written before the hook was implemented. The
hook now exists and the test suite has never been run against it.

---

### Restating docstrings

```
Command: python3 -c "
  import ast, os, re
  # walk *.py, extract FunctionDef docstrings, check if
  # docstring word set is subset of function name tokens
  # and len(docstring.split()) <= 8
"
Result: 1,185 restating docstrings across 2,384 Python files
```

Sample (representative, not exhaustive):

```
plugins/spec-kit/src/speckit/caching.py:66
  def get(self, key, data=None, ttl=None) -> Any | None:
      """Get cached data."""

plugins/spec-kit/src/speckit/caching.py:118
  def invalidate(self, key=None, data=None) -> None:
      """Invalidate cache entries."""

plugins/minister/src/minister/project_tracker.py:96
  def add_task(self, ...):
      """Add a new task to the tracker."""
```

At 1,185 instances this is a systemic pattern, not isolated. The
docstrings add no information beyond the function signature. They
consume reader attention without providing return types, error
conditions, or invariants.

---

### Code duplication in plugins/

```
Command: python3 plugins/conserve/scripts/detect_duplicates.py plugins/

Files scanned: 1,215
Total lines:   342,486
Duplicate lines: 50,970
Duplication:   14.9%
```

Primary duplication sources:

1. Comment separator blocks `# ----...` appearing 978 times
   (5-line blocks in `test_metrics.py` alone accounts for most).
2. `from __future__ import annotations` + module docstring
   boilerplate appearing 139 times across plugin tests.
3. Shared pytest fixture patterns copy-pasted rather than
   extracted to `conftest.py`.

The 14.9% is within the threshold for active development but is
trending toward the elevated zone. The separator-comment pattern
is the highest-frequency single offender.

---

### Git history signals

**Refactoring ratio:**

```
Command: git log --oneline | grep -ci "refactor|cleanup|clean up|simplify|consolidat"
Result:  91 refactor commits / 905 total = 10.1%
```

This is at the lower bound of healthy (target >10%). The ratio is
not a deficiency yet, but recent commits on this branch skew
heavily toward feature additions and slop-playbook integrations
with no corresponding refactor pass.

**Massive commits (current branch additions):**

```
b6e87193  feat(scribe): integrate 2025-26 AI slop playbook  → +3,185 lines, 21 files
0567817f  feat: extend AI slop playbook integration         → +1,752 lines, 10 files
```

Both were created 2026-05-01 within 10 minutes. The combined
4,937-line addition across 31 files in two commits is the primary
source of the slop pattern density that this audit is measuring.
There is direct meta-irony: the slop-playbook integration commits
are themselves the largest source of tier-1 slop phrase occurrences
in the codebase.

**File thrashing (>10 modifications in last 30 days):**

```
README.md                                   27 modifications
plugins/imbue/skills/rigorous-reasoning/SKILL.md  12 modifications
plugins/sanctum/skills/pr-review/SKILL.md  11 modifications
plugins/attune/skills/mission-orchestrator/SKILL.md  11 modifications
plugins/conserve/scripts/context_scanner.py  11 modifications
```

The SKILL.md files represent repeated content updates without
a clear convergence signal. Twelve modifications to
`rigorous-reasoning/SKILL.md` in 30 days suggests either active
design iteration (acceptable) or ownership churn (watch).

---

## Recommendations

### Phase 1 — P0 fixes (before next merge to master)

These are merge blockers per the slop policy:

1. Remove self-narration openers in `first-plugin.md` (P0-1) and
   `markdown-generation.md` (P0-2). Two-line fix each.
2. Resolve or delete the bare `_(TODO)_` rows in
   `docs/guides/README.md` (P0-3). Either open issues for
   Error Handling and LSP Setup guides or delete the rows.
3. Remove the stale skip guard in
   `plugins/egregore/tests/test_user_prompt_hook.py:19` (F-11)
   and run the test to verify it passes.

---

### Phase 2 — Em-dash reduction (next doc-polish pass)

The three highest-density files (`narrative-structure.md`,
`update-ci.md`, `session-to-post/SKILL.md`) together account
for 56 of the flagged em-dashes. The pattern is consistent:
`**bold label** — description`. Replace the em-dash with a colon
in all list contexts. Reserve em-dashes for genuine apposition in
prose (target: 0-2 per file).

Apply `/doc-polish` or `Skill(scribe:slop-detector)` to each file
rather than a bulk regex, because some em-dashes in prose are
correct and should be preserved.

---

### Phase 3 — "actionable" purge in SKILL.md descriptions

The word "actionable" appears 122 times across 40+ files. In most
cases it means "specific" or nothing at all. A targeted
`rg -l "actionable" --type md [exclusions]` produces the full
file list. Replace with "specific", "concrete", or delete the
adjective. Batch this as a single commit with a clear rationale.

The `structured` hits (314) are mostly false positives from
command names; no action needed unless renaming commands is in
scope.

---

### Phase 4 — Docstring quality (background)

At 1,185 restating docstrings the problem is too large for a
single pass. Recommended approach: enforce a docstring quality
lint rule in `ruff` or a custom pre-commit hook that flags
one-line docstrings whose words are a subset of the function name
tokens. Add it to the Makefile `lint` target and fix violations
incrementally at time of code change. Do not attempt a bulk
rewrite — the majority are in tests where removing the docstring
is often the correct fix.

---

### Phase 5 — Slop-playbook integration review

The two commits from 2026-05-01 (`b6e87193`, `0567817f`) added
4,937 lines without a corresponding slop-scan pass. Before these
land on master, run `Skill(scribe:slop-detector)` on the 31
affected files and apply Layer 0-2 checks. The irony of the
slop-playbook integration itself being the primary slop source
is a useful data point: playbook integrations should be
treated as authored prose, not generated boilerplate.

---

### Metric targets for next audit

| Metric | Current | Target |
|--------|---------|--------|
| Em-dash density (max) | 26.2/1000 | <2/1000 |
| Tier-1 "actionable" hits | 122 | <20 |
| Self-narration instances | 2 | 0 |
| Bare TODOs without tracker | 2 | 0 |
| Stale skip guards | 1 | 0 |
| Code duplication (plugins/) | 14.9% | <10% |
| Restating docstrings | 1,185 | <200 (enforce lint) |
| Refactoring commit ratio | 10.1% | >15% |
