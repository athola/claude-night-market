---
name: night-market-docs-and-writing
description: Maintain docs of record, ADRs, changelog, and house style. Use when writing repo docs. Do not use for release steps; use night-market-operations instead.
---

# Night Market Docs and Writing

This skill maps every document of record in claude-night-market, states
which are hand-authored and which are generated, and gives the house
prose style with the commands that enforce it. "Docs of record" means
the files other contributors treat as canonical truth. Editing the
wrong file (or a generated one) creates drift that CI then flags.

## Docs-of-record map

| File | Canonical for | Authored or generated | Update trigger |
|------|---------------|-----------------------|----------------|
| `CONSTITUTION.md` | Supreme law: 10 non-negotiable rules | Hand-authored | Amendment PR titled `constitution: amend rule N` plus repo-owner sign-off |
| `STEWARDSHIP.md` | Values and virtues behind the rules | Hand-authored | Rarely; value-level shifts only |
| `.claude/rules/` (8 files) | Repo-wide behavioral rules loaded into every session | Hand-authored | A research finding or audit graduates into policy |
| `docs/adr/` (0001-0017) | Load-bearing decisions with status and supersession | Hand-authored | New architectural decision; supersede, never rewrite |
| `docs/quality-gates.md` | Three-layer gate system and skill gate composition | Hand-authored | Gate or threshold changes |
| `docs/testing-guide.md` | Test discipline and coverage practice | Hand-authored | Testing policy changes |
| `docs/plugin-development-guide.md` | Plugin authoring, release checklist, Python tiers | Hand-authored | Plugin conventions change |
| `docs/skill-description-guide.md` | The 160-char description contract | Hand-authored | Description policy changes |
| `docs/skill-integration-guide.md` | Skill role taxonomy (entrypoint, library, hook-target) | Hand-authored | Skill graph restructuring |
| `docs/backlog/queue.md`, `docs/backlog/technical-debt.md` | Work intake and debt registry. LOCAL ONLY, not a doc of record: `docs/backlog/` is gitignored with zero tracked files, so these exist only on the authoring machine. The durable record of a deferred item is a GitHub issue | Hand-authored, gitignored | New backlog item or debt entry |
| `docs/research/` | Dated research syntheses feeding the rules pipeline. LOCAL ONLY, not a doc of record: gitignored, absent on fresh clones. Background material; put load-bearing citations into the rule or ADR itself (see night-market-research-methodology) | Hand-authored, gitignored | New research pass completes |
| `CHANGELOG.md` | Release history, Keep a Changelog 1.1.0 | Hand-authored | Every release and notable change |
| `docs/api-overview.md` | Plugin version table and CLI entry points | Hand-authored | Every release (version table row per plugin) |
| `book/src/` | Published mdBook (GitHub Pages) | Mixed: see below | Content changes; deploys on push to `book/**` |
| `book/src/reference/capabilities-*.md` | Skill/command/agent/hook lookup tables | GENERATED via sync | Never hand-edit; run `/sanctum:sync-capabilities --fix` |
| `.claude-plugin/marketplace.json` | Ecosystem version source of truth | Hand-authored (bumped by script) | Release version bump |
| `docs/tradeoffs.md`, `docs/lessons-learned.md` | Decision journal (TR-NNN / LL-NNN entries) | Hand-authored, append-only | Recording a tradeoff or lesson (contract: `leyline:decision-journal`) |
| GitHub Discussions | Collective memory ([Learning], [PR Finding], [War Room]) | Mixed (hooks post automatically) | See night-market-collective-memory |

Notes on the map:

- mdBook is the `mdbook` static-site generator. The book builds from
  `book/book.toml` (`src = "src"`, `create-missing = false`) and its
  table of contents is `book/src/SUMMARY.md` (Getting Started, then
  Plugins grouped by layer, then Reference).
- The decision journal files do not exist in the working tree as of
  2026-07-02. The `leyline:decision-journal` contract creates them on
  first append. Do not scaffold them empty.
- `docs/dependency-audit.md` and other dated reports are point-in-time
  artifacts, not living docs of record.

## Per-feature artifacts: overwritten each cycle

`docs/project-brief.md`, `docs/specification.md`, and
`docs/implementation-plan.md` are per-feature working documents. Each
feature cycle OVERWRITES them (current occupant as of 2026-07-02: the
insight-palace bridge, spec v0.1.0 Draft). Never treat their content as
permanent record. If a decision inside them must outlive the feature,
promote it to an ADR or a decision journal entry before the next cycle.

## House prose style

Full rules live in `.claude/rules/markdown-formatting.md` and
`.claude/rules/slop-scan-for-docs.md`, with the detection catalog in
`Skill(scribe:slop-detector)` modules. The load-bearing subset:

