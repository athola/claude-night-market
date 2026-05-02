# AI Hygiene Audit Report — 2026-05-02

**Branch**: ai-slop-1.9.4
**Scope**: 1,083 tracked `.md` files (excludes
`plugins/scribe/skills/slop-detector/modules/`,
`CHANGELOG.md`, `.git`, `*.venv`, `node_modules`,
`__pycache__`, `htmlcov`, `dist`, `build`)
**Baseline**: F-04 through F-14 + 3 P0 items closed in
commits `13768898` and `b6dc115f`.
R7 detector cleared (`b8c45ab0`): verified 0 hits on
tracked Python source.

---

## Layer 0: P0 Critical Patterns

### F-01 — Bandit pre-commit hook pinned to stale version

**File**: `plugins/attune/skills/precommit-setup/modules/standard-hooks.md:51`
and `plugins/attune/skills/precommit-setup/modules/ci-integration.md:77`
**Layer**: 0 (hallucination / stale command)
**Confidence**: HIGH
**Evidence**: Both files prescribe `rev: 1.8.0` for the
bandit pre-commit hook. Current PyPI release is `1.9.4`
(two minor versions ahead).
**Remediation**: Update both `rev:` pins to `1.8.0` →
`1.9.4`. Verify with `pip index versions bandit`.

---

### F-02 — Broken cross-references: `docs/guides/documentation-standards.md`

**File**: `docs/guides/documentation-standards.md:28-29`,
`:83-85`
**Layer**: 0 (referenced paths do not exist)
**Confidence**: HIGH
**Evidence**:

- `[./modules/advanced-patterns.md]` →
  `docs/guides/modules/advanced-patterns.md` (dir missing)
- `[./modules/troubleshooting.md]` →
  `docs/guides/modules/troubleshooting.md` (dir missing)
- `[hook-types/pre-tool-use.md]` →
  `docs/guides/hook-types/pre-tool-use.md` (dir missing)
- `[hook-types/post-tool-use.md]` →
  `docs/guides/hook-types/post-tool-use.md` (dir missing)
- `[hook-types/permission-request.md]` →
  `docs/guides/hook-types/permission-request.md` (dir
  missing)

**Remediation**: Either create the missing files or
remove/update the links. The `docs/guides/modules/` and
`docs/guides/hook-types/` directories do not exist.

---

### F-03 — Broken cross-references: `docs/optimization-patterns.md`

**File**: `docs/optimization-patterns.md:207`, `:239-241`,
`:332`
**Layer**: 0 (referenced paths do not exist)
**Confidence**: HIGH
**Evidence**:

- `[../../../examples/attune/microservices-example.md]` →
  path resolves outside repo root (invalid)
- `[./advanced.md]` → `docs/advanced.md` (missing)
- `[./api-reference.md]` → `docs/api-reference.md`
  (missing)
- `[./migration.md]` → `docs/migration.md` (missing)
- `[./guides/feature-guide.md]` →
  `docs/guides/feature-guide.md` (missing)

**Remediation**: Remove four stub links. The
`microservices-example.md` reference points to a file
deleted during Phase 1 cleanup; update to an existing
example or delete the reference.

---

### F-04 — Broken cross-references: `plugins/abstract/docs/claude-code-compatibility.md`

**File**:
`plugins/abstract/docs/claude-code-compatibility.md:9`,
`:12`, `:69`, `:122-124`
**Layer**: 0 (referenced paths do not exist)
**Confidence**: HIGH
**Evidence**: Six references to
`compatibility/compatibility-reference.md` and
`compatibility/compatibility-issues.md`. Only these files
exist in that directory:
`compatibility-features-march2026-early.md`,
`compatibility-features-march2026-recent.md`,
`compatibility-features-plugin-compat.md`,
`compatibility-features.md`, `compatibility-patterns.md`.
The two referenced files were never created.
**Remediation**: Create the two missing stub files or
replace the six links with references to the existing
`compatibility-features.md` and
`compatibility-patterns.md`.

---

### F-05 — Broken cross-references: `docs/examples/skill-development/authoring-best-practices.md`

**File**:
`docs/examples/skill-development/authoring-best-practices.md:108-109`
**Layer**: 0 (referenced paths do not exist)
**Confidence**: HIGH
**Evidence**:

- `[FORMS.md]` →
  `docs/examples/skill-development/FORMS.md` (missing)
- `[REFERENCE.md]` →
  `docs/examples/skill-development/REFERENCE.md` (missing)

**Remediation**: Create the two missing files or remove
the links.

---

## Layer 1: Document-Level Slop

### F-06 — Em-dash density: `plugins/scribe/commands/session-to-post.md`

**File**: `plugins/scribe/commands/session-to-post.md:68-72`
**Layer**: 1
**Confidence**: HIGH
**Evidence**: 5 em-dashes in 264 words = 18.9 per 1,000
(rule target: 0-2). All five appear in a single bullet
list using the `item — description` pattern (lines
68-72). The file is a user-facing command reference.
**Remediation**: Replace em-dashes in bullet definitions
with colons. For example:
`- \`Skill(scribe:session-to-post)\`: full skill
reference`.

