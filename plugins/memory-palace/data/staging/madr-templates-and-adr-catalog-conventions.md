---
title: MADR templates and ADR catalog conventions
source:
  type: web_fetch
  identifier: https://github.com/adr/madr
author: claude
date_captured: '2026-10-30'
palace: Engineering Practice
district: Architecture decisions
maturity: probation
tags:
- adr
- architecture-decisions
- documentation
- templates
---

# MADR templates and ADR catalog conventions

## Marginal Value Summary

- **Integration Decision**: standalone
- **Confidence**: 90%
- **Novelty Tags**: adr, architecture-decisions, documentation, templates

## Intake Content

# MADR templates and ADR catalog conventions

Sources (captured 2026-10-26 to 10-30): github.com/adr/madr (2.6k stars),
the MADR `adr-template.md` and `adr-template-minimal.md`, and
archman.dev's ADR catalog and traceability page.

## MADR full template

Frontmatter, in order: `status` (proposed, accepted, rejected,
deprecated, superseded by a later record), `date`, `decision-makers`,
`consulted` (two-way), `informed` (one-way).

Sections: title naming problem and solution; Context and Problem
Statement; Decision Drivers (optional); Considered Options; Decision
Outcome, with Consequences and Confirmation (how compliance is checked:
fitness functions, reviews, tests) as optional subsections; Pros and Cons
of the Options (optional); More Information (optional).

## MADR minimal template

Title, Context and Problem Statement, Considered Options, Decision
Outcome, and Consequences (optional, H3).

## Catalog practice (archman.dev)

- Number sequentially. The page says ADR-001 but its examples use four
  digits (`0001-use-postgresql.md`); it does not reconcile the two.
- `docs/adr/README.md` as the index, `TEMPLATE.md` for the template,
  optionally `index.json` for tooling.
- Statuses Proposed, Accepted, Deprecated, Superseded, with dated
  transitions.
- Supersession recorded on both sides: `supersedes: ADR-0028` on the new
  record; `status: Superseded`, `superseded_by`, a reason and a migration
  deadline on the old one.
- The page asserts these practices without evidence.

Relevance here: `docs/adr/` uses four-digit numbering; compare its records
against the Confirmation section, which names how a decision is checked.
