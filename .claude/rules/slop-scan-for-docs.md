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

Score the document on four checks (0-2 each). Below
7/8 is not ready to ship regardless of how clean the
sentences are.

1. **Thesis-first**: the lead states the single takeaway.
2. **Sentence weight**: every sentence carries, instances,
   bounds, or repeats the thesis. Throat-clears,
   restated headings, and "as mentioned above" are bloat.
3. **Repetition rule**: the thesis is echoed (intro,
   middle, close). Everything else that repeats is cut.
4. **Audience fit**: one reader tier is declared
   (`newcomer`, `practitioner`, `expert`, or a one-line
   `persona`), and every section serves it. When a
   document names no reader, ask for one. Do not infer
   it from the prose.

Check 4 has one move that gets skipped: **extract, do not
delete**. Content that only serves a higher tier goes to
`modules/<topic>.md` for a skill or
`docs/deep-dive/<topic>.md` for a repo doc, linked from
the parent's lead with one line naming who it is for.
Rationale a newcomer cannot use is rarely weak writing.
It is answering a question that reader has not asked yet.

Tier table, the Socratic set for eliciting a tier, and
the creative-writing carve-out (`voice-*`,
`session-to-post`, `fiction-patterns`, where the cut test
does not apply):
`Skill(scribe:slop-detector)` module
`audience-targeting.md`.

Estimate the **reader-time budget** before drafting:
audience size × read frequency × per-read time. Writing
time should match. Cheap to write, expensive to read is
the failure mode worth catching.

Full rubric, table, and worked example:
`Skill(scribe:slop-detector)` module `document-economy.md`.

Audience fit is judgment, not a string in the text, so no
regex can decide it and nothing is added to `en.yaml` for
it. The guard is the contract test
`plugins/scribe/tests/test_audience_targeting.py`.

## Layer 2: Sentence-level checks

After Layers 0 and 1 pass, you MUST run
`Skill(scribe:slop-detector)` on each modified file.

**One command locates every finding below:**

```bash
uv run --with pyyaml python scripts/slop_score.py --audit <files>
```

It takes files or directories, reports every category with a
file and a line, and exits 0. It carries what the merge gate
declines to score: the low-confidence categories
(`semicolon_splice`, the softer anthropomorphism verbs) and the
opt-in ones (`negative_definition`, `contrastive_scaffold`,
`over_explanation`), plus the per-document negation-density
reading. Those are surfaced for a person to judge and are
labeled `(low)` or `(medium)` in the output. Never auto-rewrite
one.

`scripts/slop_score.py --threshold 3.0 docs book/src` is the
same script in gate mode, which is what CI runs on those two
directories. `--ratchet REF` is the third mode: it fails a file only
when it scores over the threshold and higher than its version at
`REF`. The pre-commit hook runs it against `HEAD` on staged markdown,
and CI runs it against the merge base on the markdown a PR changed.
Documents that define patterns are skipped through `exclude_patterns`
in `.slop-config.yaml`. Auditing reports. Scoring and ratcheting
gate. Do not conflate them.

The list below says what each finding means and how to rewrite
it. Reach for a hand-written grep only when the script is
unavailable.

1. Verify prose lines wrap at 80 chars (see
   `.claude/rules/markdown-formatting.md`)
2. Em dashes: target 0-2 per 1000 words, zero in new prose.
2a. Double-dash em-dash substitution: any prose ` -- ` (outside
   code blocks and `| -- |` table cells) is slop. Replace with
   a colon or rewrite the sentence. `--` is a shell
   end-of-options separator and is not punctuation.
2b. Prose semicolon splices. A semicolon joining two
   independent clauses reads more naturally as two sentences or
   one coordinating conjunction. Rephrase rather than swapping
   in an em dash, which is usually what the semicolon replaced.
   A list whose items carry internal commas is the one durable
   keep. Confidence is low, so a person judges each hit.
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
   Use `scribe.spelling.to_american`, which preserves case and
   skips code, inline code, and URLs. Use an explicit word
   list, never a `-ise`/`-our` suffix rule (surprise,
   exercise, analysis are correct as-is).
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

**These are not repo-local rules.** Every category below is
implemented as a `tier5.*` section in
`plugins/scribe/data/languages/en.yaml`, which is the pattern
source `Skill(scribe:slop-detector)` loads at runtime. A
document scanned in any other codebase gets the same findings,
so remediation is portable rather than tied to this repository.
The list below is the human-readable rationale and the rewrite
guidance. The YAML is the enforcement. When adding a pattern
here, add it there too, with a test in
`plugins/scribe/tests/test_slop_patterns.py`, or it will only
ever apply to this repo.

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
- **Trailing contrastive negation**: the mid-sentence tail the
  `negative_parallelism` regex misses, because that one needs the
  sentence to end a word after "not". Four forms, high confidence:
  "X, not just Y" anywhere in the sentence, "isn't just X, but Y",
  "more than X, it's Y", and "not about X, it's about Y". Rewrite by
  stating the affirmed half and deleting the negated one. A negated
  half that carries a fact ("the probe does not run, because gemini
  authenticates by key") is deliberately unmatched.
- **Contrastive scaffold**: "does X rather than Y" and "does X
  instead of Y" as a definitional frame. Off by default and low
  confidence, and the reason is worth keeping: no source in the
  contrastive-negation literature names either connective, and this
  repository writes "rather than" 504 times and "instead of" 299,
  almost all correctly, these rule files included. Scoped to the
  verb-phrase form, so a noun comparison ("use rg rather than grep")
  stays untouched. Enable it for a documentation audit, surface every
  hit, never auto-rewrite.
- **Negative framing**: three shapes and a measure, all in
  `tier5`. **Litotes** (`not uncommon`, `not unlike`, `never fails
  to`, `not without merit`) says a positive thing through two
  negations; rewrite positively, high confidence. **Vacuous negation**
  (`cannot be overstated`, `not to be underestimated`, `it goes
  without saying`, `needless to say`, `no small feat`) claims weight
  and supplies none; delete it or state the consequence, high
  confidence. **Negative definition** (`doesn't handle X`, `does not
  support Y`, `is unable to`) describes behavior only as absence;
  rewrite to what the thing does. That third one is
  `default_enabled: false` and low confidence on purpose: precise
  negation is how contracts, invariants and trust boundaries are
  written, and these rule files are built out of "do not use for",
  "must not" and "never". Enable it for a documentation audit, surface
  every hit, and never auto-rewrite. Prohibitions and invariants are
  deliberately unmatched.

  For over-reliance rather than instances, `scribe.negation`
  `check_negation_density` reports the share of sentences carrying a
  negation marker against an advisory 35% bar, with an 8-sentence
  floor. It is a prompt to reread, never a merge gate.
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
- **Over-explained fixes**: narration wrapped around a change,
  in place of the change. "In order to", "this ensures that",
  "this means that", "the reason for this is", "which allows
  us to", "it is important to note that". State the defect and
  what changed, then stop. A changelog entry or commit body
  that explains its own reasoning at length costs the reader
  more than the change it describes. Off by default and low
  confidence: "in order to" is correct in a sentence that
  genuinely states a purpose, and the line between rationale
  and narration is a judgment. Enable it when auditing
  changelogs, commit bodies, and PR descriptions. The judgment
  half belongs to document economy's sentence-weight check.
  This is the lexical half.
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
