---
id: anthropic-model-roster
title: Anthropic Model Roster, Pricing, and Context Windows
maturity: growing
importance_score: 77
routing_type: both
tags:
  - anthropic
  - models
  - pricing
  - tiering
  - context-window
  - budget
sources:
  - https://platform.claude.com/docs/en/about-claude/models/overview
related_artifacts:
  - .claude/upstream-baseline.json
  - docs/agent-model-matrix.md
  - plugins/phantom/src/phantom/cost.py
  - .claude/skills/night-market-model-and-harness-updates/SKILL.md
  - docs/migrations/2026-08-02-harness-2-1-220.md
last_updated: 2026-08-02
---

## Synopsis

Capability does not track price linearly across the roster, and tier
names do not tell you where a model sits. This entry is the lookup
table that settles both questions: which model to reach for, and what
it costs when you do.

Verified against the model card on 2026-08-02. Refresh through
`Skill(night-market-model-and-harness-updates)`, which reads the card
as a mandatory source.

## Current roster

| Tier | API ID | In / Out per MTok | Context | Max out | Latency |
|------|--------|-------------------|---------|---------|---------|
| Frontier | `claude-fable-5` | $10 / $50 | 1M | 128k | Slower |
| Deep | `claude-opus-5` | $5 / $25 | 1M | 128k | Moderate |
| Standard | `claude-sonnet-5` | $3 / $15 | 1M | 128k | Fast |
| Lightweight | `claude-haiku-4-5-20251001` | $1 / $5 | 200k | 64k | Fastest |

Sonnet 5 carries introductory pricing of $2 / $10 through 2026-08-31.

## What the card settles that the name does not

**Fable is the top tier, not a creative tier.** Claude Fable 5 is
described as Anthropic's most capable widely released model, built for
long-running agents. It costs twice Opus 5 and runs slower. Reading the
name alone leads to the opposite conclusion, and this repo made exactly
that error: Fable was first placed as a Creative tier at roughly Sonnet
cost, then corrected once the card was read.

**Mythos is not available.** Claude Mythos 5 shares Fable 5's specs and
pricing but is invitation-only under Project Glasswing. It is not a
Claude Code tier and belongs in no local vocabulary.

**Haiku is the only current model under 1M context.** It holds 200k and
64k max output, so a task sized for the other three does not
necessarily fit it.

**Effort defaults to `high`** on Opus 5 and Sonnet 5 in Claude Code.
Pinning `high` matches the default rather than raising it.

## Deprecation watch

| Model | Status |
|-------|--------|
| `claude-opus-4-1-20250805` | Deprecated, retires 2026-08-05 |
| Opus 4.8, 4.7, 4.6; Sonnet 4.6, 4.5; Opus 4.5 | Legacy, still callable |

Legacy Opus generations are $5 / $25, not the $15 / $75 that Opus 4.1
charges. Copying Opus 4.1's rate onto a newer Opus overstates cost
threefold, which is the error this repo's cost tracker carried.

## Why a budget guard needs this table

`CostTracker.budget_exceeded` compares cumulative spend to a limit, so
an unpriced model is billed at whatever the fallback says. A fallback
set to Sonnet's rate understates Fable by 3.3x, and the run passes its
budget long before the guard notices. The fallback now sits at the
highest current rate so the guard fails toward stopping early.

## Open questions this does not answer

- Which tiers Claude Code exposes as agent frontmatter aliases. The
  card describes API availability, and the two sets differ: Mythos is
  callable by API and absent from Claude Code.
- What each effort level costs in practice. The card names the default,
  not the token multiplier per level.
- How quickly the roster turns over. This snapshot ages whenever a
  model ships, and nothing here signals that on its own.

## Displaces

- The `~10x` relative cost figure previously carried for `opus` in
  `docs/agent-model-matrix.md`, now restated from the card as 5x.
- The `$15 / $75` rate on `claude-opus-4-6` in
  `plugins/phantom/src/phantom/cost.py`.
