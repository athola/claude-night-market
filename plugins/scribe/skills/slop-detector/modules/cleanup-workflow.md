---
module: cleanup-workflow
category: methodology
dependencies: [Read, Grep, Bash]
estimated_tokens: 700
---

# Cleanup Workflow

**Run passes in order. Each pass is independent. Commit
between passes. Prefer deletion over rewriting.**

This module gives the multi-pass cleanup methodology. The
order matters: each pass assumes the prior passes have
landed. Mixing concerns within a pass produces diffs that
no reviewer can audit.

## The cardinal rules

1. **One pass per commit.** A commit titled "cleanup"
   that touches comments, prose, error handling, and
   tests is not reviewable. Split.
2. **Deletion beats rewriting.** When in doubt, remove
   the material. AI slop is additive; the cheapest
   correct fix is almost always to take material away.
3. **Cleanup decisions on a compromised baseline are
   themselves compromised.** Run Pass 0 first.
4. **Do not silently apply low-confidence fixes.** Surface
   them as findings, let a human decide (see
   `anti-goals.md`).
5. **Stop when a pass finds nothing.** Do not invent work
   to fill the pass.

## Pass 0: Pre-slop sweep (always first)

Before any cleanup, audit for things that should not be
in the repo at all:

- Committed agent-config files (`CLAUDE.md`, `.cursorrules`,
  `AGENTS.md`, `.codex/config.toml`, `.aider.conf.yml`,
  etc.) with secrets or broad capability grants.
- Committed credentials (run `gitleaks` / `trufflehog`).
- Untrusted MCP server entries.
- Hooks that auto-execute on session start.

Commit any redactions or revocations *before* any other
cleanup, since later passes assume an uncompromised
baseline.

```bash
# Pre-slop sweep checklist
gitleaks detect --no-banner
ls -la | grep -E '^.*(CLAUDE|cursor|codex|aider|kiro)'
find . -name '.mcp' -o -name 'mcp.json' -type f
```

## Pass 1: Surface lint sweep

Run the cheap automated detectors. Fix or delete what
they flag. This is the floor, not the ceiling.

```bash
# Linter floor
[language-specific formatter] --check
[language-specific linter] --strict

# Dependency hygiene
[unused-dep detector]
[vulnerability scanner]
```

Commit. If your linter supports an "no escape hatches"
rule (e.g. `allow_attributes = "deny"` in Rust clippy),
enable it. it prevents the most common AI-agent dodge:
silencing a lint with `#[allow(...)]` instead of fixing
the underlying code.

## Pass 2: Hallucination sweep

Run `Skill(scribe:slop-detector)` module
`hallucination-detection.md`:

- Every quoted identifier in prose: does it exist?
- Every backticked file path: does it exist?
- Every cited URL: does it 200?
- Every recommended package install: does it resolve on
  the relevant registry?
- Every config key in docs: does the code read it?

Then run module `stub-and-deferral.md`:

- Every TODO/FIXME/XXX/HACK: is there a tracked issue
  link, or is the surrounding code path defunct?
- Every `// for now`, `// placeholder`, `// dummy`: same
  question.
- Every `todo!()` / `unimplemented!()` /
  `NotImplementedError`: is this reachable from a public
  API?

Resolve, link, or delete. Commit per category.

## Pass 3: Identity & voice leaks

Run module `identity-and-voice-leaks.md`:

- **P0. identity leaks**: any "as a large language model",
  "as of my training cutoff", etc. → delete on sight.
- **Conversational voice leaks**: "Hope this helps!",
  "Great question!", "Sure!" outside transcript blocks
  → delete the phrase, keep substance.
- **Self-narration of structure**: "In this section, we
  will cover..." → strip framing, start at content.

This pass is small but high-priority. Identity leaks in
particular fail review independent of any other score.

## Pass 4: Comment slop

Walk every code comment and doc comment. For each, ask:
*does this convey information not present in the code,
names, or signatures?* If no, delete.

For doc comments specifically (docstrings, `///`, `//!`,
JSDoc, etc.), enforce the docstring/implementation ratio:

| Ratio (doc lines / impl lines) | Action |
|---|---|
| >= 2.0 | CRITICAL: almost certainly slop; trim or rewrite |
| >= 1.0 | warning; investigate |
| ~ 0.5 | acceptable for public API |
| < 0.5 | balanced or code-heavy; usually fine |

Trivial helpers should often have *no* doc comment at all
— the function name + signature is the spec. See
`anti-goals.md` Class 1 for what to keep.

Commit.

## Pass 5: Prose slop in markdown & docstrings

