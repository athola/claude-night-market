---
name: adr-digest
description: "One line per ADR: the decision and where it is enforced. The ADRs in docs/adr are the record."
---

## ADR digest

All 23 records are in `docs/adr/`. Statuses for 0001 to 0017 were
read from the files on 2026-07-02, and 0018 to 0022 on 2026-08-23.

| ADR | Title | Status | One-line takeaway |
|-----|-------|--------|-------------------|
| 0001 | Plugin Dependency Isolation | Accepted | No shared registry. Runtime filesystem detection with graceful degradation |
| 0002 | Extract QuotaTracker to Leyline | Accepted | Quota tracking moved from conjure into leyline for reuse |
| 0003 | Command Description Refactoring | Accepted | Two-part descriptions: short display line, rich identification text |
| 0004 | Skill Description Budget Optimization | Accepted (updated 2026-05-21) | 160-char cap. Budget is 2% of context, 16k fallback. Its 60k validator ceiling is stale: the enforcing script uses 90k |
| 0005 | Attune Plugin Discoverability Enhancement | Accepted (2026-02-05) | Superpowers-style trigger phrasing for attune components |
| 0006 | Self-Adapting Skill Health | Accepted (2026-02-15) | Homeostatic monitoring detects degrading skills |
| 0007 | GitHub Discussions as Agent Collective Memory | Accepted (2026-02-19) | Decisions and learnings posted to Discussions (GraphQL only) |
| 0008 | Behavioral Contract Verification Framework | Superseded (2026-03-15) | ERC-8004 blockchain dropped for cost. GitHub Attestations (SLSA) instead |
| 0009 | Sidecar Service Discovery via Port Files | Accepted | Sidecar daemons publish their ports through port files |
| 0010 | Stacked Diff Workflows | Accepted | `git --update-refs` plus `gh pr create --base` as zero-dependency stacking |
| 0011 | Shared Session-Capture Envelope | Accepted | One JSON envelope shape for friction and trace payloads, separate files |
| 0012 | Confidence-Tagged Agent Claims | Superseded by 0017 | VERIFIED/INFERRED/ASSUMPTION tags: no enforcement built |
| 0013 | Operationalizing Naur Theory-Building | Superseded by 0017 | Theory-building rituals: folded into 0017's lighter form |
| 0014 | Pensive Review-Skill Consolidation | Accepted (sequencing only) | 9 review skills, 5 sharing a verdict scaffold. Consolidation sequenced, not done |
| 0015 | Over-Built Orchestrator Skill Simplification | Accepted (data-collection phase) | Collect 30 days of usage data before simplifying over-built skills |
| 0016 | Wire-or-Archive for Three Orphan Skills | Accepted (decisions recorded) | Orphans judged on demand signal, wiring cost, and reference value |
| 0017 | Decisions on Confidence-Tagging and Theory-Building | Accepted (2026-06-18) | No enforcement mechanisms and voluntary use. Supersedes 0012 and 0013 |
| 0018 | Reuse memory-palace's Graph for the Tome Research Engine | Accepted | Tome builds on the existing graph instead of a second one |
| 0019 | Retire docs/superpowers/ and Record Its Shipped Design Decisions | Accepted | The design folder became ADR text; the folder is gone |
| 0020 | Detect a Thin Field with Positive Controls, Not Overlap Estimation | Accepted | Frontier detection uses positive controls, not overlap math |
| 0021 | PR Descriptions Carry Six Dimensions in Two Registers | Accepted (2026-08-12) | Six dimensions, but only some earn a heading |
| 0022 | The Autonomous Loop Continues by Riding the Stop Hook | Accepted, with a named open problem (2026-08-23) | Stop-hook re-injection is the loop. Cost bounded by stall detection; the reliance stays open |
