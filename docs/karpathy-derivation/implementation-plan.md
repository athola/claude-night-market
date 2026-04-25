# Implementation Plan: imbue:karpathy-principles

**Status**: Draft (Phase 3 of /attune:mission)
**Specification**: docs/karpathy-derivation/specification.md
**Mission state**: .attune/mission-state.json
**TDD posture**: Iron Law applies — write at least one
failing skill-load / structure test before implementation.

## Phase Overview

| Phase | Tasks | Verification | Risk |
|-------|-------|--------------|------|
| P0: Pre-flight | Verify imbue plugin manifest path; create skill scaffold dirs | `ls` confirms structure | LOW |
| P1: TDD red | Write skill-structure test that fails because skill does not exist yet | `pytest plugins/imbue/tests/` shows red | LOW |
| P2: Reference & attribution | Write `references/source-attribution.md` first (it grounds everything else) | Lint, slop-detector | LOW |
| P3: SKILL.md | 4-principle reference card; cross-references | Frontmatter validates; skill loads | MEDIUM |
| P4: Modules | Write all 4 modules in parallel (independent files) | Each <500 tokens; slop-clean | MEDIUM |
| P5: Cross-references | Update 5 existing skills (1-3 lines each) | grep confirms references resolve | LOW |
| P6: Plugin manifest | Register skill in imbue plugin.json | Plugin validator passes | LOW |
| P7: Verification | skills-eval, plugin-validator, slop-detector | All gates green | MEDIUM |
| P8: Optional command | `/imbue:karpathy-check` if budget remains | Command loads | LOW |

## Phase P0: Pre-flight

**T0.1**: Read `plugins/imbue/.claude-plugin/plugin.json` to
identify the schema and current skill registrations.

  - **Verify**: file exists, parseable as JSON.
  - **Output**: schema understood for P6.

**T0.2**: Confirm directory layout against an existing imbue
skill (e.g. `plugins/imbue/skills/scope-guard/`) for
structural mimicry.

  - **Verify**: existing skill matches the planned layout.
  - **Output**: confidence in target structure.

**T0.3**: Create directory scaffold:

```
plugins/imbue/skills/karpathy-principles/
├── modules/
└── references/
```

  - **Verify**: `ls -la` shows tree.

## Phase P1: TDD Red

**T1.1**: Locate `plugins/imbue/tests/` and the existing
test conventions.

**T1.2**: Write a failing test:

```python
# plugins/imbue/tests/test_karpathy_principles.py
import pathlib

SKILL_DIR = pathlib.Path("plugins/imbue/skills/karpathy-principles")

def test_skill_md_exists():
    assert (SKILL_DIR / "SKILL.md").exists()

def test_required_modules_present():
    required = [
        "modules/anti-patterns.md",
        "modules/senior-engineer-test.md",
        "modules/verifiable-goals.md",
        "modules/tradeoff-acknowledgment.md",
        "references/source-attribution.md",
    ]
    for path in required:
        assert (SKILL_DIR / path).exists(), f"missing {path}"

def test_skill_frontmatter_has_required_fields():
    text = (SKILL_DIR / "SKILL.md").read_text()
    for field in ("name:", "description:", "version:"):
        assert field in text

def test_eight_anti_patterns_present():
    text = (SKILL_DIR / "modules/anti-patterns.md").read_text()
    # Names from spec FR-3
    for case in ("Hidden Assumptions", "Multiple Interpretations",
                 "Strategy Pattern for One Function",
                 "Speculative Features", "Drive-by Refactoring",
                 "Style Drift", "Vague Success Criteria",
                 "Multi-Step Plan Without Verification"):
        assert case in text, f"missing case: {case}"

def test_attribution_cites_both_sources():
    text = (SKILL_DIR / "references/source-attribution.md").read_text()
    assert "karpathy/status/2015883857489522876" in text
    assert "forrestchang/andrej-karpathy-skills" in text
    assert "MIT" in text

def test_cross_references_added_to_existing_skills():
    targets = [
        "plugins/imbue/skills/scope-guard/SKILL.md",
        "plugins/imbue/skills/proof-of-work/SKILL.md",
        "plugins/imbue/skills/rigorous-reasoning/SKILL.md",
        "plugins/leyline/skills/additive-bias-defense/SKILL.md",
        "plugins/conserve/skills/code-quality-principles/SKILL.md",
    ]
    for target in targets:
        text = pathlib.Path(target).read_text()
        assert "karpathy-principles" in text, f"no xref in {target}"
```

  - **Verify (P1 exit)**: `pytest -k karpathy` shows ALL
    tests failing (red).
  - **Iron Law gate**: do NOT proceed to implementation
    until tests run red. If they pass without
    implementation, the test is wrong.

## Phase P2: Source Attribution Reference

**T2.1**: Write `references/source-attribution.md`. Content
includes:

- Primary citation: Karpathy X URL
- Verbatim Karpathy quote on hidden assumptions (1-3
  sentences, attributed)
- Forrest Chang derivation citation + MIT license note
- Attribution caveat: "derived from observations, not
  Karpathy-authored"
- Adjacent prior-art bibliography (9 repos surveyed)
- "No verbatim prose copied" statement

  - **Verify**: grep finds both URLs and "MIT"; slop
    detector clean.

## Phase P3: SKILL.md

**T3.1**: Write SKILL.md with:

- Frontmatter (per FR-1): name, description, version 1.9.4,
  alwaysApply false, category discipline, tags, dependencies
  pointing at imbue:scope-guard, imbue:proof-of-work,
  imbue:rigorous-reasoning, leyline:additive-bias-defense,
  conserve:code-quality-principles.
- Body opens with the verbatim Karpathy quote and
  attribution.