Walk every `*.md` and every multi-line doc-comment block.
Apply:

- `vocabulary-patterns.md`. tier-1 banned words and
  phrases.
- `structural-patterns.md`. em dashes, bullet ratio,
  paragraph blockiness.
- `document-economy.md`. thesis-first, sentence weight,
  repetition rule, reader-time budget.
- `evidence-backed-claims.md`. every quality claim
  points to repo evidence.

Strike banned vocabulary, verify quality claims, remove
emoji from headers, flatten over-deep heading trees.
Commit per category.

## Pass 6: Code idiom sweep

Apply the language-specific anti-pattern modules. For
Rust, see `pensive:rust-review` (this scribe skill
delegates code idiom checks to that plugin). For Python,
see `parseltongue:python-pro`. For shell, see
`pensive:shell-review`.

Calibrate by model: per the 2025-26 cross-evaluation
research, GPT-family-generated code has more concurrency
mistakes; Claude-family-generated code has more
omissions. Weight your audit accordingly.

Commit per category, not per file.

## Pass 7: Architecture slop

This is the highest-judgment pass and the most prone to
over-correction. See `anti-goals.md` Class 2 for what
*not* to flatten.

Look for:
- Traits with one implementor, not used as `dyn`, not
  used for mocking, not exported.
- "Manager" / "Handler" / "Service" structs that own one
  method.
- Builder patterns for structs with two fields.
- Layered structures where each layer just delegates one
  method to the next.
- An error enum with 12 variants, three of which are ever
  constructed (but see anti-goals: do not collapse public
  variants).

Prefer to leave a borderline abstraction in place rather
than delete one that turns out to be load-bearing. Commit.

## Pass 8: Test slop

Apply `tests/` audit:

- Tautological tests (`assert!(s.is_some())` after
  `Foo::new() -> Foo`).
- Tests that re-implement the function under test in the
  assertion.
- Mock-everything tests that prove only that orchestration
  calls the orchestrator.
- Snapshot tests on data with no semantic meaning.
- `#[ignore]` tests with no comment.
- One giant `test_everything()` asserting 30 unrelated
  things.

Where pure functions are under-covered, prefer property-
based tests (`hypothesis`/`proptest`/`quickcheck`) and
golden-file tests for serializers. Both resist the "test
mirrors implementation" failure mode.

Run mutation testing if available: it is the cheapest
way to expose tests that pattern-match correctly but
catch nothing.

Commit.

## Pass 9: README and public docs

Apply `evidence-backed-claims.md` strictly. The README
should open with:

1. One sentence: what it is.
2. Minimal working example (5-15 lines, runnable).
3. Install instruction.

Then features, configuration, contributing, etc. Move
deep API documentation to docs.rs / readthedocs / wiki.
Strip emoji from headers. Verify badges resolve and are
green.

Commit.

## Pass 10: Establish guardrails

The cleanup is incomplete without preventing the slop
from coming back. Add:

- A `CONSTITUTION.md` (or equivalent project rules file)
  with immutable rules the AI and contributors must
  respect (see `evidence-backed-claims.md` for the
  pattern).
- Strict linter configuration in the build config
  (e.g. `[lints.clippy]` block in `Cargo.toml`).
- A CI step running the slop-detector on changed prose
  files.
- Pre-commit hooks running the cheap detectors locally.

Commit. This is what prevents the slop you just removed
from coming back next sprint.

## Order rationale

Why this order specifically:

1. Pass 0 (pre-slop sweep) before everything because
   cleanup decisions on compromised baselines are
   themselves compromised.
2. Pass 1 (surface lint) before anything semantic because
   the linter is the cheapest signal and clears the
   trivial finds.
3. Pass 2 (hallucination & stubs) before prose work
   because polishing text that is wrong about the world
   is wasted polish.
4. Pass 3 (identity leaks) early because it is small,
   high-severity, and pattern-matchable.
5. Passes 4-5 (comments and prose) before code idiom
   because comment removal often makes code idiom issues
   visible.
6. Pass 6 (code idiom) before architecture because
   localized fixes inform whether structural patterns
   are real.
7. Pass 7 (architecture) before tests because architecture
   churn changes which tests matter.
8. Pass 8 (tests) before README because final test
   coverage informs what claims the README can make.
9. Pass 9 (README) last among content passes because it
   is downstream of everything else.
10. Pass 10 (guardrails) closes the loop.

## Stopping rule

Stop when a pass finds nothing. Do not invent work to
fill the pass. The slop sweep is a *removal* operation;
"nothing to remove" is success, not failure.

If consecutive passes find nothing, the cleanup is done.
Commit, push, and let it land.