---

### F-07 — Em-dash density: `plugins/scribe/skills/session-to-post/modules/session-extraction.md`

**File**: lines 76-100
**Layer**: 1
**Confidence**: HIGH
**Evidence**: 7 em-dashes in 384 words = 18.2 per 1,000.
Pattern: `- **Term** — definition` and
`1. [hash] [message] — [significance]`. Five in the
extraction checklist, two in the git log example.
**Remediation**: Convert `— ` to `: ` in definition
bullets. Delete the em-dash from the git log example
format line or use a comma.

---

### F-08 — Em-dash density: `plugins/imbue/skills/proof-of-work/modules/todowrite-patterns.md`

**File**: lines 53, 61, 62
**Layer**: 1
**Confidence**: HIGH
**Evidence**: 3 em-dashes in 221 words = 13.6 per 1,000.
Line 53: `TaskUpdate now supports deleting tasks... — only
delete transient tracking items`. Lines 61-62: two
definition bullets.
**Remediation**: Line 53: replace em-dash with a period
or semicolon. Lines 61-62: replace `—` with `:`.

---

### F-09 — Em-dash density: `docs/inclusive-defaults.md`

**File**: lines 55-217
**Layer**: 1
**Confidence**: HIGH
**Evidence**: 13 em-dashes in 998 words = 13.0 per 1,000.
All 13 are in bullet definition lists, spread across the
entire document.
**Remediation**: Systematic pass replacing `item —
description` with `item: description` throughout. This
file was not in the Phase 4 em-dash pass (b6dc115f).

---

### F-10 — Em-dash density: `plugins/attune/commands/mission.md`

**File**: lines 8, 51-56, 127, 178
**Layer**: 1
**Confidence**: HIGH
**Evidence**: 10 em-dashes in 886 words = 11.3 per 1,000.
Line 8 is a prose sentence:
`Orchestrate the entire attune development lifecycle —
brainstorm, specify, plan, execute — as a single
mission`. Lines 51-56 are numbered list items; lines 127
and 178 are prose sentences.
**Remediation**: Lines 8, 127, 178 (prose): replace
em-dashes with commas, colons, or parentheses. Lines
51-56 (list definitions): replace `—` with `:`.

---

## Layer 2: Sentence-Level Slop

### F-11 — Banned vocab: `.claude/agents/code-review-mode.md`

**File**: `.claude/agents/code-review-mode.md:4`, `:17`,
`:23`
**Layer**: 2
**Confidence**: HIGH
**Evidence**:

- L4: `comprehensive code review sessions` (description
  field)
- L17: `You are in comprehensive code review mode`
- L23: `Actionable Findings: Each issue includes specific
  remediation steps`

These are in the agent's system-prompt text, not in
anti-example or teaching blocks.
**Remediation**: L4: `detailed code review sessions`. L17:
`You are in evidence-based code review mode`. L23:
`Specific Findings: Each issue includes a remediation
step`.

---

### F-12 — Banned vocab: `plugins/attune/tests/TESTING.md`

**File**: `plugins/attune/tests/TESTING.md:5`, `:87`,
`:185`
**Layer**: 2
**Confidence**: MEDIUM
**Evidence**: Three uses of `Comprehensive` as a
paragraph-opening adjective: `Comprehensive test
coverage...`, `Comprehensive fixtures...`,
`Comprehensive edge case coverage`. Characteristic
AI-generated test documentation opening.
**Remediation**: L5: `Test coverage for the attune
plugin...`. L87: `Fixtures in \`conftest.py\`:`. L185:
`Edge case coverage:`.

---

### F-13 — Banned vocab: `plugins/memory-palace/skills/knowledge-intake/SKILL.md`

**File**: `plugins/memory-palace/skills/knowledge-intake/SKILL.md:75`
**Layer**: 2
**Confidence**: MEDIUM
**Evidence**: `Systematically process external resources
into actionable knowledge.` The word `actionable` here is
the slop usage (modifying abstract noun), not the domain
usage of "actionable item" (a task). The 10 other hits in
this file are `structured concurrency` (technical term)
or in the prohibited-word list (self-documenting).
**Remediation**: Replace `actionable knowledge` with
`usable knowledge` or drop the adjective:
`Systematically process external resources into the
knowledge store.`

---

## Layer 3: AI-Generation Signals

### F-14 — Refactoring deficit: 7.5% ratio below 10% target

**Metric**: 69 refactoring commits out of 919 total =
7.5% (target: >10%)
**Layer**: 3
**Confidence**: MEDIUM
**Evidence**:
`git log --oneline | grep -ci refactor` = 69;
`git rev-list --count HEAD` = 919.
The prior audit set a 5% floor; this codebase is above
that floor but below the 10% health target.
**Remediation**: Budget one refactoring pass per four
feature commits. Add `refactor(...)` prefix discipline to
cleanup work already being done (several Phase 1-5
commits are structural refactors committed as `chore`).

