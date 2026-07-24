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
2a. Scan for double-dash em-dash substitution:
   `grep -n ' -- ' file.md` — any prose match (outside
   code blocks and `| -- |` table cells) is slop.
   Replace with a real em-dash `—`, a colon, or rewrite
   the sentence. `--` is a shell end-of-options separator;
   it is not punctuation.
2b. Scan for prose semicolon splices (outside fenced AND inline
   code): `awk '/^```/{c=!c}!c' file.md | sed -E 's/`[^`]*`//g'
   | grep -oP '\w;\s+\w'`. The `sed` pass matters here more than
   for arrows or plus signs because semicolons are common inside
   backticked code (`arr.push();`). A semicolon joining two
   independent clauses reads more naturally as two sentences or
   one coordinating conjunction.
   Rephrase unless the semicolon is absolutely necessary: a
   list whose items carry internal commas is the one durable
   keep. Confidence is low, so surface each hit for a human to
   judge rather than auto-rewriting.
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
8. Normalize British spellings to American (default).
   Use `scribe.spelling.to_american` (preserves case; skips
   code, inline code, and URLs) or scan manually:
   `rg -ni '\b(colou?r|behaviou?r|organis|optimis|centre|\
   licence|defence|catalogue|grey|artefact)\w*' file.md`.
   Use an explicit word list, never a `-ise`/`-our` suffix
   rule (surprise, exercise, analysis are correct as-is).
   Opt out per project via `.slop-config.yaml`
   (`spelling: british`) or per word via the allowlist;
   leave proper nouns ("Labour Party") and quoted text
   alone. Detail: `Skill(scribe:slop-detector)` module
   `spelling-normalization.md`.
9. Run full `Skill(scribe:slop-detector)` if file > 100
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
  parentheses. In prevention mode (docs you just generated),
  the target is zero em-dashes
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
  rewrite the sentence (fine in code, math, version strings,
  and diagram labels)
- Replace a prose semicolon splice with a period (two
  sentences) or a coordinating conjunction ("and", "but",
  "so"). Keep the semicolon only when removing it creates
  ambiguity, such as a list whose items carry internal commas
- Strip "Let's", "We'll", "In this guide" framings. Start
  the sentence at the substantive content
- Replace hedging seesaw with a position
- Replace "not only X, but also Y" with the simpler form
- Replace British spellings with American by default
  (colour to color, organise to organize, centre to
  center, licence to license, catalogue to catalog). In
  prevention mode the target is zero British spellings.
  Keep British only when the document opts out or the term
  is a proper noun or direct quote

### Tier 5 / 2026 patterns (cross-source consensus)

These crystallized in early 2026 from Wikipedia *Signs of AI
writing*, Algorithmic Bridge *10 Signs*, Ignorance.ai *Field
Guide to AI Slop*, the Stop-Slop Claude skill, George Kao,
ContentBeta, and OliviaCal. Apply at the same priority as the
list above.

- **Spatial copula / animated inanimates**: replace
  "lives in", "lives at", "sits at", "sits between", "stands
  as", "rests on", "rooted in", "nestled in", "serves as",
  "boasts", "marks" (a turning point), "represents" (a shift)
  with plain "is", "has", "uses", or delete. Heuristic: if
  the subject cannot literally do the verb, the verb is slop.
  The bare and plural forms are already matched: the regex uses
  `lives?`, `sits?`, `stands?`, `rests?`, `dwells?`, so "the
  configs live in the repo root" and "adapters sit between the
  layers" fire the same as the inflected forms. No separate
  pattern is needed for them.
- **Anthropomorphism (non-human subjects)**: the spatial copula
  bullet covers putting a body somewhere. This covers giving code,
  systems, and documents mental states, volition, or bodies.
  Rewrite "the scheduler wants to", "the parser understands",
  "this module knows about", "the cache decides", "the type system
  tries to", "the compiler cares about", "the client refuses",
  "the handler reaches into", "the gateway speaks to" by naming
  the mechanism instead of the intent: "the scheduler runs these
  in order", "the parser accepts nested blocks". Medium
  confidence, surface rather than auto-rewrite: "is the seam" /
  "is the boundary" / "is the glue" (name what it does), "drives"
  with a non-human subject (use "controls", "sets", "determines"),
  "rides on top of" (use "runs on", "wraps"), and "a real fix" /
  "real work" (cut the modifier or give the number). Keep terms of
  art (observer, listener, supervisor, daemon, orphan, zombie,
  heartbeat, replica), human subjects, and API signatures
  (`Iterator::next`, `handler.handle`) untouched. The generalized
  agency verbs "handles", "manages", "owns", "talks to", "sees"
  are load-bearing in systems prose and are gated off by default.
  Detail: `Skill(scribe:slop-detector)` module
  `vocabulary-patterns.md`.
