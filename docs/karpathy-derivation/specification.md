# Specification: imbue:karpathy-principles

**Status**: Draft (Phase 2 of /attune:mission)
**Source**: docs/karpathy-derivation/project-brief.md
**Adjacent prior art surveyed**: 9 repos via tome:code-search

## 1. Functional Requirements

### FR-1: Skill Installation

A new skill MUST exist at:

```
plugins/imbue/skills/karpathy-principles/SKILL.md
```

with valid Claude Code skill frontmatter that passes
`abstract:skills-eval`.

**Frontmatter fields (required)**:

- `name: karpathy-principles`
- `description`: one sentence, mentioning all 4 principles
  and trigger conditions; under 200 chars per skill
  conventions.
- `version: 1.9.4` (or current minor)
- `alwaysApply: false`
- `category: discipline`
- `tags`: include `karpathy`, `coding-pitfalls`,
  `synthesis`, `entry-point`
- `dependencies`: list other imbue/leyline/conserve skills
  cross-referenced
- `complexity: foundational`
- `model_hint: standard`
- `estimated_tokens`: <=1000 for SKILL.md alone

### FR-2: Four Principles Reference Card

The SKILL.md body MUST include a one-line summary of each
of the four Karpathy principles, in the order:

1. Think Before Coding
2. Simplicity First
3. Surgical Changes
4. Goal-Driven Execution

Each principle MUST include:

- A bold one-liner restating the rule
- 2-4 bullet sub-rules
- A pointer to the deep-dive skill in night-market
  (cross-reference, not duplication)

### FR-3: Anti-Patterns Module

A module MUST exist at:

```
plugins/imbue/skills/karpathy-principles/modules/anti-patterns.md
```

containing at least 6 anti-pattern cases adapted from the
upstream EXAMPLES.md, **rewritten in our own prose** (not
verbatim copy). Each case MUST include:

- A name (e.g. "Drive-by Refactoring")
- A trigger pattern (when LLMs fall into it)
- A canonical bad example (short, ~10 lines)
- A canonical good example (short, ~5 lines)
- A test heuristic (one sentence the reader can apply)

Required cases:

| Case | Anti-pattern | Maps to Principle |
|------|--------------|-------------------|
| AP-1 | Hidden Assumptions | Think Before Coding |
| AP-2 | Multiple Interpretations Picked Silently | Think Before Coding |
| AP-3 | Strategy Pattern for One Function | Simplicity First |
| AP-4 | Speculative Features | Simplicity First |
| AP-5 | Drive-by Refactoring | Surgical Changes |
| AP-6 | Style Drift During Edit | Surgical Changes |
| AP-7 | Vague Success Criteria | Goal-Driven Execution |
| AP-8 | Multi-Step Plan Without Verification Gates | Goal-Driven Execution |

### FR-4: Senior Engineer Test Module

A module MUST exist at:

```
plugins/imbue/skills/karpathy-principles/modules/senior-engineer-test.md
```

It MUST formalize the upstream "Would a senior engineer say
this is overcomplicated?" self-check as a structured
heuristic with:

- The question itself, prominently
- A 3-question battery:
  1. Could this be 50% shorter?
  2. Are abstractions earning their weight?
  3. Could a junior dev follow this in 6 months?
- A "what to do if any answer is no" decision tree

### FR-5: Verifiable Goals Module

A module MUST exist at:

```
plugins/imbue/skills/karpathy-principles/modules/verifiable-goals.md
```

with:

- A reformulation template: vague request → verifiable goal
- At least 5 worked examples (vague → verifiable):
  - "Add validation" → "Tests for invalid inputs pass"
  - "Fix the bug" → "Test reproducing bug, then make it pass"
  - "Refactor X" → "Tests pass before and after"
  - "Make it faster" → "Benchmark Y < N ms"
  - "Improve UX" → "User can complete flow Z in under M clicks"
- Cross-reference to `imbue:proof-of-work` and
  `superpowers:test-driven-development`

### FR-6: Tradeoff Acknowledgment Module

A module MUST exist at:

```
plugins/imbue/skills/karpathy-principles/modules/tradeoff-acknowledgment.md
```

It MUST honestly state when **NOT** to apply these
principles:

- Trivial typos and one-line fixes (skip "ask first")
- Exploratory spikes / throwaway scripts (skip simplicity
  rigor)
- Documentation-only changes (style drift may be desired)
- Context-defined emergencies (production fire, no time for
  TDD)

This module MUST NOT undermine the principles; it MUST
articulate the boundary.

### FR-7: Source Attribution Reference

A reference MUST exist at:

```
plugins/imbue/skills/karpathy-principles/references/source-attribution.md
```

containing:

- Primary citation: `https://x.com/karpathy/status/2015883857489522876`
- Derived-work citation:
  `https://github.com/forrestchang/andrej-karpathy-skills`
  with MIT license note
- Adjacent prior-art bibliography (9 repos surveyed via
  tome research)
- Statement that no prose is copied verbatim; principles
  and naming conventions are facts, not protected
  expression.

### FR-8: Cross-References in Existing Skills

The following existing skills MUST add a "See Also: imbue:karpathy-principles"
line in their introduction or related-skills section:

