# Agent Model Matrix

Every agent in this repository pins an explicit `model` and `effort` in
its frontmatter. This document records why each one sits where it does.

## The problem this solves

Claude Code resolves a subagent's model in this order, first match wins:

1. the `CLAUDE_CODE_SUBAGENT_MODEL` environment variable
2. the per-invocation `model` parameter
3. the agent's `model:` frontmatter
4. the main conversation's model

Rung 4 is the trap. The `model` field defaults to `inherit`, so an agent
that omits it runs on whatever the parent session runs on. Explore used
to always run on Haiku; as of v2.1.198 it inherits instead, capped at
Opus on the Claude API. Plan and general-purpose inherit as well.

"Subagents are basically free" was true once. It is not true now. On an
Opus session, an unpinned background search agent is an Opus agent.

Before this matrix landed, six agents in this repository had no `model:`
field at all and seven pinned the dated ID `claude-sonnet-4-6`. Nothing
declared `effort`.

## Tier definitions

The tier vocabulary matches
`plugins/egregore/skills/summon/modules/model-routing.md`, which routes
pipeline steps by the same three tiers.

| Tier | Alias | Effort | Task shape | Relative cost |
|------|-------|--------|------------|---------------|
| Lightweight | `haiku` | `low` | Mechanical, single-turn, deterministic output | ~1x |
| Standard | `sonnet` | `medium` | Judgment inside established patterns | ~3x |
| Deep | `opus` | `high` | Architecture, adversarial reasoning, orchestration | ~10x |

`inherit` is not an accepted value. It is the default this matrix exists
to eliminate, so accepting it explicitly would defeat the gate.

## Placement rules

An agent belongs in **Lightweight** when all of these hold:

- The output shape is fixed and checkable (a list, a diff, a JSON blob).
- The task completes in one pass with no branching judgment.
- A wrong answer is obvious rather than subtle.

An agent belongs in **Deep** when any of these hold:

- It makes a decision that is expensive to reverse (architecture, schema,
  security posture).
- It reasons adversarially against an opponent that adapts (audits,
  refutation, hardening).
- It orchestrates other agents and must judge their output.
- Its whole value is divergent or analogical thinking.

Everything else is **Standard**. Standard is the floor for anything
involving judgment, which is the deliberate bias of this matrix: review
work that misses a subtle finding costs more than the tokens it saved.

## Roster

### Lightweight (`haiku` / `low`)

| Agent | Why |
|-------|-----|
| `abstract:plugin-validator` | Schema validation against a fixed manifest spec |
| `conserve:context-optimizer` | Token counting and threshold comparison |
| `egregore:sentinel` | Budget check, returns a status signal |
| `memory-palace:knowledge-navigator` | Lookup and retrieval from an existing index |
| `parseltongue:python-linter` | Applies ruff rules, output is machine-checked |
| `sanctum:commit-agent` | Formats a conventional commit from a staged diff |
| `sanctum:git-workspace-agent` | Read-only git state reporting |
| `scry:media-recorder` | Executes VHS and Playwright scripts, no judgment |
| `tome:code-searcher` | GitHub search returning repo metadata and ranking |
| `tome:discourse-scanner` | Scrapes discussion threads into a fixed schema |

### Standard (`sonnet` / `medium`)

| Agent | Why |
|-------|-----|
| `abstract:insight-engine` | Pattern analysis over logs against known categories |
| `abstract:skill-auditor` | Quality scoring against a documented rubric |
| `abstract:skill-evaluator` | Rubric application, not rubric design |
| `attune:project-implementer` | Executes an already-designed plan |
| `cartograph:codebase-explorer` | Structural extraction into a JSON model |
| `conserve:ai-hygiene-auditor` | Detects known slop and vibe-coding signatures |
| `conserve:bloat-auditor` | Runs tiered scans, ranks by documented heuristics |
| `conserve:unbloat-remediator` | Applies approved deletions with rollback |
| `gauntlet:extractor` | AST extraction plus enrichment against a schema |
| `memory-palace:garden-curator` | Maintenance against health metrics |
| `memory-palace:knowledge-librarian` | Scores and routes resources by fixed criteria |
| `parseltongue:python-optimizer` | Profiling and bottleneck fixes within known patterns |
| `parseltongue:python-pro` | Idiomatic Python inside established conventions |
| `parseltongue:python-tester` | Test generation follows existing implementation |
| `pensive:blast-radius-reviewer` | Graph-driven review with the graph as the hard input |
| `pensive:code-refiner` | Improvement within existing patterns |
| `pensive:code-reviewer` | Pattern matching against review criteria |
| `phantom:desktop-pilot` | Executes GUI steps, vision-driven but procedural |
| `sanctum:dependency-updater` | Version resolution against declared constraints |
| `sanctum:pr-agent` | Summarization, formatting, gate execution |
| `sanctum:workflow-improvement-analysis-agent` | Generates options against a template |
| `sanctum:workflow-improvement-implementer-agent` | Applies an agreed plan |
| `sanctum:workflow-improvement-planner-agent` | Converges on a plan from scored options |
| `sanctum:workflow-improvement-validator-agent` | Runs targeted validation, compares metrics |
| `sanctum:workflow-recreate-agent` | Reconstructs a session slice from context |
| `scribe:craft-reviewer` | Scores against five documented craft dimensions |
| `scribe:doc-editor` | Editing against a style profile |
| `scribe:doc-verifier` | Claim verification with proof-of-work evidence |
| `scribe:prose-reviewer` | Matches text against a voice register |
| `scribe:slop-hunter` | Pattern detection from `data/languages/en.yaml` |
| `spec-kit:implementation-executor` | Executes tasks the plan already ordered |
| `spec-kit:task-generator` | Dependency ordering from existing artifacts |
| `tome:literature-reviewer` | Paper search plus findings extraction |
| `tome:research` | Dispatches channel agents and formats the report |

