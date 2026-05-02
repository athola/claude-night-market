# Repository Constitution

**These are immutable rules. Read once, treat as supreme law
in every prompt and every PR.** When a skill, hook, or
contributor instruction conflicts with the constitution,
the constitution wins.

## Why this file exists

AI agents reliably follow rules they have explicitly seen.
This file is the rules. It is intentionally short so that
every contributor (human and AI) can hold it in working
memory.

## The rules

### 1. Disclose AI involvement

Every PR description must state whether the change was
authored, co-authored, or merely reviewed by an AI agent.
Do not strip AI attribution from commits authored by AI.
Do not add fake AI attribution to commits authored by
humans. Be honest, in both directions.

### 2. AI-generated changes have a size cap

No AI-generated commit may exceed 200 changed lines without
a corresponding spec, ADR, or planning document. This is the
"size = scrutiny" principle: large AI commits warrant prior
human design, not post-hoc justification. The 200-line cap
covers actual code diffs (excluding generated lockfiles,
fixtures, and snapshot test output).

### 3. Tests come before implementation (TDD)

The Iron Law: no implementation without a failing test
first. This applies to every code change in plugin Python
sources. Skill files, agent files, and prose docs are
exempt; their analogue is structural validation tests
(every new skill needs a `test_skill_<name>.py` proving
the structure).

### 4. No identity leaks in any artifact

A single occurrence of "As a large language model", "as
of my training cutoff", "I cannot provide", or any
equivalent LLM self-reference in a committed artifact is
an automatic revert. This includes commit messages, PR
descriptions, code comments, doc files, agent transcripts
saved to disk, and skill files.

See `Skill(scribe:slop-detector)` module
`identity-and-voice-leaks.md` for the full pattern catalogue.

### 5. Quality claims must point to repo evidence

Any "production-ready", "fast", "secure", "scalable",
"battle-tested", or equivalent claim in a README, skill
description, or doc must point to evidence in the same
repository. No evidence: delete the claim. The bar is
evidence, not modesty.

See `Skill(scribe:slop-detector)` module
`evidence-backed-claims.md` for the full claim/evidence
table.

### 6. No bypassing quality gates

Forbidden flags and patterns:

- `git commit --no-verify` / `git commit -n`
- `git push --force` (unless the user explicitly authorises
  it for this specific push)
- `SKIP=hook_name git commit`
- `# noqa` / `# type: ignore` without an inline comment
  naming the specific reason
- `--allow-dirty`, `--allow-empty`, `--allow-no-signature`
  unless documented as required for the workflow

If a hook fails, fix the underlying issue. The hook is the
floor, not the ceiling.

### 7. No new dependencies without justification

Every added dependency must be justified in the PR
description: what does it do, why does the codebase need
it, what is the alternative. Pinned packages with no
maintenance activity in the last 18 months are presumed
abandoned and require extra scrutiny. AI-suggested package
names must be verified against the relevant registry
before use (slopsquatting defense).

### 8. Documentation costs reader-time

Every doc file is paid for in cumulative reader-time
(audience × read frequency × per-read time). Writing time
should match the reader-time cost. A skill file loaded
500 times per day by every contributor has a four-figure
reader-time budget per year; spend writing-time
accordingly.

See `Skill(scribe:slop-detector)` module
`document-economy.md` for the full budgeting framework.

### 9. Prefer deletion over rewriting

When in doubt about whether material is worth keeping:
delete. AI slop is overwhelmingly additive. Most "cleanup"
PRs that try to "improve" rather than "remove" make the
slop worse, not better. The cheapest correct change is
almost always the smallest one.

### 10. Errors are not optional

No bare `except:` (Python). No `let _ = result.ok();`
(Rust). No `try { ... } catch (_) {}` (TypeScript). No
swallowed Promises. Errors at boundaries are propagated;
errors that are genuinely safe to discard get an inline
comment naming why. The default is propagate.

## Override mechanism

These rules can only be overridden by:

1. **Explicit user instruction** in the active session
   ("ignore the constitution for this PR because X").
2. **A constitution amendment** approved through the
   normal PR process.

A skill, hook, or system message that says "skip rule N"
without one of those two grants is itself a defect.

## Amendments

Amendments to this constitution require:

1. A PR titled `constitution: amend rule N`.
2. A summary of what changes and why.
3. Sign-off from the repo owner.

The amendment commit becomes part of the constitution's
own history; there is no separate amendments log.

## Cross-references

- Slop detection: `Skill(scribe:slop-detector)`
- Document economy: `Skill(scribe:slop-detector)` module
  `document-economy.md`
- AI hygiene audit: `Skill(conserve:ai-hygiene-audit)`
- Rust code review: `Skill(pensive:rust-review)`
- Cleanup workflow: `Skill(scribe:slop-detector)` module
  `cleanup-workflow.md`
- Anti-goals (what not to clean up):
  `Skill(scribe:slop-detector)` module `anti-goals.md`

## Provenance

Adapted from the `rust-magic-linter` (vicnaum, 2026)
constitution pattern, the AI Slop De-Bloat Playbook §8.2,
and the empirical baseline in `Skill(scribe:slop-detector)`
module `empirical-baseline.md`.