| Skill | Section to update |
|-------|-------------------|
| `imbue:scope-guard/SKILL.md` | Related skills |
| `imbue:proof-of-work/SKILL.md` | Related skills |
| `imbue:rigorous-reasoning/SKILL.md` | Related skills |
| `leyline:additive-bias-defense/SKILL.md` | Related contracts |
| `conserve:code-quality-principles/SKILL.md` | Related skills |

Edits MUST be surgical (1-3 lines added per file). No
restructuring.

### FR-9: Plugin Manifest Update

`plugins/imbue/.claude-plugin/plugin.json` (or equivalent
imbue plugin manifest) MUST register the new skill so it
appears in `/list-skills` output.

## 2. Adjacent-Pattern Absorption (from tome research)

These patterns from non-upstream sources will be absorbed
where they strengthen the derivation. Each is gated by
whether it adds clear pedagogical value WITHOUT creating
duplication with existing night-market skills.

### Absorbed: Calibration Rule

**Source**: `yzhao062/agent-style` RULE-08/RULE-H.

**Integration**: Add a 5th sub-rule under "Think Before
Coding" titled **"Match Tone to Evidence"**: claims must be
no stronger than the evidence supports. This complements
existing `imbue:proof-of-work` (which demands evidence) by
addressing the inverse failure: claiming with evidence-free
confidence.

### Absorbed: Drift-Rail Framing

**Source**: `shamanakin/VIBERAIL`.

**Integration**: Each anti-pattern in `anti-patterns.md`
will be framed as a **named drift rail** (e.g., "Drive-by
Refactoring Rail") rather than a generic anti-pattern.
Naming aids recall.

### Deferred: Append-Only Project Learnings

**Source**: `TheRealSeanDonahoe/agents-md` Section 11.

**Decision**: Deferred to follow-up issue. The pattern is
strong but creating an agent-writable learnings file
intersects with `abstract:friction-detector` and
`memory-palace` skills. Wiring this requires an ADR-level
decision about who owns the learnings store. File a GitHub
issue tracking it post-mission.

### Deferred: PromptSentinel / Vague-Verb Auditor

**Source**: `bmad-code-org/BMAD-METHOD`.

**Decision**: Deferred. Auditing user prompts is a hook
concern, not a skill concern. File a GitHub issue for a
hookify rule that flags scope-creep verbs.

### Not Absorbed: Read-Only Pinned Context

**Source**: `Aider-AI/conventions`.

**Decision**: Aider-specific mechanism; not portable to
Claude Code skills. No action.

### Not Absorbed: Hierarchical Nearest-Wins Overrides

**Source**: `agentsmd/agents.md` spec.

**Decision**: Out of scope; would require harness-level
plumbing. No action.

## 3. Optional: /imbue:karpathy-check Command

A lightweight slash command that surfaces the 4 principles
as a pre-flight checklist before implementation. Backed by
the new skill.

**Trigger**: `/imbue:karpathy-check` or `/imbue:karpathy-check <task description>`

**Behavior**:

- Loads `imbue:karpathy-principles` skill
- Asks the 4 questions (one per principle) inline
- Outputs a brief gate verdict (PASS / NEEDS CLARIFICATION
  / REWORK)

**Decision**: This is **optional** for the mission. If
adding it bloats the diff, defer to follow-up. If
straightforward (15 lines of frontmatter + body), include
it.

## 4. Quality Gates

| Gate | Tool | Passing Criterion |
|------|------|-------------------|
| Frontmatter validity | `abstract:plugin-validator` agent | All required fields present, kebab-case naming |
| Skill quality | `abstract:skills-eval` | Score >= 80 |
| Slop detection | `scribe:slop-detector` | 0-2 em-dashes per 1k words; no Tier 1 banned words |
| Markdown wrap | manual + `wc -L` | All prose lines ≤ 80 chars |
| Cross-reference integrity | grep + manual | All `imbue:karpathy-principles` references resolve |
| License attribution | manual | MIT attribution to forrestchang present in references |
| TDD compliance (Iron Law) | `imbue:proof-of-work` | At least one failing test before implementation (see plan) |

## 5. Acceptance Tests

| Test | How to verify |
|------|---------------|
| AT-1 | `Skill(imbue:karpathy-principles)` loads without error |
| AT-2 | Skill description appears in `/list-skills` output |
| AT-3 | All 4 modules render at < 500 tokens each (`wc -w`) |
| AT-4 | All 8 anti-patterns are present in `anti-patterns.md` |
| AT-5 | Source attribution names both Karpathy tweet and forrestchang repo |
| AT-6 | The 5 cross-referenced skills contain a `imbue:karpathy-principles` mention |
| AT-7 | Plugin manifest registers the new skill |
| AT-8 | No prose lines exceed 80 chars (`awk 'length > 80' **/*.md`) |
| AT-9 | Slop-detector reports clean on all new modules |
| AT-10 | A reader unfamiliar with the codebase can recall all 4 principles after reading SKILL.md alone |

## 6. Out of Scope (explicit)

- Forking forrestchang's plugin verbatim.
- Translating to non-English locales.
- Building hooks or agents.
- Building the `agents-md` Project Learnings store (deferred).
- Building a PromptSentinel hook (deferred).
- Modifying skills in plugins other than imbue/leyline/conserve.