- **Negative parallelism (contrastive negation)**: rewrite
  "It's not X, it's Y", "It's X, not Y" (copula-led trailing,
  e.g. "It's a tool, not a toy"), "Y, not X" (bare trailing),
  "Not just X, but Y", "Not only X, but also Y", "No X. No Y.
  Just Z.", "No X, no Y, no Z", "Not because X. Because Y.",
  "And that's okay." Positively state Y; drop the X half. The
  copula-led trailing form is the one that survives casual
  proofreading because the opener reads as a plain definition.
- **Contrastive parallelism (affirmative antithesis)**: the
  same scaffold without a "not" anchor. Rewrite "Less X,
  more Y", "Where others X, we Y", subject-swap clauses
  ("Humans propose; machines dispose"), "Old way: X. New
  way: Y.", and chiasmus. Avoid both contrastive forms in
  all but the most necessary cases: keep one only when the
  contrast is load-bearing and survives removal. Subject-swap
  and chiasmus are judgment-level; surface, do not
  auto-rewrite. Leave `Before:`/`After:` code-example labels
  alone.
- **Throat-clearing openers**: delete "Here's the thing,",
  "Look,", "So," (non-contrastive), "The thing is,", "Let
  that sink in.", "The uncomfortable truth is", "Let me
  explain.", "Bear with me.", "Let's dive in", "Picture
  this:", "Imagine a world where", "In this article, we
  will", "This article aims to", "Here's what nobody tells
  you". Start at the substantive content.
- **Three-fragment burst**: collapse "Focused. Aligned.
  Measurable." → "Focused, aligned, and measurable." Or
  rewrite as a complete sentence with content.
- **Significance cluster**: cut "stands as a testament to",
  "marks a turning point", "indelible mark", "deeply rooted",
  "setting the stage for", "shaping the future of",
  "underscores the importance", "plays a pivotal role". The
  surrounding facts carry significance better.
- **Smart quotes outside code blocks**: replace `"`/`"`
  with `"` and `'`/`'` with `'` in technical prose.
- **Semicolon splice**: a semicolon joining two independent
  clauses ("The system is fast; it scales") is a sophistication
  marker. Split into two sentences or join with "and"/"but"/
  "so". Keep the semicolon only when a list's items carry
  internal commas. Low confidence: surface, do not auto-rewrite.
- **Loop/cascade vocabulary**: replace "unpack" (verb,
  metaphor) with "explain"; "surface" (verb, metaphor) with
  "raise" or "report"; "a quiet shift" with the named shift;
  "the signal here is" with "the point is".
- **Performative honesty**: rewrite "to be honest,", "in all
  honesty,", "Honestly,", "full disclosure,", "Let me be
  clear", "Real talk:", and "Honest X" headline framings
  ("An Honest Review", "The Honest Truth About", "My Honest
  Results"). Manufactured authenticity. Scoped to framing
  nouns so "an honest mistake" passes. High confidence.
- **Sophistication marker ("prior art")**: rewrite "survey
  the prior art", "benefit from prior art", "prior art in
  this space", "standing on the shoulders of", "a body of
  work", "building on prior work", "state of the art" when
  used to sound rigorous in non-academic prose. Bare "prior
  art" in a patent or academic context is NOT slop. The
  collocation is. High confidence. Disable the category in
  IP-adjacent repos.
- **Participial tail**: rewrite comma-led fake-analysis
  tack-ons: ", highlighting", ", showcasing", ",
  underscoring", ", paving the way for", ", demonstrating",
  ", proving that". State the consequence in a new sentence
  instead.
- **Emphasis crutch**: delete "Full stop.", "Make no
  mistake", "Read that again.", "Mark my words". These stamp
  authority or drama without adding information.

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
- Do not auto-apply `confidence: low` findings; surface
  them for human decision

## Why three layers

Sentence cleanliness is necessary, not sufficient. A
clean-sentence document with an identity leak still ships
AI-generated text that escaped review. A clean-sentence
document referencing a function that does not exist still
documents the wrong world. A clean-sentence document with
no thesis still wastes reader time. Run all three layers.
Fail any, fix and rerun.