---

### F-15 — Massive commits without decomposition

**Layer**: 3
**Confidence**: MEDIUM
**Evidence**: Eight commits in recent history with
>1,000 insertions and no body (single-line message only):

| Hash | Insertions | Message |
|------|-----------|---------|
| `b6e87193` | 3,185 | feat(scribe): integrate 2025-26 AI slop playbook |
| `bdf77595` | 2,671 | chore(1.9.4): add karpathy-principles skill |
| `e2a4ba4e` | 2,240 | feat(pensive): add /performance-review skill |
| `b71bd49d` | 1,989 | feat: skill-graph-audit and skill metadata refresh |
| `0567817f` | 1,752 | feat: extend AI slop playbook across plugins |
| `e279b155` | 1,654 | chore(unbloat): Phase 1 quick wins |
| `2109b63a` | 1,278 | fix(pr-446): resolve 42 review threads |
| `d1e42ddf` | 1,076 | refactor(unbloat): Phase 5 R2/R4/R6 |

**Remediation**: Future feature additions of this scale
should be staged in 200-500 line commits. The existing
commits are closed; flag for the next major feature
cycle.

---

### F-16 — R7 docstring restate: VERIFIED CLEAN

**Layer**: 3
**Confidence**: HIGH (PASS)
**Evidence**: `git ls-files "*.py" | xargs python3
scripts/check_docstring_quality.py` exits 0 with empty
stdout. The 91 deferred hits from commit `b8c45ab0` are
confirmed cleared. No new hits introduced.
**Remediation**: None. Record as closed.

---

## Layer 4: Documentation Drift

### F-17 — Orphan docs: four `docs/` files with zero inbound references

**Layer**: 4
**Confidence**: MEDIUM
**Evidence**: Checked first 30 `docs/` files; four have
zero references from any other tracked `.md` file:

- `docs/guides/rules-templates.md` (0 refs)
- `docs/module-loading-guide.md` (0 refs)
- `docs/metrics/autonomy-dashboard.md` (0 refs)
- `docs/claude-rules-templates.md` (0 refs)

None appear in `book/src/SUMMARY.md` (64-line TOC).
**Remediation**: Verify intent. If superseded, delete or
archive. If still current, add a reference from
`docs/guides/README.md` or the book SUMMARY.

---

### F-18 — Stale version pin: `bandit 1.8.0` in precommit examples

(Duplicate of F-01 for Layer 4 tracking. See F-01.)

---

## Summary

| Finding | File | Layer | Confidence | Status |
|---------|------|-------|-----------|--------|
| F-01 | precommit-setup standard-hooks.md + ci-integration.md | 0 | HIGH | NEW |
| F-02 | docs/guides/documentation-standards.md | 0 | HIGH | NEW |
| F-03 | docs/optimization-patterns.md | 0 | HIGH | NEW |
| F-04 | plugins/abstract/docs/claude-code-compatibility.md | 0 | HIGH | NEW |
| F-05 | authoring-best-practices.md | 0 | HIGH | NEW |
| F-06 | scribe/commands/session-to-post.md | 1 | HIGH | NEW |
| F-07 | session-to-post/modules/session-extraction.md | 1 | HIGH | NEW |
| F-08 | proof-of-work/modules/todowrite-patterns.md | 1 | HIGH | NEW |
| F-09 | docs/inclusive-defaults.md | 1 | HIGH | NEW |
| F-10 | attune/commands/mission.md | 1 | HIGH | NEW |
| F-11 | .claude/agents/code-review-mode.md | 2 | HIGH | NEW |
| F-12 | attune/tests/TESTING.md | 2 | MEDIUM | NEW |
| F-13 | memory-palace/skills/knowledge-intake/SKILL.md | 2 | MEDIUM | NEW |
| F-14 | Git refactor ratio 7.5% | 3 | MEDIUM | NEW |
| F-15 | 8 massive commits >1k insertions | 3 | MEDIUM | NEW |
| F-16 | R7 docstring restate check | 3 | HIGH | PASS |
| F-17 | 4 orphan docs/ files | 4 | MEDIUM | NEW |

**P0 count (Layer 0)**: 5 findings (F-01 through F-05),
all broken cross-references or stale commands.
**No identity leaks found**: The four files that matched
the identity-leak scan are all quoting or documenting the
pattern, not exhibiting it.
**No bare TODOs in production SKILL.md or command files**
found.
**Tier 1 banned vocab**: The highest-frequency genuine
instances are in `.claude/agents/code-review-mode.md`
(system-prompt text) and `attune/tests/TESTING.md` (test
overview header). Most other hits in the 449-match pool
are in anti-example blocks, skill name usage, or
technical terms (`structured concurrency`).
