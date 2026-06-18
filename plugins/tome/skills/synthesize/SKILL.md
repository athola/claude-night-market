---
name: synthesize
description: Merges, dedupes, ranks, and formats research findings into a report. Use after research agents return results from multiple channels to produce a ranked report.
alwaysApply: false
category: synthesis
tags:
  - merge
  - rank
  - format
  - report
estimated_tokens: 150
model_hint: standard
---
# Finding Synthesis

## When To Use

- After research agents return results from multiple channels
- Producing a final ranked report from raw findings

## When NOT To Use

- No research session is active (run `/tome:research` first)
- Refining a single channel (use `/tome:dig` instead)

Merge findings from all channels into a ranked report.

## Workflow

1. Merge: `tome.synthesis.merger.merge_findings()`
2. Rank: `tome.synthesis.ranker.rank_findings()`
3. Group: `tome.synthesis.ranker.group_by_theme()`
4. Format: `tome.output.report.format_report()`
5. De-slop: before the report leaves this skill (export, paste, or post),
   run `Skill(scribe:slop-detector)` on it, or apply the markers in
   `.claude/rules/slop-scan-for-docs.md`. Replace em-dashes and arrows,
   straighten smart quotes, and cut tier-1 filler. A report posted to a
   `gh` channel hits the `slop-scan-before-post` hook if it skips this.

## Output Formats

- **report**: Full sectioned markdown
- **brief**: Condensed 1-2 pages
- **transcript**: Raw session log
