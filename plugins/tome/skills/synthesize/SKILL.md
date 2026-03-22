---
name: synthesize
description: >-
  Merge, deduplicate, rank, and format research findings
  from multiple channels into a coherent report. Use after
  research agents return their results.
category: synthesis
tags:
  - merge
  - rank
  - format
  - report
estimated_tokens: 150
---

# Finding Synthesis

Merge findings from all channels into a ranked report.

## Workflow

1. Merge: `tome.synthesis.merger.merge_findings()`
2. Rank: `tome.synthesis.ranker.rank_findings()`
3. Group: `tome.synthesis.ranker.group_by_theme()`
4. Format: `tome.output.report.format_report()`

## Output Formats

- **report**: Full sectioned markdown
- **brief**: Condensed 1-2 pages
- **transcript**: Raw session log