### Deep (`opus` / `high`)

| Agent | Why |
|-------|-----|
| `abstract:meta-architect` | Skill-graph and modularization architecture |
| `abstract:skill-improver` | Causal hypotheses about why a skill underperforms |
| `attune:project-architect` | Technology selection, expensive to reverse |
| `conserve:continuation-agent` | Inherits arbitrary parent work at any complexity |
| `egregore:orchestrator` | Runs the full lifecycle and judges every stage |
| `imbue:review-analyst` | Evidence trails that must survive adversarial reading |
| `memory-palace:palace-architect` | Spatial knowledge architecture, creative design |
| `pensive:architecture-reviewer` | ADR compliance and coupling, expensive to reverse |
| `pensive:harden-orchestrator` | Security synthesis across per-area scans |
| `pensive:rust-auditor` | Unsafe blocks, ownership, and concurrency reasoning |
| `spec-kit:spec-analyzer` | Finds the requirement that is missing, not present |
| `tome:triz-analyst` | Cross-domain analogical reasoning, the definition of divergent |

## Notable placements

**`conserve:continuation-agent` is Deep despite doing no design work.**
It picks up whatever the parent was doing when context ran out. Its
ceiling has to be the parent's ceiling or the handoff degrades the work
mid-task.

**`spec-kit:implementation-executor` and `task-generator` moved down from
Deep to Standard.** Both consume artifacts that a Deep agent already
produced. Ordering tasks from a finished plan is dependency resolution,
not design. `spec-analyzer` stayed Deep because finding an absent
requirement is a genuinely harder problem than executing a present one.

**`abstract:meta-architect` moved up from Standard to Deep.** It advises
on skill-graph structure and dependency design, which is architecture
work whose mistakes propagate across every plugin that consumes the
advice.

**`tome:code-searcher` and `discourse-scanner` are Lightweight, but
`literature-reviewer` is Standard.** The first two return metadata in a
fixed shape from search results. The third parses PDFs and extracts
findings, which requires reading for meaning rather than filling a schema.

## Enforcement

Two mechanisms keep the matrix honest.

**`scripts/check_agent_model_matrix.py`** enforces three rules. It runs
as a pre-commit hook and as `tests/scripts/test_check_agent_model_matrix.py`
in CI.

| Scope | Rule |
|-------|------|
| `plugins/*/agents/*.md` | Must pin `model` and `effort`, from the documented vocabulary, never a dated ID |
| `plugins/**/SKILL.md` | May omit `model`, but must never pin a dated ID |
| This document | Its roster must name exactly the agents that exist on disk |

The skill rule is deliberately weaker than the agent rule. A skill
spawns no subagent, so omitting `model` carries none of the inheritance
hazard. A dated ID rots either way.

The roster rule makes this document self-enforcing. The guide it
replaced rotted precisely because a hand-maintained agent list had
nothing checking it against reality, and it eventually claimed tiers for
agents that had been retiered years of commits earlier. Adding an agent
without a row here now fails the gate.

This is a hard gate, not a ratchet. The sibling guards
(`check_skill_exit_criteria_drift.py`, `check_skill_graph_drift.py`) cap a
count against a baseline because they have a backlog to burn down. This
one has no backlog: the change that introduced it brought all 56 agents
into compliance, so the illegal state is unrepresentable rather than
merely capped.

**`plugins/abstract/hooks/agent_dispatch_guard.py`** is a PreToolUse hook
matching `Agent|Task`. It denies any dispatch that omits `subagent_type`
and the denial names which tier fits which task shape. Omitting the agent
name is the one path that reaches rung 4 of model resolution regardless
of what the frontmatter says, so the frontmatter gate alone cannot cover
it.

Because the hook's own tests import it as a module, they keep passing
even if the `hooks.json` registration is deleted. A separate test class,
`TestEnforcementIsWired`, asserts that both the pre-commit entry and the
hook registration exist, so removing either fails CI rather than silently
disabling enforcement.

The frontmatter is the single source of truth for which tier an agent
sits in. There is deliberately no parallel machine-readable matrix file
for the validator to diff against: a second copy is a second thing to
drift. This document carries the reasoning and is checked for roster
drift, never consulted for the tier itself.

## Tuning the matrix

Change the `model` and `effort` in the agent's frontmatter, then update
that agent's row and its rationale here. The gate checks the shape of the
frontmatter, not its agreement with this table, so the table never blocks
a retune. It records the reasoning so the next person retuning knows what
they are overriding.

Two escape hatches exist outside the matrix:

- `CLAUDE_CODE_SUBAGENT_MODEL=haiku` forces every subagent down for a
  session, overriding all frontmatter. Useful when quota matters more
  than quality.
- The per-invocation `model` parameter on a single `Agent` call
  overrides that agent's frontmatter for that call only.

## Exit Criteria

- [ ] `python3 scripts/check_agent_model_matrix.py` exits 0
- [ ] Every file under `plugins/*/agents/` declares `model` and `effort`
- [ ] No agent or skill frontmatter contains a dated model ID
- [ ] `agent_dispatch_guard.py` denies an `Agent` call lacking
      `subagent_type` and allows one that names an agent
- [ ] Every agent in the roster above resolves to a file on disk, and
      every agent on disk appears in the roster
- [ ] Removing the pre-commit entry or the `hooks.json` registration
      fails `TestEnforcementIsWired`
