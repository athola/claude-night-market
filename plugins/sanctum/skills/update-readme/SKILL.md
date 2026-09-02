---
name: update-readme
description: Refreshes README structure favoring concision (an index, not a manual). Use when the README needs a structural update after significant project changes.
alwaysApply: false
category: artifact-generation
tags:
- readme
- documentation
- exemplars
- research
- structure
tools: []
complexity: high
model_hint: deep
estimated_tokens: 1200
modules:
- modules/language-audit.md
- modules/exemplar-research.md
progressive_loading: true
dependencies:
- sanctum:git-workspace-review
- imbue:proof-of-work
- scribe:slop-detector
- scribe:doc-generator
---
# README Update Workflow

## When To Use
Use this skill whenever the README requires a structural refresh.
Run `Skill(sanctum:git-workspace-review)` first to capture repo context and diffs.

## When NOT To Use

- Updating inline docs: use doc-updates
- Consolidating ephemeral reports: use doc-consolidation

## Required TodoWrite Items
1. `update-readme:language-audit`
2. `update-readme:exemplar-research`
3. `update-readme:outline-aligned`
4. `update-readme:edits-applied`
5. `update-readme:slop-scanned` - AI marker detection via scribe
6. `update-readme:verification-reporting`

## Step 1 - Language Audit (`update-readme:language-audit`)
- Confirm `pwd`, `git status -sb`, and the baseline branch for reference.
- Detect dominant languages using repository heuristics (manifest files, file counts).
- Note secondary languages that influence documentation (e.g., a TypeScript frontend and a Rust backend) so the README can surface both.
- Record the method and findings.

See `modules/language-audit.md` for detailed detection patterns and commands.

## Step 2 - Exemplar Research (`update-readme:exemplar-research`)
- For each primary and secondary language, use web search to locate high-quality READMEs (star count, recency, maintainer activity).
- Capture 2-3 exemplar repositories per language and summarize why each is relevant (section order, visuals, quickstart clarity, governance messaging, math exposition, etc.).
- Store citations for every exemplar so the final summary references them explicitly.

See `modules/exemplar-research.md` for search query patterns and evaluation criteria.

## Step 3 - Outline Alignment (`update-readme:outline-aligned`)

**The README is an index, not a manual.** Lead with what the
project is, how to install it, and a scannable table of its
units (plugins, commands, packages); link out for everything
else.

**A README is a `newcomer` document.** Its reader has never seen
this project, so the test for every candidate section is whether
that reader needs it before they can install and run one thing.
Rationale, alternatives considered, and internals are `expert`
material: extract them to `docs/deep-dive/<topic>.md` or the
`book/`, linked from the README in one line naming who the page
is for. Never delete them to shorten the README. Tier table and
cut test: `scribe:slop-detector` module `audience-targeting.md`.

A README that declares a different tier (an internal tool whose
only readers already run it) says so in its lead.

When this repo's root README was simplified in 2026, it
dropped from 435 to 200 lines (65% fewer words) by deleting
inlined depth and linking to `book/` instead. Aim for that
shape, not a section-by-section coverage sweep.

- Compare current README headings (`rg -n '^#' README.md`)
  against the exemplars from Step 2. Lean marketplace and
  CLI-tool READMEs (asdf-vm/asdf-plugins, ohmyzsh/ohmyzsh,
  ryoppippi/ccusage) are index-shaped: prose intro under ~500
  words, a unit table doing the work, depth behind links.
- Keep only the sections that earn a place in an index: a
  one-line value proposition, one install path, a compact
  command or unit table, a short "what's inside" summary, a
  single Documentation link section, and metadata
  (requirements, contributing, license) last. For every other
  candidate section ask: **does this belong in the README, or
  behind a link?**
- Default to linking out. Send deep architecture, FAQ,
  roadmap, changelog, alternate install methods, and per-unit
  detail to their own pages. Per-unit docs live with the unit
  (hub-and-spoke), never duplicated in the root.
- Order signals priority: title and tagline first, then
  install, then the index table, then a short feature summary,
  then Documentation links, with housekeeping (requirements,
  contributing, license) last.
- Map internal documents (docs/, book/, specs/, commands/) to
  the section that links them, so the README anchors depth
  without restating it.

**Soft budget**: a marketplace or collection root README runs
roughly 150-400 lines of prose plus any index table. A section
that grows over time (roadmap, FAQ, changelog) belongs in a
linked page, not the README.

## Step 4 - Apply Edits (`update-readme:edits-applied`)
- Implement the new structure directly in `README.md`
  (or the specified file).
- Follow `Skill(leyline:markdown-formatting)` conventions:
  wrap prose at 80 chars (prefer sentence/clause boundaries),
  blank lines around headings, ATX headings only, blank line
  before lists, reference-style links for long URLs.
- Maintain concise, evidence-based prose; avoid marketing fluff.
- Prefer deletion and linking over inlining. If a section
  duplicates a docs page, cut it and link the page; if it
  grows over time, move it out of the README entirely.
- Add comparison tables, feature lists, or diagrams only if
  they originate from current repository assets (no speculative
  content).
- When referencing algorithms or performance claims, point to
  benchmarks or tests within the repository or documented math
  reviews.

## Step 4.5 - AI Slop Detection (`update-readme:slop-scanned`)

Run `Skill(scribe:slop-detector)` on the updated README to detect AI-generated content markers.

### Scribe Integration

The scribe plugin provides AI slop detection:

```
Skill(scribe:slop-detector) --target README.md
```

This detects:
- **Tier 1 words**: delve, tapestry, comprehensive, leveraging, etc.
- **Phrase patterns**: "In today's fast-paced world", "cannot be overstated"
- **Structural markers**: Excessive em dashes, bullet overuse, sentence uniformity
- **Marketing language**: "enterprise-ready", "cutting-edge", "seamless"

### Remediation

If slop score exceeds 2.0 (moderate), apply `Skill(scribe:doc-generator)` principles:

1. Ground every claim with specifics
2. Remove formulaic openers/closers
3. Use numbers, commands, filenames over adjectives
4. Balance bullets with narrative prose
5. Show authorial perspective (trade-offs, reasoning)

For significant cleanup needs, use:

```
Agent(scribe:doc-editor) --target README.md
```

## Step 5 - Verification & Reporting (`update-readme:verification-reporting`)
- Re-read the updated README for clarity, accessibility (section lengths, bullet balance), and accurate links.
- Run `git diff README.md` (or the edited file) and capture snippets for the final report.
- Summarize detected languages, exemplar sources (with citations), key structural decisions, and follow-up TODOs (e.g., add badges, upload diagrams).

## Exit Criteria

- [ ] All `TodoWrite` items are complete.
- [ ] The README is index-shaped: prose intro within the soft
  budget (roughly 150-400 lines plus any unit table), one
  install path, and a scannable unit/command table.
- [ ] No README section duplicates a `book/` or `docs/` page;
  depth is linked, not inlined (`rg -n '^#' README.md` headings
  each map to a section that earns a place in an index).
- [ ] The README serves a `newcomer`, or declares the tier it
  serves instead in its lead.
- [ ] Content cut for tier fit landed in a linked page, not the
  bin (`docs/deep-dive/` or `book/`).
- [ ] The README references internal docs and external
  exemplars with citations.
- [ ] Research notes and command references are captured so
  future reviewers can reproduce the process.

## Troubleshooting

### Common Issues

**Documentation out of sync**
Run `make docs-sync-check` to verify the capabilities docs still
match the plugin registrations

**Build failures**
Check that all required dependencies are installed

**Links broken**
Verify relative paths in documentation files