- Wrap prose at 80 characters. Break at sentence boundaries first,
  then clauses, then before conjunctions. Never wrap tables, code
  blocks, headings, frontmatter, or URLs.
- ATX headings only (`# Title`). Blank line before AND after every
  heading and every list.
- Reference-style links when an inline link pushes a line past 80
  characters.
- Em-dash target is zero in new prose (0-2 absolute max per file).
  Use colons, periods, or parentheses. Never use a spaced double
  dash as punctuation (a repo hook flags it).
- American spelling. No semicolon splices. No smart quotes outside
  code blocks.

### The three slop layers

"Slop" is the repo term for machine-generated prose patterns that
waste reader time or ship falsehoods. Every new or edited markdown
file passes three layers before it is done:

1. **P0 critical (any hit fails outright)**: identity leaks ("As a
   large language model"), hallucinated identifiers, paths, packages,
   or URLs, and bare TODO/FIXME stubs without a tracked issue.
   Constitution rule 4 makes an identity leak an automatic revert.
2. **Document economy (scored 0-6, ship at 5+)**: thesis stated
   first, every sentence carries weight, thesis echoed rather than
   filler repeated. Rubric: `scribe:slop-detector` module
   `document-economy.md`.
3. **Sentence-level tiers**: banned vocabulary, negative parallelism,
   throat-clearing openers, participial tails, and the 2026 pattern
   set. Catalog: `scribe:slop-detector` module
   `vocabulary-patterns.md` and the rule file's tier lists.

### Slop-check CI

`.github/workflows/slop-check.yml` runs on any PR touching a `.md`
file. It scans only files under `docs/` and `book/src/` and scores
each file:

```text
score = (tier1_hits * 3 + tier2_hits * 2 + em_dashes) / words * 100
```

Any file scoring above 3.0 fails the job and gets a PR comment.
The tier-1 and tier-2 word lists live in the workflow file itself
(variables `TIER1` and `TIER2` in `slop-check.yml`); read them there
rather than memorizing. Quick local pre-check on a doc you touched:

```bash
grep -o '—' docs/your-file.md | wc -l
grep -oiE 'delve|tapestry|pivotal|meticulous|leveraging|comprehensive' \
  docs/your-file.md
```

Files outside `docs/` and `book/src/` (plugin skills, READMEs) skip
this CI job but still fall under the rule file and review.

## Reader-time budget (constitution rule 8)

Every doc is paid for in cumulative reader-time: audience size times
read frequency times per-read time. Estimate that product BEFORE
drafting and match your writing time to it. A skill loaded hundreds
of times a day earns hours of polish. A one-off report earns minutes.
If the budget is near zero, do not write the doc. Full framework:
`scribe:slop-detector` module `document-economy.md`.

## ADR conventions

An ADR (Architecture Decision Record) captures a decision that is
expensive to reverse. They live in `docs/adr/` as
`NNNN-kebab-slug.md` with zero-padded sequential numbers (0001-0017
as of 2026-07-02).

Header template (verified against ADR-0001 and ADR-0017):

```markdown
# ADR-NNNN: Title

**Date**: YYYY-MM-DD
**Status**: Accepted
**Deciders**: Claude Night Market maintainers
**Source**: Issue #NNN, Discussion #NNN
**Supersedes**: ADR-NNNN

## Context

## Decision

## Consequences
```

Rules:

- Status values in use: Accepted, Superseded by ADR-NNNN. Never
  delete or rewrite a superseded ADR. Example chain: ADR-0012 and
  ADR-0013 both carry "Superseded by ADR-0017", and 0017 lists
  "Supersedes: ADR-0012, ADR-0013" in its header.
- An ADR may supersede itself in place for a scoped correction
  (ADR-0008 swapped its mechanism and documented the change inline).
- `Source` links the issue or discussion that forced the decision.

### ADR vs journal entry vs discussion post

| Record | Use for | Where |
|--------|---------|-------|
| ADR | Load-bearing, hard-to-reverse design decision | `docs/adr/NNNN-*.md` |
| Decision journal | Tradeoff taken or lesson learned, append-only, stable TR-NNN / LL-NNN ids | `docs/tradeoffs.md`, `docs/lessons-learned.md` per `leyline:decision-journal` |
| Discussion post | Ambient collective memory: [Learning], [PR Finding], [War Room] | GitHub Discussions via GraphQL (no `gh discussion` subcommand exists) |

For the Discussions mechanics and promotion path, use the sibling
skill night-market-collective-memory.

## Changelog conventions

`CHANGELOG.md` follows Keep a Changelog 1.1.0 and SemVer:

- `## [Unreleased]` stays at the top; new entries land there and get
  moved under a `## [X.Y.Z] - YYYY-MM-DD` heading at release.
- Standard subsections: `### Added`, `### Fixed`, `### Changed`.
- Never retroactively de-slop or reword historical entries. The
  slop anti-goals (`scribe:slop-detector` module `anti-goals.md`)
  explicitly exempt changelog history: it is a record, not prose to
  polish.

## Skill description contract

Every `SKILL.md` and command `description:` field is loaded into the
model's skill-discovery budget, so length is policed:

- Hard cap: 160 characters per description (hard fail).
- Third person only. Template:
  `[Verb phrase] [domain]. Use when [trigger]. Do not use when
  [negative]; use [alternative] instead.`
- Full guide: `docs/skill-description-guide.md`.

Two pre-commit hooks enforce it:

```bash
python3 plugins/abstract/scripts/validate_budget.py
python3 scripts/fix_descriptions.py --check
```

`validate_budget.py` hard-fails any description over 160 chars and
warns when the ecosystem total approaches its budget (default 90,000
chars, override via `SLASH_COMMAND_TOOL_CHAR_BUDGET`). Note:
`docs/skill-description-guide.md` still cites an older 60,000-char
ceiling; the script value is current (the script is the enforcer).

## The book (mdBook)

- Structure: edit `book/src/SUMMARY.md` to add pages;
  `create-missing = false` means a SUMMARY entry without a file
  breaks the build.
- Local build: `cd book && mdbook build` (output in `book/build/`).
  mdbook is installed separately; CI uses the unpinned latest.
- Deploy: `.github/workflows/deploy-book.yml` publishes to GitHub
  Pages on push to master touching `book/**`. PRs touching `book/**`
  get a build check.
- `book/src/reference/capabilities-*.md` are generated from plugin
  manifests. Check drift with `make docs-sync-check` (runs
  `scripts/capabilities-sync-check.sh`); fix drift with the
  `/sanctum:sync-capabilities --fix` command, not by hand.

## Doc gate command checklist

Run before committing markdown:

```bash
python3 scripts/check-markdown-links.py path/to/file.md
python3 plugins/abstract/scripts/validate_budget.py   # if SKILL.md touched
make docs-sync-check                                  # if manifests touched
```

Then walk the three slop layers manually or via
`Skill(scribe:slop-detector)`. Every new or modified SKILL.md also
needs a `## Exit Criteria` section (`.claude/rules/skill-exit-criteria.md`,
issue #454).

## When NOT to use

- Running tests, lint, releases, or the version bump: use
  night-market-operations.
- Classifying whether a change needs an ADR-gated review at all: use
  night-market-change-control.
- Posting to or querying GitHub Discussions, journal promotion paths,
  ADR-vs-memory routing details: use night-market-collective-memory.
- Plugin/skill/hook file mechanics (frontmatter fields, discovery):
  use claude-code-plugin-reference.
- Test evidence standards and coverage thresholds: use
  night-market-validation-and-qa.

## Exit Criteria

- [ ] Any doc edit touched the file the map marks as canonical, and
      no file marked GENERATED was hand-edited (verify:
      `git diff --stat` shows no `book/src/reference/capabilities-*`
      unless produced by the sync command).
- [ ] New prose passes the local slop pre-check: zero P0 hits, zero
      new em dashes, no tier-1 vocabulary in the diff.
- [ ] `python3 scripts/check-markdown-links.py <file>` exits 0 for
      each markdown file touched.
- [ ] If a SKILL.md was touched:
      `python3 plugins/abstract/scripts/validate_budget.py` exits 0
      and the file contains a `## Exit Criteria` section.
- [ ] If a decision was recorded: it landed as a numbered ADR, a
      TR-NNN/LL-NNN journal entry, or a Discussion post, and any
      superseded ADR's Status field was updated in place.
- [ ] CHANGELOG.md still has `## [Unreleased]` as its first version
      heading and no historical entry was reworded.

## Provenance and maintenance

Compiled 2026-07-02 against repo v1.9.15 (branch
discussions-fix-1.9.14). Volatile facts and how to re-verify:

- ADR count (17) and statuses: `ls docs/adr/` and
  `rg -l "Superseded" docs/adr/`.
- Slop CI threshold (3.0) and scanned paths (docs/, book/src/):
  read `.github/workflows/slop-check.yml`.
- Description cap (160) and total budget (90,000):
  `rg "DESCRIPTION_MAX|DEFAULT_BUDGET" plugins/abstract/scripts/validate_budget.py`.
- Rules inventory (8 files): `ls .claude/rules/`.
- Per-feature doc occupant: `head -5 docs/project-brief.md`.
- Journal files existence: `ls docs/tradeoffs.md docs/lessons-learned.md`.
- Book deploy trigger: read `.github/workflows/deploy-book.yml`.
- Guide-vs-script budget drift (60K vs 90K): re-check
  `docs/skill-description-guide.md` in case the guide was updated.
