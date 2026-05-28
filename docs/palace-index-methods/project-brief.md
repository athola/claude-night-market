# Palace Index Methods: Project Brief

## Problem Statement

The memory-palace plugin auto-captures every WebFetch and WebSearch into
`hooks/memory-palace-index.yaml`. Captures land at the defaults
`routing_type: pending`, `maturity: seedling`, `importance_score: 50`,
and nothing advances them. At the start of this mission, 484 of 493
entries (98%) were inert, and 90 pointed at backing files that had been
deleted. The only reader of the index was the deduplication layer. The
captured knowledge was never incorporated, analyzed, or surfaced: a
write-only buffer.

The gap was a wiring gap, not a missing-code gap. The plugin already
ships staleness (`decay_model`), redundancy (`marginal_value`), usage
scoring (`usage_tracker`), graph centrality (`graph_analyzer`), and
retrieval (`cache_lookup`), none of which were pointed at this index.

## Goals

1. **Analyze**: a read-only report of corpus health (inert ratio,
   orphans, topic clusters, ranked promotion candidates).
2. **Incorporate**: a promotion engine that drains the pending backlog,
   dry-run by default and idempotent, with a backup before any write.
3. **Learn**: a SessionStart hook that surfaces promoted captures during
   work, disabled by default.

## Outcome

All three shipped, each gated by tests. On a copy of the live index, the
incorporation engine drained the inert count from 484 to 77 in a single
idempotent pass (335 promoted, 81 archived, 77 held), with a timestamped
backup. The methods reuse existing corpus tooling rather than duplicating
it.

## Scope

In scope: read-only analytics, the promotion/archive engine, the
surfacing hook, a curator skill, and the supporting research.

Out of scope (documented as follow-ups in `research-findings.md`):
rewriting `decay_model` to power-law or adaptive half-lives, and adding
an embedding-based retrieval layer (keyword-first is sufficient at the
current corpus scale).

## References

- Research: `docs/palace-index-methods/research-findings.md`
- Approved plan: `~/.claude/plans/ethereal-plotting-peacock.md`
- Skill: `plugins/memory-palace/skills/palace-index-curator/SKILL.md`
