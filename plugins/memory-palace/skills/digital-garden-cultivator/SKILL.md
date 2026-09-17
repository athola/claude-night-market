---
name: digital-garden-cultivator
description: Manages digital garden notes, link structures, and health metrics. Use when curating a knowledge base, pruning stale notes, or tracking content maturity.
alwaysApply: false
category: cultivation
tags:
- digital-garden
- knowledge-base
- linking
- curation
- documentation
dependencies:
- leyline:storage-templates
scripts:
- garden_metrics.py
usage_patterns:
- garden-management
- knowledge-curation
- content-lifecycle
complexity: intermediate
model_hint: standard
estimated_tokens: 500
---

# Digital Garden Cultivator

Design, manage, and evolve digital gardens as living knowledge bases. Digital gardens are interconnected note collections that grow organically, emphasizing evolution over perfection.

## What It Is

A digital garden approach to knowledge management that:
- Builds dynamic knowledge bases that evolve over time
- Connects notes through bidirectional links
- Incubates ideas before formalizing as documentation
- Creates discovery paths for information navigation
- Tracks content maturity and maintenance needs

## Quick Start

### Calculate Garden Metrics
```bash
python -m memory_palace.garden_metrics path/to/garden.json --format brief
```
**Verification:** Run `python --version` to verify Python environment.

### Output Formats
- `json` - Full metrics as JSON
- `brief` - One-line summary
- `prometheus` - Prometheus exposition format

## When To Use

- Building dynamic knowledge bases that evolve over time
- Connecting notes, skills, and palaces through bidirectional links
- Incubating ideas before formalizing as documentation
- Creating discovery paths for navigating information
- Managing content lifecycle (seedling → growing → evergreen)

## When NOT To Use

- Creating memory palace
  structures - use memory-palace-architect
- Evaluating new knowledge
  - use knowledge-intake
- Creating memory palace
  structures - use memory-palace-architect
- Evaluating new knowledge
  - use knowledge-intake

## Content Maturity Levels

| Level | Status | Description |
|-------|--------|-------------|
| **Seedling** | New/rough | Early ideas, incomplete thoughts |
| **Growing** | Developing | Being actively refined |
| **Evergreen** | Mature | Stable, well-developed content |

## Core Workflow

1. **Collect Sources** - Gather notes, bookmarks, ideas
2. **Plan Structure** - Define garden organization
3. **Create Links** - Build bidirectional connections
4. **Schedule Maintenance** - Establish tending cadence
5. **Document Outputs** - Convert mature ideas to formal docs

## Garden Layout Template

```yaml
garden:
  sections: ["research", "patterns", "experiments"]
  plots:
    - name: "My First Note"
      purpose: "reference"  # reference | evergreen | lab
      maturity: "seedling"  # seedling | growing | evergreen
      inbound_links: []
      outbound_links: []
      last_tended: "2025-11-24T10:00:00Z"
```
**Verification:** Run the command with `--help` flag to verify availability.

## Maintenance Cadence

| Action | Frequency | Purpose |
|--------|-----------|---------|
| Quick prune | Every 2 days | Remove dead links, fix typos |
| Stale review | After 7 days inactive | Assess content freshness |
| Archive | After 30 days inactive | Move to archive or delete |

## Success Metrics

- **Link density** - Average links per piece of content
- **Bidirectional coverage** - % of links that are reciprocal
- **Freshness** - Time since last update per area
- **Maturity ratio** - Evergreen content / total content

## Detailed Resources

- **Linking Patterns**: See `modules/linking-patterns.md`
- **Maintenance Guide**: See `modules/maintenance.md`
- **Metrics Integration**: See `modules/maintenance.md`

## Integration

- `memory-palace-architect` - Host garden within palace structure
- `knowledge-locator` - Search garden content
- `session-palace-builder` - Seed garden from session insights
## Troubleshooting

### Common Issues

**Pre-commit hooks failing**
Run `SKIP=... git commit` to bypass temporarily, then fix issues

**Merge conflicts**
Use `git merge --abort` to reset, then resolve conflicts carefully

**Commit rejected**
Check hook output and fix reported issues before committing again

## Exit Criteria

- [ ] `python -m memory_palace.garden_metrics` runs without error on the target
      `garden.json` and outputs link density, bidirectional coverage,
      freshness, and maturity ratio
- [ ] Stale notes (inactive for more than 7 days) are identified and
      surfaced for the user's review
- [ ] Each note in scope has a maturity level assigned as one of:
      `seedling`, `growing`, or `evergreen`
- [ ] Dead links and orphaned notes are reported so they can be pruned
      or reconnected during the maintenance pass
- [ ] If `garden.json` is absent or malformed, the error is reported
      with the path that was searched rather than silently completing
