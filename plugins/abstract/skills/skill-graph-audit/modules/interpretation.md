---
name: skill-graph-audit-interpretation
description: How to interpret graph metrics, including isolate taxonomy and false-positive guidance.
---

# Interpreting Graph Metrics

## Isolate Taxonomy

A skill flagged as "isolate" (zero inbound, zero outbound) is not
necessarily broken. Per `docs/skill-taxonomy.md`, three legitimate
roles produce zero edges:

### 1. Library skills

Skills consumed via `dependencies:` frontmatter from other skills
or via Python imports rather than `Skill()` calls. Example:
`abstract:shared-patterns`. **Action**: confirm `dependencies:` field
in callers.

### 2. Entrypoint skills

Skills invoked directly by users via slash commands or by an
external orchestrator (e.g. `egregore:summon`). Example:
`abstract:plugin-review`. **Action**: confirm a corresponding
command file exists in `plugins/<plugin>/commands/`.

### 3. Hook-target skills

Skills that hooks redirect to. Example: `imbue:proof-of-work`.
**Action**: confirm a `PreToolUse`/`PostToolUse` hook in
`plugins/<plugin>/hooks.json` references the skill.

A skill that fits none of the three is a true orphan and a
candidate for retirement.

## Hub Sensitivity

Skills with high inbound count are load-bearing. Before retiring
or splitting one:

- Run `rg "Skill\\(<plugin>:<name>\\)" plugins/` to enumerate callers
- Open a deprecation issue with at least 30-day notice
- Provide a migration target in the deprecation note

The current top-5 hubs (as of 2026-04-25) are:

1. `scribe:slop-detector`
2. `attune:project-brainstorming`
3. `sanctum:git-workspace-review`
4. `attune:project-planning`
5. `attune:project-specification`

## Dangling Reference Triage

| Class | Default action |
|-------|----------------|
| bugs | Fix in the same PR; do not merge with bugs > 0 |
| external | Confirm external plugin is documented in plugin.json |
| placeholders | Annotate with `<!-- template -->` to suppress |

## Cross-Plugin Coupling

A high count of cross-plugin edges (src plugin != dst plugin) is
healthy ecosystem behaviour, not a problem. A high count of
intra-plugin edges (src plugin == dst plugin) suggests a
plugin-internal federation worth documenting in the plugin's
README.

## Common False Positives

- Skill names in code blocks demonstrating example usage are still
  parsed. If documenting a hypothetical skill, use `<plugin>:<name>`
  without backticks or surround with `<!-- example -->`.
- Skill names mentioned in `docs/decisions/` outside SKILL.md files
  are not parsed (only SKILL.md is the source of truth).
