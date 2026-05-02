**A document costs the sum of its readers' time. Earn that
cost or cut. And: do not ship hallucinations or identity
leaks under any circumstance.**

When creating or updating markdown documentation files
(tutorials, guides, READMEs, book content, SKILL.md files),
you MUST run three layers of checks before reporting
completion: P0 critical patterns, document-level economy,
and sentence-level slop. The first layer fails the doc
outright; the second is structural; the third is local.

## Layer 0: P0 critical patterns (always fail before merge)

Run before anything else. Each of these is categorical:
a single match must be resolved before merge.

1. **Identity leaks**: any "As a large language model",
   "as of my training cutoff", "I cannot provide" must be
   deleted. See `Skill(scribe:slop-detector)` module
   `identity-and-voice-leaks.md`.
2. **Hallucinations**: every backticked identifier, every
   cited file path, every recommended `pip install` /
   `cargo install` / `npm install`, every URL must
   resolve to a real thing. See module
   `hallucination-detection.md`.
3. **Bare stubs in production paths**: every `TODO`,
   `FIXME`, `XXX`, `HACK` must either link to a tracked
   issue or be deleted. See module `stub-and-deferral.md`.

## Layer 1: Document-level economy

Score the document on three checks (0-2 each). Below
5/6 is not ready to ship regardless of how clean the
sentences are.

1. **Thesis-first**: the lead states the single takeaway.
2. **Sentence weight**: every sentence carries, instances,
   bounds, or repeats the thesis. Throat-clears,
   restated headings, and "as mentioned above" are bloat.
3. **Repetition rule**: the thesis is echoed (intro,
   middle, close). Everything else that repeats is cut.

Estimate the **reader-time budget** before drafting:
audience size × read frequency × per-read time. Writing
time should match. Cheap to write, expensive to read is
the failure mode worth catching.

Full rubric, table, and worked example:
`Skill(scribe:slop-detector)` module `document-economy.md`.

## Layer 2: Sentence-level checks

After Layers 0 and 1 pass, you MUST run
`Skill(scribe:slop-detector)` on each modified file.

**Automatic checks after writing .md files:**

1. Verify prose lines wrap at 80 chars (see
   `.claude/rules/markdown-formatting.md`)
2. Count em dashes: `grep -o '—' file.md | wc -l`
   (target: 0-2 per 1000 words)
3. Scan for tier 1 slop: "structured", "comprehensive",
   "actionable", "seamless", "robust", "myriad",
   "empower", "navigate" (as metaphor)
4. Scan for self-narration of structure: "Let's dive
   into", "In this section, we will...", "We'll cover...",
   "By the end of this guide..."
5. Scan for hedging seesaw: "While X has its merits..."
6. Scan for parallel "not just" / "not only X, but also Y"
7. Check for participial tail-loading: sentences ending
   with ", [verb]-ing ..."
8. Run full `Skill(scribe:slop-detector)` if file > 100
   words

## Layer 3: Evidence-backed claims (READMEs and public docs)

For any quality claim ("production-ready", "fast",
"memory-safe", "scalable", "battle-tested", etc.), verify
the corresponding evidence exists in the same repository:

| Claim | Required evidence |
|-------|-------------------|
| "Production-ready" | CI workflow, release doc, version >= 1.0 |
| "Fast" | `benches/` with reproducible benchmark + numbers |
| "Memory-safe" | `#![forbid(unsafe_code)]` or audited `unsafe` |
| "Scalable" | load tests or capacity numbers |
| "Robust" | concrete error-handling guarantees + test coverage |

Full table and detection commands:
`Skill(scribe:slop-detector)` module `evidence-backed-claims.md`.

No evidence: delete the claim. The bar is evidence, not
modesty.

## Fix before committing

- Replace em dashes with colons, periods, commas, or
  parentheses
- Replace "structured" with nothing (usually filler) or a
  specific word
- Replace "actionable" with "specific" or "concrete"
- Replace "comprehensive" with "thorough" or "complete"
- Replace "navigate the X" (metaphor) with "use" or
  "follow" or delete
- Replace "empower users" with "let users" + verb
- Replace "myriad" with "many" + a count if you have one
- Break up participial phrases into separate sentences
- Replace ASCII arrows (`->`, `→`) used as prose
  connectors with "to", "into", or "produces" (arrows
  are fine in code and type signatures)
- Replace `+` used as a prose conjunction with "and" or
  rewrite the sentence (fine in code, math, and labels)
- Strip "Let's", "We'll", "In this guide" framings; start
  the sentence at the substantive content
- Replace hedging seesaw with a position
- Replace "not only X, but also Y" with the simpler form

## Anti-goals (do not over-correct)

Aggressive de-slopping has its own failure modes. Before
applying a fix, verify it does not violate the anti-goals
in `Skill(scribe:slop-detector)` module `anti-goals.md`:

- Do not strip safety comments on `unsafe` blocks or
  contract-bearing code
- Do not collapse public API error variants
- Do not "simplify" typed errors to boxed/dynamic errors
- Do not inline a function with a domain-specific name
  just because it is short
- Do not touch generated code, vendored code, or
  historical changelog entries
- Do not auto-apply `confidence: low` findings — surface
  them for human decision

## Why three layers

Sentence cleanliness is necessary, not sufficient. A
clean-sentence document with an identity leak still ships
AI-generated text that escaped review. A clean-sentence
document referencing a function that does not exist still
documents the wrong world. A clean-sentence document with
no thesis still wastes reader time. Run all three layers.
Fail any, fix and rerun.
