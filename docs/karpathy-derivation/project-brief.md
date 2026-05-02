# Project Brief: Karpathy Principles Derivation

**Mission**: Derive and implement detailed insights from
`forrestchang/andrej-karpathy-skills` into the
claude-night-market plugin ecosystem, citing primary
sources, integrating with existing skills, and adding the
unique value-add (compact synthesis + concrete anti-pattern
catalog).

## Source Material

| Artifact | Size | Role |
|----------|------|------|
| `CLAUDE.md` | 2344 chars | The 4-principle contract |
| `EXAMPLES.md` | 14789 chars | Concrete diff-level anti-patterns |
| `skills/karpathy-guidelines/SKILL.md` | 2570 chars | Same 4 principles, packaged as skill |
| Primary citation | n/a | `https://x.com/karpathy/status/2015883857489522876` |
| License | n/a | MIT — derivation permitted with attribution |

## The Four Principles (verbatim source framing)

1. **Think Before Coding** — State assumptions explicitly.
   If multiple interpretations exist, present them. If
   simpler exists, push back. If unclear, stop and ask.
2. **Simplicity First** — Minimum code that solves the
   problem. No speculative features. No abstractions for
   single-use code. No error handling for impossible
   scenarios.
3. **Surgical Changes** — Touch only what you must. Don't
   improve adjacent code. Match existing style. Every
   changed line traces to the user's request.
4. **Goal-Driven Execution** — Define verifiable success
   criteria. "Add validation" becomes "write tests for
   invalid inputs, then make them pass."

## Coverage Analysis vs Existing Skills

| Karpathy Principle | Existing Coverage | Strength | Gap |
|--------------------|-------------------|----------|-----|
| 1. Think Before Coding | `imbue:rigorous-reasoning`, `superpowers:brainstorming`, `spec-kit:speckit-clarify`, `conserve:decisive-action` | Distributed across 4 skills | No single concise "list assumptions before coding" rule |
| 2. Simplicity First | `imbue:scope-guard`, `conserve:code-quality-principles` (KISS/YAGNI), `leyline:additive-bias-defense`, `.claude/rules/bounded-discovery.md` | Strong | Missing the "Would a senior engineer say this is overcomplicated?" self-check framing |
| 3. Surgical Changes | `imbue:justify`, `leyline:additive-bias-defense`, `imbue:scope-guard` | Decent | "Drive-by refactoring" anti-pattern not named; "trace-back rule" not isolated |
| 4. Goal-Driven Execution | `imbue:proof-of-work` (Iron Law), `superpowers:test-driven-development` | Strong | "Transform vague requests into verifiable goals" reformulation template missing |

**Takeaway**: ~90% coverage exists. The unique value-add is
the compact synthesis + diff-level anti-pattern catalog +
honest tradeoff framing.

## Decision: What to Build

A new skill in the **imbue** plugin (which already houses
scope-guard, proof-of-work, justify, rigorous-reasoning):

```
plugins/imbue/skills/karpathy-principles/
├── SKILL.md                       (frontmatter + 4-principle reference card)
├── modules/
│   ├── anti-patterns.md           (6 diff-level cases adapted from EXAMPLES.md)
│   ├── senior-engineer-test.md    (the self-check meta-question)
│   ├── verifiable-goals.md        (template for goal reformulation)
│   └── tradeoff-acknowledgment.md (when NOT to apply these)
└── references/
    └── source-attribution.md      (Karpathy tweet + forrestchang derivation)
```

Plus:

- Cross-references added to `imbue:scope-guard`,
  `imbue:proof-of-work`, `leyline:additive-bias-defense`,
  `conserve:code-quality-principles` pointing at the new
  unified entry-point skill.
- An imbue command `/imbue:karpathy-check` (lightweight) that
  surfaces the 4 principles as a pre-flight gate before
  implementation tasks.

## Why Not Just Install the Upstream Plugin?

1. **Integration**: A standalone plugin would not
   cross-reference our existing scope-guard / proof-of-work
   skills, leaving users with redundant guidance.
2. **Anti-pattern catalog**: EXAMPLES.md is not packaged as
   a skill upstream; it sits as a flat doc. Repackaging the
   patterns as a structured module is value-add.
3. **Voice consistency**: night-market has its own writing
   conventions (markdown-formatting, slop-scan, prose
   wrapping). A derived skill conforms; an upstream plugin
   does not.
4. **Tradeoff framing**: The honest "for trivial tasks, use
   judgment" framing benefits from being a first-class
   module, not a one-line aside.

## Success Criteria

**Functional**:

- New skill `imbue:karpathy-principles` is loadable via Skill
  tool with valid frontmatter.
- All 4 modules render under skill token budget (target:
  total skill <2000 tokens; modules <500 each).
- Cross-references in 4 existing skills compile (no broken
  links via skills-eval).
- Source attribution module cites the Karpathy X/Twitter
  URL and the forrestchang/andrej-karpathy-skills repo (MIT
  license attribution).

**Quality**:

- Slop-detector passes on all new prose (em-dashes 0-2 per
  1k words, no Tier 1 banned words).
- Markdown wrapping at 80 chars per `.claude/rules/markdown-formatting.md`.
- skills-eval gives the new skill a passing score.
- At least 6 anti-pattern cases adapted from EXAMPLES.md,
  rewritten in our own prose (not lifted verbatim).

**Pedagogical**:

- A reader who only reads the new SKILL.md (not the modules)
  can recall all 4 principles and apply them to a coding
  task.
- A reader who reads the anti-patterns module can identify
  drive-by refactoring, style drift, premature abstraction,
  and vague success criteria in their own diffs.

## Out of Scope

- Forking forrestchang's plugin into night-market verbatim
  (we are deriving, not redistributing).
- Building agents or hooks (skill + optional command only).
- Translating to non-English locales (upstream has zh, we
  defer).
- Verbatim copying of EXAMPLES.md prose (paraphrase
  required).

## Risks

| Risk | Mitigation |
|------|------------|
| Duplication with existing skills creates noise | Cross-reference deeply; position new skill as compact entry-point, not replacement |
| Verbatim copying triggers attribution issues | Adapt and paraphrase; cite both Karpathy tweet and forrestchang repo |
| Skill bloat (token budget) | Hub-and-spoke: SKILL.md is index, modules carry detail |
| "Yet another scope-control skill" perception | Frame as synthesis layer; existing skills remain authoritative on their respective dimensions |

## References

- Source repo: <https://github.com/forrestchang/andrej-karpathy-skills>
- Karpathy tweet: <https://x.com/karpathy/status/2015883857489522876>
- License: MIT
- Existing overlap candidates audited (see coverage matrix above)