- 4 sections, one per principle, each with bold one-liner +
  3-4 sub-bullets + `→ Deep dive: <skill>` cross-reference.
- Closing "When NOT to apply" pointer to tradeoff module.

  - **Token target**: ≤1000 tokens.
  - **Verify**: frontmatter validates with plugin-validator;
    `wc -w SKILL.md` < 700 words.

## Phase P4: Modules (parallel-safe)

These four files have no inter-dependency and can be
written in any order or parallel.

### T4.1: `modules/anti-patterns.md`

Structure: 8 cases, each ~30 lines, before/after
mini-diffs adapted (not copied) from upstream EXAMPLES.md.
Cases per FR-3 table.

  - **Token target**: ≤500.
  - **Verify**: all 8 case names present (T1.2 test
    catches this); slop-clean.

### T4.2: `modules/senior-engineer-test.md`

3-question battery + decision tree per FR-4.

  - **Token target**: ≤300.

### T4.3: `modules/verifiable-goals.md`

5+ vague→verifiable examples per FR-5.

  - **Token target**: ≤400.

### T4.4: `modules/tradeoff-acknowledgment.md`

Honest "when not to apply" per FR-6, with at least 2
contrarian voices cited (Willison + Mastering Product HQ
or HN commenter).

  - **Token target**: ≤350.

## Phase P5: Cross-References in Existing Skills

For each of the 5 existing skills (FR-8), add a single line
under the existing "Related skills" or near the end of
SKILL.md:

```
- `Skill(imbue:karpathy-principles)` - Compact synthesis of
  the 4 LLM-coding-pitfall principles
```

**Constraint**: Surgical edit. If the skill has no Related
section, add it as the smallest possible addition. Do NOT
restructure surrounding content.

  - **Verify (T1.2 test)**: all 5 grep positive.

## Phase P6: Plugin Manifest Registration

Update `plugins/imbue/.claude-plugin/plugin.json`:

- Add `karpathy-principles` to the `skills` array (or
  whatever schema imbue uses).
- Bump version if convention requires.

  - **Verify**: `abstract:plugin-validator` agent passes.

## Phase P7: Verification

**T7.1**: Run `pytest -k karpathy` — should now be GREEN.

**T7.2**: Run `Skill(abstract:skills-eval)` against the new
skill. Capture score and any findings; address blockers.

**T7.3**: Run `Skill(scribe:slop-detector)` against:

- `SKILL.md`
- All 4 modules
- The reference

Address any em-dash overuse, banned vocabulary, or
participial tail-loading.

**T7.4**: Manual line-length check:

```bash
awk 'length > 80 { print FILENAME":"NR": "length" chars" }' \
  plugins/imbue/skills/karpathy-principles/**/*.md
```

Address violations.

**T7.5**: Verify `Skill(imbue:karpathy-principles)` loads
in this session.

  - **Evidence capture**:
    - `[E1]` pytest output (all green)
    - `[E2]` skills-eval score
    - `[E3]` slop-detector report summary
    - `[E4]` line-length scan output

## Phase P8: Optional `/imbue:karpathy-check` Command

If P7 finishes with budget remaining:

- Create `plugins/imbue/commands/karpathy-check.md` with
  frontmatter + 15 lines of body.
- Body: invoke skill, render the 4 questions, ask user to
  confirm before proceeding.
- Verify: command loads; slash-command discoverable.

If budget is tight: defer to follow-up issue.

## Phase P9: Mission Closure

**T9.1**: Update `.attune/mission-state.json`:

- `current_phase: "complete"`
- `completed_phases: ["brainstorm", "specify", "plan", "execute"]`
- `final_artifacts`: list paths.

**T9.2**: Generate two GitHub issues for deferred items per
spec section 2:

1. "Append-only Project Learnings store (from agents-md
   pattern survey)"
2. "Hookify rule: PromptSentinel for scope-creep verbs
   (from BMAD pattern survey)"

These capture out-of-scope value for follow-up.

**T9.3**: Optional post-mission protocol per project
governance:

- `/sanctum:update-docs` (review whether docs need bumping)
- `/sanctum:update-tests` (test coverage check)

These are flagged but not blocking.

## Risk & Rollback

| Risk | Likelihood | Mitigation | Rollback |
|------|-----------|------------|----------|
| Frontmatter schema mismatch | LOW | Mimic existing imbue skill | git checkout |
| skills-eval gives low score | MEDIUM | Address findings; iterate before merge | edit in place |
| Cross-references break existing tests | LOW | Surgical edits only; run plugin tests | git checkout 5 files |
| Plugin manifest format differs from expectation | LOW | Read manifest first (P0.1) | git checkout |
| Scope creep into modifying scope-guard / proof-of-work content | MEDIUM | Discipline: one-line additions only | git checkout 5 files |

## Budget

- New files: 6 (1 SKILL.md, 4 modules, 1 reference) +
  optional 1 command = 6-7 files.
- Modified files: 5 cross-references + 1 manifest + 1
  test file = 7 files.
- Total file impact: 13-14 files.
- Lines of new content: ~600-800 lines.
- This is meaningful but bounded. User explicitly waived
  scope-guard for this mission.

## Out-of-Scope Reminders

- No verbatim copying of EXAMPLES.md prose.
- No new agents, no new hooks (deferred to follow-up).
- No edits to skills outside imbue/leyline/conserve.
- No README/docs at the top of the repo (skill docs only).

## Phase Sequencing & Dependencies

```
P0 → P1 (red) → P2 → P3 → P4 (parallel) → P5 → P6 → P7 (green) → P8 (opt) → P9
```

P4 sub-tasks T4.1-T4.4 are parallel-safe.
P5 sub-tasks (5 file edits) are parallel-safe.
P7 sub-tasks (skills-eval, slop-detector, line-length) are
parallel-safe.
